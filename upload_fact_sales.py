#!/usr/bin/env python3
"""
upload_fact_sales.py  —  Azure SQL (SQL Server) bulk upload
Resumable + FK-safe + progress + ETA

Setup (ek baar):
  1. https://aka.ms/odbc18  se ODBC Driver 18 install karo
  2. pip install pyodbc
  3. python upload_fact_sales.py
"""

import pyodbc, csv, time

SERVER = "research-db-pulsee.database.windows.net"
DATABASE = "EmployeeDatabase"
USERNAME = "Sql_server"
PASSWORD = "My-Admin"
CSV_FILE = r"C:\Users\Ayush\Downloads\mockdata\fact_sales.csv"

CHUNK_SIZE = 10_000
TARGET = 70_000_000
LOG_EVERY = 100_000

CONN_STR = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER},1433;DATABASE={DATABASE};"
    f"UID={USERNAME};PWD={PASSWORD};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
)

INSERT_SQL = """INSERT INTO dbo.Fact_Sales
(date_key,store_id,product_id,payment_mode,quantity,unit_price,discount,total_amount)
VALUES (?,?,?,?,?,?,?,?)"""


def get_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT_BIG(*) FROM dbo.Fact_Sales")
    return c.fetchone()[0]


def main():
    print("=" * 55)
    print("  Fact_Sales Upload — Azure SQL")
    print("=" * 55)
    print("\nConnecting...")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=False)
        conn.timeout = 300
        print("Connected!")
    except Exception as e:
        print(f"\nConnection FAILED:\n{e}")
        print(
            "\nCheck:\n  1. ODBC Driver 18 installed? https://aka.ms/odbc18\n  2. Password sahi?\n  3. Azure firewall mein IP allowed?"
        )
        return

    cur = conn.cursor()
    cur.fast_executemany = True

    print("\nFK checks off...")
    cur.execute("ALTER TABLE dbo.Fact_Sales NOCHECK CONSTRAINT ALL")
    conn.commit()

    already = get_count(conn)
    print(f"DB mein abhi : {already:,}")
    print(f"Remaining    : {TARGET-already:,}")

    if already >= TARGET:
        print("Already 70M!")
        conn.close()
        return

    start = time.time()
    total = already

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        if already > 0:
            print(f"\nSkipping {already:,} rows already in DB...")
            for i, _ in enumerate(range(already), 1):
                next(reader)
                if i % 1_000_000 == 0:
                    print(f"  skipped {i:,}...")
            print("Skip done. Uploading remaining rows...\n")
        else:
            print("\nStarting fresh upload...\n")

        batch = []
        for row in reader:
            if total >= TARGET:
                break
            batch.append(
                (
                    int(row[0]),
                    int(row[1]),
                    int(row[2]),
                    row[3],
                    int(row[4]),
                    float(row[5]),
                    float(row[6]),
                    float(row[7]),
                )
            )
            if len(batch) >= CHUNK_SIZE:
                try:
                    cur.executemany(INSERT_SQL, batch)
                    conn.commit()
                    total += len(batch)
                    batch = []
                    if total % LOG_EVERY == 0:
                        el = time.time() - start
                        rate = (total - already) / el if el > 0 else 1
                        eta = (TARGET - total) / rate / 60
                        print(
                            f"[{total/TARGET*100:5.1f}%] {total:,}  |  {rate:,.0f} r/s  |  ETA {eta:.1f} min"
                        )
                except Exception as e:
                    conn.rollback()
                    print(f"\nError at {total:,}: {e}")
                    print("Dobara chalao — resume hoga.")
                    conn.close()
                    return

        if batch and total < TARGET:
            try:
                cur.executemany(INSERT_SQL, batch)
                conn.commit()
                total += len(batch)
            except:
                conn.rollback()

    print("\nFK wapas on + validate...")
    cur.execute("ALTER TABLE dbo.Fact_Sales WITH CHECK CHECK CONSTRAINT ALL")
    conn.commit()
    final = get_count(conn)
    conn.close()

    print("\n" + "=" * 55)
    if final >= TARGET:
        print(f"  SUCCESS! {final:,} rows — 70M COMPLETE! ✓")
    else:
        print(f"  {final:,} rows done. {TARGET-final:,} baaki — dobara chalao.")
    print("=" * 55)


if __name__ == "__main__":
    main()
