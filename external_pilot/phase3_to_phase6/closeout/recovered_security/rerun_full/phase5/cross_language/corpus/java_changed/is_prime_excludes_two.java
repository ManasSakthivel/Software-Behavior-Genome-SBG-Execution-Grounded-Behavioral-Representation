public class IsPrimeChanged {
    public static boolean isPrime(int n) {
        if (n < 2) return false;
        if (n % 2 == 0) return false;  // BUG: returns false for n=2
        for (int i = 3; (long) i * i <= n; i += 2) {
            if (n % i == 0) return false;
        }
        return true;
    }
}
