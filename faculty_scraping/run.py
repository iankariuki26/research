from scrapers.data_science_scraper import DataScienceScraper
from scrapers.computer_science_scraper import ComputerScience_Scraper
from scrapers.psychology_scraper import PsychologyScraper
from storage.duckdb_writer import DuckDBWriter
from metrics.run_metrics import compute_run_stats
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio


async def main():

    """
    runs the end to end scrape job
    """
    
    eastern_timezone = ZoneInfo("America/New_York")
    started_at = datetime.now(eastern_timezone)
    

    
    # scraper = DataScienceScraper()
    #SCRAPERS = [DataScienceScraper(), ComputerScience_Scraper()]
    SCRAPERS = [PsychologyScraper()]


    for i in SCRAPERS:

        raw_pages, records = await i.scrape()

        print(f"Scraped {len(records)} records")
        print(f"Pages Fetched: {i.pages_fetched}")
        print(f"Parse failures: {i.parse_failures}")

        db = DuckDBWriter("faculty.duckdb")
        db.init_tables()
        db.insert_raw_pages(raw_pages)
        db.insert_records(records)

        stats = compute_run_stats(i,records, started_at)
        db.insert_scrape_run(stats)
        
        print("Data written to DuckDB")
        print(f"stats of {i}")
        print(stats)
        


if __name__ == "__main__":
    asyncio.run(main())
