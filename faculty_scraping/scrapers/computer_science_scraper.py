import string
from bs4 import BeautifulSoup
from .base import FacultyScraper


class ComputerScience_Scraper(FacultyScraper):
    """
    Scraper implementation for the University of Virginia
    Computer Science faculty directory.

    This class is responsible for:
    1. Discovering faculty profile URLs
    2. Parsing individual faculty profile pages
    """
    
    department = "Computer Science"

    #all faculty under one_url, this also includes Emeritus Faculty
    DIRECTORY_URL = "https://engineering.virginia.edu/department/computer-science/faculty"


    def get_faculty_links(self) -> list[str]:
        """
        Returns sorted list of all Data Science faculty profile URLs
        """

        links = set()

        url = self.DIRECTORY_URL

        html = self.fetch_page(url)

        soup = BeautifulSoup(html,'html.parser')
        
        for a in soup.select("a[href]^='/faculty/']"):


        



