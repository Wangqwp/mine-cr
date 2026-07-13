/**
 * =============================================
 * Lesson 10: 异常处理
 * =============================================
 *
 * 【学习目标】
 * 1. 理解异常的概念和分类
 * 2. 掌握 try-catch-finally
 * 3. 学会使用 throws 声明异常
 * 4. 了解自定义异常
 *
 * 【Java 异常体系】
 *                    Throwable
 *                   /        \
 *              Error         Exception
 *              (严重错误)       (异常)
 *                           /          \
 *                 Checked Exception   RuntimeException
 *                 (编译时异常)         (运行时异常)
 *
 * Error：程序无法处理的严重错误，如 OutOfMemoryError
 * Checked Exception：必须处理（try-catch 或 throws）
 * RuntimeException：可以不处理（数组越界、空指针等）
 */

import java.io.*;
import java.util.Scanner;

public class ExceptionDemo {

    public static void main(String[] args) {

        // ========== 1. 什么是异常 ==========
        System.out.println("=== 异常示例 ===");

        // 以下代码会抛出异常（暂时注释掉以避免程序崩溃）
        // int x = 10 / 0;                    // ArithmeticException
        // int[] arr = new int[3];
        // arr[10] = 5;                        // ArrayIndexOutOfBoundsException
        // String s = null;
        // System.out.println(s.length());     // NullPointerException


        // ========== 2. try-catch 捕获异常 ==========
        System.out.println("\n=== try-catch ===");

        try {
            int result = divide(10, 0);
            System.out.println("结果是：" + result);
        } catch (ArithmeticException e) {
            // e 是异常对象，包含了异常信息
            System.out.println("捕获到异常：" + e.getMessage());
            // e.printStackTrace();  // 打印完整的异常堆栈
        }
        System.out.println("程序继续执行...");


        // ========== 3. 多个 catch 块 ==========
        System.out.println("\n=== 多个 catch ===");

        try {
            processInput("abc");
        } catch (NumberFormatException e) {
            System.out.println("数字格式错误：" + e.getMessage());
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("数组越界：" + e.getMessage());
        } catch (Exception e) {
            // 必须把父类异常放在最后！
            System.out.println("其他异常：" + e.getMessage());
        }


        // ========== 4. finally 块 ==========
        System.out.println("\n=== finally ===");

        // finally 无论是否发生异常都会执行
        // 通常用来释放资源（关闭文件、数据库连接等）

        Scanner scanner = null;
        try {
            scanner = new Scanner(System.in);
            System.out.print("输入一个数字：");
            int num = scanner.nextInt();
            System.out.println("你输入了：" + num);
        } catch (Exception e) {
            System.out.println("输入错误");
        } finally {
            System.out.println("finally 块执行：关闭资源");
            if (scanner != null) {
                scanner.close();
            }
        }


        // ========== 5. try-with-resources（JDK 7+） ==========
        System.out.println("\n=== try-with-resources ===");

        // 自动关闭实现了 AutoCloseable 的资源
        // 不需要手动写 finally 来关闭
        try (BufferedReader reader = new BufferedReader(new FileReader("test.txt"))) {
            String line = reader.readLine();
            System.out.println("读取到：" + line);
        } catch (FileNotFoundException e) {
            System.out.println("文件未找到（这是预期的，因为 test.txt 不存在）");
        } catch (IOException e) {
            System.out.println("IO 错误：" + e.getMessage());
        }
        // reader 会自动关闭！不需要 finally


        // ========== 6. throw 抛出异常 ==========
        System.out.println("\n=== throw 抛出异常 ===");

        try {
            validateAge(-5);
        } catch (IllegalArgumentException e) {
            System.out.println("验证失败：" + e.getMessage());
        }


        // ========== 7. throws 声明异常 ==========
        System.out.println("\n=== throws 声明异常 ===");

        try {
            readFile("data.txt");
        } catch (IOException e) {
            System.out.println("读取文件失败：" + e.getMessage());
        }


        // ========== 8. 自定义异常 ==========
        System.out.println("\n=== 自定义异常 ===");

        try {
            withdraw(100, 200);
        } catch (InsufficientBalanceException e) {
            System.out.println("取款失败：" + e.getMessage());
            System.out.println("余额：" + e.getBalance() + "，需要：" + e.getAmount());
        }


        // ========== 9. finally 与 return 的执行顺序 ==========
        System.out.println("\n=== finally 与 return ===");

        System.out.println("testFinally() 返回：" + testFinally());
        // 虽然 finally 里有 return，但通常不这么写
    }


    // 除法：可能抛出 ArithmeticException
    public static int divide(int a, int b) {
        return a / b;  // 如果 b=0，抛出 ArithmeticException
    }


    // 演示多种异常
    public static void processInput(String input) {
        int num = Integer.parseInt(input);  // NumberFormatException
        int[] arr = new int[num];
        arr[0] = num;  // 如果 num 是 0 没事
    }


    // throw：手动抛出异常
    public static void validateAge(int age) {
        if (age < 0) {
            throw new IllegalArgumentException("年龄不能为负数：" + age);
        }
        if (age > 150) {
            throw new IllegalArgumentException("年龄不合法：" + age);
        }
        System.out.println("年龄 " + age + " 合法");
    }


    // throws：声明可能抛出的异常（调用者必须处理）
    public static String readFile(String filename) throws IOException {
        if (!filename.endsWith(".txt")) {
            throw new IOException("只支持 .txt 文件");
        }
        return "模拟读取文件成功";
    }


    // 自定义异常类（必须继承 Exception 或 RuntimeException）
    // 继承 Exception → Checked Exception（必须处理）
    // 继承 RuntimeException → Unchecked Exception（可以不处理）
    public static class InsufficientBalanceException extends Exception {
        private final double balance;
        private final double amount;

        public InsufficientBalanceException(double balance, double amount) {
            super("余额不足！余额：" + balance + "，需要：" + amount);
            this.balance = balance;
            this.amount = amount;
        }

        public double getBalance() { return balance; }
        public double getAmount() { return amount; }
    }


    // 使用自定义异常
    public static void withdraw(double balance, double amount)
            throws InsufficientBalanceException {
        if (amount > balance) {
            throw new InsufficientBalanceException(balance, amount);
        }
        System.out.println("取款成功：" + amount);
    }


    // finally 与 return：finally 总是在 return 之前执行
    public static int testFinally() {
        try {
            return 1;   // 先执行 finally，再 return
        } catch (Exception e) {
            return 2;
        } finally {
            System.out.println("finally 在 return 之前执行！");
            // return 3;  // 如果 finally 里有 return，会覆盖 try 的 return！
        }
    }
}
/**
 * =============================================
 * 【异常处理要点总结】
 *
 * ★ try-catch-finally
 *   try   → 监控可能出错的代码
 *   catch → 处理特定类型的异常
 *   finally → 无论是否异常都执行（释放资源）
 *
 * ★ throw 与 throws
 *   throw    → 手动抛出一个异常对象
 *   throws   → 在方法声明上告诉调用者"我会抛出这个异常"
 *
 * ★ 异常类型
 *   Checked  (编译时检查) → IOException, SQLException 等
 *   Unchecked (运行时) → NullPointerException, ArrayIndexOutOfBoundsException 等
 *
 * ★ 最佳实践
 *   - 不要用异常控制正常流程
 *   - 捕获异常后要有实际处理，不要空 catch
 *   - 使用 try-with-resources 自动关闭资源
 *   - 自定义异常要提供有意义的信息
 *   - 打印异常堆栈：e.printStackTrace()
 * =============================================
 */
