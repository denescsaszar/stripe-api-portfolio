# SQL Bible — Stripe Sigma & Beyond

A TAM-focused SQL reference covering fundamentals, Stripe Sigma tables, and real-world payment analysis queries.

---

## Part 1: SQL Fundamentals

### SELECT — Retrieving Data

```sql
-- Basic select
SELECT column1, column2 FROM table_name;

-- All columns
SELECT * FROM table_name;

-- With alias
SELECT amount / 100.0 AS amount_eur FROM payments;

-- Distinct values
SELECT DISTINCT currency FROM charges;
```

### WHERE — Filtering Rows

```sql
-- Comparison operators
SELECT * FROM charges WHERE amount > 10000;          -- greater than €100
SELECT * FROM charges WHERE status = 'succeeded';
SELECT * FROM charges WHERE created >= '2026-01-01';

-- Multiple conditions
SELECT * FROM charges
WHERE status = 'failed'
  AND amount > 5000
  AND currency = 'eur';

-- OR conditions
SELECT * FROM charges
WHERE failure_code = 'insufficient_funds'
   OR failure_code = 'card_declined';

-- IN — match any value in a list
SELECT * FROM charges
WHERE failure_code IN ('insufficient_funds', 'card_declined', 'expired_card');

-- NOT IN — exclude values
SELECT * FROM charges
WHERE status NOT IN ('succeeded', 'pending');

-- BETWEEN — range (inclusive)
SELECT * FROM charges
WHERE created BETWEEN '2026-01-01' AND '2026-01-31';

-- LIKE — pattern matching
SELECT * FROM customers
WHERE email LIKE '%@gmail.com';       -- ends with @gmail.com
-- % = any characters, _ = single character

-- IS NULL / IS NOT NULL
SELECT * FROM charges WHERE failure_code IS NOT NULL;
```

### ORDER BY — Sorting Results

```sql
-- Ascending (default)
SELECT * FROM charges ORDER BY created ASC;

-- Descending
SELECT * FROM charges ORDER BY amount DESC;

-- Multiple columns
SELECT * FROM charges ORDER BY status ASC, amount DESC;
```

### LIMIT — Restricting Results

```sql
-- First 10 rows
SELECT * FROM charges ORDER BY created DESC LIMIT 10;

-- Skip first 20, then take 10 (pagination)
SELECT * FROM charges ORDER BY created DESC LIMIT 10 OFFSET 20;
```

### GROUP BY — Aggregation

```sql
-- Count charges by status
SELECT status, COUNT(*) AS total
FROM charges
GROUP BY status;

-- Sum revenue by currency
SELECT currency, SUM(amount) / 100.0 AS total_revenue
FROM charges
WHERE status = 'succeeded'
GROUP BY currency;

-- Average payment amount by country
SELECT card_country, AVG(amount) / 100.0 AS avg_amount
FROM charges
WHERE status = 'succeeded'
GROUP BY card_country
ORDER BY avg_amount DESC;
```

### Aggregate Functions

| Function | What it does | Example |
|----------|-------------|---------|
| `COUNT(*)` | Count all rows | `SELECT COUNT(*) FROM charges` |
| `COUNT(column)` | Count non-NULL values | `COUNT(failure_code)` |
| `COUNT(DISTINCT col)` | Count unique values | `COUNT(DISTINCT customer_id)` |
| `SUM(column)` | Sum values | `SUM(amount) / 100.0` |
| `AVG(column)` | Average | `AVG(amount) / 100.0` |
| `MIN(column)` | Minimum | `MIN(created)` |
| `MAX(column)` | Maximum | `MAX(amount)` |

### HAVING — Filter After Aggregation

```sql
-- Countries with more than 100 charges
SELECT card_country, COUNT(*) AS total
FROM charges
GROUP BY card_country
HAVING COUNT(*) > 100
ORDER BY total DESC;

-- Customers who spent more than €1000
SELECT customer_id, SUM(amount) / 100.0 AS total_spent
FROM charges
WHERE status = 'succeeded'
GROUP BY customer_id
HAVING SUM(amount) > 100000
ORDER BY total_spent DESC;
```

**Remember:** WHERE filters rows BEFORE grouping, HAVING filters AFTER grouping.

### JOIN — Combining Tables

```sql
-- INNER JOIN — only matching rows from both tables
SELECT c.id, c.amount, cu.email
FROM charges c
INNER JOIN customers cu ON c.customer_id = cu.id;

-- LEFT JOIN — all rows from left table, matching from right
SELECT c.id, c.amount, r.id AS refund_id
FROM charges c
LEFT JOIN refunds r ON c.id = r.charge_id;
-- Shows all charges, NULL for refund columns if no refund exists

-- Multiple joins
SELECT c.id, c.amount, cu.email, d.reason
FROM charges c
JOIN customers cu ON c.customer_id = cu.id
LEFT JOIN disputes d ON c.id = d.charge_id;
```

| Join Type | What it returns |
|-----------|----------------|
| `INNER JOIN` | Only rows that match in BOTH tables |
| `LEFT JOIN` | ALL rows from left table + matching right |
| `RIGHT JOIN` | ALL rows from right table + matching left |
| `FULL OUTER JOIN` | ALL rows from both tables |

### Subqueries

```sql
-- Subquery in WHERE
SELECT * FROM charges
WHERE customer_id IN (
    SELECT id FROM customers WHERE email LIKE '%@company.com'
);

-- Subquery as a table (derived table)
SELECT avg_by_country.card_country, avg_by_country.avg_amount
FROM (
    SELECT card_country, AVG(amount) / 100.0 AS avg_amount
    FROM charges
    WHERE status = 'succeeded'
    GROUP BY card_country
) AS avg_by_country
WHERE avg_by_country.avg_amount > 50;
```

### CASE — Conditional Logic

```sql
-- Categorize amounts
SELECT id, amount,
    CASE
        WHEN amount < 5000 THEN 'small'
        WHEN amount < 50000 THEN 'medium'
        ELSE 'large'
    END AS size_category
FROM charges;

-- Categorize decline reasons
SELECT
    CASE
        WHEN failure_code IN ('insufficient_funds', 'card_declined') THEN 'issuer_decline'
        WHEN failure_code IN ('stolen_card', 'fraudulent') THEN 'fraud'
        WHEN failure_code IN ('processing_error', 'try_again') THEN 'temporary'
        ELSE 'other'
    END AS decline_category,
    COUNT(*) AS total
FROM charges
WHERE status = 'failed'
GROUP BY decline_category;
```

### Date Functions

```sql
-- Extract parts of a date
SELECT
    DATE_TRUNC('month', created) AS month,
    COUNT(*) AS total
FROM charges
GROUP BY DATE_TRUNC('month', created)
ORDER BY month;

-- Recent data (last 30 days)
SELECT * FROM charges
WHERE created >= CURRENT_DATE - INTERVAL '30' DAY;

-- Last 7 days
SELECT * FROM charges
WHERE created >= CURRENT_DATE - INTERVAL '7' DAY;

-- Format date
SELECT DATE_FORMAT(created, '%Y-%m-%d') AS date_str FROM charges;
```

### Window Functions (Advanced)

```sql
-- Running total
SELECT id, amount,
    SUM(amount) OVER (ORDER BY created) AS running_total
FROM charges
WHERE status = 'succeeded';

-- Rank by amount
SELECT id, amount,
    RANK() OVER (ORDER BY amount DESC) AS amount_rank
FROM charges;

-- Moving average (7-day)
SELECT
    DATE_TRUNC('day', created) AS day,
    AVG(amount) OVER (
        ORDER BY DATE_TRUNC('day', created)
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM charges;
```

### Common Table Expressions (CTEs)

```sql
-- CTE for readable complex queries
WITH failed_charges AS (
    SELECT card_country, failure_code, COUNT(*) AS fail_count
    FROM charges
    WHERE status = 'failed'
    GROUP BY card_country, failure_code
),
total_charges AS (
    SELECT card_country, COUNT(*) AS total_count
    FROM charges
    GROUP BY card_country
)
SELECT
    f.card_country,
    f.failure_code,
    f.fail_count,
    t.total_count,
    ROUND(f.fail_count * 100.0 / t.total_count, 2) AS fail_pct
FROM failed_charges f
JOIN total_charges t ON f.card_country = t.card_country
ORDER BY fail_pct DESC;
```

---

## Part 2: SQL Query Execution Order

Understanding this prevents 90% of SQL errors:

```
1. FROM / JOIN      <- which tables
2. WHERE            <- filter rows
3. GROUP BY         <- create groups
4. HAVING           <- filter groups
5. SELECT           <- choose columns
6. DISTINCT         <- remove duplicates
7. ORDER BY         <- sort results
8. LIMIT / OFFSET   <- restrict output
```

**Key insight:** You can't use a column alias from SELECT in WHERE (because WHERE runs first). But you CAN use it in ORDER BY (because ORDER BY runs last).

```sql
-- This FAILS:
SELECT amount / 100.0 AS amount_eur FROM charges WHERE amount_eur > 100;

-- This WORKS:
SELECT amount / 100.0 AS amount_eur FROM charges WHERE amount > 10000;

-- This also WORKS (alias in ORDER BY):
SELECT amount / 100.0 AS amount_eur FROM charges ORDER BY amount_eur DESC;
```

---

## Part 3: Stripe Sigma Tables

### Core Tables

| Table | What it contains |
|-------|-----------------|
| `charges` | Every charge (succeeded, failed, refunded) |
| `refunds` | All refunds linked to charges |
| `disputes` | Chargebacks and fraud claims |
| `customers` | Customer objects with email, metadata |
| `payment_intents` | PaymentIntent objects |
| `subscriptions` | Active and canceled subscriptions |
| `invoices` | Billing invoices |
| `balance_transactions` | Every money movement (fees, payouts, refunds) |
| `payouts` | Bank transfer payouts |
| `connected_accounts` | Connect platform accounts |
| `events` | Webhook events |

### Key Columns in `charges`

| Column | Type | Example |
|--------|------|---------|
| `id` | string | `ch_1234abc` |
| `amount` | integer (cents) | `34900` = EUR 349.00 |
| `currency` | string | `eur` |
| `status` | string | `succeeded`, `failed`, `pending` |
| `failure_code` | string | `insufficient_funds`, `card_declined` |
| `failure_message` | string | Human-readable error |
| `created` | timestamp | `2026-01-15 14:30:00` |
| `customer_id` | string | `cus_xyz` |
| `card_brand` | string | `visa`, `mastercard`, `amex` |
| `card_country` | string | `DE`, `US`, `GB` |
| `card_funding` | string | `credit`, `debit`, `prepaid` |
| `metadata` | JSON | Custom fields |
| `refunded` | boolean | `true` / `false` |
| `amount_refunded` | integer | Refunded amount in cents |
| `disputed` | boolean | `true` / `false` |

### Key Columns in `balance_transactions`

| Column | Type | What it means |
|--------|------|---------------|
| `amount` | integer | Gross amount (cents) |
| `fee` | integer | Stripe fee (cents) |
| `net` | integer | amount - fee |
| `type` | string | `charge`, `refund`, `payout`, `adjustment` |
| `source` | string | Related charge/refund/payout ID |
| `available_on` | timestamp | When funds become available |

---

## Part 4: Stripe Sigma Queries — TAM Toolkit

### 4.1 Decline Analysis

```sql
-- Decline breakdown by reason code
SELECT
    failure_code,
    COUNT(*) AS total_declines,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM charges
WHERE status = 'failed'
  AND created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY failure_code
ORDER BY total_declines DESC;
```

```sql
-- Decline rate by country
SELECT
    card_country,
    COUNT(*) AS total_charges,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    ROUND(
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS decline_rate_pct
FROM charges
WHERE created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY card_country
HAVING COUNT(*) > 10
ORDER BY decline_rate_pct DESC;
```

```sql
-- Decline rate trend (daily)
SELECT
    DATE_TRUNC('day', created) AS day,
    COUNT(*) AS total,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    ROUND(
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS decline_rate
FROM charges
WHERE created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY DATE_TRUNC('day', created)
ORDER BY day;
```

### 4.2 Revenue Analysis

```sql
-- Monthly revenue
SELECT
    DATE_TRUNC('month', created) AS month,
    currency,
    COUNT(*) AS num_charges,
    SUM(amount) / 100.0 AS gross_revenue,
    SUM(amount - amount_refunded) / 100.0 AS net_revenue
FROM charges
WHERE status = 'succeeded'
GROUP BY DATE_TRUNC('month', created), currency
ORDER BY month DESC;
```

```sql
-- Revenue by card brand
SELECT
    card_brand,
    COUNT(*) AS num_charges,
    SUM(amount) / 100.0 AS total_revenue,
    AVG(amount) / 100.0 AS avg_order_value
FROM charges
WHERE status = 'succeeded'
  AND created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY card_brand
ORDER BY total_revenue DESC;
```

```sql
-- Top 10 customers by spend
SELECT
    c.customer_id,
    cu.email,
    COUNT(*) AS num_purchases,
    SUM(c.amount) / 100.0 AS total_spent
FROM charges c
JOIN customers cu ON c.customer_id = cu.id
WHERE c.status = 'succeeded'
GROUP BY c.customer_id, cu.email
ORDER BY total_spent DESC
LIMIT 10;
```

### 4.3 Fraud & Dispute Analysis

```sql
-- Fraud rate (disputes / charges)
SELECT
    DATE_TRUNC('month', c.created) AS month,
    COUNT(DISTINCT c.id) AS total_charges,
    COUNT(DISTINCT d.id) AS total_disputes,
    ROUND(
        COUNT(DISTINCT d.id) * 100.0 / COUNT(DISTINCT c.id),
        3
    ) AS dispute_rate_pct
FROM charges c
LEFT JOIN disputes d ON c.id = d.charge_id
WHERE c.status = 'succeeded'
GROUP BY DATE_TRUNC('month', c.created)
ORDER BY month DESC;
-- Visa threshold: 0.75% | Mastercard: 1.0%
```

```sql
-- Disputes by reason
SELECT
    reason,
    COUNT(*) AS total,
    SUM(amount) / 100.0 AS total_amount
FROM disputes
WHERE created >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY reason
ORDER BY total DESC;
```

```sql
-- High-risk pattern: large orders from new customers
SELECT
    c.id,
    c.amount / 100.0 AS amount,
    c.card_country,
    c.card_funding,
    cu.created AS customer_since
FROM charges c
JOIN customers cu ON c.customer_id = cu.id
WHERE c.amount > 50000
  AND cu.created >= CURRENT_DATE - INTERVAL '7' DAY
  AND c.status = 'succeeded'
ORDER BY c.amount DESC;
```

### 4.4 Refund Analysis

```sql
-- Refund rate and reasons
SELECT
    r.reason,
    COUNT(*) AS num_refunds,
    SUM(r.amount) / 100.0 AS total_refunded,
    AVG(r.amount) / 100.0 AS avg_refund
FROM refunds r
WHERE r.created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY r.reason
ORDER BY total_refunded DESC;
```

```sql
-- Time between charge and refund
SELECT
    r.id AS refund_id,
    c.id AS charge_id,
    c.amount / 100.0 AS original_amount,
    r.amount / 100.0 AS refund_amount,
    DATE_DIFF('day', c.created, r.created) AS days_to_refund
FROM refunds r
JOIN charges c ON r.charge_id = c.id
WHERE r.created >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY days_to_refund DESC;
```

### 4.5 Subscription Health

```sql
-- Active vs churned subscriptions
SELECT
    status,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM subscriptions
GROUP BY status
ORDER BY total DESC;
```

```sql
-- Failed invoice recovery rate
SELECT
    DATE_TRUNC('month', created) AS month,
    COUNT(*) AS total_failed,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS recovered,
    ROUND(
        SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS recovery_rate_pct
FROM invoices
WHERE attempt_count > 1
GROUP BY DATE_TRUNC('month', created)
ORDER BY month DESC;
```

### 4.6 Payout Reconciliation

```sql
-- Payout breakdown
SELECT
    bt.type,
    COUNT(*) AS num_transactions,
    SUM(bt.amount) / 100.0 AS gross,
    SUM(bt.fee) / 100.0 AS fees,
    SUM(bt.net) / 100.0 AS net
FROM balance_transactions bt
WHERE bt.available_on BETWEEN '2026-01-01' AND '2026-01-31'
GROUP BY bt.type
ORDER BY net DESC;
```

```sql
-- Fee analysis by month
SELECT
    DATE_TRUNC('month', created) AS month,
    SUM(amount) / 100.0 AS gross_revenue,
    SUM(fee) / 100.0 AS total_fees,
    SUM(net) / 100.0 AS net_revenue,
    ROUND(SUM(fee) * 100.0 / SUM(amount), 3) AS fee_pct
FROM balance_transactions
WHERE type = 'charge'
GROUP BY DATE_TRUNC('month', created)
ORDER BY month DESC;
```

### 4.7 Payment Method Analysis (DACH relevant)

```sql
-- Payment method distribution
SELECT
    payment_method_type,
    COUNT(*) AS total,
    SUM(amount) / 100.0 AS total_revenue,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM charges
WHERE status = 'succeeded'
  AND card_country IN ('DE', 'AT', 'CH')
  AND created >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY payment_method_type
ORDER BY total DESC;
```

---

## Part 5: SQL Anti-Patterns to Avoid

| Bad Practice | Why | Fix |
|-------------|-----|-----|
| `SELECT *` in production | Slow, pulls unnecessary data | Select only needed columns |
| No WHERE on large tables | Full table scan | Always filter by date range |
| `COUNT(*)` without GROUP BY awareness | Returns 1 row | Add GROUP BY for breakdowns |
| Division without NULL check | Division by zero | Use `NULLIF(x, 0)` |
| Forgetting amounts are in cents | EUR 349 shows as 34900 | Always `amount / 100.0` |
| String dates in WHERE | Can't use index | Use proper date types |
| Not using aliases | Unreadable joins | Always alias tables |

```sql
-- Division by zero protection
SELECT
    card_country,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0) AS decline_rate
FROM charges
GROUP BY card_country;
```

---

## Part 6: Quick Reference Cheat Sheet

### Query Template for Any Metric

```sql
SELECT
    [dimension],                              -- what to group by
    COUNT(*) AS total,                         -- how many
    SUM(amount) / 100.0 AS total_amount,       -- how much
    ROUND(
        [numerator] * 100.0 / NULLIF([denominator], 0),
        2
    ) AS rate_pct                               -- what percentage
FROM [table]
WHERE created >= CURRENT_DATE - INTERVAL '30' DAY
  AND [filters]
GROUP BY [dimension]
HAVING COUNT(*) > [minimum_threshold]
ORDER BY [sort_column] DESC
LIMIT 20;
```

### String Functions

```sql
LOWER(email)                    -- lowercase
UPPER(name)                     -- uppercase
CONCAT(first, ' ', last)       -- combine strings
SUBSTRING(id, 1, 3)            -- extract part: 'ch_'
LENGTH(description)             -- string length
REPLACE(email, '@', ' at ')    -- replace text
TRIM(name)                     -- remove whitespace
COALESCE(nickname, name, 'N/A') -- first non-NULL value
```

### Comparison Operators

| Operator | Meaning |
|----------|---------|
| `=` | Equal |
| `!=` or `<>` | Not equal |
| `>`, `>=` | Greater, greater or equal |
| `<`, `<=` | Less, less or equal |
| `BETWEEN a AND b` | Range (inclusive) |
| `IN (a, b, c)` | Match any in list |
| `LIKE '%pattern%'` | Pattern match |
| `IS NULL` | Is null |
| `IS NOT NULL` | Is not null |

---

## Part 7: Interview-Ready SQL Questions

If asked "write a query that..." in an interview, use this structure:

1. **Clarify**: What table? What time range? What metric?
2. **Start simple**: Write the basic SELECT + FROM + WHERE
3. **Add aggregation**: GROUP BY + aggregate functions
4. **Refine**: Add HAVING, ORDER BY, LIMIT
5. **Explain**: Walk through what each part does

### Practice Questions

1. "Find the top 5 countries by decline rate in the last 30 days"
2. "Calculate monthly revenue trend for the last 12 months"
3. "Which customers have more than 3 disputes?"
4. "What's the average time between charge and refund?"
5. "Show the fraud rate trend by week"
6. "Find all charges over EUR 500 from prepaid cards"
7. "Compare SEPA vs card payment success rates in Germany"
8. "Calculate the fee percentage by payment method"

*Try writing each query before looking at the examples in Part 4.*

---

*Amounts in Stripe are always in cents. Always divide by 100.0 (not 100) to preserve decimals.*
