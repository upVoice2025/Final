import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
OUTPUT_FOLDER = "interview"
DETAILS_FOLDER = os.path.join(OUTPUT_FOLDER, "details")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(DETAILS_FOLDER, exist_ok=True)

BASE_URL = "https://www.upliftingvoices.org/interview.aspx"
TOTAL_RECORDS = 224
PER_PAGE = 8
TOTAL_PAGES = (TOTAL_RECORDS + PER_PAGE - 1) // PER_PAGE  # 28 pages
current_year = datetime.now().year

# --- Top Navigation (heroes-style) ---
TOP_NAV_HTML = """
<nav>
    <ul>
        <li class="nav-item mobile" id="hamburger">
            <input type="checkbox" id="toggle-mobile-menu">
            <label for="toggle-mobile-menu">&#9776;</label>
            <div id="mobile-menu">
                <div class="header-section">
                    <span class="logo-mobile"><a href="index.html"><img src="images/100xlogo-dark.png" alt="UV logo"></a></span>
                    <label for="toggle-mobile-menu">&times;</label>
                </div>
                <ul>
                    <li class="mobile-nav-item"><a href="index.html">Home</a></li>
                    <li class="mobile-nav-item"><a href="interview/interview1.html">Stories</a></li>
                    <li class="mobile-nav-item"><a href="heroes/heroes1.html">Role Models</a></li>
                    <li class="mobile-nav-item"><a href="gallery/gallery1.html">Showcase</a></li>
                    <li class="mobile-nav-item"><a href="MakingDifference.html">Making Differences</a></li>
                    <li class="mobile-nav-item"><a href="InspirationPillars.html">Pillars</a></li>
                    <li class="mobile-nav-item"><a href="showcase.html">Creative Examples</a></li>
                    <li class="mobile-nav-item"><a href="FriendlyApp.html">Friendly Apps</a></li>
                    <li class="mobile-nav-item"><a href="book.html">Read the Book</a></li>
                </ul>
            </div>
        </li>

        <li class="nav-item mobile"><span class="logo-mobile"><a href="index.html"><img src="images/100xlogo.png" alt="UV logo"></a></span></li>

        <!-- Desktop nav -->
        <li class="nav-item desktop"><a href="index.html" id="logo"><img src="images/100xlogo.png" alt="UV logo"></a></li>
        <li class="nav-item desktop"><a href="index.html">Home</a></li>
        <li class="nav-item desktop"><a href="interview/interview1.html">Stories</a></li>
        <li class="nav-item desktop"><a href="heroes/heroes1.html">Role Model</a></li>
        <li class="nav-item desktop"><a href="gallery/gallery1.html">Showcase</a></li>
        <li class="nav-item desktop dropdown">
            <a class="dropdown-button">Resources</a>
            <div class="dropdown-content">
                <a href="MakingDifference.html">Making Differences</a>
                <a href="InspirationPillars.html">Pillars</a>
                <a href="showcase.html">Creative Examples</a>
                <a href="FriendlyApp.html">Friendly Apps</a>
            </div>
        </li>
        <li class="nav-item desktop c-to-a" style="margin-left: 20px;"><a href="book.html" class="button">Read the Book</a></li>
    </ul>
</nav>
"""

# --- Footer (heroes-style) ---
FOOTER_HTML = f"""
<footer>
    <div class="container">
        <div class="row">
            <div class="columns seven">
                <ul>
                    <li><a href="index.html" aria-label="Home">Home</a></li>
                    <li class="nav-slash">/</li>
                    <li><a href="about.html" aria-label="About">About Us</a></li>
                    <li class="nav-slash">/</li>
                    <li><a href="policy.html" aria-label="policy">Policy</a></li>
                    <li class="nav-slash">/</li>
                    <li><a href="parents.html" aria-label="parents">Parents</a></li>
                    <li class="nav-slash">/</li>
                    <li><a href="faq.html" aria-label="faq">FAQ</a></li>
                    <li class="nav-slash">/</li>
                    <li><a href="contact.html" aria-label="contactus">Contact</a></li>
                    <li>
                        Copyright &copy; {current_year} Uplifting Voices. All rights reserved.
                    </li>
                </ul>
            </div>
        </div>
    </div>
</footer>
"""

# --- HTML Fixer ---
def fix_interview_html(html: str, page_num: int, total_pages: int) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Replace nav/footer
    if soup.find("nav"):
        soup.find("nav").replace_with(BeautifulSoup(TOP_NAV_HTML, "html.parser"))
    if soup.find("footer"):
        soup.find("footer").replace_with(BeautifulSoup(FOOTER_HTML, "html.parser"))
    
    # Fix CSS/JS paths
    for tag in soup.find_all("link", href=True):
        if tag["href"].startswith("css/"):
            tag["href"] = "/" + tag["href"]
    for tag in soup.find_all("script", src=True):
        if tag["src"].startswith("js/"):
            tag["src"] = "/" + tag["src"]
    
    # Fix images
    for img in soup.find_all("img", src=True):
        if img["src"].startswith("images/"):
            img["src"] = "/" + img["src"]

    # Update article links to local details pages
    for a_tag in soup.select("div#portfolio a, div#portfolio1 a"):
        href = a_tag.get("href", "")
        if "id=" in href:
            try:
                id_val = href.split("id=")[1].split("&")[0]
                a_tag["href"] = f"/interview/details/I{id_val}.html"
            except Exception:
                continue

    # Pagination links
    page_div = soup.find("div", id="page")
    if page_div:
        page_div.clear()
        if page_num > 1:
            prev_link = soup.new_tag("a", href=f"interview{page_num-1}.html", **{"class": "button"})
            prev_link.string = "Previous"
            page_div.append(prev_link)
            page_div.append(soup.new_string(" "))
        if page_num < total_pages:
            next_link = soup.new_tag("a", href=f"interview{page_num+1}.html", **{"class": "button"})
            next_link.string = "Next"
            page_div.append(next_link)
    
    return str(soup)

# --- Main Execution ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for page_num in range(1, TOTAL_PAGES + 1):
        page_url = f"{BASE_URL}?id={page_num}"
        print(f"\n📄 Fetching page {page_num}: {page_url}")
        try:
            page.goto(page_url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("div.container", timeout=20000)
            html_content = page.content()
            
            fixed_html = fix_interview_html(html_content, page_num, TOTAL_PAGES)
            output_file = os.path.join(OUTPUT_FOLDER, f"interview{page_num}.html")
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(fixed_html)
            
            print(f"✅ Saved {output_file}")
            time.sleep(1)  # polite delay
        except Exception as e:
            print(f"⚠️ Failed to fetch page {page_num}: {e}")

    browser.close()

print(f"\n🎉 All {TOTAL_PAGES} interview pages saved in '{OUTPUT_FOLDER}' with proper nav, footer, detail links, and pagination.")
