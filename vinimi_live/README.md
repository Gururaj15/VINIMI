# VINIMI Backend Notes

## Helmet Violation Migration

Run the following SQL against your local MySQL database (or apply `migrations/001_create_violation.sql`) to create the `violation` table and ensure worker phone numbers can store E.164:

```sql
CREATE TABLE IF NOT EXISTS violation (
  id INT NOT NULL AUTO_INCREMENT,
  worker_id INT NULL,
  phone VARCHAR(32) NULL,
  type ENUM('HELMET') NOT NULL DEFAULT 'HELMET',
  detected_at DATETIME NOT NULL,
  frame_path VARCHAR(255) NULL,
  sms_sid VARCHAR(64) NULL,
  sms_status VARCHAR(32) NULL,
  details JSON NULL,
  PRIMARY KEY (id),
  KEY idx_worker_time (worker_id, detected_at),
  CONSTRAINT violation_worker_fk
    FOREIGN KEY (worker_id) REFERENCES worker(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE worker
  MODIFY phone VARCHAR(32) NOT NULL;
```

This prepares the database for the Twilio SMS alert flow.
