from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://economics.virginia.edu/people/simon-anderson"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, timeout=60000)
    page.wait_for_timeout(3000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")

print("ALL H3 HEADERS ON PAGE ")
for h3 in soup.find_all("h3"):
    print("H3:", repr(h3.get_text(strip=True)))
