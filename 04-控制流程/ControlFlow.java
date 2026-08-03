/**
 * =============================================
 * Lesson 04: 控制流程（条件 + 循环）
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握 if-else 条件判断
 * 2. 学会 switch 分支结构
 * 3. 理解 for、while、do-while 三种循环
 * 4. 学会 break 和 continue 控制循环
 */

public class ControlFlow {

    public static void main(String[] args) {

        // ========== 1. if-else 条件判断 ==========
        System.out.println("=== if-else 条件判断 ===");

        int score = 85;

        if (score >= 90) {
            System.out.println("优秀！");
        } else if (score >= 80) {
            System.out.println("良好！");
        } else if (score >= 70) {
            System.out.println("中等！");
        } else if (score >= 60) {
            System.out.println("及格！");
        } else {
            System.out.println("不及格，继续加油！");
        }

        // 单行 if 可以省略大括号（但建议总是写大括号，避免出错）
        if (score > 100) System.out.println("分数不可能超过100");

        // 常见陷阱：= 与 == 的区别
        boolean flag = false;
        if (flag = true) {   // 注意！这里是赋值不是比较，结果永远是 true
            System.out.println("这是赋值操作，不是比较！");
        }
        // 上面的写法是 Java 允许的，但通常是 bug


        // ========== 2. switch 分支 ==========
        System.out.println("\n=== switch 分支 ===");

        int dayOfWeek = 3;  // 1=周一, ..., 7=周日
        String dayName;

        // 传统 switch（支持：byte, short, int, char, String, 枚举）
        switch (dayOfWeek) {
            case 1:
                dayName = "周一";
                break;           // break 跳出 switch，否则会"穿透"到下一个 case
            case 2:
                dayName = "周二";
                break;
            case 3:
                dayName = "周三";
                break;
            case 4:
                dayName = "周四";
                break;
            case 5:
                dayName = "周五";
                break;
            case 6:
            case 7:
                dayName = "周末";
                break;
            default:
                dayName = "无效的星期";
                break;
        }
        System.out.println(dayOfWeek + " → " + dayName);

        // JDK 14+ 增强版 switch（箭头语法，自动 break）
        String weather = switch (dayOfWeek) {
            case 1, 2, 3, 4, 5 -> "工作日，努力工作！";
            case 6, 7          -> "周末，好好休息！";
            default            -> "无效日期";
        };
        System.out.println("天气心情：" + weather);

        // yield 可以在箭头右侧写代码块
        String mood = switch (dayOfWeek) {
            case 6 -> {
                System.out.println("今天是周六！");
                yield "开心！";
            }
            case 7 -> {
                System.out.println("明天又要上班了...");
                yield "有点焦虑";
            }
            default -> "平常的一天";
        };
        System.out.println("心情：" + mood);


        // ========== 3. for 循环 ==========
        System.out.println("\n=== for 循环 ===");

        // 语法：for (初始化; 条件; 步进) { 循环体 }
        System.out.print("for 循环 1 到 5：");
        for (int i = 1; i <= 5; i++) {
            System.out.print(i + " ");
        }
        System.out.println();  // 换行

        // 死循环示例（不要运行！）
        // for (;;) { System.out.println("永远执行"); }

        // 用逗号在 for 中声明多个变量
        for (int i = 0, j = 10; i < j; i++, j--) {
            System.out.println("i = " + i + ", j = " + j);
        }


        // ========== 4. while 循环 ==========
        System.out.println("\n=== while 循环 ===");

        // 先判断条件，再执行循环体
        int count = 1;
        while (count <= 5) {
            System.out.print(count + " ");
            count++;
        }
        System.out.println();


        // ========== 5. do-while 循环 ==========
        System.out.println("\n=== do-while 循环 ===");

        // 无论条件是否满足，至少执行一次循环体
        int num = 1;
        do {
            System.out.print(num + " ");
            num++;
        } while (num <= 5);
        System.out.println();

        // do-while 特点：即使条件不满足也会执行一次
        int value = 100;
        do {
            System.out.println("虽然条件不满足，但我还是执行了一次！");
        } while (value < 10);  // 条件为 false，但已执行过一次


        // ========== 6. break 与 continue ==========
        System.out.println("\n=== break 与 continue ===");

        // break：立即跳出整个循环
        System.out.print("break 示例（找到 3 就停）：");
        for (int i = 1; i <= 10; i++) {
            if (i == 3) {
                break;  // 当 i=3 时跳出循环
            }
            System.out.print(i + " ");
        }
        System.out.println();

        // continue：跳过本次循环的剩余部分，进入下一次迭代
        System.out.print("continue 示例（跳过偶数）：");
        for (int i = 1; i <= 10; i++) {
            if (i % 2 == 0) {
                continue;  // 偶数跳到下一次循环
            }
            System.out.print(i + " ");
        }
        System.out.println();


        // ========== 7. 带标签的 break/continue ==========
        System.out.println("\n=== 带标签的 break（跳出多重循环） ===");

        outerLoop:      // 标签，可以随便取名
        for (int i = 1; i <= 3; i++) {
            for (int j = 1; j <= 3; j++) {
                if (i == 2 && j == 2) {
                    System.out.println("遇到 (2,2)，跳出整个外层循环！");
                    break outerLoop;  // 跳出标签指定的循环
                }
                System.out.println("(" + i + "," + j + ")");
            }
        }
        System.out.println("循环结束");


        // ========== 8. for-each 增强 for 循环 ==========
        System.out.println("\n=== for-each 循环（遍历数组/集合） ===");

        int[] numbers = {10, 20, 30, 40, 50};
        System.out.print("遍历数组：");
        for (int val : numbers) {
            System.out.print(val + " ");
        }
        System.out.println();


        // ========== 9. 打印乘法口诀表（综合练习） ==========
        System.out.println("\n=== 九九乘法表 ===");
        for (int i = 1; i <= 9; i++) {
            for (int j = 1; j <= i; j++) {
                System.out.printf("%d×%d=%-2d ", j, i, i * j);  // %-2d 左对齐占2位
            }
            System.out.println();  // 每行结束换行
        }
    }
}
/**
 * =============================================
 * 【三种循环对比】
 *
 * for 循环      → 知道循环次数时使用（如遍历数组）
 * while 循环    → 不知道循环次数，只知道条件时使用
 * do-while 循环 → 至少需要执行一次循环体时使用
 *
 * 【注意事项】
 * - 小心死循环：忘记写步进或条件永远为 true
 * - break 只跳出当前一层循环
 * - switch 的每个 case 要写 break，否则会穿透
 * - 增强版 switch（箭头语法）不需要 break
 * =============================================
 */
