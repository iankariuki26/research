from abc import ABC, abstractmethod
from datetime import datetime, timezone
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright



class FacultyScraper(ABC):

    """
    This is the abstract base class which defines the shared scaping workflow 
    and output contract for all faculty scrapers


    Subclasses are responsible only for:
        - discovering faculty profile URLs
        - parsing department-specific profile page HTML

    This class:
        - Manages HTTP state
        - Tracks run-level metrics
        - Guarantees a consistent output schema
    """

    #department name, which must be overridden by subclasses
    department: str



    def __init__(self):
        #only uses a single consistent HTTP session instead of a new one for every page
        #mimics real user to prevent scraping blocking risk
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        # Run-level counters for observability and metrics
        self.parse_failures = 0
        self.pages_fetched = 0
        self.http_fetches = 0
        self.browser_fetched = 0




    ###------------------------------------------------------------------------------------------------###

    ### Below this is the required interface for all department scrapers

    ###------------------------------------------------------------------------------------------------###


    @abstractmethod
    def get_faculty_links(self) -> list[str]:
        """
        Returns all the faculty profile URLs for a department
        
        Subclasses must implement the discovery logic
        """
        pass

    @abstractmethod 
    def parse_faculty_page(self, html:str, url:str) -> dict:
        """
        Extracts normalized faculty data from a single profile page

        Subclasses should only return the fields they can confidently extract
        The missing fields will be filled in by the normalization step
        """
        pass


    ###------------------------------------------------------------------------------------------------###

    ### Below this is the shared workflow (which will NOT be overridden in the subclasses )

    ###------------------------------------------------------------------------------------------------###

    def fetch_page(self,url:str) -> tuple[str,str]:
        """
        Fetches a page and returns raw HTML and the fetching method. 
        Tries requests first, falls back to Playwright if Cloudflare blocks.

        """
        try:
            #http request
            r = self.session.get(url, timeout = 10)
            #raises error if http response fails
            r.raise_for_status()

            if self._is_cloudflare_block(r.text):
                raise RuntimeError("Cloudflare challenge detected")

            self.http_fetches += 1
            self.pages_fetched += 1
            return r.text, "http"
        
        except (requests.HTTPError, requests.Timeout, RuntimeError) as e:
            print(f"[fetch_page] falling back to browser scrape through playwright for {url} ({e})")

            html = self._playwright_page_scraper(url)
            self.pages_fetched += 1
            self.browser_fetches += 1
            return html, "browser"
    





    def scrape(self) -> tuple[list[dict], list[dict]]:
        """This executes the scraping workflow
        
        Returns :
            raw_pages: lossless HTML Captures for reproducibility 
            records: normalized faculty records 
        """

        raw_pages = []
        records = []

        for url in self.get_faculty_links():
            try:
                html, fetch_method = self.fetch_page(url)

                #this is the raw capture which will be appended to
                raw_pages.append({
                    "department" : self.department,
                    "url" : url,
                    "html" : html,
                    "fetch_method": fetch_method,
                    "scraped_at" : datetime.now(timezone.utc)
                })

                #this is the normalized extraction
                record = self.parse_faculty_page(html, url)
 
                record["department"] = self.department
                record["webpage_link"] = url
                records.append(self._normalize(record))

            
            except Exception as e:
                self.parse_failures += 1
                print(f"[{self.department}] parse failure on {url}: {e}")

        return raw_pages, records




    ###------------------------------------------------------------------------------------------------###

    ### output contract

    ###------------------------------------------------------------------------------------------------###



    def _normalize(self, record: dict) -> dict:
        """
        Consistent schema for all the departments minus the timestamp which will be implemented through the 
        storing process in duckdb_writer.
        Any missing fields are set to None
        """

        schema = {
                "name": None,
                "department": None,
                "webpage_link": None,
                "title": None,
                "bio": None,
                "expertise": None,
                "email": None,
            }

        schema.update(record)
        return schema
            


###------------------------------------------------------------------------------------------------###

    ### url handling

###------------------------------------------------------------------------------------------------###
    
    def clean_url(self, base: str, path: str) -> str:
        """Safely joins base URL and path"""
        return urljoin(base,path)
    


###------------------------------------------------------------------------------------------------###

    ### helper functions

###------------------------------------------------------------------------------------------------###
    

    def _is_cloudflare_block(self, response_text: str) -> bool:
        """
        this is a helper function for the get_pages function. This checks to see if there is a cloudflare block 
        on the website when we are trying to scrape html through the requests package. The Computer Science department
        for example blocks http clients through cloudflare to prevent bots. If the response_text contains
        cloudflare response of "just a moment" or "cloudflare" then it will return true and utilize another scraping method
        specifically playwright which launches a real browser, runs javascript, and passes bot checks, although I must 
        keep in mind that is is slower and more computationally expensive, so always starting of with a .requests.
        """
        return (
            "Just a moment" in response_text or "cloudflare" in response_text.lower()
        )

    def _playwright_page_scraper(self, url: str) -> str:
        """
        This is the playwright scraper which utilizes real browser and mimics real user bypassing cloudflare restrictions
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout = 60000)
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()

            return html
        



                


