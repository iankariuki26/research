import string
from bs4 import BeautifulSoup
from .base import FacultyScraper
from bs4 import NavigableString


class EconomicsScraper(FacultyScraper):
    """
    Scraper implementation for the University of Virginia
    Economics faculty directory.

    This class is responsible for:
    1. Discovering faculty profile URLs
    2. Parsing individual faculty profile pages
    """


    department = "Economics"

    #directory page url with all the faculty pages
    DIRECTORY_URL = "https://economics.virginia.edu/faculty"

    #each faculty url begins with this base url
    BASE_URL = "https://economics.virginia.edu"



    async def get_faculty_links(self):
        """
        Returns a sorted list of all Economics faculty profile URLs from the directory faculty page of the 
        Economics department
        """

        url = self.DIRECTORY_URL


        #prevents duplicates across directory pages
        links = set() 


        #html of faculty listing, inherited from FacultyScraper, ignoring tuple value (html, fetch_method <-ignored)
        html, _ = await self.fetch_page(url)

        soup = BeautifulSoup(html, "html.parser")

        #grabs all the faculty urls in one page
        for a in soup.select("a[href^='/people/']"):
            links.add(self.BASE_URL + a["href"])
        

        return sorted(links)
    


    
    def parse_faculty_page(self, html, url):
        """
        Extracts the normalized faculty data within a single economics faculty profile page

        Args:
            html: the raw HTML of the faculty profile page
            url: The profile page (for context and debugging)

        Returns:
            A dictionary with all the normalized faculty fields
        """


        soup = BeautifulSoup(html, "html.parser")


        #scraping the faculty name of faculty
        name_tag = soup.select_one("article.container h1 span")
        name = name_tag.get_text(strip=True) if name_tag else None

        #scraping academic titles of faculty
        title_tags = soup.find_all("div", class_="field-field_title")
        titles = [tag.get_text(strip=True) for tag in title_tags]
        title = "; ".join(titles) if titles else None



        # scraping biographies of faculty
        body = soup.find("div", class_="field-body")
        bio = None

        if body:
            # Case 1: Explicit Biography section
            bio_header = body.find("h3", string=lambda s: s and "Biography" in s)
            if bio_header:
                bio_p = bio_header.find_next_sibling("p")
                bio = bio_p.get_text(" ", strip=True) if bio_p else None

            # Case 2: No Biography header take text until first <h3>
            else:
                bio_parts = []
                for child in body.children:
                    if getattr(child, "name", None) == "h3":
                        break  # this stops it at the first section header
                    if getattr(child, "get_text", None):
                        text = child.get_text(" ", strip=True)
                        if text:
                            bio_parts.append(text)

                bio = " ".join(bio_parts) if bio_parts else None

        # normalizing whitespace
        if bio:
            bio = " ".join(bio.split())



        #for gathering expertise in shown in two different headers titles, "fields of interest" and "research interests"
        expertise = []

        for h3 in soup.find_all("h3"):
            label = h3.get_text(strip=True)

            if label in {"Fields of Interest", "Research Interests"}:
                for sib in h3.next_siblings:
                    
                    if getattr(sib, "name", None) == "h3":
                        break

                    # capture first meaningful text (got this from LLM)
                    if isinstance(sib, NavigableString) and sib.strip():
                        expertise.append(sib.strip())
                        break

                    if getattr(sib, "get_text", None):
                        text = sib.get_text(" ", strip=True)
                        if text:
                            expertise.append(text)
                            break

        expertise = expertise if expertise else None
                




        #scrapes the email of the faculty member
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



        
