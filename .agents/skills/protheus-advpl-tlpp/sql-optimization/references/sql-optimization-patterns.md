# Universal SQL Optimization Patterns

## Query Performance Analysis
```sql
-- RUIM: Padrão ineficiente
SELECT * FROM orders o
WHERE YEAR(o.created_at) = 2024
  AND o.customer_id IN (
      SELECT c.id FROM customers c WHERE c.status = 'active'
  );

-- BOM: Query otimizada com índices
SELECT o.id, o.customer_id, o.total_amount, o.created_at
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE o.created_at >= '2024-01-01' 
  AND o.created_at < '2025-01-01'
  AND c.status = 'active';

-- Índices necessários:
-- CREATE INDEX idx_orders_created_at ON orders(created_at);
-- CREATE INDEX idx_customers_status ON customers(status);
-- CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

## Index Strategy Optimization
```sql
-- RUIM: Índice mal planejado
CREATE INDEX idx_user_data ON users(email, first_name, last_name, created_at);

-- BOM: Índice composto otimizado
CREATE INDEX idx_users_email_created ON users(email, created_at);
CREATE INDEX idx_users_name ON users(last_name, first_name);
CREATE INDEX idx_users_status_created ON users(status, created_at)
WHERE status IS NOT NULL;
```

## Subquery Optimization
```sql
-- RUIM: Subquery correlacionada
SELECT p.product_name, p.price
FROM products p
WHERE p.price > (
    SELECT AVG(price) 
    FROM products p2 
    WHERE p2.category_id = p.category_id
);

-- BOM: Window function
SELECT product_name, price
FROM (
    SELECT product_name, price,
           AVG(price) OVER (PARTITION BY category_id) as avg_category_price
    FROM products
) ranked
WHERE price > avg_category_price;
```