/**
 * =============================================
 * Lesson 09: 接口（Interface）与内部类
 * =============================================
 *
 * 【学习目标】
 * 1. 理解接口的概念和用法
 * 2. 学会实现多个接口（弥补单继承）
 * 3. 了解默认方法（default）和静态方法
 * 4. 了解匿名内部类
 *
 * 【接口 vs 抽象类】
 * 接口：契约，规定了"能做什么"（can-do）
 * 抽象类：模板，规定了"是什么"（is-a）
 */

// ========== 1. 定义接口 ==========
interface Flyable {
    void fly();
    double MAX_SPEED = 1000;

    default void takeOff() {
        System.out.println("正在起飞...");
    }
    default void land() {
        System.out.println("正在降落...");
    }
    static boolean isBirdLike(String type) {
        return "bird".equals(type) || "plane".equals(type);
    }
}

interface Swimmable {
    void swim();
    default void dive() {
        System.out.println("正在潜水...");
    }
}

// ========== 2. 类实现接口 ==========
class Airplane implements Flyable {
    private String name;
    public Airplane(String name) { this.name = name; }

    @Override
    public void fly() {
        System.out.println(name + " 在天空中飞行，速度可达 " + MAX_SPEED + " km/h");
    }
}

// 自包含的 Duck 类（不依赖其他目录）
class Duck implements Flyable, Swimmable {
    private String name;
    private int age;

    public Duck(String name, int age) {
        this.name = name;
        this.age = age;
    }

    @Override
    public void fly() {
        System.out.println(name + " 鸭子飞起来了！");
    }
    @Override
    public void swim() {
        System.out.println(name + " 在水面上游泳");
    }
    @Override
    public void takeOff() {
        System.out.println(name + " 用力拍打翅膀起飞...");
    }
    public void makeSound() {
        System.out.println(name + "：嘎嘎嘎！");
    }
    public void move() {
        System.out.println(name + " 摇摇摆摆地走");
    }
}

// ========== 3. 函数式接口 ==========
@FunctionalInterface
interface Calculator {
    int calculate(int a, int b);
}

// ========== 4. 内部类 ==========
class Outer {
    private String message = "外部类的消息";

    class Inner {
        void display() {
            System.out.println("访问外部类：" + message);
        }
    }

    static class StaticInner {
        void show() {
            System.out.println("静态内部类的方法");
        }
    }

    void localClassDemo() {
        class LocalInner {
            void print() {
                System.out.println("局部内部类，只能在方法内使用");
            }
        }
        new LocalInner().print();
    }

    void lambdaDemo() {
        String localVar = "局部变量";
        Runnable r = new Runnable() {
            @Override
            public void run() {
                System.out.println("匿名内部类访问：" + message + ", " + localVar);
            }
        };
        r.run();
    }
}

public class InterfaceDemo {
    public static void main(String[] args) {
        System.out.println("=== 接口的基本使用 ===");
        Airplane plane = new Airplane("波音 747");
        plane.takeOff();
        plane.fly();
        plane.land();
        System.out.println("isBirdLike(bird): " + Flyable.isBirdLike("bird"));
        System.out.println("MAX_SPEED = " + Flyable.MAX_SPEED);

        System.out.println("\n=== 多接口实现 ===");
        Duck duck = new Duck("唐老鸭", 5);
        duck.makeSound();
        duck.fly();
        duck.swim();
        duck.move();

        System.out.println("\n=== 接口多态 ===");
        Flyable[] flyingThings = {new Airplane("A380"), new Duck("飞天鸭", 2)};
        for (Flyable f : flyingThings) {
            f.takeOff(); f.fly(); f.land();
            System.out.println("---");
        }

        System.out.println("\n=== 匿名内部类 ===");
        Flyable balloon = new Flyable() {
            @Override
            public void fly() {
                System.out.println("热气球在缓缓飘动");
            }
        };
        balloon.takeOff();
        balloon.fly();

        System.out.println("\n=== Lambda 表达式 ===");
        Calculator add = (a, b) -> a + b;
        Calculator multiply = (a, b) -> a * b;
        System.out.println("3 + 5 = " + add.calculate(3, 5));
        System.out.println("3 x 5 = " + multiply.calculate(3, 5));

        System.out.println("\n=== 内部类 ===");
        Outer outer = new Outer();
        Outer.Inner inner = outer.new Inner();
        inner.display();
        Outer.StaticInner staticInner = new Outer.StaticInner();
        staticInner.show();
        outer.localClassDemo();
        outer.lambdaDemo();
    }
}
/**
 * =============================================
 * 【接口与内部类要点总结】
 * 接口：行为契约（can-do），抽象类：模板骨架（is-a）
 * 方法默认 public abstract，属性默认 public static final
 * JDK 8+ 可加 default/static 方法
 * 一个类可以 implements 多个接口
 * 内部类：成员 / 静态 / 局部 / 匿名
 * Lambda 只用于函数式接口（1个抽象方法）
 * =============================================
 */
