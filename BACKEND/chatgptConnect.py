import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import openai

# OpenAI API key (Replace with your actual API key)
OPENAI_API_KEY = "ENTER API KEY HERE"


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


def extract_main_text(soup):
    """Extracts main body text from the article."""
    paragraphs = soup.find_all("p")
    article_text = "\n".join([p.text.strip()
                             for p in paragraphs if p.text.strip()])
    return article_text[:4000]  # Limit to 4000 chars (ChatGPT API limit)


def extract_metadata(url):
    """Extracts all relevant metadata from an article."""
    page_content = fetch_webpage(url)
    if not page_content:
        return {"error": "Failed to retrieve the page."}

    soup = BeautifulSoup(page_content, "html.parser")

    # Extract metadata
    title = extract_title(soup)
    publish_date = extract_publishing_date(soup)
    authors = detect_author_text(soup) or extract_authors_from_script(
        soup) or "No authors found"
    article_text = extract_main_text(soup)

    return {
        "Title": title,
        "Publishing Date": publish_date,
        "Authors": authors,
        "Article Text": article_text
    }


def ask_chatgpt(content):
    """Sends extracted content to ChatGPT API and gets a response."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that extracts metadata from articles accurately."},
            {"role": "user",
                "content": f"Here is an article:\n\n{content}\n\nPlease extract the title, author(s), and publishing date."}
        ]
    )

    return response.choices[0].message.content


# Example usage
article_link = "https://www.dr.dk/nyheder/kultur/gamle-tweets-kan-faa-det-hele-til-vaelte-stor-oscar-favorit-men-det-kan-vaere-en"

# Step 1: Extract metadata
metadata = extract_metadata(article_link)

# Step 2: Send extracted content to ChatGPT
chatgpt_response = ask_chatgpt(metadata["Article Text"])

# Step 3: Print results
print("Extracted Metadata:")
for key, value in metadata.items():
    if key != "Article Text":  # Don't print full article text
        print(f"{key}: {value}")

print("\nChatGPT Corrected Metadata:")
print(chatgpt_response)
