/**
 * =============================================
 * Lesson 11: 常用类 -- String、StringBuilder、包装类
 * =============================================
 *
 * 【学习目标】
 * 1. 熟练掌握 String 类常用方法
 * 2. 理解 String 不可变性（Immutable）
 * 3. 掌握 StringBuilder 的高效字符串操作
 * 4. 了解包装类（Integer, Double 等）和自动装箱/拆箱
 */

import java.util.Arrays;

public class StringDemo {

    public static void main(String[] args) {

        // ========== 1. String 基础 ==========
        System.out.println("=== String 基础 ===");

        String s1 = "Hello";
        String s2 = new String("Hello");
        String s3 = "Hello";

        System.out.println("s1 == s2: " + (s1 == s2));      // false（不同对象）
        System.out.println("s1 == s3: " + (s1 == s3));      // true（常量池复用）
        System.out.println("s1.equals(s2): " + s1.equals(s2));  // true（比较内容）
        // 字符串比较永远用 equals()，不要用 ==

        // ========== 2. String 不可变性 ==========
        System.out.println("\n=== String 不可变性 ===");
        String str = "Hello";
        str.toUpperCase();              // 返回新字符串，原字符串不变！
        System.out.println("原字符串: " + str);  // 仍是 "Hello"
        str = str.toUpperCase();        // 必须把结果赋回去
        System.out.println("修改后: " + str);    // "HELLO"

        String a = "Hello";
        String b = a + " World";
        System.out.println(b);

        // ========== 3. String 常用方法 ==========
        System.out.println("\n=== String 常用方法 ===");
        String text = "  Hello, Java Programming!  ";
        System.out.println("length(): " + text.length());
        System.out.println("trim(): '" + text.trim() + "'");
        System.out.println("charAt(1): '" + text.charAt(1) + "'");
        System.out.println("substring(2, 7): '" + text.substring(2, 7) + "'");
        System.out.println("indexOf('Java'): " + text.indexOf("Java"));
        System.out.println("lastIndexOf('a'): " + text.lastIndexOf('a'));
        System.out.println("contains('Java'): " + text.contains("Java"));
        System.out.println("startsWith('  He'): " + text.startsWith("  He"));
        System.out.println("endsWith('!  '): " + text.endsWith("!  "));
        System.out.println("isEmpty(): " + text.isEmpty());
        System.out.println("isBlank(): " + text.isBlank());
        System.out.println("toUpperCase(): " + text.toUpperCase());
        System.out.println("toLowerCase(): " + text.toLowerCase());
        System.out.println("replace('Java','Python'): " + text.replace("Java","Python"));
        System.out.println("replaceFirst('l','L'): " + text.replaceFirst("l", "L"));

        String csv = "apple,banana,orange,grape";
        String[] fruits = csv.split(",");
        System.out.println("split: " + Arrays.toString(fruits));
        String joined = String.join(" | ", fruits);
        System.out.println("join: " + joined);
        String formatted = String.format("姓名：%s，年龄：%d，分数：%.1f", "小明", 18, 92.5);
        System.out.println("format: " + formatted);

        // ========== 4. StringBuilder（可变字符串，高效拼接） ==========
        System.out.println("\n=== StringBuilder ===");
        StringBuilder sb = new StringBuilder();
        sb.append("Java").append(" is").append(" awesome").append("!");
        System.out.println("sb: " + sb.toString());
        sb.insert(0, "I think ");
        System.out.println("insert: " + sb);
        sb.delete(0, 7);
        System.out.println("delete: " + sb);
        sb.replace(0, 4, "Python");
        System.out.println("replace: " + sb);
        sb.reverse();
        System.out.println("reverse: " + sb);
        sb.reverse();

        // ========== 5. 包装类 ==========
        System.out.println("\n=== 包装类 ===");
        Integer obj1 = Integer.valueOf(42);
        Double  obj2 = Double.valueOf(3.14);
        int val1 = obj1.intValue();
        double val2 = obj2.doubleValue();

        // 自动装箱与拆箱
        Integer autoBoxed = 100;
        int autoUnboxed = autoBoxed;
        System.out.println("自动装箱: " + autoBoxed);
        System.out.println("自动拆箱: " + autoUnboxed);

        // 缓存机制
        Integer x = 127;
        Integer y = 127;
        System.out.println("x == y (127): " + (x == y));  // true（缓存）
        Integer m = 128;
        Integer n = 128;
        System.out.println("m == n (128): " + (m == n));  // false（超出缓存）
        System.out.println("m.equals(n): " + m.equals(n)); // true（比较值）

        // ========== 6. 包装类实用方法 ==========
        System.out.println("\n=== 包装类常用方法 ===");
        int parsed = Integer.parseInt("123");
        double dParsed = Double.parseDouble("3.14");
        System.out.println("parseInt('123'): " + parsed);
        System.out.println("Integer.MAX_VALUE: " + Integer.MAX_VALUE);
        System.out.println("Character.isDigit('5'): " + Character.isDigit('5'));
        System.out.println("Character.isLetter('A'): " + Character.isLetter('A'));
        System.out.println("Character.isWhitespace(' '): " + Character.isWhitespace(' '));
        System.out.println("Character.toUpperCase('a'): " + Character.toUpperCase('a'));

        // ========== 7. String 与基本类型转换 ==========
        System.out.println("\n=== String 与基本类型转换 ===");
        String sv = String.valueOf(123);
        String strDouble = String.valueOf(3.14);
        String strBool = String.valueOf(true);
        System.out.println("valueOf(123): '" + sv + "'");
        System.out.println("strDouble: '" + strDouble + "'");
        System.out.println("strBool: '" + strBool + "'");

        int intFromStr = Integer.parseInt("456");
        double doubleFromStr = Double.parseDouble("7.89");
        boolean boolFromStr = Boolean.parseBoolean("true");
        System.out.println("parseInt('456'): " + intFromStr);
        System.out.println("parseDouble('7.89'): " + doubleFromStr);
        System.out.println("parseBoolean('true'): " + boolFromStr);
    }
}
/**
 * 【要点总结】
 * String 不可变，用 equals() 比较内容
 * StringBuilder 可变，适合大量拼接
 * 包装类支持自动装箱/拆箱，Integer 缓存 -128~127
 * 常用方法：length, substring, indexOf, split, replace
 * StringBuilder: append, insert, delete, reverse
 */
