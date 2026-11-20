import com.sun.jdi.*;
import com.sun.jdi.connect.*;
import com.sun.jdi.event.*;
import com.sun.jdi.request.*;

import java.io.*;
import java.util.*;

/**
 * SBG Java tracer: the JDI counterpart of sbg/extraction/dynamic/tracer.py.
 *
 * Emits, for code in package java_programs only, the four sys.settrace event
 * kinds the SBG genomes consume -- call, line, return, exception -- each with
 * the enclosing method name, the source line and a snapshot of the frame's
 * locals rendered in Python repr style (capped at 100 characters). Harness code
 * (package sbgharness) and the Java class library are opaque, as the SBG
 * harness and C-implemented builtins are opaque to sys.settrace.
 *
 * The traced program's stdout and stderr are drained and discarded unread.
 *
 * Usage: SbgJdiTracer <classpath> <harness-class> <start> <total> <maxEvents>
 *                     <timeoutMs> <perEventMs>
 * Output: one JSON object per trace on stdout.
 */
public class SbgJdiTracer {
    static final String PKG = "java_programs.";
    static final String MARKER = "sbgharness.SbgMarker";

    static PrintStream out;
    static int maxEvents;
    static long timeoutMs;
    static double perEventMs;

    // per-trace state
    static boolean inTrace = false;
    static boolean recording = false;
    static int traceIdx = -1;
    static long traceStart;
    static StringBuilder events;
    static int nEvents;
    static boolean truncated;
    static String exception;
    static TreeSet<Integer> coverage;
    // frame depth -> {method key, line, codeIndex}
    static Map<Integer, long[]> lastLine = new HashMap<>();
    static Map<Integer, String> lastMethod = new HashMap<>();
    // Frame depth -> method, for frames already reported as unwound by an
    // exception, so a late method-exit event for them is not double-counted.
    static Map<Integer, String> closedByException = new HashMap<>();

    static List<EventRequest> programRequests = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        out = new PrintStream(new FileOutputStream(FileDescriptor.out), true, "UTF-8");
        String cp = args[0];
        String harness = args[1];
        int start = Integer.parseInt(args[2]);
        int total = Integer.parseInt(args[3]);
        maxEvents = Integer.parseInt(args[4]);
        timeoutMs = Long.parseLong(args[5]);
        perEventMs = Double.parseDouble(args[6]);

        LaunchingConnector lc = Bootstrap.virtualMachineManager().defaultConnector();
        Map<String, Connector.Argument> ca = lc.defaultArguments();
        ca.get("main").setValue(harness + " " + start + " " + total);
        ca.get("options").setValue("-cp " + cp + " -Xss8m -Xmx512m");
        VirtualMachine vm = lc.launch(ca);
        drain(vm.process().getInputStream());
        drain(vm.process().getErrorStream());

        EventRequestManager erm = vm.eventRequestManager();
        ClassPrepareRequest cpr = erm.createClassPrepareRequest();
        cpr.addClassFilter("java_programs.*");
        cpr.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        cpr.enable();
        ClassPrepareRequest cpm = erm.createClassPrepareRequest();
        cpm.addClassFilter(MARKER);
        cpm.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        cpm.enable();

        MethodEntryRequest mer = erm.createMethodEntryRequest();
        mer.addClassFilter("java_programs.*");
        mer.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        MethodExitRequest mxr = erm.createMethodExitRequest();
        mxr.addClassFilter("java_programs.*");
        mxr.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        ExceptionRequest xr = erm.createExceptionRequest(null, true, true);
        xr.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        programRequests.add(mer);
        programRequests.add(mxr);
        programRequests.add(xr);

        EventQueue q = vm.eventQueue();
        boolean alive = true;
        while (alive) {
            if (inTrace) {
                double budget = timeoutMs + perEventMs * nEvents;
                if (System.nanoTime() / 1e6 - traceStart > budget) {
                    exception = "TimeoutError: execution exceeded budget";
                    emitTrace(true);
                    try { vm.process().destroyForcibly(); } catch (Exception e) { }
                    System.exit(3);
                }
            }
            EventSet es = q.remove(20);
            if (es == null) continue;
            for (Event ev : es) {
                if (ev instanceof VMDeathEvent || ev instanceof VMDisconnectEvent) {
                    alive = false;
                } else if (ev instanceof ClassPrepareEvent) {
                    onClassPrepare((ClassPrepareEvent) ev, erm);
                } else if (ev instanceof BreakpointEvent) {
                    onBreakpoint((BreakpointEvent) ev, erm);
                } else if (ev instanceof MethodEntryEvent) {
                    if (recording) onEntry((MethodEntryEvent) ev);
                } else if (ev instanceof MethodExitEvent) {
                    if (recording) onExit((MethodExitEvent) ev);
                } else if (ev instanceof ExceptionEvent) {
                    if (recording) onException((ExceptionEvent) ev);
                }
            }
            if (alive) es.resume();
        }
        System.exit(0);
    }

    static void drain(InputStream in) {
        Thread t = new Thread(() -> {
            byte[] buf = new byte[8192];
            try { while (in.read(buf) >= 0) { } } catch (IOException e) { }
        });
        t.setDaemon(true);
        t.start();
    }

    static void setProgramRequests(boolean on) {
        for (EventRequest r : programRequests) r.setEnabled(on);
        for (BreakpointRequest r : lineBreakpoints) r.setEnabled(on);
    }

    static List<BreakpointRequest> lineBreakpoints = new ArrayList<>();

    static void onClassPrepare(ClassPrepareEvent e, EventRequestManager erm) {
        ReferenceType rt = e.referenceType();
        if (rt.name().equals(MARKER)) {
            for (Method m : rt.methodsByName("begin")) bp(erm, m, "begin");
            for (Method m : rt.methodsByName("end")) bp(erm, m, "end");
            for (Method m : rt.methodsByName("fail")) bp(erm, m, "fail");
            return;
        }
        for (Method m : rt.methods()) {
            if (m.isAbstract() || m.isNative() || m.name().equals("<clinit>")) continue;
            try {
                for (Location loc : m.allLineLocations()) {
                    BreakpointRequest br = erm.createBreakpointRequest(loc);
                    br.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
                    br.putProperty("kind", "line");
                    br.setEnabled(recording);
                    lineBreakpoints.add(br);
                }
            } catch (AbsentInformationException ex) { }
        }
    }

    static void bp(EventRequestManager erm, Method m, String kind) {
        BreakpointRequest br = erm.createBreakpointRequest(m.location());
        br.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
        br.putProperty("kind", kind);
        br.enable();
    }

    static void onBreakpoint(BreakpointEvent e, EventRequestManager erm) {
        Object kind = e.request().getProperty("kind");
        try {
            if ("begin".equals(kind)) {
                StackFrame f = e.thread().frame(0);
                traceIdx = ((IntegerValue) f.getArgumentValues().get(0)).value();
                inTrace = true;
                recording = true;
                traceStart = (long) (System.nanoTime() / 1e6);
                events = new StringBuilder();
                nEvents = 0;
                truncated = false;
                exception = null;
                coverage = new TreeSet<>();
                lastLine.clear();
                lastMethod.clear();
                closedByException.clear();
                setProgramRequests(true);
            } else if ("fail".equals(kind)) {
                StackFrame f = e.thread().frame(0);
                List<Value> a = f.getArgumentValues();
                String type = a.get(0) == null ? "Throwable" : ((StringReference) a.get(0)).value();
                String msg = a.get(1) == null ? "None" : ((StringReference) a.get(1)).value();
                exception = type + ": " + msg;
            } else if ("end".equals(kind)) {
                setProgramRequests(false);
                recording = false;
                emitTrace(false);
                inTrace = false;
            } else if ("line".equals(kind) && recording) {
                onLine(e);
            }
        } catch (IncompatibleThreadStateException ex) {
            throw new RuntimeException(ex);
        }
    }

    // ------------------------------------------------------------------ events

    static String fname(Method m) {
        String n = m.name();
        if (n.equals("<init>")) return "__init__";
        if (n.startsWith("lambda$")) return "<lambda>";
        return n;
    }

    static boolean isProgram(Location loc) {
        String t = loc.declaringType().name();
        return t.startsWith(PKG);
    }

    static void record(String type, String fn, int line, Map<String, String> snap) {
        if (!recording) return;
        if (nEvents >= maxEvents) {
            truncated = true;
            recording = false;
            setProgramRequests(false);
            return;
        }
        if (nEvents > 0) events.append(',');
        events.append('[').append(json(type)).append(',').append(json(fn)).append(',')
              .append(line).append(",{");
        boolean first = true;
        for (Map.Entry<String, String> en : snap.entrySet()) {
            if (!first) events.append(',');
            first = false;
            events.append(json(en.getKey())).append(':').append(json(en.getValue()));
        }
        events.append("}]");
        nEvents++;
        if (line > 0) coverage.add(line);
    }

    static void onEntry(MethodEntryEvent e) {
        Method m = e.method();
        if (m.name().equals("<clinit>")) return;
        try {
            StackFrame f = e.thread().frame(0);
            int depth = e.thread().frameCount();
            lastLine.remove(depth);
            lastMethod.put(depth, m.toString());
            Map<String, String> snap = new LinkedHashMap<>();
            ObjectReference self = f.thisObject();
            if (self != null) snap.put("self", repr(self, 0));
            try {
                List<LocalVariable> args = m.arguments();
                List<Value> vals = f.getArgumentValues();
                for (int i = 0; i < args.size() && i < vals.size(); i++) {
                    snap.put(args.get(i).name(), repr(vals.get(i), 0));
                }
            } catch (AbsentInformationException ex) { }
            int line = m.location().lineNumber();
            record("call", fname(m), line, snap);
        } catch (IncompatibleThreadStateException ex) {
            throw new RuntimeException(ex);
        }
    }

    static void onLine(BreakpointEvent e) {
        Location loc = e.location();
        try {
            int depth = e.thread().frameCount();
            int line = loc.lineNumber();
            long ci = loc.codeIndex();
            long[] prev = lastLine.get(depth);
            String mkey = loc.method().toString();
            // sys.settrace reports a line when execution reaches a new line or
            // jumps backwards; a second bytecode location further along the
            // same line is not a new line event.
            if (prev != null && mkey.equals(lastMethod.get(depth)) && prev[0] == line && ci > prev[1]) {
                lastLine.put(depth, new long[]{line, ci});
                return;
            }
            lastLine.put(depth, new long[]{line, ci});
            lastMethod.put(depth, mkey);
            record("line", fname(loc.method()), line, locals(e.thread().frame(0)));
        } catch (IncompatibleThreadStateException ex) {
            throw new RuntimeException(ex);
        }
    }

    static void onExit(MethodExitEvent e) {
        Method m = e.method();
        if (m.name().equals("<clinit>")) return;
        try {
            int depth = e.thread().frameCount();
            String closed = closedByException.remove(depth);
            if (closed != null && closed.equals(m.toString())) return;   // already reported
            Map<String, String> snap = locals(e.thread().frame(0));
            record("return", fname(m), e.location().lineNumber(), snap);
            lastLine.remove(depth);
        } catch (IncompatibleThreadStateException ex) {
            throw new RuntimeException(ex);
        }
    }

    /**
     * CPython reports an exception in every frame it passes through: an
     * 'exception' event in the raising frame, a 'return' event as that frame
     * unwinds, then an 'exception' event in the next frame, and so on up to and
     * including the frame that handles it. The JDWP back end does not deliver
     * method-exit events for frames popped by an exception, so the whole
     * sequence is emitted here, at the throw, from the stack and the catch
     * location. Frames of the class library in between are opaque.
     */
    static void onException(ExceptionEvent e) {
        try {
            List<StackFrame> frames = e.thread().frames();
            int p = -1;
            for (int i = 0; i < frames.size(); i++) {
                if (isProgram(frames.get(i).location())) { p = i; break; }
            }
            if (p < 0) return;
            Location cl = e.catchLocation();
            int c = frames.size();
            if (cl != null) {
                for (int i = 0; i < frames.size(); i++) {
                    if (frames.get(i).location().method().equals(cl.method())) { c = i; break; }
                }
            }
            if (c < p) return;                       // handled inside the class library
            int n = frames.size();
            for (int i = p; i <= c && i < n; i++) {
                StackFrame f = frames.get(i);
                Location li = f.location();
                if (!isProgram(li)) continue;
                Map<String, String> snap = locals(f);
                record("exception", fname(li.method()), li.lineNumber(), snap);
                if (i < c) {                         // this frame unwinds
                    record("return", fname(li.method()), li.lineNumber(), snap);
                    int depth = n - i;
                    closedByException.put(depth, li.method().toString());
                    lastLine.remove(depth);
                }
            }
        } catch (IncompatibleThreadStateException ex) {
            throw new RuntimeException(ex);
        }
    }

    // ------------------------------------------------------------------ values

    static Map<String, String> locals(StackFrame f) {
        Map<String, String> snap = new LinkedHashMap<>();
        try {
            ObjectReference self = f.thisObject();
            if (self != null) snap.put("self", repr(self, 0));
            for (LocalVariable v : f.visibleVariables()) {
                snap.put(v.name(), repr(f.getValue(v), 0));
            }
        } catch (AbsentInformationException ex) {
        } catch (Exception ex) { }
        return snap;
    }

    static String cap(String s) { return s.length() > 100 ? s.substring(0, 100) : s; }

    static String repr(Value v, int depth) { return cap(reprRaw(v, depth)); }

    static String pyFloat(double d) {
        if (Double.isNaN(d)) return "nan";
        if (Double.isInfinite(d)) return d > 0 ? "inf" : "-inf";
        return Double.toString(d);
    }

    static String pyStr(String s) {
        String q = (s.indexOf('\'') >= 0 && s.indexOf('"') < 0) ? "\"" : "'";
        StringBuilder b = new StringBuilder(q);
        for (char ch : s.toCharArray()) {
            if (ch == '\\') b.append("\\\\");
            else if (ch == '\n') b.append("\\n");
            else if (ch == '\t') b.append("\\t");
            else if (String.valueOf(ch).equals(q)) b.append('\\').append(ch);
            else b.append(ch);
        }
        return b.append(q).toString();
    }

    static String reprRaw(Value v, int depth) {
        if (v == null) return "None";
        if (v instanceof BooleanValue) return ((BooleanValue) v).value() ? "True" : "False";
        if (v instanceof CharValue) return pyStr(String.valueOf(((CharValue) v).value()));
        if (v instanceof DoubleValue) return pyFloat(((DoubleValue) v).value());
        if (v instanceof FloatValue) return pyFloat(((FloatValue) v).value());
        if (v instanceof PrimitiveValue) return String.valueOf(((PrimitiveValue) v).longValue());
        if (v instanceof StringReference) return pyStr(((StringReference) v).value());
        if (depth > 3) return "[...]";
        if (v instanceof ArrayReference) {
            ArrayReference a = (ArrayReference) v;
            return seq(a.getValues(0, Math.min(a.length(), 40)), a.length(), depth, "[", "]");
        }
        ObjectReference o = (ObjectReference) v;
        String tn = o.referenceType().name();
        try {
            switch (tn) {
                case "java.lang.Integer": case "java.lang.Long": case "java.lang.Short":
                case "java.lang.Byte": case "java.lang.Double": case "java.lang.Float":
                case "java.lang.Boolean": case "java.lang.Character":
                    return reprRaw(field(o, "value"), depth);
                case "java.util.ArrayList": {
                    int size = ((IntegerValue) field(o, "size")).value();
                    ArrayReference data = (ArrayReference) field(o, "elementData");
                    int n = Math.min(size, 40);
                    return seq(n == 0 ? new ArrayList<>() : data.getValues(0, n), size, depth, "[", "]");
                }
                case "java.util.Arrays$ArrayList": {
                    ArrayReference data = (ArrayReference) field(o, "a");
                    return seq(data.getValues(0, Math.min(data.length(), 40)), data.length(), depth, "[", "]");
                }
                case "java.util.LinkedList": case "java.util.ArrayDeque": case "java.util.PriorityQueue":
                case "java.util.Stack": case "java.util.HashMap": case "java.util.LinkedHashMap":
                case "java.util.TreeMap": case "java.util.HashSet": case "java.util.TreeSet":
                    return sizedCollection(o, tn);
                default:
                    return "<" + tn + " object>";
            }
        } catch (Exception ex) {
            return "<" + tn + " object>";
        }
    }

    // Collections whose elements are not read cheaply: render a Python-style
    // literal of the right emptiness and size class. The state genome only
    // abstracts a value to NULL / EMPTY / SINGLETON / MULTI_ELEMENT for
    // collections, so the element text is not what it consumes.
    static String sizedCollection(ObjectReference o, String tn) {
        int size = 0;
        Value s = null;
        if (tn.equals("java.util.HashSet") || tn.equals("java.util.TreeSet")) {
            s = fieldSize((ObjectReference) field(o, tn.equals("java.util.HashSet") ? "map" : "m"));
        } else if (tn.equals("java.util.ArrayDeque")) {
            int h = ((IntegerValue) field(o, "head")).value();
            int t = ((IntegerValue) field(o, "tail")).value();
            int len = ((ArrayReference) field(o, "elements")).length();
            size = ((t - h) % len + len) % len;
        } else if (tn.equals("java.util.Stack")) {
            s = field(o, "elementCount");
        } else {
            s = field(o, "size");
        }
        if (s != null) size = ((IntegerValue) s).value();
        boolean map = tn.endsWith("Map");
        boolean set = tn.endsWith("Set");
        String open = (map || set) ? "{" : "[";
        String close = (map || set) ? "}" : "]";
        if (size == 0) return set ? "set()" : open + close;
        StringBuilder b = new StringBuilder(open);
        for (int i = 0; i < size && b.length() < 110; i++) {
            if (i > 0) b.append(", ");
            b.append(map ? "0: 0" : "0");
        }
        return b.append(close).toString();
    }

    static Value fieldSize(ObjectReference m) {
        if (m == null) return null;
        return field(m, "size");
    }

    static Value field(ObjectReference o, String name) {
        Field f = o.referenceType().fieldByName(name);
        return f == null ? null : o.getValue(f);
    }

    static String seq(List<Value> vals, int len, int depth, String open, String close) {
        StringBuilder b = new StringBuilder(open);
        int i = 0;
        for (Value x : vals) {
            if (i++ > 0) b.append(", ");
            b.append(reprRaw(x, depth + 1));
            if (b.length() > 110) break;
        }
        return b.append(close).toString();
    }

    static String json(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char ch : s.toCharArray()) {
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < 0x20) b.append(String.format("\\u%04x", (int) ch));
            else b.append(ch);
        }
        return b.append('"').toString();
    }

    static void emitTrace(boolean timedOut) {
        StringBuilder b = new StringBuilder();
        b.append("{\"idx\":").append(traceIdx)
         .append(",\"timed_out\":").append(timedOut)
         .append(",\"truncated\":").append(truncated)
         .append(",\"exception\":").append(exception == null ? "null" : json(exception))
         .append(",\"elapsed_ms\":").append((long) (System.nanoTime() / 1e6) - traceStart)
         .append(",\"coverage\":").append(coverage.toString().replace(" ", ""))
         .append(",\"events\":[").append(events).append("]}");
        out.println(b);
        out.flush();
    }
}
