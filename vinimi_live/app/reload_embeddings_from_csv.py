# reload_embeddings_from_csv.py
import pandas as pd
from datetime import datetime
from db import get_conn   # uses your existing local MySQL config in db.py

CSV_PATH = "embeddings.csv"  # adjust if needed

def main():
    df = pd.read_csv(CSV_PATH)

    print(f"Loaded {len(df)} rows from {CSV_PATH}")

    conn = get_conn()
    cur = conn.cursor()

    sql = """
        INSERT INTO embeddings (
            filename,
            id,
            asset_id,
            location_id,
            company_id,
            capture_datetime,
            name,
            worker_id,
            embedding
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    count = 0
    for _, row in df.iterrows():
        # worker_id must exist in worker table or FK will fail
        worker_id = int(row["worker_id"])

        filename = str(row["filename"])
        emb_str = str(row["embedding"])

        # id can be NULL
        id_val = None
        if "id" in row and not pd.isna(row["id"]):
            try:
                id_val = int(row["id"])
            except Exception:
                id_val = None

        # optional fields – keep as None if missing
        asset_id = row.get("asset_id")
        if pd.isna(asset_id):
            asset_id = None

        loc_id = row.get("location_id")
        if pd.isna(loc_id):
            loc_id = None
        else:
            loc_id = str(loc_id)

        comp_id = row.get("company_id")
        if pd.isna(comp_id):
            comp_id = None
        else:
            comp_id = str(comp_id)

        name_val = row.get("name")
        if pd.isna(name_val):
            name_val = None

        # capture_datetime – use CSV value if present, else now()
        cap_dt = row.get("capture_datetime")
        if pd.isna(cap_dt) or cap_dt is None:
            cap_dt = datetime.now()
        else:
            # let MySQL parse the text; it's already in 'YYYY-MM-DD HH:MM:SS' format
            cap_dt = str(cap_dt)

        cur.execute(
            sql,
            (
                filename,
                id_val,
                asset_id,
                loc_id,
                comp_id,
                cap_dt,
                name_val,
                worker_id,
                emb_str,   # keep the embedding string EXACTLY as in CSV
            ),
        )
        count += 1

    conn.commit()
    conn.close()
    print(f"Inserted {count} rows into embeddings")

if __name__ == "__main__":
    main()
