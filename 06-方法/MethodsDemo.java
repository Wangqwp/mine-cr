/**
 * =============================================
 * Lesson 06: 方法
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握方法的定义和调用
 * 2. 理解参数传递（值传递）
 * 3. 学会方法重载（Overloading）
 * 4. 了解递归
 */

public class MethodsDemo {

    public static void main(String[] args) {

        // ========== 1. 调用方法 ==========
        System.out.println("=== 方法调用 ===");

        // 调用无参数方法
        sayHello();

        // 调用有参数的方法
        greet("小明");

        // 调用有返回值的方法
        int sum = add(10, 20);
        System.out.println("10 + 20 = " + sum);

        // 方法调用的返回值可以直接使用
        System.out.println("3 + 5 = " + add(3, 5));


        // ========== 2. 方法签名 ==========
        System.out.println("\n=== 方法签名 ===");

        // 方法的"签名" = 方法名 + 参数类型列表
        // 例如：add(int, int) 和 add(double, double) 是不同的方法
        System.out.println("add(int, int): " + add(3, 4));
        System.out.println("add(double, double): " + add(3.5, 4.2));
        System.out.println("add(String, String): " + add("Hello ", "Java"));


        // ========== 3. 方法重载（同一方法名，不同参数） ==========
        System.out.println("\n=== 方法重载 ===");
        System.out.println("sum(2, 3) = " + sum(2, 3));
        System.out.println("sum(2, 3, 4) = " + sum(2, 3, 4));
        System.out.println("sum(1.5, 2.5) = " + sum(1.5, 2.5));


        // ========== 4. 值传递与引用传递 ==========
        System.out.println("\n=== 参数传递 ===");

        // Java 只有值传递！
        int x = 10;
        System.out.println("调用前 x = " + x);
        modifyPrimitive(x);
        System.out.println("调用后 x = " + x);  // 仍然是 10！方法内的修改不影响外部

        // 但对于引用类型，传递的是"引用的副本"，指向同一个对象
        int[] arr = {1, 2, 3};
        System.out.println("调用前 arr[0] = " + arr[0]);
        modifyArray(arr);
        System.out.println("调用后 arr[0] = " + arr[0]);  // 被修改了！

        // ★ 关键区别：基本类型传的是值副本，引用类型传的是引用副本（仍指向同一对象）


        // ========== 5. 可变参数（Varargs） ==========
        System.out.println("\n=== 可变参数 ... ===");
        System.out.println("可变参数求和：");
        System.out.println("  sumVar(1, 2, 3) = " + sumVar(1, 2, 3));
        System.out.println("  sumVar(10, 20, 30, 40, 50) = " + sumVar(10, 20, 30, 40, 50));
        System.out.println("  sumVar() = " + sumVar());  // 也可以传 0 个参数


        // ========== 6. 递归 ==========
        System.out.println("\n=== 递归 ===");

        // 计算 5!（5 的阶乘）= 5 × 4 × 3 × 2 × 1 = 120
        int n = 5;
        int fact = factorial(n);
        System.out.println(n + "! = " + fact);

        // 斐波那契数列
        System.out.println("Fibonacci(10) = " + fibonacci(10));  // 55


        // ========== 7. 方法的返回值与 return ==========
        System.out.println("\n=== return ===");

        printGrade(95);
        printGrade(72);
        printGrade(45);


        // ========== 8. 方法体中的局部变量 ==========
        System.out.println("\n=== 局部变量 ===");

        // 方法内部声明的变量叫"局部变量"
        // 局部变量必须初始化才能使用（不像成员变量有默认值）
        // 局部变量的作用域：从声明处到包含它的代码块结束
        {
            int blockVar = 100;
            System.out.println("代码块内的变量：" + blockVar);
        }
        // System.out.println(blockVar);  // 错误！这里访问不到 blockVar
    }

    // ========== 方法定义格式 ==========
    // 修饰符  返回值类型  方法名(参数列表) {
    //     方法体
    //     return 返回值;  // 如果返回值类型不是 void
    // }

    // 无参数，无返回值
    public static void sayHello() {
        System.out.println("Hello!");
    }

    // 有参数，无返回值
    public static void greet(String name) {
        System.out.println("你好，" + name + "！");
    }

    // 有参数，有返回值
    public static int add(int a, int b) {
        return a + b;
    }

    // 重载：参数类型不同
    public static double add(double a, double b) {
        return a + b;
    }

    // 重载：参数类型不同
    public static String add(String a, String b) {
        return a + b;
    }

    // 重载：参数数量不同
    public static int sum(int a, int b) {
        return a + b;
    }

    public static int sum(int a, int b, int c) {
        return a + b + c;
    }

    public static double sum(double a, double b) {
        return a + b;
    }

    // 演示值传递：基本类型不会被修改
    public static void modifyPrimitive(int value) {
        value = 999;  // 只修改了局部副本，不影响原变量
        System.out.println("  方法内 value = " + value);
    }

    // 演示引用传递：对象内容可以被修改
    public static void modifyArray(int[] array) {
        array[0] = 999;  // 修改了数组的第一个元素
        System.out.println("  方法内 array[0] = " + array[0]);
    }

    // 可变参数：本质上是数组
    // 一个方法只能有一个可变参数，且必须是最后一个参数
    public static int sumVar(int... numbers) {
        int total = 0;
        for (int num : numbers) {
            total += num;
        }
        return total;
    }

    // 递归：阶乘
    // n! = n × (n-1)!
    // 必须有"终止条件"来结束递归
    public static int factorial(int n) {
        if (n <= 1) {          // 终止条件（基准情况）
            return 1;
        }
        return n * factorial(n - 1);  // 递归调用
    }

    // 递归：斐波那契数列
    // f(0)=0, f(1)=1, f(n)=f(n-1)+f(n-2)
    public static int fibonacci(int n) {
        if (n <= 1) {
            return n;
        }
        return fibonacci(n - 1) + fibonacci(n - 2);
    }

    // 多个 return 分支
    public static void printGrade(int score) {
        if (score < 0 || score > 100) {
            System.out.println("无效分数");
            return;  // 提前返回
        }

        String grade;
        if (score >= 90) {
            grade = "A";
        } else if (score >= 80) {
            grade = "B";
        } else if (score >= 70) {
            grade = "C";
        } else if (score >= 60) {
            grade = "D";
        } else {
            grade = "F";
        }
        System.out.println("分数 " + score + " → 等级 " + grade);
        // 这里不需要 return，void 方法可以省略 return
    }
}
/**
 * =============================================
 * 【方法要点总结】
 *
 * 1. 方法定义：修饰符 返回值类型 方法名(参数列表) { 方法体 }
 * 2. void 方法不需要 return，可以提前 return;
 * 3. 方法重载：同名不同参（参数类型、数量或顺序不同）
 * 4. Java 只有值传递：基本类型传副本，引用类型传引用副本
 * 5. 可变参数：类型... 参数名，本质上是一个数组
 * 6. 递归必须有终止条件，否则会栈溢出 StackOverflowError
 * 7. 局部变量必须初始化，作用域在花括号内
 * =============================================
 */
