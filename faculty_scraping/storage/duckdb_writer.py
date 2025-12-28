import duckdb
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import logging


logger = logging.getLogger(__name__)



class DuckDBWriter:
    """
    Storage layer for the faculty scraping pipeline
    """

    def __init__(self, db_path: str = "faculty.duckdb"):
        """
        connects to the DuckDB database file, creates one if doesn't exist
            
        """

        self.con = duckdb.connect(db_path)
        logger.info(f"Connected to DuckDB at {db_path}")


    def init_tables(self):
        """
        Creates the required tables if they dont exist
        
        """
        
        #table for keeping all the history html snapshots
        #multiple rows per URL are allowed to keep track of changes 
        

        self.con.execute("""                
            CREATE TABLE IF NOT EXISTS faculty_raw_pages (
                run_id TEXT,
                department TEXT,
                url TEXT,
                html TEXT,
                fetch_method TEXT, 
                scraped_at TIMESTAMP
                );

        """)



        #stores the latest normalized faculty data records
        #one row per faculty webpage
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS faculty_records (
                name TEXT,
                department TEXT,
                webpage_link TEXT PRIMARY KEY,
                title TEXT,
                bio TEXT,
                expertise TEXT,
                email TEXT,
                scraped_at TIMESTAMP                               
                )
            
        """)


        #stores run-time metrics
        #one row per execution
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                run_id TEXT,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                pages_fetched INTEGER,
                records_parsed INTEGER,
                parse_failures INTEGER,
                emails_found INTEGER
            );

        """)


        self.con.execute("""
            CREATE TABLE IF NOT EXISTS department_metrics (
                run_id TEXT,
                department TEXT,
                total_urls INTEGER,
                pages_fetched INTEGER,
                parse_failures INTEGER,
                failed_pct DOUBLE,
                records_parsed INTEGER,
                emails_found INTEGER,
                email_pct DOUBLE,
                browser_fallbacks INTEGER,
                browser_pct DOUBLE,
            );
                         
        """)

        logger.info(f"DuckDB tables initialized")


    def insert_raw_pages(self, raw_pages: list[dict]):
            """
            Inserts the raw HTML pages of each of the faculty members into the db

            """

            if not raw_pages:
                 logger.warning("No raw pages to insert")
                 return

            self.con.executemany("""
            INSERT INTO faculty_raw_pages (run_id, department, url, html, fetch_method, scraped_at)
            VALUES (?,?,?,?,?,?) """, 
            
            
            [ (p["run_id"], p["department"], p["url"], p["html"],p["fetch_method"], p["scraped_at"]) for p in raw_pages ])

            logger.info(f"inserted {len(raw_pages)} raw pages")



    def insert_records(self, records: list[dict]):
            """
            This inserts or updates the normalized faculty records

            """

            if not records:
                 logger.Warning(f"No faculty records fount to insert")
                 return

            #the timestamp for the insertion of these records used for the scraped_at column
            eastern_timezone = ZoneInfo("America/New_York")
            now = datetime.now(eastern_timezone)

            
        

            #if the primary key webpage_link (faculty member) already exists, update all the fields with the new data, overwriting old
            #if not then insert a new row
            self.con.executemany("""
            INSERT INTO faculty_records
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT (webpage_link) DO UPDATE SET         
                        name = excluded.name,
                        department = excluded.department,
                        title = excluded.title,
                        bio = excluded.bio,
                        expertise = excluded.expertise,
                        email = excluded.email,
                        scraped_at = excluded.scraped_at
            """, 
            
            [( r["name"], r["department"], r["webpage_link"], r["title"], r["bio"], 
                 json.dumps(r["expertise"]) if r["expertise"] else None, r["email"], now )for r in records]
            )

            logger.info(f"Upserted {len(records)} faculty records")



    
    def insert_scrape_run(self, metrics: dict):
        """
        storing the metrics, each row corresponds to a single entire scrape execution
        """
        self.con.execute("""
            INSERT INTO scrape_runs VALUES (?,?,?,?,?,?,?)               
            """, (
                metrics["run_id"],
                metrics["started_at"],
                metrics["finished_at"],
                metrics["pages_fetched"],
                metrics["records_parsed"],
                metrics["parse_failures"],
                metrics["emails_found"],
            ),
        )

        logger.info(
             f"Inserted scrape run metrics | "
             f"pages = {metrics[ 'pages_fetched']} "
             f"records={metrics['records_parsed']} "
             f"failures={metrics["parse_failures"]}"
        )


    
    def insert_department_metrics(self, metrics: dict):
         self.con.execute(
            """
            INSERT INTO department_metrics VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                metrics["run_id"],
                metrics["department"],
                metrics["total_urls"],
                metrics["pages_fetched"],
                metrics["parse_failures"],
                metrics["failed_pct"],
                metrics["records_parsed"],
                metrics["emails_found"],
                metrics["email_pct"],
                metrics["browser_fallbacks"],
                metrics["browser_pct"],

            ),
            
                    
        )




