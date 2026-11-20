/**
 * BubbleSort.java — Bubble sort with print-based trace instrumentation.
 *
 * Behavioral Specification: matches p01_bubble_sort.py
 *   Input:  space-separated integers on stdin
 *   Output: sorted integers on stdout
 *
 * Trace instrumentation: ENTER/EXIT events written to stderr using
 *   System.err.println so they are cleanly separated from program output.
 */
public class BubbleSort {

    // Static call-depth counter shared across all instrumented methods.
    static int callDepth = 0;

    /**
     * Sort arr in-place (ascending bubble sort).
     * Returns the same array for chaining convenience.
     */
    public static int[] sort(int[] arr) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            int n = arr.length;
            for (int i = 0; i < n - 1; i++) {
                for (int j = 0; j < n - 1 - i; j++) {
                    if (arr[j] > arr[j + 1]) {
                        int temp = arr[j];
                        arr[j] = arr[j + 1];
                        arr[j + 1] = temp;
                    }
                }
            }
            return arr;
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    /**
     * Parse stdin: one line of space-separated integers.
     * Empty line → empty array.
     */
    static int[] parseInput(String line) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            line = line.trim();
            if (line.isEmpty()) return new int[0];
            String[] parts = line.split("\\s+");
            int[] arr = new int[parts.length];
            for (int i = 0; i < parts.length; i++) {
                arr[i] = Integer.parseInt(parts[i]);
            }
            return arr;
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    public static void main(String[] args) throws Exception {
        java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(System.in));
        String line = reader.readLine();
        if (line == null) line = "";

        int[] arr = parseInput(line);
        sort(arr);

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(' ');
            sb.append(arr[i]);
        }
        System.out.println(sb.toString());
    }
}
