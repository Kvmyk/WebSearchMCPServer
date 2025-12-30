import httpx
from bs4 import BeautifulSoup

# Test lite.duckduckgo.com structure
url = 'https://lite.duckduck go.com/lite/?q=test'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

resp = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
soup = BeautifulSoup(resp.text, 'html.parser')

print("=== HTML STRUCTURE ANALYSIS ===\n")

# Find all tables
tables = soup.find_all('table')
print(f"Total tables found: {len(tables)}\n")

# Analyze first few tables
for i, table in enumerate(tables[:3]):
    print(f"\n--- Table {i} ---")
    classes = table.get('class', [])
    print(f"Classes: {classes}")
    rows = table.find_all('tr')
    print(f"Rows: {len(rows)}")
    
    if i == 0:  # Show structure of first table
        print("\nFirst table HTML (truncated):")
        print(str(table)[:800])
        
        # Try to find links
        links = table.find_all('a')
        print(f"\nLinks in first table: {len(links)}")
        if links:
            print(f"First link: {links[0]}")
