#!/usr/bin/env python3
"""
Script to scrape LinkedIn jobs data and save to JSON
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import json
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

def scrape_linkedin_jobs():
    """
    Scrapes LinkedIn jobs data and saves to JSON and database
    """
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Warning: SUPABASE_URL and SUPABASE_KEY environment variables not found.")
        print("Data will only be saved to JSON file.")
        supabase = None
    else:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase client initialized successfully.")
    
    # LinkedIn jobs search URL
    url = "https://www.linkedin.com/jobs/search/?currentJobId=4318630051&distance=100&f_TPR=r86400&keywords=data&location=casablanca&origin=JOB_SEARCH_PAGE_JOB_FILTER&trk=jobs_jserp_facet_geo_city"
    
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Setup Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # Navigate to the LinkedIn jobs page
        print("Opening LinkedIn jobs search page...")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Try to close the sign-in modal if it appears
        try:
            print("Attempting to close sign-in modal...")
            close_button = driver.find_element(By.CSS_SELECTOR, "#base-contextual-sign-in-modal > div > section > button")
            close_button.click()
            print("Sign-in modal closed successfully!")
            time.sleep(2)
        except Exception as e:
            print(f"Sign-in modal not found or already closed: {e}")
        
        # Wait for jobs list to load
        print("Waiting for jobs list to load...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#main-content > section.two-pane-serp-page__results-list > ul")))
        
        # Find all job items
        jobs_list = driver.find_element(By.CSS_SELECTOR, "#main-content > section.two-pane-serp-page__results-list > ul")
        job_items = jobs_list.find_elements(By.CSS_SELECTOR, "li")
        
        print(f"Found {len(job_items)} job listings")
        
        scraped_jobs = []
        
        for i, job_item in enumerate(job_items):
            try:
                print(f"Scraping job {i+1}/{len(job_items)}...")
                
                # Initialize job data with default values
                job_data = {
                    "logo": "-",
                    "title": "-",
                    "description": "-",
                    "company": "-",
                    "location": "-",
                    "url": "-"
                }
                
                # Extract job card element
                job_card = job_item.find_element(By.CSS_SELECTOR, "div")
                
                # Extract logo
                try:
                    logo_element = job_card.find_element(By.CSS_SELECTOR, ".search-entity-media img")
                    job_data["logo"] = logo_element.get_attribute("src") or "-"
                except:
                    pass
                
                # Extract title
                try:
                    title_element = job_card.find_element(By.CSS_SELECTOR, ".base-search-card__title")
                    job_data["title"] = title_element.text.strip() or "-"
                except:
                    pass
                
                # Extract company
                try:
                    company_element = job_card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle a")
                    job_data["company"] = company_element.text.strip() or "-"
                except:
                    pass
                
                # Extract location
                try:
                    location_element = job_card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                    job_data["location"] = location_element.text.strip() or "-"
                except:
                    pass
                
                # Extract URL
                try:
                    url_element = job_card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                    job_data["url"] = url_element.get_attribute("href") or "-"
                except:
                    pass
                
                # For description, we'll use a placeholder since it's not visible in the list view
                job_data["description"] = "Job description not available in list view"
                
                scraped_jobs.append(job_data)
                print(f"  Title: {job_data['title']}")
                print(f"  Company: {job_data['company']}")
                print(f"  Location: {job_data['location']}")
                
            except Exception as e:
                print(f"Error scraping job {i+1}: {e}")
                continue
        
        # Save to JSON file
        output_file = "linkedin_jobs_scraped.json"
        metadata = {
            "metadata": {
                "total_jobs": len(scraped_jobs),
                "scraped_at": datetime.now().isoformat(),
                "source": "LinkedIn",
                "location": "Casablanca, Morocco",
                "keywords": "data"
            },
            "jobs": scraped_jobs
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\nScraping completed! Data saved to {output_file}")
        print(f"Total jobs scraped: {len(scraped_jobs)}")
        
        # Insert into Supabase database if available
        if supabase:
            _insert_to_supabase(supabase, scraped_jobs)
        else:
            print("Skipping database insertion - Supabase not configured.")
        
        # Keep browser open for a moment to see results
        print("Browser will close in 10 seconds...")
        time.sleep(10)
        driver.quit()
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print("Make sure you have Chrome browser installed on your system.")


def _insert_to_supabase(supabase: Client, jobs: list) -> None:
    """Insert the scraped jobs into Supabase internships table"""
    try:
        print(f"\n{'='*80}")
        print("Inserting LinkedIn jobs into Supabase...")
        print(f"{'='*80}")
        
        # Insert jobs in batches of 50 to avoid payload size issues
        batch_size = 50
        total_inserted = 0
        total_failed = 0
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            
            try:
                # Insert batch into Supabase
                response = supabase.table("internships").insert(batch).execute()
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
    scrape_linkedin_jobs()
