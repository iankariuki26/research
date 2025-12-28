import string
from bs4 import BeautifulSoup
from .base import FacultyScraper
import asyncio


class ComputerScience_Scraper(FacultyScraper):
    """
    Scraper implementation for the University of Virginia
    Computer Science faculty directory.

    This class is responsible for:
    1. Discovering faculty profile URLs
    2. Parsing individual faculty profile pages
    """

    def __init__(self, run_id: str):
        super().__init__(run_id)
        self.department = "Computer Science"
    
    # department = "Computer Science"

    #all faculty under one_url, this also includes Emeritus Faculty
    DIRECTORY_URL = "https://engineering.virginia.edu/department/computer-science/faculty"
    
    BASE_URL = "https://engineering.virginia.edu"

    async def get_faculty_links(self) -> list[str]:
        """
        Returns sorted list of all Computer Science faculty profile URLs
        """
        url = self.DIRECTORY_URL

        #prevents duplicates across directory pages
        links = set()

        #html of faculty listing, inherited from FacultyScraper, ignoring tuple value (html, fetch_method <-ignored)
        html, _ = await self.fetch_page(url)

        soup = BeautifulSoup(html, "html.parser")

        #grabs all the faculty urls in one page
        for a in soup.select("a[href^='/faculty/']"):
                links.add(self.BASE_URL + a["href"])
        

        return sorted(links)
    
    
    def parse_faculty_page(self, html, url):
        """
        Extracts the normalized faculty data within a single computer science faculty profile page

        Args:
            html: the raw HTML of the faculty profile page
            url: The profile page (for context and debugging)

        Returns:
            A dictionary with all the normalized faculty fields
        """

        soup = BeautifulSoup(html, "html.parser")

        name_tag = soup.find("h1", class_="page_title")
        name = name_tag.get_text(strip=True) if name_tag else None

        title_tags = soup.find_all("span", class_="page_intro_position_label")
        titles = [tag.get_text(strip=True) for tag in title_tags]
        title = "; ".join(titles) if titles else None

        bio_header = soup.find("h2", string="About")
        bio_tag = bio_header.find_next_sibling("p") if bio_header else None
        bio = bio_tag.get_text(" ", strip = True) if bio_tag else None

        expertise_tags = soup.find_all("div", class_="directory_grid_item")
        expertise = (
             [tag.get_text(strip=True) for tag in expertise_tags]
             if expertise_tags else None
        )


        email_link = soup.select_one("a[href^='mailto:']")
        email = email_link.get_text(strip=True) if email_link else None


        #Normalizing the fields into a clean dictionary, missing fields stored as none
        info: dict = {
            "name": name,
            "title": title,
            "bio": bio,
            "expertise": expertise,
            "email": email,
        }
        
        return info


    



       

    


        



