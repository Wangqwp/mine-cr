/**
 * =============================================
 * Lesson 02: 变量与数据类型
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握 Java 的 8 种基本数据类型
 * 2. 学会声明和初始化变量
 * 3. 理解类型转换（自动 vs 强制）
 * 4. 了解 final 常量
 *
 * 【Java 数据类型分类】
 * ┌─ 基本类型（primitive）：存储在栈内存，值本身
 * │   ├─ 整型：byte, short, int, long
 * │   ├─ 浮点：float, double
 * │   ├─ 字符：char
 * │   └─ 布尔：boolean
 * └─ 引用类型（reference）：存储在堆内存，存的是地址
 *     ├─ 类（class）
 *     ├─ 接口（interface）
 *     └─ 数组（array）
 */

public class Variables {

    public static void main(String[] args) {

        // ========== 1. 整型（整数） ==========

        // byte: 1 字节，范围 -128 ~ 127
        byte byteVar = 100;
        System.out.println("byte: " + byteVar);

        // short: 2 字节，范围 -32,768 ~ 32,767
        short shortVar = 30000;
        System.out.println("short: " + shortVar);

        // int: 4 字节（最常用），范围约 ±21 亿
        int intVar = 2_000_000_000;  // 可以用下划线分隔数字，增加可读性
        System.out.println("int: " + intVar);

        // long: 8 字节，后面必须加 L 或 l
        long longVar = 9_000_000_000_000_000_000L;
        System.out.println("long: " + longVar);


        // ========== 2. 浮点型（小数） ==========

        // float: 4 字节，单精度，后面必须加 F 或 f
        float floatVar = 3.14159F;
        System.out.println("float: " + floatVar);

        // double: 8 字节，双精度（默认），更精确
        double doubleVar = 3.141592653589793;
        System.out.println("double: " + doubleVar);


        // ========== 3. 字符型 ==========

        // char: 2 字节，用单引号括起来，只能存一个字符
        char char1 = 'A';
        char char2 = '中';   // Java 使用 Unicode，支持中文
        char char3 = 97;     // 也可以写 ASCII 码，97 对应 'a'
        System.out.println("char1: " + char1);
        System.out.println("char2: " + char2);
        System.out.println("char3 (ASCII 97): " + char3);


        // ========== 4. 布尔型 ==========

        // boolean: 只有两个值 true / false
        boolean isJavaFun = true;
        boolean isHard = false;
        System.out.println("Java 好玩吗？" + isJavaFun);
        System.out.println("难吗？" + isHard);


        // ========== 5. 引用类型：String（字符串） ==========

        // String 是一个类，不是基本类型。用双引号括起来。
        String greeting = "你好，Java！";
        System.out.println(greeting);


        // ========== 6. 类型转换 ==========

        // 自动类型转换（隐式）：小范围 → 大范围
        // byte → short → int → long → float → double
        byte b = 10;
        int i = b;          // byte 自动转成 int
        double d = i;       // int 自动转成 double
        System.out.println("自动转换: byte " + b + " → int " + i + " → double " + d);

        // 强制类型转换（显式）：大范围 → 小范围（可能丢失精度）
        double pi = 3.1415926;
        int piInt = (int) pi;  // 截断小数部分，变成 3
        System.out.println("强制转换: double " + pi + " → int " + piInt);

        // 注意：强制转换可能溢出
        int bigInt = 300;
        byte smallByte = (byte) bigInt;  // 300 超过了 byte 的范围（127），结果会出错
        System.out.println("溢出示例: int 300 → byte " + smallByte);  // 结果是 44


        // ========== 7. final 常量 ==========

        // 用 final 修饰的变量只能赋值一次，之后不能改变
        final double PI = 3.141592653589793;
        // PI = 3.14;  // 这行如果取消注释，会编译报错！
        System.out.println("PI = " + PI);


        // ========== 8. var 关键字（JDK 10+） ==========

        // var 可以让编译器自动推断类型，但变量必须初始化
        var message = "这是 var 声明的字符串";  // 编译器知道这是 String
        var number = 42;                       // 编译器知道这是 int
        // message = 123;  // 不能改变类型！var 一旦确定类型就固定了
        System.out.println(message);
        System.out.println("number is " + number);


        // ========== 9. 字面量写法 ==========
        System.out.println("\n--- 不同进制的整数 ---");
        int decimal = 100;       // 十进制
        int octal = 0144;        // 八进制（以 0 开头）
        int hex = 0x64;          // 十六进制（以 0x 开头）
        int binary = 0b1100100;  // 二进制（以 0b 开头，JDK 7+）
        System.out.println("十进制 100 = " + decimal);
        System.out.println("八进制 0144 = " + octal);
        System.out.println("十六进制 0x64 = " + hex);
        System.out.println("二进制 0b1100100 = " + binary);
    }
}
/**
 * =============================================
 * 【知识要点总结】
 *
 * 基本类型        大小      默认值        范围
 * ───────      ──────    ────────    ─────────────
 * byte           1 字节    0          -128 ~ 127
 * short          2 字节    0          -32,768 ~ 32,767
 * int            4 字节    0          ≈ ±21 亿
 * long           8 字节    0L         巨大
 * float          4 字节    0.0f       约 ±3.4E38
 * double         8 字节    0.0d       约 ±1.8E308
 * char           2 字节    '\u0000'   Unicode 字符
 * boolean        1 位      false      true / false
 *
 * 【变量命名规则】
 * - 可以包含：字母、数字、下划线 _、美元符号 $
 * - 不能以数字开头
 * - 不能是关键字（如 int、class、public 等）
 * - 区分大小写（age 和 Age 是两个不同的变量）
 * - 建议使用驼峰命名：myVariableName
 * =============================================
 */
