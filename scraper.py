"""
Multi-Source Job Scraper using RapidAPI
Scrapes data internship listings from multiple job sources (LinkedIn, Indeed, etc.)
targeting France and Morocco to get at least 100 listings
"""

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client


class JobsScraper:
    """
    Multi-source scraper for data internship listings using various RapidAPI endpoints
    """
    
    def __init__(self):
        """Initialize the scraper with API configurations"""
        self.api_key = os.getenv("RAPIDAPI_KEY", "9bfe219b91msh957f3b51263836bp155d1djsnff364ca7ec93")
        
        # Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # API configurations for multiple sources
        self.apis = {
            "jsearch": {
                "url": "https://jsearch.p.rapidapi.com/search",
                "host": "jsearch.p.rapidapi.com"
            },
            "active_jobs_db": {
                "url": "https://active-jobs-db.p.rapidapi.com/modified-ats-24h",
                "host": "active-jobs-db.p.rapidapi.com"
            }
        }
        
        self.countries = ["France", "Morocco"]
        self.all_jobs = []
        
    def run(self) -> List[Dict]:
        """
        Scrape at least 100 data internship listings from multiple sources
        targeting France and Morocco
        
        Returns:
            List of dictionaries containing job data
        """
        print("="*80)
        print("Starting Multi-Source Job Scraper for Data Internships")
        print("Search Terms: data internships, data scientist internships, software engineering internships, data engineering internships")
        print("Target: At least 100 listings")
        print("="*80 + "\n")
        
        all_jobs = []
        
        # Fetch jobs from JSearch API
        jsearch_jobs = self._fetch_jsearch_jobs()
        all_jobs.extend(jsearch_jobs)
        print(f"Total collected so far: {len(all_jobs)}")
        
        # Fetch jobs from Active Jobs DB API
        active_jobs_db_jobs = self._fetch_active_jobs_db()
        all_jobs.extend(active_jobs_db_jobs)
        print(f"Total collected so far: {len(all_jobs)}")
        
        # Remove duplicates based on title + company
        all_jobs = self._remove_duplicates(all_jobs)
        
        print(f"\n{'='*80}")
        print(f"Total unique jobs collected: {len(all_jobs)}")
        print(f"{'='*80}\n")
        
        # Print results
        self._print_results(all_jobs)
        
        # Save to JSON file
        self._save_to_json(all_jobs)
        
        # Insert into Supabase
        self._insert_to_supabase(all_jobs)
        
        return all_jobs
    
    def _fetch_jsearch_jobs(self) -> List[Dict]:
        """Fetch jobs from JSearch API"""
        print("\n[JSearch API] Fetching data internships...")
        jobs = []
        
        # Query for data internships without country restriction
        for query in ["data internships", "data scientist internships", "software engineering internships", "data engineering internships"]:
            try:
                params = {
                    "query": query,
                    "page": "1",
                    "num_pages": "1",
                    "date_posted": "all"
                }
                
                headers = {
                    "x-rapidapi-host": self.apis["jsearch"]["host"],
                    "x-rapidapi-key": self.api_key
                }
                
                response = requests.get(self.apis["jsearch"]["url"], headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    api_jobs = data.get("data", [])
                    
                    for job in api_jobs:
                        structured_job = self._parse_jsearch_job(job)
                        if structured_job:
                            jobs.append(structured_job)
                    
                    print(f"  ✓ Found {len(api_jobs)} jobs for '{query}'")
                else:
                    print(f"  ✗ Failed to fetch jobs for '{query}': Status {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  ✗ Error fetching jobs for '{query}': {e}")
        
        print(f"[JSearch API] Total collected: {len(jobs)}")
        return jobs
    
    def _fetch_active_jobs_db(self) -> List[Dict]:
        """Fetch jobs from Active Jobs DB API"""
        print("\n[Active Jobs DB API] Fetching data internships...")
        jobs = []
        
        try:
            params = {
                "limit": "500",
                "offset": "0",
                "description_type": "text"
            }
            
            headers = {
                "x-rapidapi-host": self.apis["active_jobs_db"]["host"],
                "x-rapidapi-key": self.api_key
            }
            
            response = requests.get(self.apis["active_jobs_db"]["url"], headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                api_jobs = data.get("data", []) or data.get("jobs", []) or []
                
                for job in api_jobs:
                    structured_job = self._parse_active_jobs_db_job(job)
                    if structured_job:
                        jobs.append(structured_job)
                
                print(f"  ✓ Found {len(api_jobs)} jobs from Active Jobs DB")
            else:
                print(f"  ✗ Failed to fetch jobs from Active Jobs DB: Status {response.status_code}")
            
        except Exception as e:
            print(f"  ✗ Error fetching Active Jobs DB jobs: {e}")
        
        print(f"[Active Jobs DB API] Total collected: {len(jobs)}")
        return jobs
    
    
    def _parse_jsearch_job(self, job_data: Dict) -> Optional[Dict]:
        """Parse job data from JSearch API"""
        try:
            # Extract employer logo
            logo = job_data.get("employer_logo", None)
            
            # Extract job title
            title = job_data.get("job_title", None)
            
            # Extract job description
            description = job_data.get("job_description", None)
            
            # If description is HTML, clean it with BeautifulSoup
            if description and "<" in description:
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text(strip=True)
            
            # Extract company name
            company = job_data.get("employer_name", None)
            
            # Extract location
            location = None
            if job_data.get("job_city") and job_data.get("job_country"):
                location = f"{job_data.get('job_city')}, {job_data.get('job_country')}"
            elif job_data.get("job_city"):
                location = job_data.get("job_city")
            elif job_data.get("job_country"):
                location = job_data.get("job_country")
            else:
                location = job_data.get("job_location", None)
            
            # Extract job URL
            url = job_data.get("job_apply_link", None) or job_data.get("job_google_link", None)
            
            return {
                "logo": logo,
                "title": title,
                "description": description,
                "company": company,
                "location": location,
                "url": url
            }
        except Exception as e:
            print(f"    Error parsing JSearch job: {e}")
            return None
    
    def _parse_active_jobs_db_job(self, job_data: Dict) -> Optional[Dict]:
        """Parse job data from Active Jobs DB API"""
        try:
            description = job_data.get("description", None)
            if description and "<" in description:
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text(strip=True)
            
            return {
                "logo": job_data.get("logo", None) or job_data.get("company_logo", None),
                "title": job_data.get("title", None) or job_data.get("job_title", None) or job_data.get("name", None),
                "description": description,
                "company": job_data.get("company", None) or job_data.get("company_name", None) or job_data.get("employer", None),
                "location": job_data.get("location", None) or job_data.get("city", None),
                "url": job_data.get("url", None) or job_data.get("link", None) or job_data.get("job_url", None)
            }
        except Exception as e:
            print(f"    Error parsing Active Jobs DB job: {e}")
            return None
    
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title + company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique key from title and company
            key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            
            if key not in seen and key != "_":  # Ensure both title and company exist
                seen.add(key)
                unique_jobs.append(job)
        
        print(f"\nRemoved {len(jobs) - len(unique_jobs)} duplicate jobs")
        return unique_jobs
    
    def _print_results(self, jobs: List[Dict]) -> None:
        """Print the scraped job listings in a readable format"""
        print("\n" + "="*80)
        print(f"DATA INTERNSHIP LISTINGS - GLOBAL SEARCH")
        print("="*80 + "\n")
        
        # Print first 10 jobs in detail
        print("First 10 Jobs (detailed):")
        print("-" * 80)
        
        for idx, job in enumerate(jobs[:10], 1):
            print(f"\nJob #{idx}")
            print(f"Title: {job.get('title', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")
            print(f"URL: {job.get('url', 'N/A')}")
            
            if job.get('logo'):
                print(f"Logo: {job.get('logo')}")
            
            description = job.get('description', 'N/A')
            if description and description != 'N/A' and len(description) > 150:
                description = description[:150] + "..."
            print(f"Description: {description}")
            print("-" * 80)
        
        if len(jobs) > 10:
            print(f"\n... and {len(jobs) - 10} more jobs")
        
        print(f"\n{'='*80}")
        print(f"Total unique jobs scraped: {len(jobs)}")
        print(f"{'='*80}")
    
    def _save_to_json(self, jobs: List[Dict], filename: str = "linkedin_jobs.json") -> None:
        """Save the scraped jobs to a JSON file"""
        try:
            # Prepare metadata
            output = {
                "metadata": {
                    "total_jobs": len(jobs),
                    "scraped_at": datetime.now().isoformat(),
                    "target_countries": self.countries,
                    "query": "data internship"
                },
                "jobs": jobs
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Results saved to {filename}")
            print(f"  Total jobs: {len(jobs)}")
            print(f"  File size: {os.path.getsize(filename) / 1024:.2f} KB")
            
        except Exception as e:
            print(f"✗ Error saving to JSON: {e}")
    
    def _insert_to_supabase(self, jobs: List[Dict]) -> None:
        """Insert the scraped jobs into Supabase internships table"""
        try:
            print(f"\n{'='*80}")
            print("Inserting jobs into Supabase...")
            print(f"{'='*80}")
            
            # Insert jobs in batches of 100 to avoid payload size issues
            batch_size = 100
            total_inserted = 0
            total_failed = 0
            
            for i in range(0, len(jobs), batch_size):
                batch = jobs[i:i + batch_size]
                
                try:
                    # Insert batch into Supabase
                    response = self.supabase.table("internships").insert(batch).execute()
                    batch_inserted = len(batch)
                    total_inserted += batch_inserted
                    print(f"  ✓ Inserted batch {i//batch_size + 1}: {batch_inserted} jobs")
                    
                except Exception as e:
                    total_failed += len(batch)
                    print(f"  ✗ Failed to insert batch {i//batch_size + 1}: {e}")
            
            print(f"\n{'='*80}")
            print(f"Supabase insertion complete!")
            print(f"  Total inserted: {total_inserted}")
            if total_failed > 0:
                print(f"  Total failed: {total_failed}")
            print(f"{'='*80}")
            
        except Exception as e:
            print(f"✗ Error inserting to Supabase: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MULTI-SOURCE DATA INTERNSHIP SCRAPER")
    print("="*80)
    
    scraper = JobsScraper()
    jobs = scraper.run()
    
    print(f"\n✓ Scraping completed successfully!")
    print(f"✓ Collected {len(jobs)} unique data internship listings")
    
    if len(jobs) >= 100:
        print(f"✓ Target achieved: {len(jobs)} >= 100 listings")
    else:
        print(f"⚠ Target not fully achieved: {len(jobs)} < 100 listings")
        print(f"  Note: Some APIs may require subscription or have limited free tier access")