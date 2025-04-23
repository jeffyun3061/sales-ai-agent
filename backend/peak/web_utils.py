# DuckDuckGo 무료 검색 기반 회사 정보 요약
# pip install duckduckgo-search beautifulsoup4 requests

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests, re

def _clean(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

def get_company_info(name: str, max_chars: int = 500) -> str:
    """
    DuckDuckGo에서 '{회사명} 회사' 검색 후,
    상위 3개 페이지의 제목·설명·H1을 뽑아 최대 max_chars 글자로 요약
    """
    with DDGS() as ddgs:
        links = [r["href"] for r in ddgs.text(f"{name} 회사", max_results=3)]

    snippets = []
    for url in links:
        try:
            html = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla"}).text
            soup = BeautifulSoup(html, "html.parser")

            title = _clean(soup.title.get_text()) if soup.title else ""
            desc  = soup.find("meta", attrs={"name": "description"})
            desc  = _clean(desc["content"]) if desc and desc.get("content") else ""
            h1    = _clean(soup.h1.get_text()) if soup.h1 else ""

            text = " · ".join(filter(None, [title, desc, h1]))
            if text:
                snippets.append(text)
        except Exception:
            continue

    if not snippets:
        return f"🔍 DuckDuckGo 검색 결과가 없습니다: {name}"

    summary = " ".join(snippets)[:max_chars]
    return f"🔍 웹 요약({name}) : {summary}"
