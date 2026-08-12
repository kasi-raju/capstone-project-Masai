"""
queries.py
----------
Runs the required SQL queries against books.db, prints their output,
and demonstrates that pd.read_sql(...) and pd.merge(...) produce
equivalent results for the JOIN query.

Run:
    python queries.py
"""

import sqlite3
import pandas as pd

DB_PATH = "books.db"


def run(cur, label, sql, params=()):
    print(f"\n--- {label} ---")
    print(sql.strip())
    rows = cur.execute(sql, params).fetchall()
    cols = [d[0] for d in cur.description]
    print(cols)
    for r in rows:
        print(r)
    return rows, cols


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. SELECT / WHERE -----------------------------------------------
    run(
        cur,
        "Q1: Books in stock under 20 GBP (SELECT / WHERE)",
        """
        SELECT title, price_gbp, in_stock
        FROM books
        WHERE in_stock = 1 AND price_gbp < 20;
        """,
    )

    # 2. ORDER BY / LIMIT ----------------------------------------------
    run(
        cur,
        "Q2: 10 most expensive books (ORDER BY / LIMIT)",
        """
        SELECT title, price_gbp
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10;
        """,
    )

    # 3. DISTINCT --------------------------------------------------------
    run(
        cur,
        "Q3: Distinct categories present (DISTINCT)",
        """
        SELECT DISTINCT category_name
        FROM categories
        ORDER BY category_name;
        """,
    )

    # 4. IN / BETWEEN ------------------------------------------------------
    run(
        cur,
        "Q4: Mid-priced books, 20-40 GBP, rated 4 or 5 (BETWEEN + IN)",
        """
        SELECT title, price_gbp, rating
        FROM books
        WHERE price_gbp BETWEEN 20 AND 40
          AND rating IN (4, 5)
        ORDER BY price_gbp;
        """,
    )

    # 5. JOIN -- top-rated books per category ------------------------------
    join_sql = """
        SELECT c.category_name, b.title, b.rating, b.price_gbp
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.rating = 5
        ORDER BY c.category_name, b.price_gbp DESC;
    """
    run(cur, "Q5: Five-star books per category (JOIN)", join_sql)

    # --- pd.read_sql vs pd.merge equivalence check ------------------------
    print("\n=== pd.read_sql vs pd.merge equivalence check ===")

    df_join_sql = pd.read_sql(join_sql, conn)

    books_df = pd.read_sql("SELECT * FROM books", conn)
    categories_df = pd.read_sql("SELECT * FROM categories", conn)

    df_join_pandas = (
        books_df.merge(categories_df, on="category_id")
        .query("rating == 5")[["category_name", "title", "rating", "price_gbp"]]
        .sort_values(["category_name", "price_gbp"], ascending=[True, False])
        .reset_index(drop=True)
    )

    df_join_sql_sorted = df_join_sql.sort_values(
        ["category_name", "price_gbp"], ascending=[True, False]
    ).reset_index(drop=True)

    print("\npd.read_sql result:")
    print(df_join_sql_sorted)

    print("\npd.merge result:")
    print(df_join_pandas)

    are_equal = df_join_sql_sorted.equals(df_join_pandas)
    print(f"\nResults match: {are_equal}")

    # Also read back a second query (Q2) into a DataFrame, per the brief.
    top10_df = pd.read_sql(
        "SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 10", conn
    )
    print("\n--- Q2 read back via pd.read_sql ---")
    print(top10_df)

    conn.close()


if __name__ == "__main__":
    main()
