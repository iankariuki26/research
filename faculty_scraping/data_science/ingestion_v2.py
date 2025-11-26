import duckdb
import requests
from bs4 import BeautifulSoup
from itertools import chain



def one_page_names(url: str) -> list[str]:
    """gets the list of all the names in one page of the DS faculty search given the url"""
    try:
    
        #gets access to the page
        page = requests.get(url)
        people = BeautifulSoup(page.text,'html.parser')
        names = people.find_all(class_ = "field--name")
        
        #parses through the beautifulsoup object ignoring the tags (div, class, etc) and extracting the text (names)
        list_names = [i.get_text(strip=True) for i in names]
        
        return list_names

    except Exception as e:
        print(f"an error has occurred fetching the names: {e}")

def combiner(url_head: str, pageNumber: int) -> list[str]:
    """appends page number to end of url"""
    
    final = url_head + str(pageNumber)
    return final

def valid_page_numbers() -> list[int]:
    """Returns a list of all valid page numbers within the search page containing faculty"""
    try:
        url_head = "https://datascience.virginia.edu/search?t=people&page="
        list_of_real_pages = []
        pageNum = 1
        while True:
            result = one_page_names(combiner(url_head,pageNum))
            if not result:
                break
            else:
                list_of_real_pages.append(pageNum)
                pageNum += 1
        return list_of_real_pages
    
    except Exception as e:
        print(f"error occurred trying to retrieve all valid page numbers: {e}")



def all_faculty_links():
    """returns all the faculty links within each page of the faculty search page"""
    
    total_fac = []
    try:
        url = "https://datascience.virginia.edu/search?t=people&page="
        for i in valid_page_numbers():
            specific_url = combiner(url,i)
            soup = BeautifulSoup(requests.get(specific_url).text, "html.parser")
            links = {
                "https://datascience.virginia.edu" + a["href"]
                for a in soup.select("a[href^='/people/']")
            }
            total_fac.append(links)
        links_flattened = list(chain.from_iterable(total_fac))
        return sorted(links_flattened)
    except Exception as e:
        print(f"error occurred trying to retrieve all the faculty links: {e}")
        
def faculty_bio():
    """returns a list of all the bios of every faculty within the course page. Some faculty have no bio"""
    links = all_faculty_links()
    list_of_bios = []

    session = requests.Session()
    session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    })
    try:
        for url in links:
            page = session.get(url, timeout=10)
            page.raise_for_status()

            soup = BeautifulSoup(page.text, "html.parser")
            bio_div = soup.find("div", class_="field--bio field--body")

            if bio_div:
                list_of_bios.append(bio_div.get_text(strip=True))
            else:
                list_of_bios.append(None)
                
        return list_of_bios

    except Exception as e:
        list_of_bios.append(None)
        print(f"Error fetching {url}: {e}")

def all_names():
    names = []
    try:
        url = "https://datascience.virginia.edu/search?t=people&page="
        for i in valid_page_numbers():
            specific_url = combiner(url,i)
            names.append(one_page_names(specific_url))
        links_flattened = list(chain.from_iterable(names))
        return sorted(links_flattened)
    except Exception as e:
        print(f"error occurred trying to retrieve all the faculty names: {e}")

        

if __name__ == "__main__":
    print(all_faculty_links())

    """
    What works:
    I was able to get all the faculty in the uva department, including names, bios, and links. Only have one duplicate
    (Alyssa Brown) 



    Problem:
    I only need research faculty, not the entire bsds staff


    What now:
    Going to create a new version that pulls specifically from the research category of faculty, it also has a dropdown
    their specific area of research so I will be able to add another feature to the dataset. Instead of iterating through
    each page number to check whether there is faculty, I will iterate through the alphabetical letters for name pages
    which will be a constant of 26. New faculty will just fall within one of the 26, allowing for reusability.
    I've found that the area of expertise is within the faculty bio page under research. My goal is to have 
    duckdb database with a table consisting of first name, lastname, area of interest, bio, link to specific faculty page
 

    """