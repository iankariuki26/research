from abc import ABC, abstractmethod
from datetime import datetime, timezone
import requests
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import asyncio
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


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



    def __init__(self, run_id: str, *args, **kwargs):
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
        self.run_id = run_id


        self._playwright = None
        self._browser = None

        # metrics
        self.parse_failures = 0
        self.pages_fetched = 0
        self.http_fetches = 0
        self.browser_fetched = 0

        #concurrency
        self.http_sem = asyncio.Semaphore(10) #allows for many http fetches
        self.browser_sem = asyncio.Semaphore(3) #restricts playwright tabs

        logger.info(f"Initialized {self.__class__.__name__} | "
                    f"http_concurrency={self.http_sem._value} | "
                    f"browser_concurrency={self.browser_sem._value}"            
        )




    ###------------------------------------------------------------------------------------------------###

    ### Below this is the required interface for all department scrapers

    ###------------------------------------------------------------------------------------------------###



    @abstractmethod
    async def get_faculty_links(self) -> list[str]:
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



    async def fetch_page(self,url:str) -> tuple[str,str]:
        """
        Fetches a page and returns raw HTML and the fetching method. 
        Tries requests first, falls back to Playwright if Cloudflare blocks.

        """
        try:
            async with self.http_sem:
                #http request
                r = self.session.get(url, timeout = 10)
                #raises error if http response fails
                r.raise_for_status()

                #checks to see if cloudflare blocks scraping through bot test
                if self._is_cloudflare_block(r.text):
                    raise RuntimeError("Cloudflare challenge detected")

                #if scrape successful
                self.http_fetches += 1
                self.pages_fetched += 1

                #returns the raw html and our fetch method, http since successful
                return r.text, "http"
        

        except (requests.HTTPError, requests.Timeout, RuntimeError) as e:
            print(f"[fetch_page] falling back to browser scrape through playwright for {url} because of -> ({e})")
            logger.warning(
                "Falling back to Playwright",
                extra={
                    "department": self.department,
                    "url": url,
                    "reason": str(e),
                },
            )

            async with self.browser_sem:
                #using real browser to load page and get the html
                html = await self._playwright_page_scraper(url)

            self.pages_fetched += 1
            self.browser_fetched += 1
            return html, "browser"





    async def _scrape_one(self, url: str):
        """
        Scrapes a single faculty profile page

        Returns snapshot of html page with some metadata, and returns and normalized faculty data
        """
        try:
            html, fetch_method = await self.fetch_page(url)

            raw_page = {
                "run_id" : self.run_id,
                "department": self.department,
                "url": url,
                "html": html,
                "fetch_method": fetch_method,
                "scraped_at": datetime.now(ZoneInfo("America/New_York")),
            }

            #parse_faculty page is defined uniquely for each department, gets metadata from single faculty page
            record = self.parse_faculty_page(html, url)
            record["department"] = self.department
            record["webpage_link"] = url

            return raw_page, self._normalize(record)

        except Exception as e:
            self.parse_failures += 1
            print(f"[{self.department}] parse failure on {url}: {e}")
            logger.error(
                f"[{self.department}] Parse failure",
                extra={"url":url, "error": str(e)},
            )
            return None, None




    async def scrape(self) -> tuple[list[dict], list[dict]]:
        """This executes the full scraping workflow for a department


            Discovers all faculty profile URLs
            Scrapes all pages concurrently
            Collects both raw HTML captures and normalized faculty records
        
        Returns :
            raw_pages: lossless HTML Captures for reproducibility 
            records: normalized faculty records 
        """

        logger.info(f"[{self.department}] Starting scrape")

        try:
            
            #obtains all faculty profile urls from directory page
            urls = await self.get_faculty_links()

            #creates one scraping task per URL, the tasks run concurrently and are rate-limited
            #by semaphore in fetch_page()
            tasks = [self._scrape_one(url) for url in urls]

            #executes all scraping tasks concurrently and wait for completion
            results = await asyncio.gather(*tasks)



            raw_pages = []
            records = []


            #Appends raw html files and records to respective lists
            #failed scraped are skipped and returned as None
            for raw, record in results:
                if raw:
                    raw_pages.append(raw)  
                if record:
                    records.append(record)   

            return raw_pages, records       

        finally:
            await self.close()

            logger.info(
            f"[{self.department}] Finished scrape | "
            f"pages={self.pages_fetched} "
            f"http={self.http_fetches} "
            f"browser={self.browser_fetched} "
            f"parse_failures={self.parse_failures}"
)







    ###------------------------------------------------------------------------------------------------###

    ### output consistency

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

    ### Playwright Functions for browser scraping when requests fail, utilizing async as well

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







    async def _playwright_page_scraper(self, url: str) -> str:
        """
        This is the playwright scraper which utilizes real browser and mimics real user bypassing cloudflare restrictions
        """
        
        #gets or reuses a shared Chromium browser instance
        browser = await self._get_browser()

        #opens a page/tab in the browser
        page = await browser.new_page()


        #Goes to the target url and waits until the initial html is loaded and parsed
        await page.goto(url, wait_until="domcontentloaded", timeout = 60000)

        #Some of the faculty pages (computer science) can't be used until a specific element appears
        # if this is a faculty page, wait for the page tittle to confirm the real content has loaded
        if "/faculty/" in url:
            await page.wait_for_selector("h1.page_title", timeout=10000)

        # pull the html from the rendered page
        html = await page.content()

        #close the tab to free resources, the browser stays open
        await page.close()


        return html
    





    async def _get_browser(self):
        """
        initializes and returns a playwright browser instance

        The browser is created once per scraper run and is reused across multiple pages to avoid 
        the computational cost of reopening a new browser after each request
        """

        #if browser hasn't been cerated yet, launch it
        if self._browser is None:
            logger.info("[playwright] Launching browser")

            #this starts the playwright engine
            self._playwright = await async_playwright().start()


            
            #launches chromium browser. headless= false means that the browser will pop up visibly in runs 
            #which actually passes the cloudflare bot detection test like in the computer science faculty page
            #If I do this on EC2, it could work without having an UI pop up on the screen
            self._browser = await self._playwright.chromium.launch(headless=False)

        #returns the exiting browser instance
        return self._browser
    




    async def close(self):
        """
        shuts down playwright resources when finished

        """
        #close chromium if exists
        if self._browser:
            await self._browser.close()
            self._browser = None

        #stop playwright engine if exists
        if self._playwright:    
            await self._playwright.stop()
            self._playwright = None

        logger.info(f"[{self.department}] shutting down Playwright resources")

        
        



                


