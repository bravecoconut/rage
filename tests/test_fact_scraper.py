import requests
from bs4 import BeautifulSoup
import re

url = "https://www.thefactsite.com/daily-facts/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

print("Filtered Facts:")
facts = []
for p in soup.find_all('p'):
    text = p.get_text(strip=True)
    classes = p.get('class', [])
    
    # User said: "fact are in p element with a random class"
    # Looking at our previous output, it's typically gb-text and gb-text-<8-hex-chars>
    # e.g., gb-text-2a98bcfc, gb-text-fed63eb9, gb-text-fd34e53f
    has_random_class = any(re.match(r'^gb-text-[a-f0-9]{8}$', c) for c in classes)
    
    if has_random_class and len(text) > 30:
        # Filter out obvious non-facts like footers
        if "Learn something about everything" in text: continue
        if "Luke Ward is the owner" in text: continue
        if "The facts on this page" in text: continue
        if "If you notice anything" in text: continue
        if "The Fact Site is the number one source" in text: continue
        
        facts.append(text)

for i, f in enumerate(facts):
    print(f"[{i}] {f}")
print(f"Total facts: {len(facts)}")
