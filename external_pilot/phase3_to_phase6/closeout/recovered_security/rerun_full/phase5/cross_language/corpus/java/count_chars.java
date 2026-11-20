import java.util.HashMap;
import java.util.Map;

public class CountChars {
    public static Map<Character, Integer> countChars(String s) {
        Map<Character, Integer> counts = new HashMap<>();
        for (char ch : s.toCharArray()) {
            counts.put(ch, counts.getOrDefault(ch, 0) + 1);
        }
        return counts;
    }
}
