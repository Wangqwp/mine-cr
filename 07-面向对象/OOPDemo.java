/**
 * =============================================
 * Lesson 07: 面向对象编程（OOP）基础
 * =============================================
 *
 * 【学习目标】
 * 1. 理解类（class）和对象（object）的概念
 * 2. 学会定义类，创建对象，访问成员
 * 3. 掌握构造方法、this 关键字
 * 4. 理解封装、访问修饰符、getter/setter
 * 5. 了解 static 成员
 *
 * 【面向对象三大特征】
 * ① 封装（Encapsulation） — 把数据和操作数据的方法打包在一起
 * ② 继承（Inheritance）   — 复用现有类的功能（下一课）
 * ③ 多态（Polymorphism）  — 同一操作在不同对象上有不同表现
 */

// ========== 定义一个"类" ==========
// 类就像一张"蓝图"，描述了对象应该有什么属性和行为
class Student {

    // ========== 1. 属性（成员变量 / 字段） ==========

    // 实例变量（每个对象都有自己的副本）
    String name;       // 默认值 null
    int age;           // 默认值 0
    String studentId;  // 默认值 null

    // 访问修饰符：
    // public    → 所有人都可以访问
    // private   → 只有类内部可以访问（推荐！）
    // protected → 子类 + 同包可以访问
    // （不写）   → 默认（包级可见）

    private double score;          // 私有属性，外部不能直接访问
    public static String school = "清华大学";  // 静态属性（属于类，不属于对象）

    // 常量（属于类，不可修改）
    public static final String COUNTRY = "中国";


    // ========== 2. 构造方法 ==========
    // 构造方法名与类名相同，没有返回值
    // 用来初始化新创建的对象

    // 无参构造方法（如果不写，Java 会自动提供一个）
    public Student() {
        System.out.println("调用了无参构造方法");
    }

    // 带参构造方法
    public Student(String name, int age) {
        this.name = name;   // this.name 表示"当前对象的 name 属性"
        this.age = age;     // name 是参数
        System.out.println("调用了带参构造方法");
    }

    // 构造方法重载
    public Student(String name, int age, String studentId) {
        this(name, age);    // this() 调用另一个构造方法（必须写在第一行！）
        this.studentId = studentId;
    }


    // ========== 3. 方法（行为） ==========

    // 实例方法
    public void introduce() {
        System.out.println("大家好，我是 " + name + "，今年 " + age + " 岁");
    }

    public void study(String subject) {
        System.out.println(name + " 正在学习 " + subject);
    }


    // ========== 4. 封装：getter / setter ==========

    // 对私有属性提供公共的访问方法
    public double getScore() {
        return score;
    }

    public void setScore(double score) {
        if (score >= 0 && score <= 100) {
            this.score = score;  // this 区分成员变量和参数
        } else {
            System.out.println("分数必须在 0-100 之间！");
        }
    }

    // 静态方法（属于类，通过类名调用）
    public static void printSchool() {
        System.out.println("学校：" + school);
        // System.out.println(name);  // 错误！静态方法不能访问实例变量
    }


    // ========== 5. toString 方法 ==========
    // 所有类都继承自 Object，可以重写 toString
    @Override  // 注解：告诉编译器这是重写父类方法
    public String toString() {
        return "Student{name='" + name + "', age=" + age + "}";
    }
}


public class OOPDemo {

    public static void main(String[] args) {

        // ========== 1. 创建对象（实例化） ==========
        System.out.println("=== 创建对象 ===");

        // 用 new 关键字创建对象
        // 1. 在堆内存中分配空间
        // 2. 执行构造方法
        // 3. 返回对象的引用（地址）

        Student s1 = new Student();                     // 无参构造
        Student s2 = new Student("小红", 20);           // 带参构造
        Student s3 = new Student("小明", 21, "2024001"); // 3 个参数


        // ========== 2. 访问属性（字段） ==========
        System.out.println("\n=== 访问属性 ===");

        s1.name = "张三";
        s1.age = 22;
        System.out.println(s1.name + " " + s1.age);

        // 静态成员通过类名访问
        System.out.println("学校：" + Student.school);
        System.out.println("国家：" + Student.COUNTRY);
        // 也可以通过对象访问（但不推荐）
        System.out.println("通过对象访问学校：" + s1.school);


        // ========== 3. 调用方法 ==========
        System.out.println("\n=== 调用方法 ===");

        s2.introduce();
        s2.study("Java");
        s3.introduce();


        // ========== 4. 使用 getter/setter ==========
        System.out.println("\n=== 封装 -- setter/getter ===");

        s2.setScore(95.5);
        System.out.println(s2.name + " 的成绩：" + s2.getScore());

        s2.setScore(150);  // 无效值，setter 会拒绝
        System.out.println("尝试设置 150 后：" + s2.getScore());  // 仍然是 95.5


        // ========== 5. toString ==========
        System.out.println("\n=== toString ===");

        System.out.println(s1);  // 自动调用 s1.toString()
        System.out.println(s2);
        System.out.println(s3);


        // ========== 6. 多个对象 ==========
        System.out.println("\n=== 多个对象 ===");

        Student[] classmates = new Student[3];
        classmates[0] = new Student("李四", 19, "2024002");
        classmates[1] = new Student("王五", 20, "2024003");
        classmates[2] = new Student("赵六", 18, "2024004");

        for (Student s : classmates) {
            s.introduce();
        }


        // ========== 7. 静态方法调用 ==========
        System.out.println("\n=== 静态方法 ===");
        Student.printSchool();


        // ========== 8. = 与 equals 的区别 ==========
        System.out.println("\n=== 比较对象 ===");

        Student a = new Student("测试", 18);
        Student b = new Student("测试", 18);
        Student c = a;

        System.out.println("a == b：" + (a == b));        // false（不同对象的引用）
        System.out.println("a == c：" + (a == c));        // true（指向同一对象）
        // System.out.println("a.equals(b)：" + a.equals(b));  // 默认也是比较引用，除非重写


        // ========== 9. 匿名对象 ==========
        System.out.println("\n=== 匿名对象 ===");

        // 不赋值给变量，直接使用
        new Student("匿名", 0).introduce();
        // 匿名对象只能用一次，之后就无法访问了
    }
}
/**
 * =============================================
 * 【面向对象要点总结】
 *
 * ★ 类和对象的关系
 *   类 = 图纸（定义属性和行为）
 *   对象 = 根据图纸造出来的实物
 *
 * ★ 创建对象
 *   Student s = new Student();
 *   └──类型──┘ └──调用构造方法──┘
 *   └───── 引用 ──────────┘     └──── 实际对象 ────┘
 *
 * ★ new 关键字做了什么
 *   ① 在堆中分配内存
 *   ② 初始化属性为默认值
 *   ③ 执行构造方法
 *   ④ 返回对象引用
 *
 * ★ 封装原则
 *   - 属性用 private 隐藏
 *   - 通过 public getter/setter 访问
 *   - setter 中可以加入校验逻辑
 *
 * ★ static 关键字
 *   - 静态成员属于类，所有对象共享
 *   - 静态方法只能访问静态成员
 *   - 通过"类名."调用
 *
 * ★ this 关键字
 *   - 指向当前对象
 *   - 用来区分成员变量和参数
 *   - this() 调用另一个构造方法
 * =============================================
 */
