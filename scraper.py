"""
scraper.py
----------
Scrapes book data from books.toscrape.com (a public scraping-practice site)
across at least 3 categories and writes the raw rows to raw_books.csv.

Run this file yourself with a normal internet connection:
    python scraper.py

Why these categories?
We pick a handful of category listing pages (rather than the unfiltered
"All products" pages) because each category page already groups books
by category for us, so we don't have to parse the category out of each
book's own detail page. Any category selection works as long as the
total is >= 60 books across >= 3 categories -- feel free to add/remove
categories in CATEGORY_URLS below.
"""

import time
import requests
from bs4 import BeautifulSoup
import csv

BASE_URL = "http://books.toscrape.com/"

# category slug -> starting listing page. Add more from the site's sidebar
# if you want a bigger sample; each page holds up to 20 books and links to
# "next" for further pages.
CATEGORY_URLS = {
    "Travel": "catalogue/category/books/travel_2/index.html",
    "Mystery": "catalogue/category/books/mystery_3/index.html",
    "Historical Fiction": "catalogue/category/books/historical-fiction_4/index.html",
    "Sequential Art": "catalogue/category/books/sequential-art_5/index.html",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraping exercise)"}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def scrape_category(category_name: str, start_path: str) -> list[dict]:
    """Scrape every book in a category, following pagination ('next') links."""
    rows = []
    next_url = BASE_URL + start_path

    while next_url:
        soup = get_soup(next_url)
        articles = soup.select("article.product_pod")

        for art in articles:
            title = art.h3.a["title"]

            price_text = art.select_one("p.price_color").text  # e.g. "£45.17"

            # The star rating is encoded as a CSS class, e.g.
            # <p class="star-rating Three">. We grab the second class token.
            rating_classes = art.select_one("p.star-rating")["class"]
            star_rating = [c for c in rating_classes if c != "star-rating"][0]

            availability = art.select_one("p.instock.availability").text.strip()

            rows.append(
                {
                    "title": title,
                    "price": price_text,
                    "star_rating": star_rating,
                    "availability": availability,
                    "category": category_name,
                }
            )

        # Follow pagination within the category, if there is a "next" page.
        next_link = soup.select_one("li.next a")
        if next_link:
            # next_link['href'] is relative to the current page's folder
            current_dir = next_url.rsplit("/", 1)[0]
            next_url = current_dir + "/" + next_link["href"]
        else:
            next_url = None

        time.sleep(0.5)  # be polite to the server between requests

    return rows


def main():
    all_rows = []
    for category_name, start_path in CATEGORY_URLS.items():
        print(f"Scraping category: {category_name}")
        category_rows = scrape_category(category_name, start_path)
        print(f"  -> {len(category_rows)} books found")
        all_rows.extend(category_rows)

    print(f"\nTotal books scraped: {len(all_rows)}")

    with open("raw_books.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "price", "star_rating", "availability", "category"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print("Saved to raw_books.csv")


if __name__ == "__main__":
    main()
