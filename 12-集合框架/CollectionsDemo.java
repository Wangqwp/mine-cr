/**
 * =============================================
 * Lesson 12: 集合框架（Collections Framework）
 * =============================================
 *
 * 【学习目标】
 * 1. 理解集合框架的体系结构
 * 2. 掌握 List、Set、Map 的基本用法
 * 3. 学会遍历和操作集合
 * 4. 了解泛型（Generic）
 *
 * 【集合框架体系】
 *
 * ┌── Collection（接口：单列集合）
 * │   ├── List（接口：有序，可重复）
 * │   │   ├── ArrayList（数组实现，查询快）
 * │   │   └── LinkedList（链表实现，增删快）
 * │   ├── Set（接口：无序，不可重复）
 * │   │   ├── HashSet（哈希表，最快）
 * │   │   └── TreeSet（红黑树，有序）
 * │   └── Queue（队列，FIFO）
 * │
 * └── Map（接口：键值对）
 *     ├── HashMap（哈希表，最快）
 *     ├── TreeMap（红黑树，键排序）
 *     └── LinkedHashMap（保持插入顺序）
 */

import java.util.*;
import java.util.stream.Collectors;

public class CollectionsDemo {

    public static void main(String[] args) {

        // ==========================================
        // 0. 泛型简介
        // ==========================================
        System.out.println("=== 泛型（Generic）===");

        // <类型> 指定集合中存储的元素类型
        // 编译时检查类型安全，避免强制类型转换

        // 不使用泛型（不安全）
        List oldList = new ArrayList();
        oldList.add("Hello");
        oldList.add(123);        // 可以添加任意类型！危险
        String str = (String) oldList.get(0);  // 需要强制转型
        // String str2 = (String) oldList.get(1); // 运行时报错！ClassCastException

        // 使用泛型（安全）
        List<String> safeList = new ArrayList<>();
        safeList.add("Hello");
        // safeList.add(123);  // 编译错误！只能添加 String
        String item = safeList.get(0);  // 不需要转型
        System.out.println("泛型让集合类型安全：" + item);


        // ==========================================
        // 1. List（列表）
        // ==========================================
        System.out.println("\n=== List ===");

        // ArrayList：基于数组，查询快，增删慢（尾部增删也快）
        List<String> list = new ArrayList<>();

        // 添加元素
        list.add("Apple");
        list.add("Banana");
        list.add("Cherry");
        list.add("Apple");    // List 允许重复
        System.out.println("添加后：" + list);

        // 指定位置插入
        list.add(1, "Blueberry");
        System.out.println("插入后：" + list);

        // 获取元素
        System.out.println("get(0): " + list.get(0));

        // 修改
        list.set(0, "Avocado");
        System.out.println("修改后：" + list);

        // 删除
        list.remove("Banana");     // 按对象删除（只删除第一个匹配的）
        list.remove(2);            // 按索引删除
        System.out.println("删除后：" + list);

        // 大小
        System.out.println("size: " + list.size());
        System.out.println("contains 'Apple': " + list.contains("Apple"));
        System.out.println("indexOf 'Apple': " + list.indexOf("Apple"));

        // 判断空
        System.out.println("isEmpty: " + list.isEmpty());

        // 清空
        // list.clear();


        // ========== 遍历 List ==========
        System.out.println("\n--- 遍历 List ---");

        list.add("Banana");
        list.add("Date");

        // 方式 1：for-each（最常用）
        System.out.print("for-each: ");
        for (String fruit : list) {
            System.out.print(fruit + " ");
        }
        System.out.println();

        // 方式 2：传统 for + 索引
        System.out.print("for+索引: ");
        for (int i = 0; i < list.size(); i++) {
            System.out.print(list.get(i) + " ");
        }
        System.out.println();

        // 方式 3：迭代器（Iterator）
        System.out.print("Iterator: ");
        Iterator<String> it = list.iterator();
        while (it.hasNext()) {
            System.out.print(it.next() + " ");
        }
        System.out.println();

        // 方式 4：forEach（JDK 8+ Lambda）
        System.out.print("forEach(Lambda): ");
        list.forEach(item2 -> System.out.print(item2 + " "));
        System.out.println();


        // ==========================================
        // 2. Set（集合：不重复）
        // ==========================================
        System.out.println("\n=== Set ===");

        // HashSet：无序，最快（基于 HashMap）
        Set<String> set = new HashSet<>();

        set.add("Java");
        set.add("Python");
        set.add("JavaScript");
        set.add("Java");        // 重复元素不会添加成功

        System.out.println("HashSet: " + set);  // 顺序不确定！
        System.out.println("size: " + set.size());  // 3（"Java" 只存了一次）

        // TreeSet：自动排序
        Set<String> treeSet = new TreeSet<>(set);
        System.out.println("TreeSet（排序后）: " + treeSet);

        // Set 常用操作
        System.out.println("contains 'Java': " + set.contains("Java"));
        set.remove("Python");
        System.out.println("删除后: " + set);

        // 遍历 Set
        System.out.print("遍历 Set: ");
        for (String lang : set) {
            System.out.print(lang + " ");
        }
        System.out.println();


        // ==========================================
        // 3. Map（映射：键值对）
        // ==========================================
        System.out.println("\n=== Map ===");

        // HashMap：基于哈希表，键无序
        Map<String, Integer> scores = new HashMap<>();

        // 添加键值对
        scores.put("小明", 95);
        scores.put("小红", 88);
        scores.put("小刚", 76);
        scores.put("小明", 98);  // 键相同会覆盖旧值

        System.out.println("HashMap: " + scores);

        // 获取
        System.out.println("小明的分数: " + scores.get("小明"));
        System.out.println("小张的分数（不存在）: " + scores.get("小张"));  // null
        System.out.println("小张的分数（带默认值）: " + scores.getOrDefault("小张", 0));

        // 判断
        System.out.println("containsKey: " + scores.containsKey("小红"));
        System.out.println("containsValue: " + scores.containsValue(76));

        // 删除
        scores.remove("小刚");
        System.out.println("删除后: " + scores);

        // 大小
        System.out.println("size: " + scores.size());

        // ========== 遍历 Map ==========
        System.out.println("\n--- 遍历 Map ---");

        // 方式 1：遍历键值对（推荐）
        System.out.println("遍历键值对:");
        for (Map.Entry<String, Integer> entry : scores.entrySet()) {
            System.out.println("  " + entry.getKey() + " → " + entry.getValue());
        }

        // 方式 2：只遍历键
        System.out.print("遍历键: ");
        for (String key : scores.keySet()) {
            System.out.print(key + " ");
        }
        System.out.println();

        // 方式 3：只遍历值
        System.out.print("遍历值: ");
        for (int val : scores.values()) {
            System.out.print(val + " ");
        }
        System.out.println();

        // 方式 4：forEach（JDK 8+）
        System.out.println("forEach(Lambda):");
        scores.forEach((name, score) ->
            System.out.println("  " + name + " → " + score)
        );


        // ==========================================
        // 4. Collections 工具类
        // ==========================================
        System.out.println("\n=== Collections 工具类 ===");

        List<Integer> numbers = new ArrayList<>();
        Collections.addAll(numbers, 5, 3, 8, 1, 9, 2, 7);

        System.out.println("原始: " + numbers);

        Collections.sort(numbers);
        System.out.println("排序: " + numbers);

        Collections.reverse(numbers);
        System.out.println("反转: " + numbers);

        Collections.shuffle(numbers);
        System.out.println("打乱: " + numbers);

        System.out.println("最大值: " + Collections.max(numbers));
        System.out.println("最小值: " + Collections.min(numbers));

        // 创建不可变集合
        List<String> immutable = Collections.unmodifiableList(list);
        // immutable.add("New");  // 运行时报错！UnsupportedOperationException
        System.out.println("不可变集合: " + immutable);


        // ==========================================
        // 5. List.of / Set.of / Map.of（JDK 9+）
        // ==========================================
        System.out.println("\n=== 便捷创建集合 ===");

        List<String> cityList = List.of("北京", "上海", "广州");
        Set<String> citySet = Set.of("北京", "上海", "深圳");
        Map<String, Integer> cityMap = Map.of("北京", 2000, "上海", 2400, "广州", 1500);

        System.out.println("List.of: " + cityList);
        System.out.println("Set.of: " + citySet);
        System.out.println("Map.of: " + cityMap);


        // ==========================================
        // 6. Stream API（JDK 8+）
        // ==========================================
        System.out.println("\n=== Stream 流式操作 ===");

        List<Integer> scores2 = List.of(85, 92, 58, 73, 100, 67, 88);

        // 筛选及格分数，排序，收集
        List<Integer> passed = scores2.stream()
            .filter(s -> s >= 60)           // 过滤
            .sorted()                        // 排序
            .collect(Collectors.toList());   // 收集到 List

        System.out.println("及格分数（升序）: " + passed);

        // 计算平均值
        double avg = scores2.stream()
            .mapToInt(Integer::intValue)
            .average()
            .orElse(0);
        System.out.println("平均分: " + avg);

        // 分组
        Map<String, List<Integer>> grouped = scores2.stream()
            .collect(Collectors.groupingBy(s -> s >= 60 ? "及格" : "不及格"));
        System.out.println("分组: " + grouped);
    }
}
/**
 * =============================================
 * 【集合框架要点总结】
 *
 * ★ 如何选择？
 *   - 需要存多个元素，允许重复 → List
 *     - 查询多，尾部增删多     → ArrayList ✓
 *     - 头尾增删多，中间操作多 → LinkedList
 *   - 需要存多个元素，不允许重复 → Set
 *     - 不需要排序            → HashSet ✓
 *     - 需要自动排序          → TreeSet
 *   - 需要键值对              → Map
 *     - 不需要排序            → HashMap ✓
 *     - 需要按键排序          → TreeMap
 *     - 需要保持插入顺序       → LinkedHashMap
 *
 * ★ 常用方法
 *   List: add, get, set, remove, size, contains, indexOf
 *   Set:  add, remove, contains, size
 *   Map:  put, get, getOrDefault, remove, containsKey, keySet, values, entrySet
 *   Collections: sort, reverse, shuffle, max, min, addAll
 *
 * ★ 遍历方式
 *   1. for-each（最简洁）
 *   2. Iterator（可删元素）
 *   3. forEach(Lambda)（JDK 8+）
 *   4. Stream（JDK 8+ 函数式）
 *
 * ★ 注意
 *   - 泛型：List<String> 指定类型
 *   - 迭代时不能直接修改集合（用 Iterator.remove()）
 *   - hashCode() 和 equals() 影响 HashSet/HashMap 的正确性
 * =============================================
 */
