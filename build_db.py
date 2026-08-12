"""
build_db.py
-----------
Loads clean_books.csv into a normalized two-table SQLite schema:

    categories(category_id PK, category_name UNIQUE)
    books(book_id PK, title, price_gbp, price_inr, rating, in_stock,
          category_id FK -> categories.category_id)

Run:
    python build_db.py
This (re)creates books.db from scratch, so it's safe to re-run any time.
"""

import sqlite3
import pandas as pd

DB_PATH = "books.db"


def main():
    df = pd.read_csv("clean_books.csv")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Start clean every run.
    cur.executescript(
        """
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS categories;

        CREATE TABLE categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE books (
            book_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            price_gbp   REAL NOT NULL,
            price_inr   REAL NOT NULL,
            rating      INTEGER NOT NULL,
            in_stock    INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );
        """
    )

    # Insert categories first, get back their generated ids.
    categories = sorted(df["category"].unique())
    cur.executemany(
        "INSERT INTO categories (category_name) VALUES (?)",
        [(c,) for c in categories],
    )
    conn.commit()

    cat_id_map = dict(
        cur.execute("SELECT category_name, category_id FROM categories").fetchall()
    )

    book_rows = [
        (
            row.title,
            row.price_gbp,
            row.price_inr,
            int(row.rating),
            int(bool(row.in_stock)),
            cat_id_map[row.category],
        )
        for row in df.itertuples()
    ]

    cur.executemany(
        """INSERT INTO books
           (title, price_gbp, price_inr, rating, in_stock, category_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        book_rows,
    )
    conn.commit()

    n_books = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    n_cats = cur.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    print(f"Loaded {n_books} books across {n_cats} categories into {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
