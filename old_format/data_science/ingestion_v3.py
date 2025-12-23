import duckdb
import requests
from bs4 import BeautifulSoup
import string
import pandas as pd



def one_page_names(url: str) -> list[str]:
    """gets the list of all the names in one page of the DS faculty search given the url, (ex. page A, or page B)"""
    try:
    
        page = requests.get(url)
        people = BeautifulSoup(page.text,'html.parser')
        names = people.find_all(class_ = "field--name")
        
        #parses through the beautifulsoup object ignoring the tags (div, class, etc) and extracting the text (names)
        list_names = [i.get_text(strip=True) for i in names]
        
        return list_names

    except Exception as e:
        print(f"an error has occurred fetching the names: {e}")
        return []



def all_alphabet_urls() -> list[str]:
    """Returns a list of all the links ending with each Alphabetical Letter in which the faculty names fall under within the search page"""
    
    url = "https://datascience.virginia.edu/faculty-research?letter="
    return [url + letter for letter in string.ascii_uppercase]




def research_faculty_links() -> list[str]:
    """returns all the faculty links within each page of the faculty search page"""
    
    all_fac_links = []
    try:
        for i in all_alphabet_urls():            
            soup = BeautifulSoup(requests.get(i).text, "html.parser")
            links = {
                    "https://datascience.virginia.edu" + a["href"]
                    for a in soup.select("a[href^='/people/']")
                }
            all_fac_links.extend(links)
        return sorted(set(all_fac_links))
    except Exception as e:
        print(f"error occurred trying to retrieve all the faculty links: {e}")
        return []



def faculty_bio() -> list[str | None]:
    """returns a list of every faculties bio. Some faculty have no bio"""
    links = research_faculty_links()
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
        print(f"Error fetching {url}: {e}")
        return list_of_bios




def all_names() -> list[str]:
    """returns a list of names of every research faculty"""

    names = []
    try:
        urls = all_alphabet_urls()
        for i in urls:
            names.extend(one_page_names(i))
        return sorted(names)
        
    except Exception as e:
        print(f"error occurred trying to retrieve all the faculty names: {e}")
        return []




def faculty_expertise() -> list[list[str] | None]:
    """returns a list of all the faculties expertise in lists"""

    session = requests.Session()
    all_expertise = []

    for link in research_faculty_links():
        try:
            response = session.get(link)
            soup = BeautifulSoup(response.text, 'html.parser')

            tags = soup.find_all("div", class_ = "list-text")
            expertise_list = [t.get_text(strip=True) for t in tags]

            all_expertise.append(expertise_list if expertise_list else None)

        except Exception as e:
            print(f"Error fetching {link}: {e}")
            all_expertise.append(None)

    return all_expertise



def count_null_expertise() -> int:
    """see how many faculty are missing expertise"""
    return faculty_expertise().count(None) 


def next_version(con):
    "figures out what the next version number should be for my duckDB table"
    tables = con.execute("SHOW TABLES").fetchall()
    versions = []

    for (name,) in tables:
        if name.startswith("faculty_v"):
            try:
                versions.append(int(name.replace("faculty_v", "")))
            except:
                pass
    
    if not versions:
        return 1
    return max(versions) + 1



def move_to_duckdb():
    """turning names, faculty links, faculty bios, and faculty expertise into a pandas dataframe then loading the table into DuckDB"""

    names = all_names()
    links = research_faculty_links()
    bios = faculty_bio()
    expertise = faculty_expertise()

    records = []

    try:
        for i in range(len(names)):
            records.append({
                "name": names[i],
                "webpage_link": links[i],
                "bio": bios[i],
                "expertise": expertise[i]
            })

        df = pd.DataFrame(records)

        
        con = duckdb.connect("faculty.duckdb")

        v = next_version(con)
        table_name = f"faculty_v{v}"
        con.register("df", df)
        con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
        print(f"Created new version of faculty table: {table_name}")

    except Exception as e:
        print(f"something went wrong trying to upload to duckdb: {e}")

    


        

if __name__ == "__main__":
    # print("all of these should be equal")
    # print(len(names))
    # print(len(links))
    # print(len(bios))
    # print(len(expertise))
    move_to_duckdb()




    """
    Intent:
    I was able to successfully pull all of the names, websites, and expertise of the UVADS Faculty! 

    

    Problem:
    Because of my methodology for pulling the faculties areas of expertise, we have 14/57 faculties lacking a description for their areas of expertise,
    Those faculty are: 
                                    | Austin Rivera    |
                                    │ Brian Wright     │
                                    │ Bruce Corliss    │
                                    │ Gerard Learmonth │
                                    │ Jeffrey Woo      │
                                    │ Jon Tupitza      │
                                    │ Mai Dahshan      │
                                    │ Marc Ruggiano    │
                                    │ Nur Yildirim     │
                                    │ Peter Beling     │
                                    │ Philip Waggoner  │
                                    │ Renée Cummings   │
                                    │ Tyler Cody       │
                                    │ YY Ahn           |  


    What now:
    Check in with Dr.Gates and see where I should go from here!


    """