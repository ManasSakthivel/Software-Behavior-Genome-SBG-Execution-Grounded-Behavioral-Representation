public class Fibonacci {
    public static long fibonacci(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be non-negative");
        if (n == 0) return 0;
        long a = 0, b = 1;
        for (int i = 1; i < n; i++) {
            long temp = b;
            b = a + b;
            a = temp;
        }
        return b;
    }
}
