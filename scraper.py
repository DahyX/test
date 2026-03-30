# -*- coding: utf-8 -*-
"""
scraper.py — Jarvis Web Eyes (BeautifulSoup)
Gathers intelligence from the internet.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import json


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return a BeautifulSoup object."""
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            print(f"[Scraper] Error fetching {url}: {e}")
            return None

    def get_text(self, url: str) -> str:
        """Extract clean text from a webpage."""
        soup = self.fetch_page(url)
        if not soup:
            return ""
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    def get_links(self, url: str, filter_text: Optional[str] = None):
        """Extract all links from a page, optionally filtered by text."""
        soup = self.fetch_page(url)
        if not soup:
            return []
        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if filter_text and filter_text.lower() not in text.lower():
                continue
            links.append({"text": text, "href": href})
        return links

    def scrape_structured(self, url: str, selector: str):
        """Extract elements matching a CSS selector."""
        soup = self.fetch_page(url)
        if not soup:
            return []
        return [el.get_text(strip=True) for el in soup.select(selector)]

    def search_duckduckgo(self, query: str, num_results: int = 5):
        """Search DuckDuckGo and return result titles + URLs."""
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        soup = self.fetch_page(url)
        if not soup:
            return []
        results = []
        for result in soup.select(".result__title")[:num_results]:
            a = result.find("a")
            if a:
                results.append({
                    "title": a.get_text(strip=True),
                    "url": a.get("href", "")
                })
        return results


# Quick test
if __name__ == "__main__":
    s = Scraper()
    results = s.search_duckduckgo("Python automation bots", num_results=3)
    print(json.dumps(results, indent=2))
