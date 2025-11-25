-- VINIMI Migration 001: Helmet violation tracking + SMS metadata

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
