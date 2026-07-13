/**
 * =============================================
 * Lesson 05: 数组
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握数组的声明、创建和初始化
 * 2. 学会遍历和操作数组
 * 3. 理解二维数组
 * 4. 了解 Arrays 工具类的常用方法
 */

import java.util.Arrays;

public class ArraysDemo {

    public static void main(String[] args) {

        // ========== 1. 声明并创建数组 ==========
        System.out.println("=== 一维数组 ===");

        // 方式 1：先声明，再分配空间
        int[] arr1;          // 推荐写法：类型[] 数组名
        arr1 = new int[5];   // 分配 5 个 int 空间，默认值为 0

        // 方式 2：声明的同时分配空间
        int[] arr2 = new int[3];

        // 方式 3：声明并直接初始化（静态初始化）
        int[] arr3 = {10, 20, 30, 40, 50};

        // 方式 4：new + 初始化值
        int[] arr4 = new int[]{1, 2, 3, 4, 5};

        // 数组长度用 length 属性获取（不是方法！）
        System.out.println("arr3 的长度：" + arr3.length);


        // ========== 2. 访问和修改数组元素 ==========
        System.out.println("\n=== 访问与修改 ===");

        int[] scores = new int[5];
        // 索引从 0 开始，到 length-1 结束
        scores[0] = 95;
        scores[1] = 87;
        scores[2] = 78;
        scores[3] = 90;
        scores[4] = 88;
        // scores[5] = 100;  // 错误！索引越界：ArrayIndexOutOfBoundsException

        System.out.println("第一个元素：" + scores[0]);  // 95
        System.out.println("最后一个元素：" + scores[scores.length - 1]);  // 88


        // ========== 3. 遍历数组 ==========
        System.out.println("\n=== 遍历数组 ===");

        // 方式 1：传统 for 循环
        System.out.print("for 循环：");
        for (int i = 0; i < scores.length; i++) {
            System.out.print(scores[i] + " ");
        }
        System.out.println();

        // 方式 2：for-each 增强 for 循环（不需要索引时更简洁）
        System.out.print("for-each：");
        for (int score : scores) {
            System.out.print(score + " ");
        }
        System.out.println();

        // 方式 3：Arrays.toString() 直接打印
        System.out.println("Arrays.toString：" + Arrays.toString(scores));


        // ========== 4. 数组常用操作 ==========
        System.out.println("\n=== 常用操作 ===");

        // 排序
        int[] nums = {38, 27, 43, 3, 9, 82, 10};
        Arrays.sort(nums);  // 快速排序
        System.out.println("排序后：" + Arrays.toString(nums));

        // 二分查找（必须先排序）
        int index = Arrays.binarySearch(nums, 27);
        System.out.println("27 的位置：" + index);

        // 填充
        int[] fillArr = new int[5];
        Arrays.fill(fillArr, 42);
        System.out.println("填充后的数组：" + Arrays.toString(fillArr));

        // 复制
        int[] copy = Arrays.copyOf(scores, scores.length);
        System.out.println("复制数组：" + Arrays.toString(copy));

        // 复制一部分
        int[] partialCopy = Arrays.copyOfRange(scores, 1, 4);  // 从索引 1 到 3
        System.out.println("部分复制（1-3）：" + Arrays.toString(partialCopy));

        // 比较
        System.out.println("两个数组相等吗？" + Arrays.equals(scores, copy));


        // ========== 5. 数组作为方法参数与返回值 ==========
        System.out.println("\n=== 数组传参 ===");
        int[] numbers = {5, 3, 8, 1, 9};
        System.out.println("最大值：" + findMax(numbers));


        // ========== 6. 二维数组 ==========
        System.out.println("\n=== 二维数组 ===");

        // 声明方式：int[行][列]
        int[][] matrix = new int[3][4];  // 3 行 4 列

        // 静态初始化
        int[][] grid = {
            {1, 2, 3},    // 第 0 行
            {4, 5, 6},    // 第 1 行
            {7, 8, 9}     // 第 2 行
        };

        // 访问元素
        System.out.println("grid[1][2] = " + grid[1][2]);  // 第 1 行第 2 列 = 6

        // 遍历二维数组
        System.out.println("二维数组遍历：");
        for (int i = 0; i < grid.length; i++) {
            for (int j = 0; j < grid[i].length; j++) {
                System.out.print(grid[i][j] + " ");
            }
            System.out.println();
        }

        // 锯齿状数组：每行的列数可以不同
        int[][] jagged = new int[3][];
        jagged[0] = new int[]{1, 2};
        jagged[1] = new int[]{3, 4, 5, 6};
        jagged[2] = new int[]{7, 8, 9};
        System.out.println("锯齿数组：");
        for (int[] row : jagged) {
            System.out.println("  行长度 " + row.length + " → " + Arrays.toString(row));
        }


        // ========== 7. main 方法的 args 参数 ==========
        // 运行：java ArraysDemo arg1 arg2 arg3
        System.out.println("\n=== 命令行参数 ===");
        if (args.length > 0) {
            System.out.println("收到了 " + args.length + " 个参数：");
            for (int i = 0; i < args.length; i++) {
                System.out.println("  args[" + i + "] = " + args[i]);
            }
        } else {
            System.out.println("没有传入命令行参数。试试：java ArraysDemo hello world");
        }


        // ========== 8. 多维数组（三维举例） ==========
        System.out.println("\n=== 三维数组 ===");
        int[][][] cube = {
            {{1, 2}, {3, 4}},
            {{5, 6}, {7, 8}}
        };
        System.out.println("cube[0][1][0] = " + cube[0][1][0]);  // 第一个面的第1行第0列 = 3
    }

    // 方法：查找数组中的最大值
    public static int findMax(int[] arr) {
        int max = arr[0];
        for (int num : arr) {
            if (num > max) {
                max = num;
            }
        }
        return max;
    }
}
/**
 * =============================================
 * 【数组要点总结】
 *
 * 1. 数组是固定长度的，创建后长度不能改变
 * 2. 索引从 0 开始，最后一个元素索引是 length - 1
 * 3. 访问越界会抛出 ArrayIndexOutOfBoundsException
 * 4. 数组是引用类型，赋值传递的是地址（引用）
 * 5. 基本类型数组默认值：int=0, double=0.0, boolean=false, char='\u0000'
 * 6. Arrays 工具类提供：sort, binarySearch, fill, copyOf, equals, toString
 * 7. 想用可变长度？后面学 ArrayList
 * =============================================
 */
