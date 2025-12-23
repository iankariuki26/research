from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from uuid import uuid4



def compute_run_stats(scraper, records: list[dict], started_at: datetime) -> dict:
    eastern_time = ZoneInfo("America/New_York")
    finished_at = datetime.now(eastern_time)
    total = len(records)

    emails = sum(1 for r in records if r.get("email"))

    return {
        "run_id": str(uuid4()),                     #unique identifier that groups all data produced by the same run
        "started_at": started_at,                   #when when the scrape began to run
        "finished_at": finished_at,                 #when the run was finished
        "pages_fetched": scraper.pages_fetched,     #amount of http pages successfully requested
        "records_parsed": total,                    #number of faculty records that were successfully extracted
        "parse_failures": scraper.parse_failures,   #the amount of pages that raised errors during parsing
        "emails_found": emails,                     #the amount of records that contain an extracted email address
    }
