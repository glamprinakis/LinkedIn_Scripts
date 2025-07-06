import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import pandas as pd
from collections import Counter

options = uc.ChromeOptions()
driver = uc.Chrome(options=options)
driver.get('https://www.linkedin.com/login')

print("Please log in manually and then press ENTER here.")
input()

driver.get('https://www.linkedin.com/my-items/saved-jobs/')
time.sleep(5)

# ----- PAGINATION LOOP -----
job_links = set()
page = 1

while True:
    print(f"Processing Saved Jobs page {page}...")
    time.sleep(3)

    # Scroll to bottom to load all jobs
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    jobs = driver.find_elements(By.CSS_SELECTOR, 'a[data-control-name="job_card_click"]')
    if len(jobs) == 0:
        jobs = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/view/"]')

    print(f"Found {len(jobs)} jobs on this page.")
    for job in jobs:
        href = job.get_attribute('href')
        if href and '/jobs/view/' in href:
            job_links.add(href)

    # Try to find the NEXT button (pagination)
    try:
        # If LinkedIn shows pages: find the next page button
        next_btn = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Next")]')
        if not next_btn.is_enabled():
            print("No more pages.")
            break
        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", next_btn)
        page += 1
        time.sleep(3)
    except Exception:
        # No more next button
        print("No next page button found. Pagination complete.")
        break

print(f"\nTotal unique jobs collected: {len(job_links)}")
job_links = list(job_links)

# ----- REST OF THE SCRIPT: Process Each Job -----
def extract_all_skills_from_modal(driver):
    skills = []
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button.job-details-jobs-unified-top-card__job-insight-text-button')
        skills_button = None
        for btn in buttons:
            if "Skills:" in btn.text:
                skills_button = btn
                break
        if skills_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", skills_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", skills_button)
            time.sleep(2.5)
            skill_divs = driver.find_elements(By.CSS_SELECTOR, 'div[aria-label*="as a skill"]')
            for div in skill_divs:
                skill_text = div.text.strip()
                if skill_text and skill_text not in skills:
                    skills.append(skill_text)
            # Try to close the modal
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, 'button.artdeco-modal__dismiss')
                driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(1)
            except Exception:
                pass
    except Exception as e:
        print(f"Error extracting skills from modal: {e}")
    return skills

all_skills = []
for idx, url in enumerate(job_links, 1):
    driver.get(url)
    print(f"\n[{idx}/{len(job_links)}] {url}")
    time.sleep(3)
    skills = extract_all_skills_from_modal(driver)
    print(f"Skills: {skills}")
    all_skills.extend(skills)

skill_counter = Counter(all_skills)
df = pd.DataFrame(skill_counter.most_common(), columns=['Skill', 'Count'])
print(df)
df.to_csv("ranked_skills1.csv", index=False)
driver.quit()