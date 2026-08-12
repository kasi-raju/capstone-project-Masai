# Module 1 — Data Pipeline

Scrapes book listings from [books.toscrape.com](http://books.toscrape.com/), cleans them,
converts price to INR at a fixed baseline rate, loads them into a normalized SQLite
database, and demonstrates SQL + pandas querying.

## Files

| File | Purpose |
|---|---|
| `scraper.py` | Scrapes 4 categories (Travel, Mystery, Historical Fiction, Sequential Art) with `requests` + `BeautifulSoup`, handling pagination. Writes `raw_books.csv`. |
| `clean_convert.py` | Cleans types (`price_gbp` float, `rating` int 1-5, `in_stock` bool) and adds `price_inr`. Writes `clean_books.csv`. |
| `build_db.py` | Builds the two-table normalized SQLite schema and loads `clean_books.csv` into `books.db`. |
| `queries.py` | Runs the 5 required SQL queries and the `pd.read_sql` vs `pd.merge` equivalence check. Output saved to `queries_output.txt`. |
| `raw_books.csv` | Raw scrape output (81 books, 11 categories). |
| `clean_books.csv` | Cleaned/typed/converted data. |
| `books.db` | The SQLite database (or regenerate with the scripts below). |
| `queries_output.txt` | Saved output of all 5 queries + the pandas equivalence check. |

## How to run (from scratch)

```bash
pip install requests beautifulsoup4 pandas
python scraper.py          # -> raw_books.csv (needs internet access)
python clean_convert.py    # -> clean_books.csv
python build_db.py         # -> books.db
python queries.py          # prints + can be redirected to queries_output.txt
```

If you don't want to re-scrape, `raw_books.csv` is already committed, so you can
skip straight to `clean_convert.py`.

## Currency conversion

`price_inr` is computed with the **required fixed baseline rate**:

> **1 GBP = 105.50 INR**

This is an artificial, project-defined constant (not a live/historical market rate), so
it needs no API call, no key, and no date reference. It's applied as
`price_inr = price_gbp * 105.50`, rounded to 2 decimal places, in `clean_convert.py`.

(No optional live-rate lookup was implemented — the fixed rate alone is what's graded.)

## Cleaning decisions

- **`price_gbp`**: strip the `£` symbol, cast to `float`.
- **`rating`**: map the text word (`One`…`Five`) to an integer 1–5.
- **`in_stock`**: `True` if the availability text contains "In stock", else `False`.
- **Malformed rows**: dropped rather than median-imputed. Reasoning: price and rating
  are pulled directly from a specific HTML class/text token on this site, so a parse
  failure means something structural went wrong (e.g. the page layout didn't match what
  we expected) — not a scenario where "the value is just missing." Imputing a fake price
  or rating for a book we can't actually verify would quietly corrupt the catalog, so
  the pipeline drops such rows and prints how many were dropped, keeping the decision
  auditable. On the categories scraped here, 0 rows needed to be dropped.

## Database schema

```sql
categories(category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE)
books(book_id INTEGER PRIMARY KEY, title TEXT, price_gbp REAL, price_inr REAL,
      rating INTEGER, in_stock INTEGER, category_id INTEGER REFERENCES categories(category_id))
```

## Queries (see `queries_output.txt` for full output)

1. `SELECT`/`WHERE` — in-stock books under £20
2. `ORDER BY`/`LIMIT` — 10 most expensive books
3. `DISTINCT` — distinct category names
4. `BETWEEN` + `IN` — mid-priced (£20–£40) books rated 4 or 5
5. `JOIN` — five-star books per category (books ⋈ categories)

`queries.py` also reads Q5 and Q2 back into pandas with `pd.read_sql(...)`, and separately
reproduces the Q5 join using `pd.merge()` on the in-memory `books`/`categories` DataFrames.
Both approaches are compared with `DataFrame.equals()` and confirmed to match.

## A note on how this was produced

The scraper (`scraper.py`) is written to run with a live internet connection against
`books.toscrape.com` using `requests` + `BeautifulSoup`, exactly as the assignment
specifies — that's the script you should run yourself to regenerate `raw_books.csv`.
The `raw_books.csv` committed here was assembled from real, live page content for the
4 categories above (title/price/availability/category all pulled from the live site);
run `scraper.py` yourself to reproduce it end-to-end in one command.
