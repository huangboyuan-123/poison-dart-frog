"""
SQLAgent 基本使用示例。

运行前请确保:
1. 已安装依赖: pip install -e .
2. 已配置 .env 文件中的 API Key
3. 有可用的数据库连接
"""

from sqlagent.agent import SQLAgent
from sqlagent.database import DatabaseManager


def example_01_query():
    """示例 1: 基本查询"""
    print("=" * 60)
    print("示例 1: 基本自然语言查询")
    print("=" * 60)

    agent = SQLAgent(database_url="sqlite:///:memory:")

    # 准备测试数据
    with agent.db.engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, category TEXT)"))
        conn.execute(text("INSERT INTO products VALUES (1, '笔记本电脑', 5999, '电子产品')"))
        conn.execute(text("INSERT INTO products VALUES (2, '机械键盘', 399, '电子产品')"))
        conn.execute(text("INSERT INTO products VALUES (3, 'Python编程书', 79, '图书')"))
        conn.execute(text("INSERT INTO products VALUES (4, '显示器', 1999, '电子产品')"))
        conn.commit()

    # 执行查询
    result = agent.run("电子产品类别中有哪些商品？按价格从高到低排列")
    print(f"回答: {result}")


def example_02_schema():
    """示例 2: 查看数据库结构"""
    print("\n" + "=" * 60)
    print("示例 2: 查看数据库结构")
    print("=" * 60)

    db = DatabaseManager("sqlite:///:memory:")
    with db.engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL)"))
        conn.commit()

    schema = db.get_schema()
    print(schema)


def example_03_custom_config():
    """示例 3: 自定义配置"""
    print("\n" + "=" * 60)
    print("示例 3: 使用自定义配置创建 Agent")
    print("=" * 60)

    agent = SQLAgent(
        database_url="sqlite:///my_custom.db",
        model="gpt-4o-mini",  # 使用更快的模型
        read_only=True,
    )
    print(f"数据库 URL: {agent.database_url}")
    print(f"模型: {agent.model}")
    print(f"只读模式: {agent.read_only}")


def example_04_connection_test():
    """示例 4: 测试连接"""
    print("\n" + "=" * 60)
    print("示例 4: 测试连接状态")
    print("=" * 60)

    agent = SQLAgent(database_url="sqlite:///:memory:")
    results = agent.test_connection()
    for name, status in results.items():
        state = "✅ 正常" if status else "❌ 失败"
        print(f"  {name}: {state}")


if __name__ == "__main__":
    example_01_query()
    example_02_schema()
    example_03_custom_config()
    example_04_connection_test()
