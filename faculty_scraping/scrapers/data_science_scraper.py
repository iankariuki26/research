import string
from bs4 import BeautifulSoup
from .base import FacultyScraper


class DataScienceScraper(FacultyScraper):
    """
    Scraper implementation for the University of Virginia
    Data Science faculty directory.

    This class is responsible for:
    1. Discovering faculty profile URLs
    2. Parsing individual faculty profile pages
    """


    department = "Data Science"


    #this is the base domain for all Data Science pages
    BASE_URL = "https://datascience.virginia.edu"

    #The directory pages are organized alphabetically by last name
    DIRECTORY_URL = BASE_URL + "/faculty-research?letter="



    async def get_faculty_links(self) -> list[str]:
        """
        Returns a sorted list of all Data Science faculty profile URLs by iterating
        through the A-Z directory pages
        """

        #prevents duplicates across directory pages
        links = set()

        #for every directory page per letter A-Z
        for letter in string.ascii_uppercase:

            url = self.DIRECTORY_URL + letter

            #html of faculty listing, inherited from FacultyScraper, ignoring tuple value (html, fetch_method <-ignored)
            html, _ = await self.fetch_page(url)
            
            
            soup = BeautifulSoup(html, "html.parser")

            #grabs all the faculty urls in one page
            for a in soup.select("a[href^='/people/']"):
                links.add(self.BASE_URL + a["href"])

        return sorted(links)
    
    

    def parse_faculty_page(self, html: str, url: str) -> dict:
        """
        Extracts the normalized faculty data within a single data science faculty profile page

        Args:
            html: the raw HTML of the faculty profile page
            url: The profile page (for context and debugging)

        Returns:
            A dictionary with all the normalized faculty fields
        """

        soup = BeautifulSoup(html, "html.parser")


        #the name of the faculty is consistently stored in the <h1> tag
        name_tag = soup.find("h1")
        name = " ".join(name_tag.stripped_strings) if name_tag else None

        title_tag = soup.select_one("div.field--title")
        title = title_tag.get_text(strip=True) if title_tag else None

        #pulls the bio text
        bio_tag = soup.find("div", class_="field--bio field--body")
        bio = bio_tag.get_text(strip=True) if bio_tag else None

        #pulls the expertise text
        expertise_tags = soup.find_all("div", class_="list-text")
        expertise = ([t.get_text(strip=True) for t in expertise_tags] if expertise_tags else None)

        #pulls the email, the person section allows for only the person field to be considered, not the links and info at the bottom
        email_link = soup.select_one("section.person a[href^='mailto:']")
        email = (email_link["href"].replace("mailto:", "") if email_link else None)

    

        #Normalizing the fields into a clean dictionary, missing fields stored as none
        info: dict = {
            "name": name,
            "title": title,
            "bio": bio,
            "expertise": expertise,
            "email": email,
        }
        
        return info
    


    