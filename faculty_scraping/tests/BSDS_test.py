from scrapers.data_science_scraper import DataScienceScraper
from metrics.run_metrics import compute_run_stats
from datetime import datetime, timezone


The_scraper = DataScienceScraper()

raw_pages, records = The_scraper.scrape()
now = datetime.now(timezone.utc)

# print("Records:", len(records))
# print("Pages fetched:", scraper.pages_fetched)
# print("Parse failures:", scraper.parse_failures)
# print(raw_pages)
print(compute_run_stats(The_scraper, records, started_at=now))




