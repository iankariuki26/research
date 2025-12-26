import string
from bs4 import BeautifulSoup
from .base import FacultyScraper


class PsychologyScraper(FacultyScraper):
    """
    Scraper implementation for the University of Virginia
    Psychology faculty directory.

    This class is responsible for:
    1. Discovering faculty profile URLs
    2. Parsing individual faculty profile pages
    """


    department = "Psychology"

    DIRECTORY_URL = "https://psychology.as.virginia.edu/faculty"
    BASE_URL = "https://psychology.as.virginia.edu"

    async def get_faculty_links(self):
        """
        Returns a sorted list of all Psychology faculty profile URLs from the directory faculty page of the 
        psychology department
        """

        url = self.DIRECTORY_URL

        links = set() 



        html, _ = await self.fetch_page(url)

        soup = BeautifulSoup(html, "html.parser")

        #grabs all the faculty urls in one page
        for a in soup.select("a[href^='/people/']"):
            links.add(self.BASE_URL + a["href"])
        

        return sorted(links)
    


    
    def parse_faculty_page(self, html, url):
        """
        Extracts the normalized faculty data within a single psychology faculty profile page

        Args:
            html: the raw HTML of the faculty profile page
            url: The profile page (for context and debugging)

        Returns:
            A dictionary with all the normalized faculty fields
        """

        soup = BeautifulSoup(html, "html.parser")

        article = soup.find("article", class_="container")
        name_tag = article.find("h1") if article else None
        name = name_tag.get_text(strip=True) if name_tag else None

        title_tags = soup.find_all("div", class_="field-field_title")
        titles = [tag.get_text(strip=True) for tag in title_tags]
        title = "; ".join(titles) if titles else None

        body = soup.find("div", class_="field-body")
        bio = None
        if body:
            h3 = body.find("h3", string="Biography")
            if h3:
                p = h3.find_next_sibling("p")
                bio = p.get_text(" ", strip=True) if p else None
                

        area_tags = soup.find_all("a", href=lambda h: h and h.startswith("/taxonomy/term/"))

        expertise = ( [tag.get_text(strip=True) for tag in area_tags] if area_tags else [] )

        #some of the faculty have a research focus portion separate from their research area,
        #this will add the focus to the expertise if exists
        focus = soup.find("div", class_="field-body")
        if focus:
            focus_header = focus.find("h3", string="Research Focus")
            if focus_header:
                focus_p = focus_header.find_next_sibling("p")
                if focus_p:
                    expertise.append(focus_p.get_text(" ", strip=True))

        expertise = expertise if expertise else None



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



        
