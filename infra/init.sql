-- CrossBorder AI Copilot — Database Schema
-- Run once on first boot (handled by docker-entrypoint-initdb.d)

CREATE TABLE IF NOT EXISTS products_raw (
    id               SERIAL PRIMARY KEY,
    source_platform  VARCHAR(50)  NOT NULL,
    source_url       TEXT         NOT NULL UNIQUE,
    source_id        VARCHAR(200),
    raw_html_path    TEXT,
    raw_json         JSONB,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products_normalized (
    id               SERIAL PRIMARY KEY,
    raw_product_id   INTEGER      REFERENCES products_raw(id) ON DELETE CASCADE,
    platform         VARCHAR(50)  NOT NULL,
    title            TEXT,
    brand            VARCHAR(200),
    category         VARCHAR(200),
    price_min        NUMERIC(12,4),
    price_max        NUMERIC(12,4),
    currency         VARCHAR(10),
    moq              INTEGER,
    material         TEXT,
    size             TEXT,
    color            TEXT,
    package_quantity INTEGER,
    attributes_json  JSONB,
    images_json      JSONB,
    rating           NUMERIC(4,2),
    review_count     INTEGER,
    seller_name      VARCHAR(300),
    ship_from        VARCHAR(200),
    normalized_text  TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_tasks (
    id                VARCHAR(50)  PRIMARY KEY,
    status            VARCHAR(20)  NOT NULL DEFAULT 'queued',
    stage             VARCHAR(50),
    progress          INTEGER      NOT NULL DEFAULT 0,
    source_url        TEXT         NOT NULL,
    target_marketplace VARCHAR(50) NOT NULL DEFAULT 'amazon-us',
    cost_params       JSONB,
    source_product_id INTEGER,
    error_message     TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_matches (
    id                      SERIAL PRIMARY KEY,
    task_id                 VARCHAR(50)  NOT NULL,
    source_product_id       INTEGER      NOT NULL,
    target_product_id       INTEGER      NOT NULL,
    match_score             NUMERIC(5,2) NOT NULL,
    match_level             VARCHAR(20)  NOT NULL,
    similarity_breakdown    JSONB,
    match_reason            TEXT,
    diff_summary            TEXT,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competitor_reports (
    id                          SERIAL PRIMARY KEY,
    task_id                     VARCHAR(50)  NOT NULL,
    source_product_id           INTEGER      NOT NULL,
    report_json                 JSONB,
    summary_text                TEXT,
    pain_points_json            JSONB,
    keywords_json               JSONB,
    differentiation_suggestions TEXT,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS margin_calculations (
    id                      SERIAL PRIMARY KEY,
    task_id                 VARCHAR(50)  NOT NULL,
    product_id              INTEGER      NOT NULL,
    cost_purchase           NUMERIC(12,4) NOT NULL,
    domestic_shipping       NUMERIC(12,4) NOT NULL DEFAULT 0,
    international_shipping  NUMERIC(12,4) NOT NULL DEFAULT 0,
    fba_fee                 NUMERIC(12,4) NOT NULL DEFAULT 0,
    commission_fee          NUMERIC(12,4) NOT NULL DEFAULT 0,
    ads_cost                NUMERIC(12,4) NOT NULL DEFAULT 0,
    tax_cost                NUMERIC(12,4) NOT NULL DEFAULT 0,
    exchange_rate           NUMERIC(8,4)  NOT NULL DEFAULT 7.2,
    sell_price              NUMERIC(12,4) NOT NULL,
    total_cost              NUMERIC(12,4) NOT NULL,
    gross_profit            NUMERIC(12,4) NOT NULL,
    net_profit              NUMERIC(12,4) NOT NULL,
    gross_margin            NUMERIC(8,6)  NOT NULL,
    net_margin              NUMERIC(8,6)  NOT NULL,
    suggested_price_min     NUMERIC(12,4),
    suggested_price_max     NUMERIC(12,4),
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS listing_drafts (
    id              SERIAL PRIMARY KEY,
    task_id         VARCHAR(50)  NOT NULL,
    product_id      INTEGER      NOT NULL,
    market          VARCHAR(50)  NOT NULL DEFAULT 'amazon-us',
    language        VARCHAR(10)  NOT NULL DEFAULT 'en',
    title           TEXT,
    bullets_json    JSONB,
    description     TEXT,
    search_terms    TEXT,
    image_copy_json JSONB,
    version         INTEGER      NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status    ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_matches_task_id ON product_matches(task_id);
CREATE INDEX IF NOT EXISTS idx_listing_task_id ON listing_drafts(task_id);
