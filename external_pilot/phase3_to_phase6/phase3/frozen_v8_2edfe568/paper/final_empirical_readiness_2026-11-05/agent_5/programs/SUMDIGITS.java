package java_programs;
public class SUMDIGITS {
    public static int sumdigits(int n) {
        int total = 0;
        int m = n < 0 ? -n : n;
        while (m > 0) {
            total += m % 10;
            m = m / 10;
        }
        return total;
    }
}
