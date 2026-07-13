/**
 * Lesson 01: 第一个 Java 程序 — Hello World
 *
 * 学习目标：
 * 1. 理解 Java 程序的基本结构
 * 2. 学会定义类（class）和 main 方法
 * 3. 掌握编译和运行的过程
 * 4. 了解注释的三种写法
 *
 * 核心概念：
 * - 类（class）：Java 程序的基本单位，一切代码都写在类里
 * - main 方法：程序的入口，JVM 从这里开始执行
 * - System.out.println：向控制台输出一行文字
 */

public class HelloWorld {

    // 注释写法1：单行注释，以 // 开头，只在本行有效

    /*
     * 注释写法2：多行注释
     * 以 /* 开始，以紧随其后的 * + / 结束
     * 可以跨越多行，适合写较长的说明
     */

    // 注释写法3：文档注释 /** ... */ （这里不展开，避免嵌套问题）

    /*
     * main 方法是 Java 程序的"大门"。
     * 写法是固定的：
     *   public   -> 访问修饰符，表示任何人都可以调用
     *   static   -> 静态方法，属于类本身，不需要创建对象
     *   void     -> 返回值类型，void 表示不返回任何值
     *   main     -> 方法名，固定写法
     *   String[] args -> 命令行参数
     */
    public static void main(String[] args) {

        // 1. 输出 Hello, World! -- 每个程序员的第一个程序
        System.out.println("Hello, World!");

        // 2. print 不换行 vs println 自动换行
        System.out.print("这是 print，");
        System.out.print("不会换行。");
        System.out.println(" 这是 println，会自动换行。");

        // 3. 格式化输出：printf
        // %s 表示字符串，%d 表示整数，%n 表示换行
        String name = "小明";
        int age = 18;
        System.out.printf("我叫 %s，今年 %d 岁。%n", name, age);
    }
}
/**
 * 动手试一试：
 * 1. javac HelloWorld.java  编译
 * 2. java HelloWorld        运行
 * 3. 试试把 System.out 换成 System.err
 * 4. 修改输出的文字再编译运行
 */
