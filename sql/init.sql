-- ============================================
-- SQLAgent 数据库初始化脚本
-- MySQL 容器首次启动时自动执行
-- ============================================

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建示例表 (可根据项目需要修改)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '用户名',
    email VARCHAR(200) COMMENT '邮箱',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '用户ID',
    product_name VARCHAR(200) NOT NULL COMMENT '产品名称',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/paid/shipped/cancelled',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- 插入示例数据
INSERT INTO users (name, email) VALUES
    ('张三', 'zhangsan@example.com'),
    ('李四', 'lisi@example.com'),
    ('王五', 'wangwu@example.com'),
    ('赵六', 'zhaoliu@example.com'),
    ('孙七', 'sunqi@example.com');

INSERT INTO orders (user_id, product_name, amount, status, order_date) VALUES
    (1, '笔记本电脑', 5999.00, 'paid', '2026-07-01 10:00:00'),
    (1, '机械键盘', 399.00, 'paid', '2026-07-15 14:30:00'),
    (2, '显示器', 1999.00, 'shipped', '2026-07-20 09:00:00'),
    (3, 'Python编程书', 79.00, 'paid', '2026-07-22 16:00:00'),
    (2, '鼠标', 149.00, 'cancelled', '2026-07-25 11:00:00'),
    (4, '耳机', 299.00, 'paid', '2026-07-28 08:30:00'),
    (5, '平板电脑', 3499.00, 'paid', '2026-07-30 20:00:00'),
    (3, '数据线', 29.00, 'pending', '2026-08-01 12:00:00');

-- 验证数据
SELECT '初始化完成' AS status, COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS order_count FROM orders;
