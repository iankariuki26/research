def compute_run_stats(run_id, started_at, finished_at, scrapers) -> dict:

    pages_fetched = sum(s.pages_fetched for s in scrapers)
    parse_failures = sum(s.parse_failures for s in scrapers)
    records_parsed = pages_fetched - parse_failures
    emails_found = sum(s.email_count for s in scrapers if hasattr(s,"email_count"))

    return {
        "run_id": run_id,                     #unique identifier that groups all data produced by the same run
        "started_at": started_at,                   #when when the scrape began to run
        "finished_at": finished_at,                 #when the run was finished
        "pages_fetched": pages_fetched,             #amount of http pages successfully requested
        "records_parsed": records_parsed,                    #number of faculty records that were successfully extracted
        "parse_failures": parse_failures,           #the amount of pages that raised errors during parsing
        "emails_found": emails_found,               #the amount of records that contain an extracted email address
    }


