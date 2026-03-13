import requests
from bs4 import BeautifulSoup
from app.utils.logger import get_logger
from urllib.parse import urljoin, urlparse

log = get_logger()

def get_all_doc_links(base_url: str) -> list[str]:
    """Finds all links on the page that belong to the same domain."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        domain = urlparse(base_url).netloc
        
        links = {base_url.split('#')[0]}
        for a in soup.find_all('a', href=True):
            full_url = urljoin(base_url, a['href'])
            # Only include links from the same website and exclude anchors (#)
            if urlparse(full_url).netloc == domain:
                links.add(full_url.split('#')[0])
        
        return sorted(links)
    except Exception as e:
        log.error(f"Error finding links: {e}")
        return [base_url]

def extract_text_from_url(url: str) -> str:
    """
    Fetches HTML from a URL and extracts clean text.
    """
    try:
        log.info(f"Scraping documentation from: {url}")
        # Use a User-Agent to avoid being blocked by websites
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove elements that aren't useful for documentation text
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Get text with newlines so your clean.py can process it better
        return soup.get_text(separator="\n")

    except Exception as e:
        log.error(f"Web scraping failed: {e}")
        return ""
