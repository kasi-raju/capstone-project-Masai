"""
clean_convert.py
-----------------
Reads raw_books.csv (produced by scraper.py) and cleans it into proper
types, then adds the price_inr column using the project's fixed baseline
conversion rate.

Fixed conversion rate (as required by the assignment brief):
    1 GBP = 105.50 INR
This is an artificial, project-defined constant -- not a live market
rate -- so it needs no API call, no key, and no date reference.

Cleaning decisions (documented, as the brief asks):
- price: strip the leading "£" and cast to float -> price_gbp
- star_rating: map the text word ("One".."Five") to an int 1-5 -> rating
- availability: any text containing "In stock" -> True, else False -> in_stock
- Rows where price or rating fail to parse are DROPPED rather than
  median-imputed. Justification: on this site, price and rating are
  scraped straight from a CSS class/text token, so a parse failure means
  the row's structure didn't match what we expected at all (e.g. a
  malformed page) -- imputing a fake price/rating for a book we can't
  otherwise verify would quietly corrupt the catalog rather than protect
  it, whereas simply dropping the (rare/nonexistent, in practice) bad row
  keeps the dataset trustworthy. We print how many rows were dropped so
  the decision is auditable.
"""

import pandas as pd

GBP_TO_INR = 105.50  # fixed, project-defined constant -- see README

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- price_gbp -----------------------------------------------------
    df["price_gbp"] = (
        df["price"].astype(str).str.replace("£", "", regex=False).str.strip()
    )
    df["price_gbp"] = pd.to_numeric(df["price_gbp"], errors="coerce")

    # --- rating ----------------------------------------------------------
    df["rating"] = df["star_rating"].map(RATING_WORDS)

    # --- in_stock --------------------------------------------------------
    df["in_stock"] = df["availability"].astype(str).str.contains(
        "In stock", case=False, na=False
    )

    before = len(df)
    df = df.dropna(subset=["price_gbp", "rating"])
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} row(s) that failed to parse price/rating.")

    df["rating"] = df["rating"].astype(int)

    # --- price_inr (required fixed-rate baseline) -------------------------
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)

    return df[
        ["title", "category", "price_gbp", "price_inr", "rating", "in_stock"]
    ]


def main():
    raw = pd.read_csv("raw_books.csv")
    print(f"Loaded {len(raw)} raw rows.")

    cleaned = clean(raw)
    print(f"{len(cleaned)} clean rows after type conversion.")

    cleaned.to_csv("clean_books.csv", index=False)
    print("Saved to clean_books.csv")
    print(cleaned.head())


if __name__ == "__main__":
    main()
