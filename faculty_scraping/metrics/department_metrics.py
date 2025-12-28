def compute_department_metrics(scraper, records, total_urls, run_id):
    records_parsed = len(records)
    parse_failures = scraper.parse_failures
    pages_fetched = scraper.pages_fetched
    browser_fallbacks = scraper.browser_fetched
    emails_found = sum(1 for r in records if r.get("email"))


    return {
        "run_id": run_id,
        "department": scraper.department,
        "total_urls": total_urls,
        "pages_fetched": pages_fetched,
        "parse_failures": parse_failures,
        "failed_pct": parse_failures / total_urls if total_urls else 0.0,
        "records_parsed": records_parsed,
        "emails_found": emails_found,
        "email_pct": emails_found / records_parsed if records_parsed else 0.0,
        "browser_fallbacks": browser_fallbacks,
        "browser_pct": browser_fallbacks / pages_fetched if pages_fetched else 0.0
    }

    