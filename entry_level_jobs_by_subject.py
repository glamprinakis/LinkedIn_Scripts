import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import pandas as pd
from collections import defaultdict

KEYWORDS = [
    "software engineer",
    "devops",
    "cloud engineer",
    "system administrator",
    "site reliability engineer",
    "platform engineer",
]
LOCATION = "Greece"
SLEEP_BETWEEN_PAGES = 2
MAX_BLANK_PAGES = 2
MAX_PAGES = 40

options = uc.ChromeOptions()
driver = uc.Chrome(options=options)
driver.get('https://www.linkedin.com/login')
print("Please log in manually and then press ENTER here.")
input()

job_dict = {}
keyword_jobs = defaultdict(dict)
keyword_stats = defaultdict(lambda: {'total': 0, 'remote': 0, 'hybrid': 0, 'onsite': 0})

def scroll_job_list_container(driver, max_scrolls=20):
    """
    Scrolls the actual LinkedIn job results list container, not the window.
    """
    time.sleep(1)
    try:
        container = driver.find_element(By.CSS_SELECTOR, 'div.scaffold-layout__list[tabindex="-1"]')
    except Exception:
        print("ERROR: Could not find job list container. Make sure you are on a LinkedIn Jobs search page.")
        return
    last_height = -1
    for i in range(max_scrolls):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
        time.sleep(0.6)
        new_height = driver.execute_script("return arguments[0].scrollHeight", container)
        if new_height == last_height:
            break
        last_height = new_height

def get_work_type_from_location(job_element):
    try:
        loc_spans = job_element.find_elements(By.XPATH, ".//span[contains(@class, 'job-card-container__metadata-item')]")
        for span in loc_spans:
            text = span.text.lower()
            if "remote" in text:
                return "remote"
            elif "hybrid" in text:
                return "hybrid"
            elif "on-site" in text or "onsite" in text:
                return "onsite"
        loc_lis = job_element.find_elements(By.XPATH, ".//li[contains(@class, 'job-card-container__metadata-item')]")
        for li in loc_lis:
            text = li.text.lower()
            if "remote" in text:
                return "remote"
            elif "hybrid" in text:
                return "hybrid"
            elif "on-site" in text or "onsite" in text:
                return "onsite"
    except Exception:
        pass
    return "unknown"

for keyword in KEYWORDS:
    print(f"\nSearching for: {keyword}")
    page = 0
    blank_pages = 0
    seen_on_this_keyword = set()
    while page < MAX_PAGES:
        url = (
            f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}"
            f"&location={LOCATION.replace(' ', '%20')}&start={page*25}&f_E=2"
        )
        driver.get(url)
        time.sleep(SLEEP_BETWEEN_PAGES)
        scroll_job_list_container(driver, max_scrolls=20)  # <-- This now works

        jobs = driver.find_elements(By.CSS_SELECTOR, 'a.job-card-list__title')
        if len(jobs) == 0:
            jobs = driver.find_elements(By.XPATH, '//a[contains(@href, "/jobs/view/")]')

        print(f"Page {page+1}: Found {len(jobs)} jobs")
        if len(jobs) == 0:
            blank_pages += 1
            if blank_pages >= MAX_BLANK_PAGES:
                print("No more jobs found. Breaking pagination loop.")
                break
            else:
                page += 1
                continue
        else:
            blank_pages = 0

        for job in jobs:
            href = job.get_attribute('href')
            title = job.text.strip()
            if not href or '/jobs/view/' not in href:
                continue

            try:
                parent = job.find_element(By.XPATH, "./ancestor::li[contains(@class, 'jobs-search-results__list-item')]")
                work_type = get_work_type_from_location(parent)
            except Exception:
                work_type = get_work_type_from_location(job)

            if href not in keyword_jobs[keyword]:
                keyword_jobs[keyword][href] = {'Title': title, 'URL': href, 'Work Type': work_type}

            if href not in job_dict:
                job_dict[href] = {'title': title, 'work_type': work_type, 'keywords': set([keyword])}
            else:
                job_dict[href]['keywords'].add(keyword)

            seen_on_this_keyword.add(href)

        page += 1

    # Tally up stats for this keyword
    total = len(seen_on_this_keyword)
    remote = sum(1 for h in seen_on_this_keyword if job_dict[h]['work_type'] == 'remote')
    hybrid = sum(1 for h in seen_on_this_keyword if job_dict[h]['work_type'] == 'hybrid')
    onsite = sum(1 for h in seen_on_this_keyword if job_dict[h]['work_type'] == 'onsite')
    keyword_stats[keyword] = {'total': total, 'remote': remote, 'hybrid': hybrid, 'onsite': onsite}
    print(f"Stats for '{keyword}': Total={total} | Remote={remote} | Hybrid={hybrid} | Onsite={onsite}")

driver.quit()

# ---- PRINT RESULTS GROUPED AND CLEAR ----
output_rows = []
for keyword in KEYWORDS:
    stats = keyword_stats[keyword]
    print(f"\n{keyword}: Total={stats['total']} | Remote={stats['remote']} | Hybrid={stats['hybrid']} | Onsite={stats['onsite']}")
    output_rows.append([f"{keyword}: Total={stats['total']} | Remote={stats['remote']} | Hybrid={stats['hybrid']} | Onsite={stats['onsite']}"])
    for job in keyword_jobs[keyword].values():
        print(f"  {job['Title']}\n    {job['URL']}\n    Work Type: {job['Work Type']}")
        output_rows.append([job['Title'], job['URL'], job['Work Type']])
    output_rows.append([""])  # Empty row for spacing

csv_rows = [["Job Title", "URL", "Work Type"]]
for row in output_rows:
    csv_rows.append(row)

csv_filename = "linkedin_jobs_grouped.csv"
pd.DataFrame(csv_rows).to_csv(csv_filename, header=False, index=False)
print(f"\nSaved grouped jobs to {csv_filename}")