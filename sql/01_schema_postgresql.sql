-- E-Commerce Sales & KPI Dashboard — PostgreSQL schema
-- Star schema: two dimensions (products, customers), one fact (orders).
-- All monetary values in Indian Rupees (INR). The source CSVs use friendly
-- display headers (Product Code, Order Date, ...); python/etl_pipeline.py
-- maps them to these database column names on load.

CREATE TABLE IF NOT EXISTS dim_products (
    product_code      VARCHAR(10) PRIMARY KEY,  -- unique product code, e.g. SKU-101
    product_name      VARCHAR(120) NOT NULL,    -- product display name
    product_category  VARCHAR(40)  NOT NULL,    -- Electronics / Apparel / FMCG / ...
    selling_price_inr NUMERIC(12,2) NOT NULL,   -- list selling price of one unit, in rupees
    unit_cost_inr     NUMERIC(12,2) NOT NULL    -- cost of one unit, in rupees
);

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id         VARCHAR(12) PRIMARY KEY,  -- unique customer id, e.g. CUST-10001
    customer_city       VARCHAR(40) NOT NULL,     -- home city
    customer_region     VARCHAR(10) NOT NULL,     -- North / South / East / West
    acquisition_channel VARCHAR(20) NOT NULL,     -- channel the customer signed up through
    signup_date         DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id        VARCHAR(12) PRIMARY KEY,    -- unique order id, e.g. ORD-500001
    order_date      DATE NOT NULL,              -- date the order was placed
    customer_id     VARCHAR(12) NOT NULL REFERENCES dim_customers(customer_id),
    product_code    VARCHAR(10) NOT NULL REFERENCES dim_products(product_code),
    sales_channel   VARCHAR(20) NOT NULL,       -- Mobile App / Website / Marketplace
    quantity        INTEGER NOT NULL,           -- units in the order
    unit_price_inr  NUMERIC(12,2) NOT NULL,     -- price of one unit at order time
    discount_percent NUMERIC(5,2) NOT NULL,     -- discount applied, %
    order_value_inr NUMERIC(12,2) NOT NULL,     -- what the customer paid (after discount)
    payment_method  VARCHAR(25) NOT NULL,       -- UPI / Credit/Debit Card / Cash on Delivery / Net Banking
    order_status    VARCHAR(12) NOT NULL,       -- Delivered / Returned / Cancelled
    delivery_days   INTEGER NOT NULL            -- days from order to delivery
);

CREATE INDEX IF NOT EXISTS idx_orders_date     ON fact_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_orders_product  ON fact_orders (product_code);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_channel  ON fact_orders (sales_channel);
