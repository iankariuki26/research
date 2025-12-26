## December 25, 2025:  MERRY CHRISTMAS

`Objective:`
To implement the Psychology and Economics Scrapers, add some comments to base class describing playwright



`Challenges Encountered:`

- (1) there found out that the psychology department also had a cloudflare scrape protection, which resulted in my code switching to utilizing playwright. Although it's detection was not as strong as the computer science, which allowed me to utilize a headless mode, meaning the browser ui didn't have to pop up on my screen visibly for the scraping to work.

- (2) A majority of faculty had an expertise section with short text, although others had an additional section of a more robust description of their research, a few with different header names (research interest, research focus, etc). 
  
- (3) Similar to the psychology department, the economics department faculty pages display multiple different presentations of expertise ("Research Interests", "Fields of Interest"), some individual, but unlike the other departments, the expertise content was not reliably contained within a single parent container such as field-body. Instead, different faculty profiles used different page templates, with expertise text sometimes appearing as bare text nodes immediately following h3 headers. This issue took a decent amount of time to identify and debug with an LLM

- (4) I have at least one duplicate professor in my duckdb database, "Denis Nekipelov" who has a faculty page in both the computer science department and the economics department. Will need to figure out how to account for multi department faculty which will only share the same name but different url faculty page links.  
  

`Solution Implemented:`

- (1) I found that if I were to utilize my scraper under a virtual machine like an aws ec2 instance, there wouldn't be any screen pop ups for the browser scraping since they don't utilize a UI, all the while still being just as effective since it would functionally be doing the exact same thing under the hood as when playwright headless = false. 

- (2) implemented more cases in my expertise scrape and appended them to the list
    
- (3) I had to move away from containerized based scraping and shifted with the help of LLM to header-anchored parsing, where the scraper locates relevant h3 section headers globally and extracts the first meaningful content that follows them. Debugging this issue required isolating the rendered DOM, verifying that the content was absent from HTTP responses, and adjusting the parsing strategy to match the actual post-rendered page structure.





`Next Steps:`

Reach out via email to Dr.Alex Gates to check in, figure out duplicate professor instances when appearance in multiple departments, think about other departments, think about moving to aws ec2, figure out a more robust storage system, add metrics that give the for every department metric occurrence  to count ratio  -> ex.(data science faculty with bios -> 50/51)