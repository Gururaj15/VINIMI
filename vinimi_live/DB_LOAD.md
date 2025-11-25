## Embeddings CSV → MySQL (one-time import)

Run against `vinimi_local` (adjust user/password/paths). Back up first.

```sql
-- sanity
SELECT COUNT(*) FROM embeddings;
TRUNCATE TABLE embeddings;

-- relax worker_id during import if needed
ALTER TABLE embeddings MODIFY worker_id INT NULL;
ALTER TABLE embeddings DROP PRIMARY KEY;
ALTER TABLE embeddings ADD PRIMARY KEY (filename);

SET GLOBAL local_infile=1;
-- Example path if sourced from scaffold_vinimi:
--   /Users/rajiniboini/Desktop/projectV/backup v2.0/scaffold_vinimi/embeddings_with_vectors.csv
LOAD DATA LOCAL INFILE '/ABSOLUTE/PATH/TO/embeddings_with_vectors.csv'
INTO TABLE embeddings
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@filename, @id, @asset_id, @location_id, @company_id, @capture_dt, @name, @worker_id, @embedding)
SET
  filename         = @filename,
  id               = NULLIF(@id,''),
  asset_id         = @asset_id,
  location_id      = NULLIF(@location_id,''),
  company_id       = NULLIF(@company_id,''),
  capture_datetime = STR_TO_DATE(REPLACE(NULLIF(@capture_dt,''), 'T',' '), '%Y-%m-%d %H:%i:%s'),
  name             = NULLIF(@name,''),
  worker_id        = NULLIF(@worker_id,''),
  embedding        = @embedding;

SELECT COUNT(*) FROM embeddings;
SELECT filename, LEFT(embedding,40) AS head FROM embeddings LIMIT 5;

-- optional: restore stricter PK only if worker_id is always present
-- ALTER TABLE embeddings DROP PRIMARY KEY;
-- ALTER TABLE embeddings MODIFY worker_id INT NOT NULL;
-- ALTER TABLE embeddings ADD PRIMARY KEY (filename, worker_id);
```
