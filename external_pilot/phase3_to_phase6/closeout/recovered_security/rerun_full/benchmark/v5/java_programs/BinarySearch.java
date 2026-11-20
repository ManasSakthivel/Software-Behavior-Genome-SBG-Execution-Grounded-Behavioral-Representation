/**
 * BinarySearch.java — Binary search with print-based trace instrumentation.
 *
 * Behavioral Specification: matches p03_binary_search.py
 *   Input:  line 1 = space-separated sorted integers
 *           line 2 = integer target
 *   Output: index (0-based) of target, or -1 if not found
 *
 * Trace instrumentation: ENTER/EXIT events written to stderr.
 */
public class BinarySearch {

    static int callDepth = 0;

    /**
     * Binary search on a sorted int array.
     * Returns the index of target, or -1 if absent.
     */
    public static int search(int[] arr, int target) {
        callDepth++;
        System.err.println("TRACE ENTER " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
        try {
            int low = 0;
            int high = arr.length - 1;
            while (low <= high) {
                int mid = (low + high) / 2;
                if (arr[mid] == target) {
                    return mid;
                } else if (arr[mid] < target) {
                    low = mid + 1;
                } else {
                    high = mid - 1;
                }
            }
            return -1;
        } finally {
            System.err.println("TRACE EXIT " + Thread.currentThread().getStackTrace()[1].getMethodName() + " depth=" + callDepth);
            callDepth--;
        }
    }

    static int[] parseIntArray(String line) {
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

        String line1 = reader.readLine();
        String line2 = reader.readLine();
        if (line1 == null) line1 = "";
        if (line2 == null) line2 = "0";

        int[] arr = parseIntArray(line1);
        int target = Integer.parseInt(line2.trim());

        int result = search(arr, target);
        System.out.println(result);
    }
}
