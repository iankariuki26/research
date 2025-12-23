from abc import ABC, abstractmethod
from datetime import datetime, timezone
import requests
from urllib.parse import urljoin



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

    def fetch_page(self,url:str) -> str:
        """
        Fetches a page and returns raw HTML

        """

        #http request
        r = self.session.get(url, timeout = 10)
        #raises error if http response fails
        r.raise_for_status()

        self.pages_fetched += 1
        return r.text




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
                html = self.fetch_page(url)

                #this is the raw capture which will be appended to
                raw_pages.append({
                    "department" : self.department,
                    "url" : url,
                    "html" : html,
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
    



        
        

            


