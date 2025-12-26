## December 25, 2025:  MERRY CHRISTMAS

`Objective:`
To implement the Psychology scraper, add some comments to base class describing playwright



`Challenges Encountered:`

- (1) there found out that the psychology department also had a cloudflare scrape protection, which resulted in my code switching to utilizing playwright. Although it's detection was not as strong as the computer science, which allowed me to utilize a headless mode, meaning the browser ui didn't have to pop up on my screen visibly for the scraping to work.

- (2) Pretty much all the faculty had an expertise section with short text, but some had an additional section of a more robust description of their research, a few with different header names (research interest, research focus, etc). 


  

`Solution Implemented:`

- (1) I found that if I were to utilize my scraper under a virtual machine like an aws ec2 instance, there wouldn't be any screen pop ups for the browser scraping since they don't utilize a UI, all the while still being just as effective since it would functionally be doing the exact same thing under the hood as when playwright headless = false. 

- (2) implemented more cases in my expertise scrape and appended them to the list
    






`Next Steps:`

