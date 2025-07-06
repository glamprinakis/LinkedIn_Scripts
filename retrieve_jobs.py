from bs4 import BeautifulSoup
import requests
import json
import urllib.parse

def retrieve_job_urls(job_search_url):
    # Make an HTTP GET request to get the HTML of the page
    response = requests.get(job_search_url)

    # Access the HTML and parse it
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Where to store the scraped data
    job_urls = []

    # Scraping logic
    job_url_elements = soup.select('[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
    for job_url_element in job_url_elements:
      # Extract the job page URL and append it to the list
      job_url = job_url_element["href"]
      job_urls.append(job_url)

    return job_urls

def scrape_job(job_url):
    # Send an HTTP GET request to fetch the page HTML
    response = requests.get(job_url)

    # Access the HTML text from the response and parse it
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Scraping logic
    title_element = soup.select_one("h1")
    title = title_element.get_text(strip=True) if title_element else None

    company_element = soup.select_one('[data-tracking-control-name="public_jobs_topcard-org-name"]')
    company_name = company_element.get_text(strip=True) if company_element else None
    company_url = company_element["href"] if company_element else None

    location_element = soup.select_one(".topcard__flavor--bullet")
    location = location_element.get_text(strip=True) if location_element else None

    applicants_element = soup.select_one(".num-applicants__caption")
    applicants = applicants_element.get_text(strip=True) if applicants_element else None

    salary_element = soup.select_one(".salary")
    if salary_element is not None:
      salary = salary_element.get_text(strip=True)
    else:
       salary = None

    description_element = soup.select_one(".description__text .show-more-less-html")
    description = description_element.get_text(strip=True) if description_element else None

    criteria = []
    criteria_elements = soup.select(".description__job-criteria-list li")
    for criteria_element in criteria_elements:
        name_element = criteria_element.select_one(".description__job-criteria-subheader")
        name = name_element.get_text(strip=True) if name_element else None

        value_element = criteria_element.select_one(".description__job-criteria-text")
        value = value_element.get_text(strip=True) if value_element else None

        if name and value:
            criteria.append({
                "name": name,
                "value": value
            })


    # Collect the scraped data and return it
    job = {
        "url": job_url,
        "title": title,
        "company": {
            "name": company_name,
            "url": company_url
        },
        "location": location,
        "applications": applicants,
        "salary": salary,
        "description": description,
        "criteria": criteria
    }
    return job

# --- Define your search parameters here ---
search_keywords_list = ["DevOps", "Site Reliability Engineer", "Cloud Engineer", "Platform Engineer"]
search_location = "Greece"
scraping_limit = 10

all_jobs_by_keyword = {}
for search_keywords in search_keywords_list:
    print(f"--- Searching for '{search_keywords}' in {search_location} ---")
    # URL-encode the parameters
    encoded_keywords = urllib.parse.quote_plus(search_keywords)
    encoded_location = urllib.parse.quote(search_location)

    page_num = 0
    all_job_urls = []
    print("Starting job retrieval from LinkedIn search...")

    while True:
        # The public URL of the LinkedIn Jobs search page is built from your parameters
        public_job_search_url = f"https://www.linkedin.com/jobs/search?keywords={encoded_keywords}&location={encoded_location}&position=1&pageNum={page_num}"

        # Retrieving the single URLs for each job on the page
        job_urls_on_page = retrieve_job_urls(public_job_search_url)

        if not job_urls_on_page:
            # Break the loop if no more job URLs are found
            break

        all_job_urls.extend(job_urls_on_page)

        if len(all_job_urls) >= scraping_limit:
            break
        
        page_num += 1

    # Remove duplicate URLs
    unique_job_urls = list(dict.fromkeys(all_job_urls))
    print(f"Retrieved {len(unique_job_urls)} unique job URLs\n")

    # Scrape all the retrieved jobs
    jobs_to_scrape = unique_job_urls[:scraping_limit]

    print(f"Scraping {len(jobs_to_scrape)} jobs...\n")

    jobs_for_keyword = []
    # Scrape data from each job position page
    for job_url in jobs_to_scrape:
        print(f'Starting data extraction on "{job_url}"')

        job = scrape_job(job_url)
        jobs_for_keyword.append(job)

        print(f"Job scraped")
    
    all_jobs_by_keyword[search_keywords] = jobs_for_keyword

# Export the scraped data to JSON
total_jobs = sum(len(jobs) for jobs in all_jobs_by_keyword.values())
print(f"\nExporting {total_jobs} scraped jobs to JSON")
file_name = "jobs.json"
with open(file_name, "w", encoding="utf-8") as file:
    json.dump(all_jobs_by_keyword, file, indent=4, ensure_ascii=False)

print(f"Jobs successfully saved to \"{file_name}\"\n")