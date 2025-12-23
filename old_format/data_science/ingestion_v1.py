import duckdb
import requests
from bs4 import BeautifulSoup
import pandas
from itertools import chain




#this gets the list of all the names in one page of the DS faculty search given the url
def one_page_names(url):
    try:
    
        #gets access to the page
        page = requests.get(url)
        people = BeautifulSoup(page.text,'html.parser')
        names = people.find_all(class_ = "field--name")
        
        #parses through the beautifulsoup object ignoring the tags (div, class, etc) and extracting the text (names)
        list_names = []
        for i in names:
            list_names.append(i.get_text(strip=True))
        
        return list_names

    except Exception as e:
        print(f"an error has occurred fetching the names: {e}")

#transforms name into faculty page url 
def url_maker(name):
    try:    
        url_head = "https://datascience.virginia.edu/people/"
        parts = name.split()
        dashed = "-".join(parts)
        lowered = dashed.lower()
        final_link = url_head + lowered
        return final_link
    
    except Exception as e:
        print(f"an error has occurred creating link: {e}")


#adds page number to end of link
def combiner(pageNumber):
    url_head = "https://datascience.virginia.edu/search?t=people&persons=team&page="
    final = url_head + str(pageNumber)
    return final


#checks to see if a page exists and returns all the valid page numbers to a list
def valid_page_numbers():
    try:
        list_of_real_pages = []
        pageNum = 1
        while True:
            result = one_page_names(combiner(pageNum))
            if not result:
                break
            else:
                list_of_real_pages.append(pageNum)
                pageNum += 1
        return list_of_real_pages
    
    except Exception as e:
        print(f"error occurred trying to retrieve all valid page numbers: {e}")

#returns the links of all the valid pages so that we can pull all the names from each
def list_of_search_page_links(): 
    list_of_page_numbers = valid_page_numbers()
    
    page_links = []
    for i in list_of_page_numbers:
        page_links.append(combiner(i))
    return page_links
    

#returns a list of all the faculty names
def all_faculty_names():
    all_page_links = list_of_search_page_links()
    all_faculty_names = []
    for i in all_page_links:
        all_faculty_names.append(one_page_names(i))
    
    #flatten so that no longer list of name lists
    names_flattened = list(chain.from_iterable(all_faculty_names))

    return names_flattened
    

#returns all the links of all the faculty
def faculty_page_links():
    all_faculty_page_urls = []
    x = all_faculty_names()

    for i in x:
        all_faculty_page_urls.append(url_maker(i))
    return all_faculty_page_urls
    
def faculty_bio():
    links = faculty_page_links()
    list_of_bios = []

    session = requests.Session()

    for url in links:
        try:
            page = session.get(url, timeout=10)
            page.raise_for_status()

            soup = BeautifulSoup(page.text, "html.parser")
            bio_div = soup.find("div", class_="field--bio field--body")

            if bio_div:
                list_of_bios.append(bio_div.get_text(strip=True))
            else:
                list_of_bios.append(None)

        except Exception as e:
            list_of_bios.append(None)
            print(f"Error fetching {url}: {e}")








if __name__ == "__main__":
    print(faculty_page_links())
    #print(all_faculty_names())
    #print(faculty_page_links())

    """
    Intent:
    
    My goal was to retrieve all of the names, links, and bios of the faculty of UVA's School of Data Science
    I noticed that all the links to their faculty pages had the same url prefix, and had their first and last names
    hyphenated as the ending suffix. 
    
    (Ex. https://datascience.virginia.edu/people/neal-magee,   <- Neal Magee
         https://datascience.virginia.edu/people/aaron-abrams) <- Aaron Abrams

    I set a constant for the prefix link, and wanted to retrieve all the names of the staff to append to the end of
    each link. So I went to the faculty page and realized there were multiple pages, and so I would have to write
    a function that takes into account the number of pages it will be parsing without going to far into the page 
    number count in which no faculty existed in. I then pulled all the names and hyphenated them (later having
    to take into account people with 3 parts to their name in their link, first name, and a compound surname( John Van Horn),
    instead of two (first and last), and appended them to the end of the urls, and then had the function return 
    all the generated links. 

    

    
    Problem:
    When i tried to then pull the bios from each faculty's page in my list of links, I thankfully ran into a issue 
    with one person, that being our dean Phillip Bourne. You see, although Phillip had his name as Phillip Bourne 
    On the faculty search page, his faculty link had a different name, a nickname, /phil-bourne. This explains why 
    just one of my values returns None, and why I have to readjust the code to account for other nicknames that
    newer staff may have. 
    
    

    
    What Now:
    So I am now turning to a version two of the code where i try to directly pull the links
    from the faculty pages instead of generating them on my own. I will still have to implement the incrementing 
    of faculty pages since there are more than one, pull the bios from those links, and store the names, links, 
    and bios in a database. The database (duckdb) should take into account if a record already exists, since we
    do not want duplicates.


                                          


    """



