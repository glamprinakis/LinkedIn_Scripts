from bs4 import BeautifulSoup
import requests
import json
import urllib.parse

def retrieve_job_urls(job_search_url):
    response = requests.get(job_search_url)
    soup = BeautifulSoup(response.text, "html.parser")
    job_urls = []
    job_url_elements = soup.select('[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
    for job_url_element in job_url_elements:
        job_urls.append(job_url_element["href"])
    return job_urls

def scrape_job(job_url, arrangement_type):
    response = requests.get(job_url)
    soup = BeautifulSoup(response.text, "html.parser")

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
    salary = salary_element.get_text(strip=True) if salary_element else None

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
            criteria.append({"name": name, "value": value})

    job = {
        "url": job_url,
        "title": title,
        "company": {"name": company_name, "url": company_url},
        "location": location,
        "arrangement": arrangement_type,
        "applications": applicants,
        "salary": salary,
        "description": description,
        "criteria": criteria
    }
    return job

# --- Main script execution ---

search_keywords_list = ["DevOps", "Site Reliability Engineer", "System Administrator", "Cloud Engineer", "Python"]
search_location = "Greece"
scraping_limit = 100
work_arrangements = {
    "On-site": "1",
    "Remote": "2",
    "Hybrid": "3"
}
experience_levels = {
    #"Internship": "1",
    "Entry level": "2",
    #"Associate": "3",
    #"Mid-Senior level": "4",
    #"Director": "5",
    #"Executive": "6"
}

all_jobs_by_keyword = {}
statistics = {}
scraped_urls = set()

for search_keywords in search_keywords_list:
    print(f"--- Searching: '{search_keywords}' in {search_location} ---")
    encoded_keywords = urllib.parse.quote_plus(search_keywords)
    encoded_location = urllib.parse.quote(search_location)

    urls_by_filter = {arr: {exp: [] for exp in experience_levels} for arr in work_arrangements}
    all_unique_urls_for_keyword = set()
    keyword_stats = {arr: {} for arr in work_arrangements}

    for arrangement_name, arrangement_code in work_arrangements.items():
        print(f"\n-- {arrangement_name} jobs --")
        for experience_name, experience_code in experience_levels.items():
            print(f"   - Experience: '{experience_name}'")
            page_num = 0
            urls_for_combination = []
            while True:
                public_job_search_url = (
                    f"https://www.linkedin.com/jobs/search?keywords={encoded_keywords}"
                    f"&location={encoded_location}&f_WT={arrangement_code}&f_E={experience_code}"
                    f"&position=1&pageNum={page_num}"
                )
                job_urls_on_page = retrieve_job_urls(public_job_search_url)
                if not job_urls_on_page:
                    break
                urls_for_combination.extend(job_urls_on_page)
                if len(urls_for_combination) >= scraping_limit:
                    break
                page_num += 1
            unique_urls_for_combination = list(dict.fromkeys(urls_for_combination))[:scraping_limit]
            job_count = len(unique_urls_for_combination)
            keyword_stats[arrangement_name][experience_name] = job_count
            print(f"     Found {job_count} jobs.")
            urls_by_filter[arrangement_name][experience_name].extend(unique_urls_for_combination)
            all_unique_urls_for_keyword.update(unique_urls_for_combination)

    statistics[search_keywords] = keyword_stats
    print(f"\nTotal unique jobs to scrape for '{search_keywords}': {len(all_unique_urls_for_keyword)}\n")

    jobs_for_keyword = []
    for arrangement_name, exp_urls_dict in urls_by_filter.items():
        for experience_name, urls_list in exp_urls_dict.items():
            for job_url in urls_list:
                if job_url in scraped_urls:
                    continue  # Skip duplicates
                job = scrape_job(job_url, arrangement_name)
                jobs_for_keyword.append(job)
                scraped_urls.add(job_url)
    all_jobs_by_keyword[search_keywords] = jobs_for_keyword

# --- Print statistics and export ---

print("\n--- Job Search Statistics ---")
for keyword, arrangement_stats in statistics.items():
    print(f"\nKeyword: '{keyword}'")
    for arrangement, exp_stats in arrangement_stats.items():
        print(f"  - {arrangement}:")
        for experience, count in exp_stats.items():
            print(f"    - {experience}: {count} jobs")
    print(f"  - Total unique jobs for this keyword: {len(all_jobs_by_keyword.get(keyword, []))}")

total_jobs = sum(len(jobs) for jobs in all_jobs_by_keyword.values())
print(f"\nExporting {total_jobs} jobs to JSON")
file_name = "jobs.json"
with open(file_name, "w", encoding="utf-8") as file:
    json.dump(all_jobs_by_keyword, file, indent=4, ensure_ascii=False)
print(f"Jobs saved to \"{file_name}\"\n")