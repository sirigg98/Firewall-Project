import re
from re import finditer
import os.path
import traceback
import logging
import math
import time
import random
from pathlib import Path
import urllib.parse as urlparse

import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException


from scrape_selenium import openbrowser, paper_page_contains_en_keywords, text_changed
from scrape import CITATION_REGEX
import warnings

warnings.filterwarnings("ignore")
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO)
os.chdir("D:/git repo/SerpAPI-Call-Clean/data")

DATA_FOLDER = 'citation graphs'
GOOGLE_BOT_DETECTED_TEXT = 'Our systems have detected unusual traffic from your computer network'

def paper_link(author_id, paper_id):
    return f'https://scholar.google.com/citations?user={author_id}&hl=en&oi=sra#d=gs_md_cita-d&u=%2Fcitations%3Fview_op%3Dview_citation%26hl%3Den%26user%3D{author_id}%26citation_for_view%3D{author_id}%3A{paper_id}%26tzom%3D240'
    # return f'https://scholar.google.com/citations?user={author_id}&hl=en#d=gs_md_cita-d&u=%2Fcitations%3Fview_op%3Dview_citation%26hl%3Den%26user%3D{author_id}%26cstart%3D300%26pagesize%3D100%26citation_for_view%3D{author_id}%3A{paper_id}%26tzom%3D-480'
    #return f'https://scholar.google.com/citations?user={author_id}&citation_for_view={author_id}:{paper_id}'
    
def extract_citation_count(citation_count_link):
    matched = re.search(CITATION_REGEX, citation_count_link.text, re.IGNORECASE)
    return int(matched.group(1))

def save_citation_page(browser, filename):
    with open(filename, 'w') as f:
        popup_el = browser.find_element_by_id('gsc_oci_graph')
        f.write(popup_el.get_attribute('innerHTML'))


def cited_by_page_filename(author_id, paper_id, year, current_page_count, total_page_count):
    return f'{DATA_FOLDER}/paper_{author_id}_{paper_id}_cited_by_{year}_year_{current_page_count}_of_{total_page_count}.html'


def cited_by_done_filename(author_id, paper_id, year=None, complete=True, error=False):
    if error:
        foldername = 'done_error'
    else:
        foldername = 'done' if complete else 'done_incomplete'

    # filename = f'{DATA_FOLDER}/{foldername}/paper_{author_id}_{paper_id}'
    filename = f'{DATA_FOLDER}/{foldername}/paper_{author_id}_{paper_id}'
    if year:
        filename += f'_{year}'
    return filename


def save_cited_by_page(author_id, paper_id, year, page_count, citation_page_count):
    filename = cited_by_page_filename(author_id, paper_id, year, page_count, citation_page_count)
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write(browser.page_source)
    else:
        logging.info(f'already downloaded, skipping {author_id}, {paper_id}, {year}, cited by page {page_count}/{citation_page_count}')


def wait_for_el_on_page(selector, text_before=None, timeout=1):
    try:
        if not text_before:
            ui.WebDriverWait(browser, timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
        else:
            ui.WebDriverWait(browser, timeout).until(
                    text_changed((By.CSS_SELECTOR, selector), text_before))
        return True

    except TimeoutException:
        missing_paper_els = browser.find_elements_by_xpath("//div[@class='gs_alrt'][contains(text(),'This citation doesn')]")
        if missing_paper_els:
            logging.error(f'This citation doesn\'t exist.')
            return False

        # traceback.print_stack()

        captcha_el = browser.find_elements_by_css_selector('#gs_captcha_f')
        recaptcha_el = browser.find_elements_by_css_selector('#captcha-form')
        if captcha_el or recaptcha_el:
            input('Solve the captcha then press any key to continue')
            return wait_for_el_on_page(selector, text_before, timeout)
        else:
            # citation page with error "The system can't perform the operation now. Try again later."
            # But error may not be in English so simply check for non-emptiness
            alert_el = browser.find_elements_by_css_selector('#gs_md_cita-l div.gs_alrt')
            if (alert_el and alert_el[0].text.strip()) or GOOGLE_BOT_DETECTED_TEXT in browser.find_element_by_name('body').text:
                input('Google likely detected bot. paused. Try refreshing page & solving the captcha then press any key to continue')
                return wait_for_el_on_page(selector, text_before, timeout)
            else:
                raise RuntimeError(f'element not found {selector}')

    except StaleElementReferenceException:
        return wait_for_el_on_page(selector, text_before, timeout)

    return False


def mark_paper_done(author_id, paper_id, year=None, error=False, complete=True):
    Path(cited_by_done_filename(author_id, paper_id, year, error, complete)).touch()


def paper_attempted(author_id, paper_id, year=None):
    error = os.path.exists(cited_by_done_filename(author_id, paper_id, year, error=True))
    incomplete = os.path.exists(cited_by_done_filename(author_id, paper_id, year, complete=False))
    complete = os.path.exists(cited_by_done_filename(author_id, paper_id, year, complete=True))
    return error or incomplete or complete


def download_cited_by_pages(browser, author_id, paper_id):
    fully_downloaded = True

    # scroll to bottom of page to make sure citation by year graph is visible
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    links_el = browser.find_elements_by_css_selector('a.gsc_vcd_g_a')

    link_year_counts = []
    for i, link_el in enumerate(links_el):
        try:
            link = link_el.get_attribute('href')
        except StaleElementReferenceException:
            time.sleep(0.5)
            link_el = browser.find_elements_by_css_selector('a.gsc_vcd_g_a')[i]
            link = link_el.get_attribute('href')
        year = urlparse.parse_qs(urlparse.urlparse(link).query)['as_yhi'][0]
        citation_count = int(link_el.get_attribute('textContent'))
        link_year_counts.append((link, year, citation_count))

    # need a separate loop to avoid StaleElementReferenceException
    for link, year, citation_count in link_year_counts:
        if paper_attempted(author_id, paper_id, year):
            continue

        # open the by year cited-by page in new tab
        browser.switch_to.window(browser.window_handles[0])
        browser.execute_script("window.open('');")
        browser.switch_to.window(browser.window_handles[-1])
        time.sleep(random.random())
        browser.get(link)

        # save first cited by page HTML
        page_count = 1
        citation_page_count = math.ceil(citation_count / 10)
        citing_page_loaded = wait_for_el_on_page(".gs_rt", 5)
        save_cited_by_page(author_id, paper_id, year, page_count, citation_page_count)

        # click through all other citing paper pages & save HTML
        next_els = browser.find_elements_by_css_selector('.gs_ico.gs_ico_nav_next')
        while next_els:
            next_els[0].click()

            page_count += 1
            save_cited_by_page(author_id, paper_id, year, page_count, citation_page_count)

            next_els = browser.find_elements_by_css_selector('.gs_ico.gs_ico_nav_next')

        # close current tab
        browser.close()

        complete = (page_count == citation_page_count)
        if not complete:
            fully_downloaded = False
            logging.warning(f'{author_id}, {paper_id}, {year} citations pages not fully downloaded.')

        mark_paper_done(author_id, paper_id, year, complete=complete)

    return fully_downloaded

def extract_citation_details(author_id, paper_id):
    try:
        with open(f'{DATA_FOLDER}//paper_{author_id}_{paper_id}.html', 'r', encoding='utf-8') as source:
        # with open(f'{DATA_FOLDER}//paper_uZ2BR8MAAAAJ_-f6ydRqryjwC.html', 'r', encoding='utf-8') as source:
            sourcecode_bar = source.read()
    except FileNotFoundError:
        return
    pat_year_count = re.compile('as_yhi=([0-9]{4})')
    pat_count = re.compile('class="gsc_oci_g_al">([0-9]+)</span>')
    counts = []
    temp_counts = []
    year_counts = []
    for match_count in pat_count.finditer(sourcecode_bar):
        count_num = match_count.group(1)
        temp_counts.append(count_num)
        
    for match_year_count in pat_year_count.finditer(sourcecode_bar):
        year = match_year_count.group(1)
        year_counts.append(int(year))
        
    for i in range(len(year_counts)):
        counts.append([year_counts[i], temp_counts[i]])
    
    counts_final = counts
    for i in range(len(counts)-1):
        if counts[i][0] != counts[i+1][0]-1:
            diff = counts[i+1][0] - counts[i][0]
            for j in range(1,diff):
                counts_final.append([counts[i][0]+j, 0])
    counts_final.sort(key = lambda x: x[0])
    counts_append = []
    years_append = []
    ids_append = []
    for i in counts_final:
        years_append.append(i[0])
        counts_append.append(i[1])
        ids_append.append(author_id_paper_id)
    
    return years_append, counts_append, ids_append


if __name__ == "__main__":
    browser = openbrowser()

    citations_by_year = pd.read_csv(r'D:\git repo\SerpAPI-Call-Clean\data\final data\citations_v2.csv')
    citations = citations_by_year.groupby('author_id_paper_id', as_index=False).agg({"citation_count": "sum"})
    
    # Replacing outdated author ids
    # old_ids = ["-7QaPhMAAAAJ", "5xJizRYAAAAJ", "#Y1f2unMAAAAJ", "#tt48sngAAAAJ", "#7vNt_0gAAAAJ", 
    #            "#DAFLSCEoAAAJ", "#AFLSCEoAAAAJ", "BV8WIV8AAAAJ", "#0qXvmz4AAAAJ", "#4_5p7N0AAAAJ", "#CjRk8DYAAAAJ", 
    #            "NYwpYYgAAAAJ", "MT2JdLAAAAAJ", "#ToLjCNgAAAAJ", "FCTDxigAAAAJ", "ILZqfIsAAAAJ", "LJkgWDMAAAAJ", 
    #            "#ND_WxhQAAAAJ", "#WdZ2JzMAAAAJ", "X4WN_d0AAAAJ", "XaOmQk4AAAAJ", "#Xj2qmLUAAAAJ", "#KqMjbEoAAAAJ", 
    #            "ZKRWBZsAAAAJ", "ZtW_i4MAAAAJ", "f7k5lWUAAAAJ", "fAIzeToAAAAJ", "hN75BIUAAAAJ", "hdoeGB0AAAAJ", 
    #            "i39wDTcAAAAJ", "#it-OqIIAAAAJ", "kyue4JAAAAAJ", "lbqAV0UAAAAJ", "#m53YNYUAAAAJ", "#qdeq7DgAAAAJ", 
    #            "rzt08QwAAAAJ", "#oTcCfoYAAAAJ", "wvl1mTMAAAAJ", "yxjfaQQAAAAJ", "zPB2xwsAAAAJ"]
    
    old_ids = ["-7QaPhMAAAAJ", "5xJizRYAAAAJ", "BV8WIV8AAAAJ", "NYwpYYgAAAAJ", "MT2JdLAAAAAJ", "FCTDxigAAAAJ", 
               "ILZqfIsAAAAJ", "LJkgWDMAAAAJ", "X4WN_d0AAAAJ", "XaOmQk4AAAAJ", "ZKRWBZsAAAAJ", "ZtW_i4MAAAAJ", 
               "f7k5lWUAAAAJ", "fAIzeToAAAAJ", "hN75BIUAAAAJ", "hdoeGB0AAAAJ", "kyue4JAAAAAJ", "lbqAV0UAAAAJ", 
               "rzt08QwAAAAJ","wvl1mTMAAAAJ", "yxjfaQQAAAAJ", "zPB2xwsAAAAJ"]
    new_ids = ["gjB2OVUAAAAJ", "tt48sngAAAAJ", "RB-RKykAAAAJ", "Hfat62oAAAAJ", "NEgPmz4AAAAJ", "t20dQloAAAAJ", 
               "_eAufagAAAAJ", "7OG9U1cAAAAJ", "FBd3e1cAAAAJ", "dANuS64AAAAJ", "nYRbXP4AAAAJ", "3_Y22fEAAAAJ",
               "ptGn114AAAAJ", "wUeII3QAAAAJ", "_eOMu1wAAAAJ", "8FhLBYMAAAAJ", "VnYF208AAAAJ", "pqN1Fi4AAAAJ", 
               "eK211CkAAAAJ", "X1_BP00AAAAJ", "MXQ3WZoAAAAJ", "kZ-mZeEAAAAJ"]
    
    for i in range(len(old_ids)): 
        citations['author_id_paper_id'] = citations['author_id_paper_id'].str.replace(old_ids[i], new_ids[i])
    
    #Scraping citation data
    for index, row in tqdm(citations.iterrows(), total=citations.shape[0]):
        # if index < 100835:
        #     continue
        author_id = row['author_id_paper_id'][:12]
        paper_id = row['author_id_paper_id'][13:]
        if paper_attempted(author_id, paper_id):
            continue

        paper_url = paper_link(author_id, paper_id)
        browser.switch_to.window(browser.window_handles[0])
        browser.get(paper_url)

        # check if citation by year graph is present
        citation_by_year_graph_selector = '#gsc_oci_graph'
        try:
            by_year_graph_loaded = wait_for_el_on_page(citation_by_year_graph_selector, 5)
        except NoSuchElementException:
            # logging.error(f'404 Error for {author_id}, paper {paper_id}, url {paper_url}')
            continue
        
        if not by_year_graph_loaded:
            # logging.error(f'Citation by year chart missing, skipping author {author_id}, paper {paper_id}, url {paper_url}')
            mark_paper_done(author_id, paper_id, error=True)
            continue

        # updated paper html is stored in folder named data_citation_details, with prefix paper_
        filename = f'{DATA_FOLDER}//paper_{author_id}_{paper_id}.html'
        save_citation_page(browser, filename)

        done = download_cited_by_pages(browser, author_id, paper_id)
        if not done:
            logging.warning(f'{author_id}, {paper_id} citations pages not fully downloaded. Paper URL: {paper_url}')

        mark_paper_done(author_id, paper_id, complete=done)
    
    #Extracting citation data from scraped bar graphs
    ids = []
    year_full = []
    counts_full = []
    missed = []
    for index, row in tqdm(citations.iterrows(), total=citations.shape[0]):
        author_id = row['author_id_paper_id'][:12]
        paper_id = row['author_id_paper_id'][13:]
        author_id_paper_id = row['author_id_paper_id']
        res = extract_citation_details(author_id, paper_id)
        try:
            ids += res[2]
            year_full += res[0]
            counts_full += res[1]
        except TypeError:
            continue
    
    #Change updated ids back to previous to facilitate merge later.
    for i in range(len(old_ids)):
        for j in ids:
            j.replace(new_ids[i], old_ids[i])
        
    final_citation_df = pd.DataFrame({'author_id_paper_id': ids, 'year': year_full, 'citation_count': counts_full})