/**
 * =============================================
 * Lesson 03: 运算符
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握算术、赋值、关系、逻辑运算符
 * 2. 理解自增自减的前置与后置区别
 * 3. 了解位运算符和三元运算符
 * 4. 理解运算符优先级
 */

public class Operators {

    public static void main(String[] args) {

        int a = 10;
        int b = 3;


        // ========== 1. 算术运算符 ==========
        System.out.println("=== 算术运算符 ===");
        System.out.println("a = " + a + ", b = " + b);
        System.out.println("a + b = " + (a + b));  // 加法
        System.out.println("a - b = " + (a - b));  // 减法
        System.out.println("a * b = " + (a * b));  // 乘法
        System.out.println("a / b = " + (a / b));  // 整数除法：结果是 3（不是 3.33！）
        System.out.println("a % b = " + (a % b));  // 取模（余数）：10 ÷ 3 = 3 余 1

        // 如果想得到小数结果，至少有一个操作数要是浮点数
        System.out.println("(double)a / b = " + ((double)a / b));  // 3.333...


        // ========== 2. 自增与自减 ==========
        System.out.println("\n=== 自增 ++ / 自减 -- ===");

        int x = 5;
        System.out.println("初始 x = " + x);

        // 后置自增：先使用当前值，再自增
        System.out.println("x++ = " + (x++));  // 输出 5，然后 x 变成 6
        System.out.println("之后 x = " + x);    // 6

        // 前置自增：先自增，再使用
        System.out.println("++x = " + (++x));  // x 先变成 7，再输出 7
        System.out.println("之后 x = " + x);    // 7

        // 自减同理
        System.out.println("x-- = " + (x--));  // 输出 7，然后 x 变成 6
        System.out.println("之后 x = " + x);    // 6


        // ========== 3. 赋值运算符 ==========
        System.out.println("\n=== 赋值运算符 ===");

        int n = 10;
        n += 5;   // 等价于 n = n + 5
        System.out.println("n += 5  → " + n);  // 15
        n -= 3;   // 等价于 n = n - 3
        System.out.println("n -= 3  → " + n);  // 12
        n *= 2;   // 等价于 n = n * 2
        System.out.println("n *= 2  → " + n);  // 24
        n /= 4;   // 等价于 n = n / 4
        System.out.println("n /= 4  → " + n);  // 6
        n %= 4;   // 等价于 n = n % 4
        System.out.println("n %= 4  → " + n);  // 2


        // ========== 4. 关系运算符（比较） ==========
        System.out.println("\n=== 关系运算符 ===");
        System.out.println("a == b : " + (a == b));  // 等于
        System.out.println("a != b : " + (a != b));  // 不等于
        System.out.println("a > b  : " + (a > b));   // 大于
        System.out.println("a < b  : " + (a < b));   // 小于
        System.out.println("a >= b : " + (a >= b));  // 大于等于
        System.out.println("a <= b : " + (a <= b));  // 小于等于


        // ========== 5. 逻辑运算符 ==========
        System.out.println("\n=== 逻辑运算符 ===");

        boolean t = true;
        boolean f = false;

        System.out.println("true && false : " + (t && f));  // AND：两个都为 true 才为 true
        System.out.println("true || false : " + (t || f));  // OR：一个为 true 就为 true
        System.out.println("!true        : " + (!t));       // NOT：取反

        // 短路特性
        int m = 5;
        boolean result = (m > 10) && (m++ > 0);
        // 因为 m > 10 已经是 false，所以 (m++ > 0) 不会执行！
        System.out.println("短路 AND 后 m = " + m);  // 5，没有自增

        result = (m < 10) || (m++ > 0);
        // 因为 m < 10 已经是 true，所以 (m++ > 0) 不会执行！
        System.out.println("短路 OR 后 m = " + m);   // 5，没有自增


        // ========== 6. 三元运算符（？：） ==========
        System.out.println("\n=== 三元运算符 ===");

        // 语法：条件 ? 表达式1 : 表达式2
        // 条件为 true 返回表达式1，否则返回表达式2
        int score = 85;
        String grade = score >= 60 ? "及格" : "不及格";
        System.out.println("分数 " + score + "：" + grade);

        // 三元运算符可以嵌套（但不建议太复杂）
        String level = score >= 90 ? "优秀"
                     : score >= 80 ? "良好"
                     : score >= 70 ? "中等"
                     : score >= 60 ? "及格"
                     : "不及格";
        System.out.println("等级：" + level);


        // ========== 7. 位运算符（了解即可） ==========
        System.out.println("\n=== 位运算符 ===");
        // 位运算直接操作二进制位
        int p = 5;   // 二进制：0101
        int q = 3;   // 二进制：0011

        System.out.println("p = " + p + " (0101), q = " + q + " (0011)");
        System.out.println("p & q  = " + (p & q));   // AND：0101 & 0011 = 0001 = 1
        System.out.println("p | q  = " + (p | q));   // OR： 0101 | 0011 = 0111 = 7
        System.out.println("p ^ q  = " + (p ^ q));   // XOR：0101 ^ 0011 = 0110 = 6
        System.out.println("~p     = " + (~p));      // NOT：取反（涉及补码，结果是 -6）
        System.out.println("p << 1 = " + (p << 1));  // 左移：0101 << 1 = 1010 = 10（相当于 ×2）
        System.out.println("p >> 1 = " + (p >> 1));  // 右移：0101 >> 1 = 0010 = 2（相当于 ÷2）


        // ========== 8. instanceof 运算符 ==========
        System.out.println("\n=== instanceof 运算符 ===");
        String text = "Hello";
        boolean isString = text instanceof String;  // 判断是否为 String 类型
        System.out.println("\"Hello\" instanceof String: " + isString);  // true

        Object obj = text;  // 向上转型
        System.out.println("obj instanceof String: " + (obj instanceof String));  // true
        System.out.println("obj instanceof Object: " + (obj instanceof Object));  // true
    }
}
/**
 * =============================================
 * 【运算符优先级（从高到低）】
 *
 * 优先级  运算符                         结合性
 * ─────  ────────────                    ─────
 *  1     () [] .                         从左到右
 *  2     ++ -- ~ !                       从右到左
 *  3     * / %                           从左到右
 *  4     + -                             从左到右
 *  5     << >> >>>                       从左到右
 *  6     < <= > >= instanceof            从左到右
 *  7     == !=                           从左到右
 *  8     &                               从左到右
 *  9     ^                               从左到右
 *  10    |                               从左到右
 *  11    &&                              从左到右
 *  12    ||                              从左到右
 *  13    ?:                              从右到左
 *  14    = += -= *= /= %= &= ^= |=       从右到左
 *
 * 记不住的技巧：不确定优先级时加括号 () 总没错！
 * =============================================
 */
