# Java 入门学习教程

本教程包含 **12 个课时**，从零开始系统学习 Java。每个文件都是可直接运行的 Java 程序，包含丰富的中文注释和讲解。

---

## 学习路线（建议按顺序）

| 序号 | 目录 | 文件 | 内容 |
|------|------|------|------|
| 01 | `01-基本语法与HelloWorld/` | HelloWorld.java | 第一个程序、类结构、main 方法、注释、输出 |
| 02 | `02-变量与数据类型/` | Variables.java | 8 种基本类型、变量声明、类型转换、常量、var |
| 03 | `03-运算符/` | Operators.java | 算术/赋值/比较/逻辑/位运算、自增自减、三元运算 |
| 04 | `04-控制流程/` | ControlFlow.java | if-else、switch（传统+增强版）、for/while/do-while、break/continue |
| 05 | `05-数组/` | ArraysDemo.java | 一维/二维数组、遍历、Arrays 工具类、命令行参数 |
| 06 | `06-方法/` | MethodsDemo.java | 方法定义、重载、值传递、可变参数、递归 |
| 07 | `07-面向对象/` | OOPDemo.java | 类与对象、构造方法、封装、getter/setter、static、this |
| 08 | `08-继承与多态/` | InheritanceDemo.java | extends、Override、多态、abstract、final、instanceof |
| 09 | `09-接口与内部类/` | InterfaceDemo.java | interface、多实现、默认方法、Lambda、内部类 |
| 10 | `10-异常处理/` | ExceptionDemo.java | try-catch-finally、throw/throws、自定义异常、try-with-resources |
| 11 | `11-常用类/` | StringDemo.java | String 不可变性、StringBuilder、包装类、自动装箱/拆箱 |
| 12 | `12-集合框架/` | CollectionsDemo.java | List/Set/Map、泛型、遍历、Collections 工具类、Stream |

---

## 如何使用

### 编译
打开终端，进入对应目录，运行：
```bash
cd 01-基本语法与HelloWorld
javac HelloWorld.java

# 或者一次性编译所有文件
# javac **/*.java
```

### 运行
```bash
java HelloWorld
```

### 环境要求
- JDK 17+（本教程使用 JDK 26）
- 项目内置了 Oracle JDK 26，路径：`oracleJdk-26/bin/`
- 也可以在命令行设置：
  ```bash
  set JAVA_HOME=%CD%\oracleJdk-26
  set PATH=%JAVA_HOME%\bin;%PATH%
  ```

---

## 学习建议

1. **按顺序学习** — 每一课都建立在前面内容的基础上
2. **边看边改** — 修改代码中的数字、文字，观察输出变化
3. **多编译运行** — 只看不动手是学不会编程的
4. **尝试自己写** — 学完一课，试着写一个类似的程序
5. **查官方文档** — [Java 官方文档](https://docs.oracle.com/en/java/javase/)

---

祝学习愉快！🐱‍👤
