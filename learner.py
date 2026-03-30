# -*- coding: utf-8 -*-
"""
learner.py — Smart Internet Self-Learning Crawler
Improvements over v1:
  - Source ranking (docs/official/GitHub > general web)
  - Content quality filtering
  - Deduplication via embeddings
  - Chunked storage with metadata
  - Time-sensitivity detection
"""

import threading
import time
import random
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, unquote
from urllib.robotparser import RobotFileParser
from memory import Memory
from collections import deque

# Per-domain last-request timestamp
_domain_last_hit: dict = {}
_robots_cache: dict = {}

def _is_allowed_by_robots(url: str) -> bool:
    """Check robots.txt for a URL. Cached per domain."""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    if domain not in _robots_cache:
        rp = RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        try:
            rp.read()
            _robots_cache[domain] = rp
        except Exception:
            _robots_cache[domain] = None
    rp = _robots_cache.get(domain)
    if rp is None:
        return True
    return rp.can_fetch("*", url)

def _domain_rate_limit(url: str, min_delay: float = 3.0):
    """Enforce per-domain minimum delay between requests."""
    parsed = urlparse(url)
    domain = parsed.netloc
    last = _domain_last_hit.get(domain, 0)
    elapsed = time.time() - last
    if elapsed < min_delay:
        time.sleep(min_delay - elapsed)
    _domain_last_hit[domain] = time.time()
from memory import Memory
from collections import deque


# ── Seed topics ──────────────────────────────────────────────────────────────
SEED_TOPICS = [
    "artificial intelligence", "machine learning", "deep learning",
    "python programming", "computer science", "cybersecurity",
    "robotics", "natural language processing", "data science",
    "history of the world", "mathematics", "physics", "biology",
    "chemistry", "astronomy", "space exploration", "medicine",
    "english language", "grammar", "philosophy", "psychology",
    "economics", "climate change", "renewable energy", "quantum computing",
    "blockchain", "internet of things", "software engineering",
    "networking", "cloud computing", "linux", "human anatomy",
    "nutrition", "fitness", "mental health", "world news",
    "science news", "technology news", "business",
]

# ── Source quality rankings ──────────────────────────────────────────────────
HIGH_QUALITY_DOMAINS = {
    # Documentation & reference
    "docs.python.org": 0.95, "developer.mozilla.org": 0.95,
    "docs.microsoft.com": 0.90, "learn.microsoft.com": 0.90,
    "docs.oracle.com": 0.90, "docs.aws.amazon.com": 0.85,
    # Encyclopedia & educational
    "en.wikipedia.org": 0.85, "britannica.com": 0.90,
    "khanacademy.org": 0.85, "coursera.org": 0.80,
    "mit.edu": 0.90, "stanford.edu": 0.90, "harvard.edu": 0.90,
    # Technical
    "github.com": 0.80, "stackoverflow.com": 0.75,
    "arxiv.org": 0.90, "nature.com": 0.90, "sciencedirect.com": 0.85,
    # News (time-sensitive)
    "reuters.com": 0.80, "bbc.com": 0.80, "apnews.com": 0.80,
    "techcrunch.com": 0.70, "arstechnica.com": 0.75,
}

LOW_QUALITY_INDICATORS = [
    "click here", "subscribe now", "buy now", "limited offer",
    "sign up free", "download now", "sponsored", "advertisement",
    "cookie policy", "privacy policy", "terms of service",
]

NEWS_DOMAINS = {
    "reuters.com", "bbc.com", "apnews.com", "cnn.com",
    "techcrunch.com", "arstechnica.com", "theverge.com",
    "wired.com", "nytimes.com", "theguardian.com",
}

# ── Blocked domains ──────────────────────────────────────────────────────────
BLOCKED_DOMAINS = [
    "facebook.com", "twitter.com", "instagram.com", "tiktok.com",
    "pinterest.com", "linkedin.com", "reddit.com", "youtube.com",
    "amazon.com", "ebay.com", "etsy.com", "aliexpress.com",
    "doubleclick.net", "googleadservices.com",
]

BLOCKED_PATTERNS = [
    r'/login', r'/signup', r'/register', r'/cart', r'/checkout',
    r'/account', r'\.pdf$', r'\.jpg$', r'\.png$', r'\.gif$',
    r'\.mp4$', r'\.zip$', r'javascript:', r'mailto:', r'tel:',
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_CONTENT_LENGTH = 8000
CRAWL_DELAY = (3, 8)
MAX_QUEUE_SIZE = 2000
MIN_CONTENT_LENGTH = 300


class Learner:
    def __init__(self, memory: Memory, verbose: bool = False):
        self.memory = memory
        self.verbose = verbose
        self.queue = deque()
        self._load_queue()
        self.running = False
        self._thread = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._topic_index = 0
        self._failed_urls = set()
        self._pages_learned = 0
        self._pages_skipped = 0

    def _log(self, msg: str):
        """Only print if verbose mode is on."""
        if self.verbose:
            print(msg)

    QUEUE_KEY = "learner_queue"

    def _save_queue(self):
        """Persist current queue to working memory."""
        try:
            items = list(self.queue)[:500]  # cap at 500
            self.memory.set_working(self.QUEUE_KEY, json.dumps(items))
        except Exception:
            pass

    def _load_queue(self):
        """Restore queue from working memory on startup."""
        try:
            entry = self.memory.get_working(self.QUEUE_KEY)
            if entry and entry.get("value"):
                items = json.loads(entry["value"])
                self.queue.extend(items)
                self._log(f"[Learner] Restored {len(items)} queued URLs from memory")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    #  SOURCE QUALITY
    # ─────────────────────────────────────────────────────────────────────────
    def _get_source_quality(self, url: str) -> float:
        """Rate source quality from 0.0 to 1.0."""
        try:
            domain = urlparse(url).netloc.lower().lstrip("www.")
            # Check exact match
            if domain in HIGH_QUALITY_DOMAINS:
                return HIGH_QUALITY_DOMAINS[domain]
            # Check partial match (subdomain)
            for hq_domain, score in HIGH_QUALITY_DOMAINS.items():
                if domain.endswith(hq_domain):
                    return score * 0.9
            # Educational domains
            if domain.endswith(".edu") or domain.endswith(".gov"):
                return 0.85
            if domain.endswith(".org"):
                return 0.65
            return 0.4  # Unknown general web
        except Exception:
            return 0.3

    def _is_time_sensitive(self, url: str, content: str) -> bool:
        """Detect if content is time-sensitive (news, dated articles)."""
        domain = urlparse(url).netloc.lower()
        if any(nd in domain for nd in NEWS_DOMAINS):
            return True
        # Check for date-heavy content
        date_patterns = r'\b(2024|2025|2026|yesterday|today|this week|breaking|latest)\b'
        if len(re.findall(date_patterns, content[:500], re.IGNORECASE)) >= 2:
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    #  CONTENT QUALITY
    # ─────────────────────────────────────────────────────────────────────────
    def _assess_content_quality(self, text: str, soup: BeautifulSoup) -> float:
        """Score content quality from 0.0 to 1.0."""
        if len(text) < MIN_CONTENT_LENGTH:
            return 0.0

        score = 0.5  # baseline

        # Penalize low information density
        words = text.split()
        if len(words) < 50:
            return 0.1

        # Check for low-quality indicators
        text_lower = text.lower()
        spam_count = sum(1 for ind in LOW_QUALITY_INDICATORS if ind in text_lower)
        score -= spam_count * 0.08

        # Reward long-form content
        if len(words) > 200:
            score += 0.15
        if len(words) > 500:
            score += 0.1

        # Reward structured content (paragraphs, headings)
        p_tags = len(soup.find_all("p"))
        h_tags = len(soup.find_all(re.compile(r'^h[1-6]$')))
        if p_tags > 3:
            score += 0.1
        if h_tags > 1:
            score += 0.1

        # Penalize too many links relative to text (link farms)
        links = len(soup.find_all("a"))
        if links > 0 and len(words) > 0:
            link_ratio = links / len(words)
            if link_ratio > 0.3:
                score -= 0.2

        # Reward code blocks (technical content)
        code_blocks = len(soup.find_all(["code", "pre"]))
        if code_blocks > 0:
            score += 0.1

        return max(0.0, min(1.0, score))

    # ─────────────────────────────────────────────────────────────────────────
    #  URL FILTERING
    # ─────────────────────────────────────────────────────────────────────────
    def _is_blocked(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            if any(b in domain for b in BLOCKED_DOMAINS):
                return True
            if any(re.search(p, url, re.IGNORECASE) for p in BLOCKED_PATTERNS):
                return True
            return False
        except Exception:
            return True

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ("http", "https")
                and bool(parsed.netloc)
                and not self._is_blocked(url)
                and url not in self._failed_urls
            )
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    #  SEARCH & CRAWL
    # ─────────────────────────────────────────────────────────────────────────
    def _duckduckgo_search(self, query: str, num_results: int = 10) -> list:
        urls = []
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            resp = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select(".result__title a"):
                href = a.get("href", "")
                if "uddg=" in href:
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        href = unquote(match.group(1))
                if href.startswith("http") and self._is_valid_url(href):
                    if not self.memory.already_visited(href) and href not in urls:
                        urls.append(href)
        except Exception as e:
            self._log(f"[Learner] Search failed for '{query}': {e}")

        # Sort by source quality (best sources first)
        urls.sort(key=lambda u: self._get_source_quality(u), reverse=True)
        return urls[:num_results]

    def _clean_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "iframe", "noscript", "form", "button"]):
            tag.decompose()
        main = soup.find("article") or soup.find("main") or soup.find("body")
        text = main.get_text(separator=" ", strip=True) if main else soup.get_text(separator=" ", strip=True)
        return re.sub(r'\s+', ' ', text)[:MAX_CONTENT_LENGTH]

    def _extract_topic(self, soup: BeautifulSoup, url: str) -> str:
        title = soup.find("title")
        if title:
            t = re.split(r'\s*[|\-]\s*', title.get_text(strip=True))[0].strip()
            return t[:120]
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)[:120]
        return urlparse(url).netloc

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        links = []
        base_domain = urlparse(base_url).netloc
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"]).split("#")[0].split("?")[0]
            if (
                self._is_valid_url(href)
                and not self.memory.already_visited(href)
                and href not in self.queue
            ):
                links.append(href)

        # Prioritize high-quality sources
        links.sort(key=lambda u: self._get_source_quality(u), reverse=True)

        same = [l for l in links if urlparse(l).netloc == base_domain]
        other = [l for l in links if urlparse(l).netloc != base_domain]
        return (same[:6] + other[:4])[:10]

    def _crawl_one(self, url: str):
        if not _is_allowed_by_robots(url):
            self._log(f"[Learner] Blocked by robots.txt: {url}")
            return
        _domain_rate_limit(url)
        if self.memory.already_visited(url) or not self._is_valid_url(url):
            return
        try:
            resp = self.session.get(url, timeout=12, allow_redirects=True)
            resp.raise_for_status()
            if "text/html" not in resp.headers.get("Content-Type", ""):
                return

            soup = BeautifulSoup(resp.text, "html.parser")
            topic = self._extract_topic(soup, url)
            content = self._clean_text(soup)

            # Quality gate
            quality = self._assess_content_quality(content, soup)
            source_quality = self._get_source_quality(url)
            combined_quality = (quality * 0.6) + (source_quality * 0.4)

            if combined_quality < 0.25:
                self._pages_skipped += 1
                # Still mark as visited to avoid re-checking
                with self.memory._connect() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO visited_urls (url, visited_at) VALUES (?, ?)",
                        (url, __import__("datetime").datetime.now().isoformat())
                    )
                    conn.commit()
                return

            is_time_sensitive = self._is_time_sensitive(url, content)

            # Store with quality metadata (memory handles chunking + dedup)
            stored = self.memory.store_semantic(
                url, topic, content,
                source_quality=combined_quality,
                is_time_sensitive=is_time_sensitive
            )

            self._pages_learned += 1
            quality_label = "★★★" if combined_quality > 0.7 else "★★" if combined_quality > 0.4 else "★"
            self._log(f"[Learner] {quality_label} Learned: {topic[:60]} ({stored} chunks)")

            for link in self._extract_links(soup, url):
                if len(self.queue) < MAX_QUEUE_SIZE:
                    self.queue.append(link)

        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            self._failed_urls.add(url)
        except Exception as e:
            self._log(f"[Learner] Skipped: {str(e)[:60]}")

    def _discover_new_urls(self):
        topic = SEED_TOPICS[self._topic_index % len(SEED_TOPICS)]
        self._topic_index += 1
        self._log(f"[Learner] Discovering: {topic}")
        urls = self._duckduckgo_search(topic, num_results=10)
        for url in urls:
            if len(self.queue) < MAX_QUEUE_SIZE:
                self.queue.append(url)

    def _run_loop(self):
        self._log("[Learner] Starting smart learning loop...")
        random.shuffle(SEED_TOPICS)
        for topic in SEED_TOPICS[:10]:
            urls = self._duckduckgo_search(topic, num_results=5)
            for url in urls:
                self.queue.append(url)
            time.sleep(1)

        while self.running:
            if len(self.queue) < 20:
                self._discover_new_urls()
            if not self.queue:
                time.sleep(5)
                continue
            url = self.queue.popleft()
            if len(self.queue) % 10 == 0:
                self._save_queue()
            self._crawl_one(url)
            time.sleep(random.uniform(*CRAWL_DELAY))

        self._log("[Learner] Learning loop stopped.")

    def start(self):
        if self._thread and self._thread.is_alive():
            self._log("[Learner] Already running.")
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._log("[Learner] Background learning started!")

    def stop(self):
        self.running = False

    def add_topic(self, query: str):
        self._log(f"[Learner] Searching the web for: {query}")
        urls = self._duckduckgo_search(query, num_results=8)
        added = 0
        for url in urls:
            if not self.memory.already_visited(url):
                self.queue.appendleft(url)
                added += 1
        if added:
            self._save_queue()
            self._log(f"[Learner] Queued {added} pages about: {query}")
        else:
            self._log(f"[Learner] No new pages found for: {query}")

    def status(self) -> str:
        stats = self.memory.stats()
        state = "Running" if self.running else "Stopped"
        return (
            f"Learning Status: {state}\n"
            f"Queue: {len(self.queue)} pages pending\n"
            f"Semantic chunks: {stats['semantic_chunks']}\n"
            f"Legacy facts: {stats['legacy_facts']}\n"
            f"URLs visited: {stats['urls_visited']}\n"
            f"Pages learned: {self._pages_learned} | Skipped (low quality): {self._pages_skipped}\n"
            f"Episodes: {stats['episodes']} | Procedures: {stats['procedures']}\n"
            f"Last learned: {stats['last_learned']}"
        )
