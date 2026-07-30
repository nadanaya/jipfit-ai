PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS regions (
    region_code TEXT PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE,
    demo_cost_index REAL NOT NULL CHECK (demo_cost_index > 0),
    note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_mode TEXT NOT NULL CHECK (rule_mode IN ('screening', 'discovery')),
    official_url TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    source_note TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 100),
    monthly_income INTEGER NOT NULL CHECK (monthly_income > 0),
    assets INTEGER NOT NULL CHECK (assets >= 0),
    region_code TEXT NOT NULL,
    monthly_housing_cost INTEGER NOT NULL CHECK (monthly_housing_cost >= 0),
    affordability_ratio REAL NOT NULL CHECK (affordability_ratio >= 0),
    recommended_housing_cost INTEGER NOT NULL CHECK (recommended_housing_cost >= 0),
    risk_class INTEGER NOT NULL CHECK (risk_class IN (0, 1, 2)),
    policy_ids_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (region_code) REFERENCES regions(region_code)
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_created_at
    ON analysis_runs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_policies_category_active
    ON policies(category, is_active);
