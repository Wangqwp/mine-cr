/**
 * =============================================
 * Lesson 08: 继承（Inheritance）与多态（Polymorphism）
 * =============================================
 *
 * 【学习目标】
 * 1. 掌握继承（extends）的基本写法
 * 2. 理解方法重写（Override）
 * 3. 理解多态：父类引用指向子类对象
 * 4. 了解 abstract 抽象类和 final 关键字
 * 5. 了解 super 关键字
 */

// ========== 父类（基类 / 超类） ==========

/**
 * 动物类 — 所有动物的基类
 *
 * abstract 表示这个类是"抽象的"：
 * - 抽象类不能直接 new（不能实例化）
 * - 抽象类可以包含抽象方法（只有声明，没有实现）
 * - 子类必须实现所有的抽象方法（除非子类也是抽象类）
 */
abstract class Animal {

    // 父类的属性
    protected String name;  // protected：子类可以访问
    protected int age;

    // 构造方法
    public Animal(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // 普通方法（有实现）
    public void sleep() {
        System.out.println(name + " 在睡觉... Zzz...");
    }

    // 抽象方法（没有方法体，子类必须实现）
    public abstract void makeSound();

    // 抽象方法
    public abstract void move();

    // 公共的 getter
    public String getName() {
        return name;
    }
}


// ========== 子类：狗 ==========
class Dog extends Animal {

    // 子类特有的属性
    private String breed;  // 品种

    // 子类构造方法
    public Dog(String name, int age, String breed) {
        super(name, age);   // super() → 调用父类的构造方法（必须是第一行！）
        this.breed = breed;
    }

    // 重写（Override）：子类重新实现父类的方法
    // @Override 注解：检查是否真的在重写
    @Override
    public void makeSound() {
        System.out.println(name + "（" + breed + "）：汪汪！");
    }

    @Override
    public void move() {
        System.out.println(name + " 四条腿奔跑 🐕");
    }

    // 子类特有的方法
    public void wagTail() {
        System.out.println(name + " 摇尾巴...");
    }
}


// ========== 子类：猫 ==========
class Cat extends Animal {

    private boolean isIndoor;

    public Cat(String name, int age, boolean isIndoor) {
        super(name, age);
        this.isIndoor = isIndoor;
    }

    @Override
    public void makeSound() {
        System.out.println(name + "：喵～喵～");
    }

    @Override
    public void move() {
        System.out.println(name + " 悄悄地走 🐱");
    }

    // 重写父类的 sleep（super 调用父类版本）
    @Override
    public void sleep() {
        System.out.println(name + " 蜷缩成一团...");
        super.sleep();  // 调用父类的 sleep 方法
    }
}


// ========== 子类：鸟 ==========
class Bird extends Animal {

    public Bird(String name, int age) {
        super(name, age);
    }

    @Override
    public void makeSound() {
        System.out.println(name + "：叽叽喳喳！");
    }

    @Override
    public void move() {
        System.out.println(name + " 展翅飞翔 🐦");
    }
}


// ========== final 关键字演示 ==========

// final 类：不能被继承
final class MathConstants {
    public static final double PI = 3.141592653;
    // final 方法：不能被重写（这里没有演示）
}
// class ExtendedMath extends MathConstants {}  // 编译错误！final 类不能继承


// ========== 主程序 ==========
public class InheritanceDemo {

    public static void main(String[] args) {

        // ========== 1. 基本继承 ==========
        System.out.println("=== 基本继承 ===");

        // Animal a = new Animal("动物", 0);  // 错误！抽象类不能实例化

        Dog dog = new Dog("旺财", 3, "金毛");
        Cat cat = new Cat("咪咪", 2, true);

        // 子类拥有父类的所有非 private 成员
        dog.sleep();         // 继承自 Animal
        dog.makeSound();     // 重写的方法
        dog.wagTail();       // 子类自己的方法

        cat.sleep();
        cat.makeSound();


        // ========== 2. super 关键字 ==========
        System.out.println("\n=== super 关键字 ===");

        // super 可以访问父类的：
        // - 构造方法：super(参数)
        // - 方法：super.方法名()
        // - 属性：super.属性名
        cat.sleep();  // 猫重写了睡眠方法，内部调用了 super.sleep()


        // ========== 3. 多态（Polymorphism） ==========
        System.out.println("\n=== 多态 ===");

        // 父类引用指向子类对象
        // "编译看左边，运行看右边"
        Animal[] animals = new Animal[3];
        animals[0] = new Dog("小黑", 1, "拉布拉多");
        animals[1] = new Cat("小白", 3, false);
        animals[2] = new Bird("小黄", 1);

        for (Animal animal : animals) {
            // 多态：同一行代码，不同类型的对象有不同的行为
            animal.makeSound();  // 运行时决定调用哪个子类的方法
            animal.move();
            System.out.println("---");
        }


        // ========== 4. instanceof 检查类型 ==========
        System.out.println("=== instanceof ===");

        Animal someAnimal = animals[0];  // 实际是 Dog

        if (someAnimal instanceof Dog) {
            Dog d = (Dog) someAnimal;    // 向下转型
            d.wagTail();                  // 调用 Dog 特有的方法
        }

        // 模式匹配 instanceof（JDK 16+）
        if (someAnimal instanceof Dog d) {
            d.wagTail();  // 不需要手动转型
        }


        // ========== 5. 向上转型与向下转型 ==========
        System.out.println("\n=== 类型转换 ===");

        // 向上转型（隐式转换，安全）
        Animal animal = new Dog("大黄", 4, "中华田园犬");
        animal.sleep();
        animal.makeSound();
        // animal.wagTail();  // 编译错误！Animal 类型没有 wagTail 方法

        // 向下转型（显式转换，可能不安全）
        if (animal instanceof Dog) {
            Dog dog2 = (Dog) animal;  // 强制转换
            dog2.wagTail();          // 可以调用子类特有方法了
        }

        // 错误的转型
        // Cat c = (Cat) animal;  // ClassCastException！animal 实际是 Dog


        // ========== 6. 继承中的构造方法链 ==========
        System.out.println("\n=== 构造方法链 ===");

        // 创建子类对象时，会先执行父类构造方法，再执行子类构造方法
        // 就像搭积木：先搭底层的（父类），再搭上层的（子类）
        System.out.println("创建子类对象：");
        Dog puppy = new Dog("小黄", 1, "柯基");
    }
}
/**
 * =============================================
 * 【继承与多态要点总结】
 *
 * ★ 继承：子类 extends 父类
 *   - 子类自动拥有父类的非 private 成员
 *   - 子类可以扩展新的属性和方法
 *   - Java 单继承：一个类只能有一个直接父类
 *
 * ★ 重写（Override）：子类重新实现父类的方法
 *   - 方法名、参数列表、返回值类型必须相同
 *   - 访问修饰符不能比父类更严格
 *   - @Override 不是必须的，但强烈建议加
 *
 * ★ 多态：父类引用，子类对象
 *   Animal a = new Dog();
 *   a.makeSound();  // 实际调用的是 Dog 的 makeSound
 *
 * ★ super 的用法
 *   - super()：调用父类构造方法
 *   - super.xxx：访问父类的成员
 *
 * ★ abstract 抽象类
 *   - 不能实例化
 *   - 可以包含抽象方法（子类必须实现）
 *   - 也可以包含普通方法
 *
 * ★ final 关键字
 *   - final 类：不能被继承
 *   - final 方法：不能被重写
 *   - final 变量：常量值，不能修改
 *
 * ★ instanceof
 *   - 判断对象的实际类型
 *   - 做向下转型前一定要检查，避免 ClassCastException
 * =============================================
 */
