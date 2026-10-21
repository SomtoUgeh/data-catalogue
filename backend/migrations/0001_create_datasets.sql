-- Datasets table plus the three sample entries from the brief. Tags are a JSON array string.
CREATE TABLE datasets (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  name            TEXT NOT NULL,
  owner           TEXT NOT NULL,
  description     TEXT NOT NULL,
  tags            TEXT NOT NULL,
  summary         TEXT NOT NULL,
  curation_status TEXT NOT NULL CHECK (curation_status IN ('ok', 'failed'))
);

INSERT INTO datasets (id, name, owner, description, tags, summary, curation_status) VALUES
  (1, 'Customer Transactions', 'Finance Team',
   'Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.',
   '["finance", "transactions", "PII", "daily"]',
   'A daily feed of customer transaction records covering amounts, currencies, and timestamps.', 'ok'),
  (2, 'Product Inventory', 'Operations Team',
   'Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.',
   '["inventory", "operations", "warehouse"]',
   'A warehouse snapshot tracking stock levels and reorder thresholds per product SKU.', 'ok'),
  (3, 'Employee Directory', 'HR Team',
   'List of current employees with name, department, role, and office location. Updated weekly.',
   '["HR", "PII", "employees", "weekly"]',
   'A weekly-refreshed directory of employees including role, department, and location.', 'ok');
