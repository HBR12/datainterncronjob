# Indeed Internship Scraper

A Python script that scrapes Indeed for new internship listings and automatically saves them to a Supabase database.

## Features

- 🔍 Scrapes Indeed for internship listings
- 📊 Extracts job details (title, company, location, salary, description, URL)
- 💾 Saves data to Supabase database
- 🚫 Prevents duplicate entries
- 🤖 Uses Selenium for dynamic content loading
- ⚡ Configurable search parameters

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Supabase account and project

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd scraper
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `env.example` to `.env`:
     ```bash
     copy env.example .env
     ```
   - Edit `.env` and add your Supabase credentials:
     ```
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your-anon-key-here
     ```

## Supabase Setup

Create a table named `internships` in your Supabase database with the following schema:

```sql
CREATE TABLE internships (
  id BIGSERIAL PRIMARY KEY,
  logo TEXT,
  title TEXT NOT NULL,
  description TEXT,
  company TEXT NOT NULL,
  location TEXT,
  url TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster duplicate checking
CREATE INDEX idx_internships_url ON internships(url);
```

## Usage

### Basic Usage

Run the scraper with default settings:

```bash
python scraper.py
```

### Custom Configuration

Edit the parameters in `scraper.py` at the bottom of the file:

```python
if __name__ == "__main__":
    scraper = IndeedScraper()
    scraper.run(
        search_query="software engineering internship",  # Customize search
        location="New York, NY",  # Specify location or leave empty
        num_pages=5   # Number of pages to scrape
    )
```

### Programmatic Usage

You can also import and use the scraper in your own scripts:

```python
from scraper import IndeedScraper

scraper = IndeedScraper()
scraper.run(
    search_query="data science internship",
    location="San Francisco, CA",
    num_pages=3
)
```

## How It Works

1. **Initialization**: Connects to Supabase using credentials from `.env`
2. **Web Scraping**: Uses Selenium to load Indeed pages and extract job listings
3. **Data Extraction**: Parses each job card for:
   - Job title
   - Company name
   - Location
   - Salary (if available)
   - Job description
   - Job URL
   - Date posted
4. **Duplicate Prevention**: Checks existing URLs before inserting
5. **Database Storage**: Saves new listings to Supabase

## Configuration Options

### Search Parameters

- **search_query**: The job search term (e.g., "internship", "software engineering internship")
- **location**: Geographic location (e.g., "New York, NY", "Remote") - leave empty for all locations
- **num_pages**: Number of Indeed result pages to scrape (each page has ~10 listings)

### Scraping Behavior

The scraper includes:

- Headless browser mode (runs in background)
- Rate limiting (2-second delay between pages)
- Duplicate detection (by URL)
- Error handling for missing elements

## Troubleshooting

### Common Issues

1. **"ChromeDriver not found"**

   - The script will automatically download ChromeDriver on first run
   - Ensure Chrome browser is installed

2. **"SUPABASE_URL and SUPABASE_KEY must be set"**

   - Check that `.env` file exists and contains valid credentials
   - Ensure `.env` is in the same directory as `scraper.py`

3. **"Timeout waiting for page to load"**

   - Your internet connection may be slow
   - Indeed may be blocking requests - try reducing `num_pages`

4. **No results found**
   - Try a different search query
   - Check if Indeed is accessible from your location

## Best Practices

- ⏰ Run the scraper periodically (e.g., daily) using a scheduler
- 🎯 Use specific search queries for better results
- 📊 Monitor your Supabase usage/limits
- 🤝 Be respectful of Indeed's servers (don't scrape too aggressively)

## Automation

To run automatically on a schedule, you can use:

**Windows Task Scheduler:**

1. Open Task Scheduler
2. Create a new task
3. Set trigger (e.g., daily at 9 AM)
4. Set action to run: `python C:\path\to\scraper.py`

**Linux/macOS Cron:**

```bash
# Edit crontab
crontab -e

# Add line to run daily at 9 AM
0 9 * * * cd /path/to/scraper && /path/to/venv/bin/python scraper.py
```

## License

This project is for educational purposes. Please respect Indeed's Terms of Service and use responsibly.

## Support

For issues or questions, please check:

- Supabase documentation: https://supabase.com/docs
- Selenium documentation: https://selenium-python.readthedocs.io/
