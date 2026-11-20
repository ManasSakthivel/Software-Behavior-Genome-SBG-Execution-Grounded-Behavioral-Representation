/**
 * LinkedList.java — Singly-linked list with print-based trace instrumentation.
 *
 * Behavioral Specification:
 *   Input:  one command per line — "add X", "remove X", "contains X"
 *   Output: one result line per command
 *           add     → prints nothing (side-effect only)
 *           remove  → "true" or "false"
 *           contains → "true" or "false"
 *
 * Trace instrumentation: ENTER/EXIT events written to stderr.
 */
public class LinkedList {

    static int callDepth = 0;

    // --- Node ---
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }

    static Node head = null;

    // --- List operations ---

    static void add(int val) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            Node newNode = new Node(val);
            if (head == null) {
                head = newNode;
            } else {
                Node cur = head;
                while (cur.next != null) {
                    cur = cur.next;
                }
                cur.next = newNode;
            }
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    static boolean remove(int val) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            if (head == null) return false;
            if (head.val == val) {
                head = head.next;
                return true;
            }
            Node cur = head;
            while (cur.next != null) {
                if (cur.next.val == val) {
                    cur.next = cur.next.next;
                    return true;
                }
                cur = cur.next;
            }
            return false;
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    static boolean contains(int val) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            Node cur = head;
            while (cur != null) {
                if (cur.val == val) return true;
                cur = cur.next;
            }
            return false;
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    public static void main(String[] args) throws Exception {
        java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(System.in));
        String line;
        while ((line = reader.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            String[] parts = line.split("\\s+", 2);
            String cmd = parts[0].toLowerCase();
            int val = parts.length > 1 ? Integer.parseInt(parts[1]) : 0;
            switch (cmd) {
                case "add":
                    add(val);
                    break;
                case "remove":
                    System.out.println(remove(val));
                    break;
                case "contains":
                    System.out.println(contains(val));
                    break;
                default:
                    System.err.println("UNKNOWN COMMAND: " + cmd);
            }
        }
    }
}
