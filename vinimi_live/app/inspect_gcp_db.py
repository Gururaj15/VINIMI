# # app/db_inspect.py
# from __future__ import annotations
# import os
# from typing import List, Any, Tuple

# from google.cloud.sql.connector import Connector
# import pymysql


# # Reuse a single Connector instance
# _connector = Connector()


# def get_conn():
#     """
#     Open a new connection to the GCP Cloud SQL (MySQL) database.
#     Uses the same env vars as your script:
#       CLOUD_SQL_INSTANCE, DB_USER, DB_PASS, DB_NAME
#     """
#     conn = _connector.connect(
#         os.environ["CLOUD_SQL_INSTANCE"],
#         "pymysql",
#         user=os.environ["DB_USER"],
#         password=os.environ["DB_PASS"],
#         db=os.environ["DB_NAME"],
#     )
#     return conn


# def list_tables() -> List[str]:
#     with get_conn() as conn:
#         cur = conn.cursor()
#         cur.execute("SHOW TABLES")
#         return [row[0] for row in cur.fetchall()]


# def describe_table(table: str) -> List[Tuple[Any, ...]]:
#     """
#     Returns list of column info tuples:
#     (Field, Type, Null, Key, Default, Extra)
#     """
#     with get_conn() as conn:
#         cur = conn.cursor()
#         cur.execute(f"DESCRIBE `{table}`")
#         return cur.fetchall()


# def get_rows(table: str, limit: int = 50) -> List[Tuple[Any, ...]]:
#     with get_conn() as conn:
#         cur = conn.cursor()
#         cur.execute(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
#         return cur.fetchall()
