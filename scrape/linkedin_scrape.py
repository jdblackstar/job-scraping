import datetime
import os
import time

import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def login(logger):
    """
    :param logger

    :returns wd - Chromium webdriver object from the selenium library
    """

    url_login = "https:///www.linkedin.com/"
    load_dotenv()

    # From .env file
    LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    # create headless instance of Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    # Actually log in to LinkedIn
    logger.info(f"Looging into LinkedIn as {LINKEDIN_USERNAME}...")
    wd = webdriver.Chrome(executable_path="./chromedriver", options=chrome_options)
    wd.get(url_login)
    wd.find_element_by_id("session_key").send_keys(LINKEDIN_USERNAME)
    wd.find_element_by_id("session_password").send_keys(LINKEDIN_PASSWORD)
    wd.find_element_by_xpath("//button[@class='sign-in-form__submit-button']").click()

    # not sure how often this happens, but sometimes there's a popup to confirm login info
    try:
        wd.find_element_by_xpath("//buton[@class='primary-action-new']").click()
    except:
        pass
    logger.info("     ...logged in")
    return wd


def page_search(
    wd,
    search_location,
    search_keyword,
    search_remote,
    search_posted,
    search_page,
    logger,
):
    """
    :param wd - the web driver object
    :param search_location - search location parameter for the URL
    :param search_keyword - search keyword for the URL
    :param search_remote - flag for the URL to find remote jobs
    :param search_posted - days since posted
    :param search_page - pagination
    :param search_count - total results returned
    :param file - file to log to
    :param logger - the logging object (will eventually replace this with loguru)

    :returns search_page
    :returns search_count
    :returns url_search
    """

    page_wait = 30
    click_wait = 5
    async_wait = 5
    retry_attempts = 3

    url_search = (
        f"https://www.linkedin.com/jobs/search/?f_TPR={search_posted}"
        f"&f_WT={search_remote}"
        f"&geoId=103644278"
        f"&keywords={search_keyword}"
        f"&location={search_location}"
        f"&start={search_page}"
    )

    logger.info("Navigating to jobs page...")
    wd.get(url_search)
    time.sleep(page_wait)  # sneaky sneaky sleep
    logger.info("     ...succeeded")

    search_count = wd.find_element(
        By.CSS_SELECTOR, "small.jobs-search-results-list__text"
    ).text
    search_count = int(search_count.split(" ")[0].replace(",", ""))
    logger.info(
        f"Loading page {round(search_page/25) + 1} of {round(search_count/25)} for {search_keyword}'s {search_count} results..."
    )

    # collects job_ids for the current page
    result_ids = []
    for attempt in range(retry_attempts):
        try:
            logger.info("Collecting job IDs for the current page...")
            search_results = wd.find_element(
                By.XPATH, "//ul[@class='jobs-search-results__list list-style-none']"
            ).find_elements(By.TAG_NAME, "li")
            result_ids = [
                result.get_attribute("id")
                for result in search_results
                if result.get_attribute("id") != ""
            ]
            break
        except:
            # EXCEPTION:
            # wait a few attempts, if not throw an exception and then skip to next page
            time.sleep(click_wait)
        logger.info("     ...Successfully gathered all job IDs")

    # cycle through each id and append the job data to a new list called list_jobs
    list_jobs = []
    if result_ids:
        for res_id in result_ids:
            try:
                logger.info("Looking for the job id...")
                job = wd.find_element(By.ID, res_id)
                logger.info("     ...Found the job")
                logger.info("Getting attributes...")
                job_id = job.get_attribute("data-occludable-entity-urn").split(":")[-1]
                logger.info(f"     ...Found. job_id = {job_id}")
                logger.info("Digging in deeper...")
                wd.find_element(By.XPATH, f"//div[@data-job-id='{job_id}']").click()
            except:
                # EXCEPTION:
                # exception probably caused by the job posting being deleted?
                # either way, probably better to just except it here and skip forward
                logger.error("     ...Couldn't find the job id div")
                continue

            # FIND JOB TITLE
            for attempt in range(retry_attempts):
                try:
                    logger.info("Getting the Job title...")
                    job_title = wd.find_element(By.XPATH, "//h2[@class='t-24 t-bold']")
                    logger.info("     ...Found the job title")
                    job_title = job_title.text
                    break
                except:
                    # EXCEPTION:
                    # having some issues with the xpath thing up there ^
                    # making an exception here to just wait for the click delay
                    # then move to the next job
                    job_title = ""
                    time.sleep(click_wait)
                    logger.error("     ...Couldn't find the job title")

            # GET COMPANY NAME, LOCATION AND REMOTE STATUS
            for attempt in range(retry_attempts):
                try:
                    logger.info(
                        "Looking for the company name, location and if this job is remote..."
                    )
                    job_top_card = wd.find_element(
                        By.XPATH,
                        "//span[@class='jobs-unified-top-card__subtitle-primary-grouping mr2 t-black']",
                    ).find_elements(By.TAG_NAME, "span")
                    logger.info("     ...found")
                    company = job_top_card[0].text
                    location = job_top_card[1].text
                    if len(job_top_card) > 2:
                        # the format of LinkedIn job cards is like
                        # Company, Location, (Remote)
                        # so we'll only grab the Remote tag if it's present
                        remote = job_top_card[2].text
                    else:
                        # Otherwise, set Remote to an empty string
                        remote = ""
                    break
                except:
                    logger.error("     ...wasn't able to find these attributes")
                    company = ""
                    location = ""
                    remote = ""
                    time.sleep(click_wait)

            # GET DATE POSTED (OR REPOSTED) AND NUMBER OF APPLICANTS
            for attempt in range(retry_attempts):
                try:
                    logger.info("Getting the number of applicants to this position...")
                    job_top_card2 = wd.find_element(
                        By.XPATH,
                        "//span[@class='jobs-unified-top-card__subtitle-secondary-grouping t-black--light']",
                    ).find_elements(By.TAG_NAME, "span")
                    update_time = job_top_card2[0].text
                    if len(job_top_card2) > 1:
                        applicants = job_top_card2[1].text.split(" ")[0]
                    else:
                        logger.info("     ...No applicants to this job so far")
                        applicants = ""
                    break
                except:
                    update_time = ""
                    applicants = ""
                    time.sleep(click_wait)
                    logger.warning("Unable to determine the number of applicants")

            job_time = None
            job_position = None
            job_pay = None

            # GET JOB_TIME (FULL-TIME, PART-TIME, CONTRACT)
            # GET JOB_POSITION (ENTRY LEVEL, ASSOCIATE, ETC.)
            # GET JOB_PAY (DISCARD LINKEDIN ESTIMATE NONSENSE)
            for attempt in range(retry_attempts):
                try:
                    # make sure HTML element is loaded
                    element = WebDriverWait(wd, 10).until(
                        ec.presence_of_all_elements_located(
                            (By.XPATH, "//div[@class='mt5 mb2']/div[1]")
                        )
                    )
                    # make sure text is loaded
                    try:
                        job_info = element.text
                        if job_info != "":
                            # separate job info on time requirements and position
                            job_info = job_info.split(" · ")
                            if len(job_info) == 1:
                                job_pay = ""
                                job_time = job_info[0]
                                job_position = ""
                            elif (len(job_info) >= 2) and ("$" in job_info[0]):
                                job_pay = job_info[0]
                                job_time = job_info[1]
                                if len(job_info) >= 3:
                                    job_position = job_info[2]
                                else:
                                    job_position = ""
                            else:
                                job_time = job_info[0]
                                job_position = job_info[1]
                                job_pay = ""
                            break
                        else:
                            time.sleep(async_wait)
                    except:
                        # error means page didn't load so try again
                        time.sleep(async_wait)
                        logger.error("Exception at 0005")
                except:
                    # error means page didn't load so try again
                    time.sleep(async_wait)
                    logger.error("Exception at 0006")

            # get company details and seperate on size and industry
            company_size = ""  # assigning as blanks as not important info and can skip if not obtained below
            company_industry = ""
            job_details = ""
            for attempt in range(retry_attempts):
                try:
                    company_details = wd.find_element(
                        By.XPATH, "//div[@class='mt5 mb2']/div[2]"
                    ).text
                    if " · " in company_details:
                        company_size = company_details.split(" · ")[0]
                        company_industry = company_details.split(" · ")[1]
                    else:
                        company_size = company_details
                        company_industry = ""
                    job_details = wd.find_element(By.ID, "job-details").text.replace(
                        "\n", " "
                    )
                    break
                except:
                    time.sleep(click_wait)
                    logger.error("Exception at 0007")

            # append (a) line to list_jobs
            date_time = datetime.datetime.now().strftime("%d%b%Y-%H:%M:%S")
            search_keyword = search_keyword.replace("%20", " ")
            list_job = [
                date_time,
                search_keyword,
                search_count,
                job_id,
                job_title,
                company,
                location,
                remote,
                update_time,
                applicants,
                job_pay,
                job_time,
                job_position,
                company_size,
                company_industry,
                job_details,
            ]
            list_jobs.append(list_job)
            logger.info(f"Current job: {list_job}")

    # Convert list_jobs to a DataFrame
    df_jobs = pd.DataFrame(
        list_jobs,
        columns=[
            "date_time",
            "search_keyword",
            "search_count",
            "job_id",
            "job_title",
            "company",
            "location",
            "remote",
            "update_time",
            "applicants",
            "job_pay",
            "job_time",
            "job_position",
            "company_size",
            "company_industry",
            "job_details",
        ],
    )

    logger.info(
        f"Page {round(search_page/25) + 1} of {round(search_count/25)} loaded for {search_keyword}"
    )
    search_page += 25

    return search_page, search_count, url_search, df_jobs
