# #!/usr/bin/env python3
# """
# generate_fact_csv.py
# --------------------
# 70 MILLION FK-safe fact rows -> fact_sales.csv

# FK SAFETY:
#   - Valid keys WAHI dim CSVs se padhta hai jo tumne DB mein import kiye the
#     (dim_store.csv / dim_product.csv / dim_date.csv).
#   - Fact ki har store_id / product_id / date_key isi list se aati hai,
#     isliye wo DB ke dim mein 100% exist karegi -> koi FK mismatch nahi.

# IDENTITY:
#   - sale_id CSV mein NAHI hai. Table ka IDENTITY khud unique sale_id banayega.

# Run:
#   python generate_fact_csv.py
#   (dim_store.csv, dim_product.csv, dim_date.csv usi folder mein hone chahiye)
# """

# import csv
# import random

# random.seed(7)

# TARGET = 70_000_000        # 7 crore
# CHUNK  = 1_000_000         # ek baar mein itne rows process (memory friendly)

# # ---------- 1) Valid dim keys padho (yehi keys DB ke dims mein hain) ----------
# def load_keys(path, col):
#     with open(path, newline="", encoding="utf-8") as f:
#         return [int(r[col]) for r in csv.DictReader(f)]

# store_ids   = load_keys("dim_store.csv",   "store_id")
# product_ids = load_keys("dim_product.csv", "product_id")
# date_keys   = load_keys("dim_date.csv",    "date_key")
# PAYMENTS    = ["Cash", "Card", "UPI", "Wallet"]

# print(f"keys loaded -> stores:{len(store_ids)}  products:{len(product_ids)}  dates:{len(date_keys)}")

# # ---------- 2) 70M fact rows likho (chunk by chunk) ----------
# choices = random.choices
# randint = random.randint

# with open("fact_sales.csv", "w", newline="", encoding="utf-8") as f:
#     w = csv.writer(f)
#     w.writerow(["date_key", "store_id", "product_id", "payment_mode",
#                 "quantity", "unit_price", "discount", "total_amount"])  # sale_id NAHI

#     written = 0
#     while written < TARGET:
#         n = min(CHUNK, TARGET - written)

#         dk = choices(date_keys,   k=n)
#         si = choices(store_ids,   k=n)
#         pi = choices(product_ids, k=n)
#         pm = choices(PAYMENTS,    k=n)

#         rows = []
#         for i in range(n):
#             qty   = randint(1, 50)
#             price = randint(1000, 50000) / 100.0      # 10.00 - 500.00
#             disc  = randint(0, 9000) / 100.0          # 0.00 - 90.00
#             total = round(qty * price - disc, 2)
#             rows.append((dk[i], si[i], pi[i], pm[i], qty,
#                          round(price, 2), round(disc, 2), total))
#         w.writerows(rows)

#         written += n
#         print(f"written: {written:,}")

# print("\nDONE -> fact_sales.csv  (sale_id IDENTITY se auto banega)")
import pandas as pd

chunk_count = 0
total_rows = 0

for chunk in pd.read_csv("fact_sales.csv", chunksize=100000):
    chunk_count += 1
    total_rows += len(chunk)

print(f"Total Chunks: {chunk_count}")
print(f"Total Rows: {total_rows:,}")