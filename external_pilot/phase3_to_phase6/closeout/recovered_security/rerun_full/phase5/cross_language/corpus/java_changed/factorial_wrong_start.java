public class FactorialChanged {
    public static long factorial(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be non-negative");
        long result = 1;
        for (int i = 1; i <= n; i++) {  // same result but different iteration count
            result *= i;
        }
        return result;
    }
}
