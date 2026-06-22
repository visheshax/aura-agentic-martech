-- Enable pgvector extension for similarity search on zero-party embeddings
create extension if not exists vector;

-- Table for raw customer touchpoints (messy ingested events)
create table if not exists raw_customer_touchpoints (
    id uuid default gen_random_uuid() primary key,
    email varchar(255),
    phone varchar(50),
    device_id varchar(255),
    event_type varchar(50), -- e.g., 'page_view', 'cart_abandonment', 'purchase', 'zero_party_survey'
    event_data jsonb,       -- e.g., { "product_category": "Luxury Watch", "price": 1200, "browser": "Chrome" }
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Table for consolidated customer profiles (C360 unified profiles)
create table if not exists customer_profiles (
    id uuid default gen_random_uuid() primary key,
    email varchar(255) unique,
    phone varchar(50),
    full_name varchar(255),
    interests text[],       -- stitched product preferences
    preferred_channel varchar(50) default 'email',
    avg_order_value numeric(10, 2) default 0.0,
    price_sensitivity varchar(50) default 'medium', -- 'high', 'medium', 'low'
    profile_embedding vector(1536),                 -- vector representation of preferences & context
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Table for tracking marketing agent orchestration runs and outputs
create table if not exists campaign_logs (
    id uuid default gen_random_uuid() primary key,
    profile_id uuid references customer_profiles(id) on delete cascade,
    trigger_event varchar(100), -- e.g., 'abandoned_cart_high_value'
    generated_email_subject text,
    generated_email_body text,
    generated_advisor_script text,
    coupon_code varchar(100),
    coupon_discount_percent int,
    compliance_approved boolean default false,
    compliance_report jsonb, -- legal/GDPR checks details
    total_cost_saved numeric(5, 2), -- simulated P&L impact metric
    conversion_probability numeric(4, 3), -- simulated conversion probability (0 to 1)
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create a mock dataset insert helper
create or replace function insert_mock_data() returns void as $$
begin
    -- Clear existing profiles
    truncate table campaign_logs cascade;
    truncate table customer_profiles cascade;
    truncate table raw_customer_touchpoints cascade;

    -- Raw messy touchpoints for Person A (Siddharth)
    insert into raw_customer_touchpoints (email, event_type, event_data) values
    ('sid@example.com', 'page_view', '{"product_category": "Premium Running Shoes", "price": 150}'),
    ('sid@example.com', 'zero_party_survey', '{"preferred_sport": "marathon", "frequency": "daily"}'),
    ('sid@example.com', 'cart_abandonment', '{"product_category": "Premium Running Shoes", "price": 150}');

    -- Raw messy touchpoints for Person B (Emma)
    insert into raw_customer_touchpoints (email, event_type, event_data) values
    ('emma.jones@example.com', 'page_view', '{"product_category": "Luxury Smartwatch", "price": 850}'),
    ('emma.jones@example.com', 'purchase', '{"product_category": "Leather Band", "price": 95}'),
    ('emma.jones@example.com', 'page_view', '{"product_category": "Luxury Smartwatch", "price": 850}');
end;
$$ language plpgsql;
