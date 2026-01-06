import requests
from bs4 import BeautifulSoup
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

def check_site(url, name):
    print(f"\n--- Checking {name} ---")
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.find_all('article', limit=3)
        
        if not articles:
            print("No articles found.")
            return

        for i, article in enumerate(articles):
            print(f"\nArticle {i+1}:")
            print(f"Title: {article.find('h2').get_text().strip() if article.find('h2') else 'No H2'}")
            
            # Print all text to see where date is
            print(f"Full Text: {article.get_text(separator=' | ', strip=True)}")
            
            # Try to find specific date container candidates
            spans = article.find_all('span')
            for s in spans:
                txt = s.get_text().strip()
                if any(x in txt for x in ['WIB', 'lalu', 'hours', 'mins', 'Jan', 'Feb', 'Mar', '2025', '2026']):
                    print(f"Potential Date Candidate (span): '{txt}' | Classes: {s.get('class')}")

    except Exception as e:
        print(f"Error: {e}")

check_site("https://www.cnbcindonesia.com/search?query=BBCA", "CNBC Indonesia")
check_site("https://www.cnnindonesia.com/search/?query=BBCA", "CNN Indonesia")
