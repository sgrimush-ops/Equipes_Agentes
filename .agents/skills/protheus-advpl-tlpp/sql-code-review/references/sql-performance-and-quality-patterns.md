# SQL Performance & Quality Patterns

## Query Structure Analysis

```sql
-- RUIM: Padrão ineficiente
SELECT DISTINCT u.* 
FROM users u, orders o, products p
WHERE u.id = o.user_id 
AND o.product_id = p.id
AND YEAR(o.order_date) = 2024;

-- BOM: Estrutura otimizada
SELECT u.id, u.name, u.email
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.order_date >= '2024-01-01' 
AND o.order_date < '2025-01-01';
```

## Index Strategy Review
- Falta de índices
- Índices redundantes
- Índices compostos
- Manutenção de índices

## Join Optimization
- Tipos de join
- Ordem dos joins
- Produtos cartesianos
- Subquery vs JOIN

## Aggregate and Window Functions

```sql
-- RUIM: Agregação ineficiente
SELECT user_id, 
       (SELECT COUNT(*) FROM orders o2 WHERE o2.user_id = o1.user_id) as order_count
FROM orders o1
GROUP BY user_id;

-- BOM: Agregação eficiente
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id;
```

---

## Code Quality & Maintainability

### SQL Style & Formatting

```sql
-- RUIM: Formatação ruim
select u.id,u.name,o.total from users u left join orders o on u.id=o.user_id where u.status='active' and o.order_date>='2024-01-01';

-- BOM: Formatação limpa e legível
SELECT u.id, u.name, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
  AND o.order_date >= '2024-01-01';
```