-- VINIMI Migration 002: enrich violation records with worker/location metadata

ALTER TABLE violation
  ADD COLUMN worker_name VARCHAR(255) NULL AFTER worker_id,
  ADD COLUMN location_id INT NULL AFTER phone,
  ADD COLUMN location_name VARCHAR(255) NULL AFTER location_id,
  ADD KEY idx_location_time (location_id, detected_at);

ALTER TABLE violation
  ADD CONSTRAINT violation_location_fk
    FOREIGN KEY (location_id) REFERENCES location(id)
    ON DELETE SET NULL;
