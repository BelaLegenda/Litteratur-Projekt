import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime


def fetch_webpage(url):
    """Fetches webpage content."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    return None


def extract_title(soup):
    """Extracts the title of the article."""
    title_tag = soup.find("title")
    return title_tag.text.strip() if title_tag else "Title not found"


def extract_publishing_date(soup):
    """Extracts publishing date from meta tags and formats it as DD/MM/YYYY."""
    date_meta = soup.find("meta", {"property": "article:published_time"})
    if date_meta and "content" in date_meta.attrs:
        raw_date = date_meta["content"]
        try:
            formatted_date = datetime.strptime(
                raw_date[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
            return formatted_date  # Return as DD/MM/YYYY
        except ValueError:
            return "Publishing date not found"

    return "Publishing date not found"


def detect_author_text(soup):
    """Attempts to find an author's name from visible text using regex."""
    text_content = soup.get_text(separator="\n")

    author_patterns = [
        r"By ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        r"Written by ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        r"Author: ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
    ]

    for pattern in author_patterns:
        match = re.search(pattern, text_content)
        if match:
            return match.group(1)

    return None


def extract_authors_from_script(soup):
    """Extracts author names from JSON-encoded script tags dynamically."""
    script_tags = soup.find_all("script", string=True)

    for script in script_tags:
        try:
            script_text = script.string.strip()
            json_data = json.loads(script_text)

            for key in json_data.keys():
                if "author" in key.lower():
                    authors = json_data[key]
                    if isinstance(authors, list):
                        return ", ".join(authors)
                    elif isinstance(authors, dict) and "name" in authors:
                        return authors["name"]
                    elif isinstance(authors, str):
                        return authors

        except (json.JSONDecodeError, AttributeError):
            continue

    return None


def determine_website_type(url):
    """Determines if the website is an article, newspaper, blogpost, or scientific paper."""
    if "news" in url or "article" in url:
        return "Newspaper"
    elif "blog" in url:
        return "Blogpost"
    elif "journals" in url or "doi.org" in url:
        return "Scientific Paper"
    else:
        return "Article"


def extract_metadata(url):
    """Extracts all relevant metadata from an article."""
    page_content = fetch_webpage(url)
    if not page_content:
        return {"error": "Failed to retrieve the page."}

    soup = BeautifulSoup(page_content, "html.parser")

    # Extracting metadata
    title = extract_title(soup)
    publish_date = extract_publishing_date(soup)
    access_date = datetime.now().strftime("%d/%m/%Y")  # Current date
    authors = detect_author_text(soup) or extract_authors_from_script(
        soup) or "No authors found"
    website_type = determine_website_type(url)

    return {
        "Title": title,
        "Publishing Date": publish_date,
        "Date of Access": access_date,
        "URL": url,
        "Type of Website": website_type,
        "Authors": authors
    }
