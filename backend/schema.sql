-- chesterwindowcleaner DDL.
-- All timestamps are unix epoch seconds (INTEGER).
-- All prices are integer pence.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  source TEXT NOT NULL,           -- 'wizard' | 'chat' | 'contact_form'
  status TEXT NOT NULL DEFAULT 'new',
  name TEXT,
  email TEXT,
  phone TEXT,
  address TEXT,
  postcode TEXT,
  property_type TEXT,
  addons_json TEXT,
  frequency TEXT,                 -- 'regular_6w' | 'one_off' | NULL
  poa INTEGER NOT NULL DEFAULT 0,
  quote_pence INTEGER,
  preferred_contact TEXT,
  notes_visitor TEXT,
  notes_owner TEXT,
  interest_flags_json TEXT,
  access_blocked INTEGER NOT NULL DEFAULT 0,
  out_of_area INTEGER NOT NULL DEFAULT 0,
  ip_address TEXT,
  user_agent TEXT,
  customer_id INTEGER REFERENCES customers(id)
);
CREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_postcode ON leads(postcode);

CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  address TEXT NOT NULL,
  postcode TEXT NOT NULL,
  preferred_contact TEXT,
  property_type TEXT,
  addons_json TEXT,
  frequency TEXT NOT NULL,
  price_pence INTEGER NOT NULL,
  last_cleaned_date TEXT,
  next_due_date TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  notes TEXT,
  lead_id INTEGER REFERENCES leads(id)
);
CREATE INDEX IF NOT EXISTS idx_customers_next_due ON customers(active, next_due_date);
CREATE INDEX IF NOT EXISTS idx_customers_postcode ON customers(postcode);

CREATE TABLE IF NOT EXISTS clean_log (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  cleaned_date TEXT NOT NULL,
  paid INTEGER NOT NULL DEFAULT 0,
  price_charged_pence INTEGER NOT NULL,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_clean_log_customer_date ON clean_log(customer_id, cleaned_date DESC);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  messages_json TEXT NOT NULL,
  resulted_in_lead INTEGER NOT NULL DEFAULT 0,
  lead_id INTEGER REFERENCES leads(id),
  llm_input_tokens INTEGER NOT NULL DEFAULT 0,
  llm_output_tokens INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS review_requests (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  queued_at INTEGER NOT NULL,
  sent_at INTEGER,
  reminder_sent_at INTEGER,
  review_received INTEGER NOT NULL DEFAULT 0,
  marked_received_at INTEGER
);
