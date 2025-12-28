from storage.duckdb_writer import DuckDBWriter
from metrics.run_metrics import compute_run_stats
from metrics.department_metrics import compute_department_metrics
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import uuid
import argparse


#my department specific scrapers
from scrapers.data_science_scraper import DataScienceScraper
from scrapers.computer_science_scraper import ComputerScienceScraper
from scrapers.psychology_scraper import PsychologyScraper
from scrapers.economics_scraper import EconomicsScraper
import asyncio

DEPARTMENT_SCRAPERS = {
    "data science": DataScienceScraper,
    "computer science": ComputerScienceScraper,
    "economics": EconomicsScraper,
    "psychology": PsychologyScraper,
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the faculty scraping pipeline"
    )

    parser.add_argument(
        "--departments",
        nargs="+",
        choices=DEPARTMENT_SCRAPERS.keys(),
        required=True,
        help="Departments to scrape"
    )

    return parser.parse_args()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(), #for showing logs in terminal
        logging.FileHandler("../logs/scrape.log"), #puts logs in scrape.log file
    ]
)
logger = logging.getLogger(__name__)





async def main():

    """
    runs the end to end scrape job
    """

    #for command line arguments
    args=parse_args()
    
    eastern_timezone = ZoneInfo("America/New_York")

    #unique identifier that groups all data produced by the same run
    run_id = str(uuid.uuid4())

    started_at = datetime.now(eastern_timezone)

    logger.info(f"Starting scrape run {run_id}")

    
    db = DuckDBWriter("faculty.duckdb")
    db.init_tables()
    
    # SCRAPERS = [
    #         DataScienceScraper(run_id=run_id), 
    #         ComputerScienceScraper(run_id=run_id),
    #         PsychologyScraper(run_id=run_id),
    #         EconomicsScraper(run_id=run_id)
    # ]

    SCRAPERS = [DEPARTMENT_SCRAPERS[dept](run_id=run_id) for dept in args.departments]
  

    for scraper in SCRAPERS:
        urls = await scraper.get_faculty_links()
        raw_pages, records = await scraper.scrape()

    
        db.insert_raw_pages(raw_pages)
        db.insert_records(records)

        dept_metrics = compute_department_metrics(
            scraper=scraper,
            records=records,
            total_urls=len(urls),
            run_id=run_id,
        )

        db.insert_department_metrics(dept_metrics)

        logger.info(
            f"[{scraper.department}] "
            f"fail={dept_metrics['failed_pct']:.1%}, "
            f"email={dept_metrics['email_pct']:.1%}"
        )

    finished_at = datetime.now(eastern_timezone)


    run_stats = compute_run_stats(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            scrapers=SCRAPERS,
        )
    db.insert_scrape_run(run_stats)
    logger.info(f"Finished scrape run {run_id}")
    logger.info(f"Data Written to DuckDB")
        



if __name__ == "__main__":
    asyncio.run(main())
