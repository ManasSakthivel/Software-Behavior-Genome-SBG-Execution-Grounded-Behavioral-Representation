package java_programs;
public class MAXRUN {
    public static int maxrun(int[] xs) {
        int best = 0;
        int cur = 0;
        for (int i = 0; i < xs.length; i++) {
            if (i > 0 && xs[i] == xs[i - 1]) {
                cur++;
            } else {
                cur = 1;
            }
            if (cur > best) {
                best = cur;
            }
        }
        return best;
    }
}
