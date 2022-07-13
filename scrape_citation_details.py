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

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import _find_element
from rapidfuzz import fuzz
import warnings
from bs4 import BeautifulSoup
os.chdir("D:/git repo/Firewall-Project")
from Name_DeDuplicator import name_type

warnings.filterwarnings("ignore")
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO)
os.chdir("D:/git repo/Firewall-Project/data")

PAPERNAME_MATCH = re.compile('">(.+)</a>')
DATA_FOLDER = 'Paper Source 2'
GOOGLE_BOT_DETECTED_TEXT = 'Our systems have detected unusual traffic from your computer network'
CITATION_REGEX = ' (\d+)$'
PAPER_TITLE_MATCH = '<a href="([^"]+)" class="gsc_a_at">([^<]+)</a><div class="gs_gray">'
ID_MATCH = re.compile("paper_(.{12})_(.{12})")
PAPER_NAME_MATCH1 = re.compile(r'class="gsc_oci_title_link" href="[^"]+" data-clk="[^"]+">([^<]+)')
PAPER_NAME_MATCH2 = re.compile(r'id="gsc_oci_title">([^<]+)')
PAPER_NAME_MATCH3 = re.compile(r'href="[^"]+" class="gsc_a_at">([^<]+)')
ID_RE = re.compile(r'([^:]{12}):([a-zA-Z0-9_\-]{12})')


JOURNAL_MATCH = re.compile(r'Journal</div><div class="gsc_oci_value">([^<]+)<')
PUB_MATCH = re.compile(r'Publisher</div><div class="gsc_oci_value">([^<]+)<')
DATE_MACTH = re.compile(r'Publication date</div><div class="gsc_oci_value">([^<]+)<')
DESC_MATCH = re.compile(r'Description</div><div class="gsc_oci_value" id="gsc_oci_descr"><div class="gsh_small"><div><div><div class="gsh_csp">([^<]+)<')
LINK_YEAR_REGEX = 'yhi=(\d+)$'
PAPER_HEADERS = ['author', 'author_google_name', 'author_google_id',
        'paper_google_id', 'author_id_paper_id', 'paper_title',
        'publication_date', 'co-authors', 'journal', 'publisher',
        'total_citation_count', 'citation_count_and_breakdown_sum_diff',
        'description', 'title_ref_china', 'desc_ref_china']


import os
from twocaptcha import TwoCaptcha


# author_df = pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1')
from anticaptchaofficial.recaptchav2proxyless import *
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
def captcha_solver(url, sitekey):
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key("27f9b155a2be75d06a428cf34e73dd7e")
    solver.set_website_url(url)
    solver.set_website_key(sitekey)
    #set optional custom parameter which Google made for their search page Recaptcha v2
    #solver.set_data_s('"data-s" token from Google Search results "protection"')
    
    g_response = solver.solve_and_return_solution()
    if g_response != 0:
        return g_response
    else:
        return
        

class text_changed(object):
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        actual_text = _find_element(driver, self.locator).text
        return actual_text != self.text
    
def paper_page_contains_en_keywords(filename):
    with open(filename) as f:
        content = f.read()
        return ('Total citations' in content and 'Cited by' in content)
    
def openbrowser():
    global browser

    url = "http://google.com/"

    capabilities = dict(DesiredCapabilities.CHROME)
    capabilities['loggingPrefs'] = { 'browser':'ALL' }

    options = webdriver.ChromeOptions()
    for arg in open('D:/git repo/scholar-scrape/config/account.txt').readlines():
        options.add_argument(arg)
    #Downloads chrome driver to match the version of chrome you use.
    browser = webdriver.Chrome(ChromeDriverManager().install(), desired_capabilities=capabilities, options=options)
    return browser

def paper_link(author_id, paper_id):
    return f'https://scholar.google.com/citations?user={author_id}&hl=en&oi=sra#d=gs_md_cita-d&u=%2Fcitations%3Fview_op%3Dview_citation%26hl%3Den%26user%3D{author_id}%26citation_for_view%3D{author_id}%3A{paper_id}%26tzom%3D240'
    # return f'https://scholar.google.com/citations?user={author_id}&hl=en#d=gs_md_cita-d&u=%2Fcitations%3Fview_op%3Dview_citation%26hl%3Den%26user%3D{author_id}%26cstart%3D300%26pagesize%3D100%26citation_for_view%3D{author_id}%3A{paper_id}%26tzom%3D-480'
    #return f'https://scholar.google.com/citations?user={author_id}&citation_for_view={author_id}:{paper_id}'
    
# def extract_citation_count(citation_count_link):
#     matched = re.search(CITATION_REGEX, citation_count_link.text, re.IGNORECASE)
#     return int(matched.group(1))

def save_citation_page(browser, filename):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding = 'utf-8') as f:
            try:
                f.write(repr(browser.page_source))
            except UnicodeEncodeError:
                f.write(repr(str(browser.page_source.encode('utf-8'))))
            
            
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


def wait_for_el_on_page(selector, text_before=None, timeout=0.5):
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
            # response = captcha_solver()
            # if response:
            #     browser.execute_script("""document.getElementById("g-recaptcha-response").innerHTML = '""" + g_response + "'")
            #     browser.find_element_by_css_selector("").click()
            # else:
            input('Solve the captcha then press any key to continue')
            return wait_for_el_on_page(selector, text_before, timeout)
        else:
            # citation page with error "The system can't perform the operation now. Try again later."
            # But error may not be in English so simply check for non-emptiness
            alert_el = browser.find_elements_by_css_selector('#gs_md_cita-l div.gs_alrt')
            if (alert_el and alert_el[0].text.strip()) or GOOGLE_BOT_DETECTED_TEXT in browser.page_source:
                input('Google likely detected bot. paused. Try refreshing page & solving the captcha then press any key to continue')
                return wait_for_el_on_page(selector, text_before, timeout)
            elif "<p><b>404.</b> <ins>That’s an error.</ins>\n  </p><p>The requested URL <code>" in browser.page_source:
                return False
            else:
                #raise RuntimeError(f'element not found {selector}')
                return False

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



def extract_paper_names(author_id, paper_id):
    try:
        with open(f'{DATA_FOLDER}//paper_{author_id}_{paper_id}.html', 'r', encoding='utf-8') as source:
        # with open(f'{DATA_FOLDER}//paper_uZ2BR8MAAAAJ_-f6ydRqryjwC.html', 'r', encoding='utf-8') as source:
            sourcecode_name = source.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return ''
    try:
        return re.split("<|>", sourcecode_name)[-3]
    except IndexError:
        return ''
    
def author_link(author_id):
    return f'https://scholar.google.com/citations?user={author_id}&hl=en&oi=sra'

def get_author_source(browser, author_id):
    if not os.path.exists(f"author_main_page/author_{author_id}.txt"):
        link = author_link(author_id)
        browser.get(link)
        
        disabled = False
        while not disabled:
            time.sleep(1)
            browser.execute_script("window.scrollTo(0, 1080)") 
            if not wait_for_el_on_page('#gsc_bpf_more'):
                return
            showmore = browser.find_element_by_xpath('//*[@id="gsc_bpf_more"]')
            if showmore.is_enabled():
                showmore.send_keys('\n')
            else:
                disabled = True
                
        source = browser.page_source
    
        with open(f"author_main_page/author_{author_id}.txt", 'w', encoding="utf-8") as f:
            f.write(source)

# def df_papers(author_id, author):
#     try:
#         with open(f"author_main_page/author_{author_id}.txt", 'r', encoding="utf-8") as f:
#             source = f.read()
#     except FileNotFoundError:
#         return 
        
#     ls_papers = []
#     for m in re.finditer(PAPER_TITLE_MATCH, source):
#         ls_papers.append([author_id, author, m.group(1), m.group(2)])
    
#     df_papers = pd.DataFrame(ls_papers, columns = ['author_id', 'author', 'paper_url', 'paper_title'])
    
#     return df_papers

# def df_papers_all_authors(author_df):
#     ret_df = pd.DataFrame(columns = ['author_id', 'author', 'paper_url', 'paper_title'])

#     for index, row in tqdm(author_df.iterrows(), total = author_df.shape[0]):
#         author = row['author']
#         author_id = row['new_author_google_id']
#         temp_df = df_papers(author_id, author)
        
#         if temp_df is None:
#             continue
            
#         ret_df = ret_df.append(temp_df)
    
#     return ret_df
        
# def match_papers(main_papers, new_papers):
#     cols = ['author_id', 'author', 'paper_url', 'author_id_paper_id1', 'paper_title1', 'author_id_paper_id2', 'paper_title2']
#     ret_df = pd.DataFrame(columns = cols)
#     for index, row in tqdm(main_papers.iterrows(), total = main_papers.shape[0]):
#         author_id = row['new_author_google_id']
#         temp_df = new_papers[new_papers["author_id"] == author_id]
#         paper_title1 = row['paper_title']
#         for index1, row1 in temp_df.iterrows():    
#             paper_title2 = row1['paper_title']
#             if fuzz.ratio(paper_title1.lower(), paper_title2.lower()) > 75:
#                 m = re.search('citation_for_view=(.{12}):(.{12})', row1['paper_url'])
#                 author_id2 = m.group(1)
#                 paper_id2 = m.group(2)
#                 temp_ls = [[row1['author_id'], row1['author'], row1['paper_url'], row['author_id_paper_id'], paper_title1, author_id2 + '_' + paper_id2, paper_title2]]
#                 temp_row = pd.DataFrame(temp_ls, columns = cols)
#                 ret_df = ret_df.append(temp_row)
                
#     return ret_df

    
def download_paper_source(paper_df, re_send = set(), matched = False):
    def correct_encoding(filename):
        with open(f'{DATA_FOLDER}//filename.html', 'r', encoding='utf-8') as source:
            sourcecode_name = source.read()
            if repr(sourcecode_name) == sourcecode_name:
                return True
        
    browser = openbrowser()
    c = 0
    #creating a set of papers with no citation graphs
    error_check = set(os.listdir('D:\git repo\Firewall-Project\data\Paper Source 2\done_error'))
    for index, row in tqdm(paper_df.iterrows(), total=paper_df.shape[0]):
        #if using matched_df
        if matched:
            author_id = row['author_id_paper_id2'][:12]
            paper_id = row['author_id_paper_id2'][13:]

        else:
            match_ids = ID_RE.search(row['paper_url'])
            author_id = match_ids.group(1)
            paper_id = match_ids.group(2)
    
        filename = f'{DATA_FOLDER}//paper_{author_id}_{paper_id}.html'
        #Change start index if code stops running
        #Checks whether paage has citation graph
        #Checks if file already exists
        if index < 10300 or os.path.exists(filename) or f'paper_{author_id}_{paper_id}' in error_check:
            continue



        paper_url = paper_link(author_id, paper_id)
        # browser.switch_to.window(browser.window_handles[0])
        browser.get(paper_url)
        try:
            browser.find_element_by_xpath('''//*[@id="gs_bdy_ccl"]/div/div[1]/div[2]/span''')
            continue
        except NoSuchElementException:
            pass
        

        # check if citation by year graph is present
        citation_by_year_graph_selector = '#gsc_oci_graph'
        try:
            by_year_graph_loaded = wait_for_el_on_page(citation_by_year_graph_selector, timeout = 0.2)
        except NoSuchElementException:
            # logging.error(f'404 Error for {author_id}, paper {paper_id}, url {paper_url}')
            continue
    
        if not by_year_graph_loaded:
            #logging.error(f'Citation by year chart missing, skipping author {author_id2}, paper {paper_id2}, url {paper_url}')
            mark_paper_done(author_id, paper_id, error=True)
            continue
        # updated paper html is stored in folder named data_citation_details, with prefix paper_
        save_citation_page(browser, filename)

    
def extract_citation_details(filename):
    try:
        with open(f'{DATA_FOLDER}//{filename}', 'r', encoding='utf-8') as source:
        # with open(f'{DATA_FOLDER}//paper_uZ2BR8MAAAAJ_-f6ydRqryjwC.html', 'r', encoding='utf-8') as source:
            sourcecode = source.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return
    IDs = ID_MATCH.search(filename)
    author_id = IDs.group(1)
    paper_id = IDs.group(2)

    author_id_paper_id = author_id+"_"+ paper_id
    pat_year_count = re.compile('as_yhi=([0-9]{4})')
    pat_count = re.compile('class="gsc_oci_g_al">([0-9]+)</span>')
    counts = []
    temp_counts = []
    year_counts = []
    for match_count in pat_count.finditer(sourcecode):
        count_num = match_count.group(1)
        temp_counts.append(int(count_num))
        
    for match_year_count in pat_year_count.finditer(sourcecode):
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

def ref_china(text):
    return ('china' in text.lower() or 'chinese' in text.lower())


def parse_paper_page(filename):
    with open(f'{DATA_FOLDER}//{filename}', 'r', encoding='utf-8') as source:
        page = source.read()
        
    soup = BeautifulSoup(page, 'html.parser')
    paper_title = soup.select_one('#gsc_oci_title').text
    
    IDS = ID_MATCH.search(filename)
    author_id = IDS.group(1)
    paper_id = IDS.group(2)
    author_id_paper_id = author_id + '_' + paper_id
    try:
        author = author_df.query('new_author_google_id == @author_id')['author'].reset_index(drop = True)[0]
    except (KeyError, ValueError):
        try:
            author = author_df.query('author_google_id == @author_id')['author'].reset_index(drop = True)
        except:
            print(author_id)
    
    def extract_field_by_label(label_text):
        if label_text == 'Author Google name':
            return re.compile('<img alt="([^"]+)"').search(str(soup.find('span', class_='gs_rimg gs_pp_sm'))).group(1)
        value = ''
        value_label = soup.find('div', class_='gsc_oci_field', text=label_text)
        if value_label:
            value_el = value_label.find_next('div', class_='gsc_oci_value')
            value_link = value_el.find('a')
            if value_link:
                value = value_link.text # total citation field
            else:
                value = value_el.text
        return value
    author_google_name = extract_field_by_label('Author Google name')
    publication_date = extract_field_by_label('Publication date')
    co_authors = extract_field_by_label('Authors')
    publisher = extract_field_by_label('Publisher')
    journal = extract_field_by_label('Journal')
    description = extract_field_by_label('Description')

    total_citation_count = None
    total_citation_string = extract_field_by_label('Total citations')
    if total_citation_string:
        matched = re.search(CITATION_REGEX, total_citation_string, re.IGNORECASE)
        total_citation_count = int(matched.group(1))
    else:
        return {} # uncited paper
    desc_ref_china = str(ref_china(description))
    title_ref_china = str(ref_china(paper_title))
    citations_by_year = []
    citation_count_and_breakdown_sum_diff = 0
    year_els = soup.find_all('span', class_='gsc_oci_g_t')
    cite_links = soup.find_all('a', class_='gsc_oci_g_a')

    if year_els and cite_links:
        years_with_cites = {}
        for link_el in cite_links:
            year = int(re.search(LINK_YEAR_REGEX, link_el['href']).group(1))
            cites = link_el.find('span', class_='gsc_oci_g_al')
            years_with_cites[year] = int(cites.text)

        years = [int(el.text) for el in year_els]
        citations_by_year = []
        for year in years:
            citations_by_year.append((year, years_with_cites.get(year, 0)))
        citation_count_and_breakdown_sum_diff = total_citation_count - sum(years_with_cites.values())
    else:
        logging.warning(f'{paper_title}: missing citation by year breakdown')

    return pd.DataFrame({'author': author, 
            'author_google_name': author_google_name,
            'author_google_id': author_id,
            'paper_google_id': paper_id,
            'author_id_paper_id': author_id_paper_id,
             'paper_title': paper_title,
             'publication_date': publication_date,
             'co-authors': co_authors,
             'journal': journal,
             'publisher':publisher,
             'total_citation_count': total_citation_count,
             'citation_count_and_breakdown_sum_diff':citation_count_and_breakdown_sum_diff,
             'description': description,
             'desc_ref_china': desc_ref_china,
             'title_ref_china': title_ref_china},
                        index = [0])

def compile_cite_df():
    ids = []
    names = []
    year_full = []
    counts_full = []
    source_files = []
    for file in os.listdir(f'{DATA_FOLDER}'):
        if file.endswith('.html'):
            source_files.append(file)
    # check['name_check'] = ''
    for filename in tqdm(source_files, total=len(source_files)):
        res = extract_citation_details(filename)
        try:
            ids += res[2]
            year_full += res[0]
            counts_full += res[1]
        except TypeError:
            continue
    
    
    ret_df = pd.DataFrame({'author_id_paper_id': ids, 'year': year_full, 'citation_count': counts_full})
    
    return ret_df.reset_index(drop = True)

DBLCOMMA_RE = re.compile(',[\s]*,')
STARTCOMMA_RE = re.compile('^[\s]*?,')
ENDCOMMA_RE = re.compile(',[\s]*?$')

def compile_paper_df():
    #Some authors appear as main author and the list of coauthors. Correcting this so no double counting
    def clean_coauthors(author, coauthors):
        if not isinstance(author, str) or not isinstance(coauthors, str):
            return
        author = author.replace(".", "")
        author_decode = unidecode.unidecode(author)
        author_ls = author.split()
        author_name_type = name_type(author)
        coauthors = coauthors.replace(".", "")
        coauthors_decode = unidecode.unidecode(coauthors)
        
        re_ls = []
        if author_name_type in {1, 2, 3, 4}:
            try:
                re_ls = [re.compile(f'\s?{author}, re.IGNORECASE'), 
                        re.compile(f'\s?{author_ls[0][0]}[^(,|&|)]* ({author_ls[1][0]}?[^(,|&|)]*\s)?{author_ls[-1]}\s?', re.IGNORECASE)]
            except:
                return coauthors
            for AUTH_RE in re_ls: 
                ret_coauths = re.sub(AUTH_RE, '', coauthors, 1).strip()
                if ret_coauths != coauthors:
                    break
                
        elif author_name_type in {5, 6}:
            try:
                AUTH_RE = re.compile(f'\s?{author_ls[0][0]}[^(,|&|)]* {author_ls[-1]}\s?', re.IGNORECASE)
            except:
                return coauthors
            ret_coauths = re.sub(AUTH_RE, '', coauthors, 1).strip()
        else:
            return coauthors
        
        ret_coauths = re.sub(DBLCOMMA_RE, ',', ret_coauths)
        ret_coauths = re.sub(STARTCOMMA_RE, '', ret_coauths)
        ret_coauths = re.sub(ENDCOMMA_RE, '', ret_coauths)
        return ret_coauths.strip()
        
    ret_df = pd.DataFrame(columns = PAPER_HEADERS)
    dir_files = os.listdir(f'{DATA_FOLDER}')
    for filename in tqdm(dir_files, total = len(dir_files)):
        if filename.endswith('.html'):
            row = parse_paper_page(filename)
            ret_df = ret_df.append(row)
        
    ret_df = ret_df.reset_index(drop = True)
    ret_df['coauthors_clean'] = ret_df.apply(lambda row: clean_coauthors(row['author_google_name'], row['co-authors']), axis = 1)
    
        
    return ret_df
        


# def get_maxcites(df, matched_df):
#     temp_df = df.groupby('author_id_paper_id')['citation_count'].sum().reset_index()
#     temp_df2 = pd.merge(matched_df, temp_df, left_on = 'author_id_paper_id2', right_on = 'author_id_paper_id', how = 'inner').sort_values('citation_count', ascending = False).groupby('author_id_paper_id1').head(1)
    
#     max_papers = temp_df2['author_id_paper_id2']
    
#     temp_df3 = pd.merge(df, max_papers, left_on = 'author_id_paper_id', right_on = 'author_id_paper_id2', how = 'inner')
#     ret_df = pd.merge(matched_df, temp_df3, on = 'author_id_paper_id2', how = 'inner').drop_duplicates(['year', 'author_id_paper_id1'])[['author_id_paper_id1', 'year', 'citation_count']].rename(columns = {'author_id_paper_id1': 'author_id_paper_id'})
#     return ret_df

#Author names sometimes appear as main author name AND in te list of ocuahtors.
#Function searches and cleans these names.

    
    
    
if __name__ == "__main__":
    # browser = openbrowser()
    # test = v23_merge.query('_merge == "left_only"')
    # resend_df = pd.DataFrame()
    # for index, row in tqdm(test.iterrows(), total = test.shape[0]):
    #     author_id = row['author_id_paper_id'][:12]
    #     paper_id = row['author_id_paper_id'][13:]
    #     browser.get(paper_link(author_id, paper_id))
    #     try:
    #         browser.find_element_by_xpath('''//*[@id="gs_bdy_ccl"]/div/div[1]/div[2]/span''')
    #     except NoSuchElementException:
    #         resend_df = resend_df.append(row)
    
    
    
    # authors = list(pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1').iloc[:,0])
    # author_ids = list(pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1').iloc[:,5])
    # author_df = pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1')[['author', 'author_google_id']]
    # main_papers = pd.read_excel(r"D:\git repo\Firewall-Project\Data\mains.xlsx")
    # for index, row  in tqdm(author_df.iterrows()):
    #     author = row['author']
    #     for index1, row1 in changed.iterrows():
    #         if row1['author'] == author:
    #             author_df.at[index, 'new_author_google_id'] = row1['new_author_google_id']
    #             break
    #     else:
    #         author_df.at[index, 'new_author_google_id'] = row['author_google_id']
    
    
    
    # for index, row  in tqdm(main_papers.iterrows()):
    #     author = row['author']
    #     for index1, row1 in changed.iterrows():
    #         if row1['author'] == author:
    #             main_papers.at[index, 'new_author_google_id'] = row1['new_author_google_id']
    #             break
    #     else:
    #         main_papers.at[index, 'new_author_google_id'] = row['author_google_id']
    
    # new_papers = df_papers_all_authors(author_df).reset_index(drop = True)
    # match_papers(main_papers[main_papers['paper_title'] == 'Parental guidance and supervised learning'], new_papers[new_papers['paper_title'] == 'Parental guidance and supervised learning'])

    # matched_df = match_papers(main_papers, new_papers)
    # download_paper_source(matched_df)
    pass
    # df1 = pd.DataFrame(df2['author_id_paper_id'],
    #                    columns = ['author_id_paper_id'])
    # # 
    # citations_by_year = pd.read_csv(r'D:\git repo\SerpAPI-Call-Clean\data\final data\citations_v2.csv')
    # df2 = citations_by_year.groupby('author_id_paper_id', as_index=False).agg({"citation_count": "sum"})

    # citations  = pd.merge(df1, df2, how='outer',on='author_id_paper_id', indicator = True).loc[lambda x : x['_merge']=='left_only'].reset_index()

    
    # # Replacing outdated author ids
    # # old_ids = ["-7QaPhMAAAAJ", "5xJizRYAAAAJ", "#Y1f2unMAAAAJ", "#tt48sngAAAAJ", "#7vNt_0gAAAAJ", 
    # #            "#DAFLSCEoAAAJ", "#AFLSCEoAAAAJ", "BV8WIV8AAAAJ", "#0qXvmz4AAAAJ", "#4_5p7N0AAAAJ", "#CjRk8DYAAAAJ", 
    # #            "NYwpYYgAAAAJ", "MT2JdLAAAAAJ", "#ToLjCNgAAAAJ", "FCTDxigAAAAJ", "ILZqfIsAAAAJ", "LJkgWDMAAAAJ", 
    # #            "#ND_WxhQAAAAJ", "#WdZ2JzMAAAAJ", "X4WN_d0AAAAJ", "XaOmQk4AAAAJ", "#Xj2qmLUAAAAJ", "#KqMjbEoAAAAJ", 
    # #            "ZKRWBZsAAAAJ", "ZtW_i4MAAAAJ", "f7k5lWUAAAAJ", "fAIzeToAAAAJ", "hN75BIUAAAAJ", "hdoeGB0AAAAJ", 
    # #            "i39wDTcAAAAJ", "#it-OqIIAAAAJ", "kyue4JAAAAAJ", "lbqAV0UAAAAJ", "#m53YNYUAAAAJ", "#qdeq7DgAAAAJ", 
    # #            "rzt08QwAAAAJ", "#oTcCfoYAAAAJ", "wvl1mTMAAAAJ", "yxjfaQQAAAAJ", "zPB2xwsAAAAJ"]
    
    # old_ids = ["-7QaPhMAAAAJ", "5xJizRYAAAAJ", "BV8WIV8AAAAJ", "NYwpYYgAAAAJ", "MT2JdLAAAAAJ", "FCTDxigAAAAJ", 
    #             "ILZqfIsAAAAJ", "LJkgWDMAAAAJ", "X4WN_d0AAAAJ", "XaOmQk4AAAAJ", "ZKRWBZsAAAAJ", "ZtW_i4MAAAAJ", 
    #             "f7k5lWUAAAAJ", "fAIzeToAAAAJ", "hN75BIUAAAAJ", "hdoeGB0AAAAJ", "kyue4JAAAAAJ", "lbqAV0UAAAAJ", 
    #             "rzt08QwAAAAJ","wvl1mTMAAAAJ", "yxjfaQQAAAAJ", "zPB2xwsAAAAJ"]
    # new_ids = ["gjB2OVUAAAAJ", "tt48sngAAAAJ", "RB-RKykAAAAJ", "Hfat62oAAAAJ", "NEgPmz4AAAAJ", "t20dQloAAAAJ", 
    #             "_eAufagAAAAJ", "7OG9U1cAAAAJ", "FBd3e1cAAAAJ", "dANuS64AAAAJ", "nYRbXP4AAAAJ", "3_Y22fEAAAAJ",
    #             "ptGn114AAAAJ", "wUeII3QAAAAJ", "_eOMu1wAAAAJ", "8FhLBYMAAAAJ", "VnYF208AAAAJ", "pqN1Fi4AAAAJ", 
    #             "eK211CkAAAAJ", "X1_BP00AAAAJ", "MXQ3WZoAAAAJ", "kZ-mZeEAAAAJ"]
    
    # for i in range(len(old_ids)): 
    #     df1['author_id_paper_id'] = df1['author_id_paper_id'].str.replace(old_ids[i], new_ids[i])
    
    # # #Scraping citation data
    # # for index, row in tqdm(check.iterrows(), total=check.shape[0]):
    # #     if index < 3682 or isinstance(row['author_id_paper_id'], float):
    # #         continue
    # #     author_id = row['author_id_paper_id'][:12]
    # #     paper_id = row['author_id_paper_id'][13:]
    # #     if paper_attempted(author_id, paper_id):
    # #         continue

    # #     paper_url = paper_link(author_id, paper_id)
    # #     browser.switch_to.window(browser.window_handles[0])
    # #     browser.get(paper_url)

    # #     # check if citation by year graph is present
    # #     citation_by_year_graph_selector = '#gsc_oci_title'
    # #     try:
    # #         by_year_graph_loaded = wait_for_el_on_page(citation_by_year_graph_selector, 5)
    # #     except NoSuchElementException:
    # #         # logging.error(f'404 Error for {author_id}, paper {paper_id}, url {paper_url}')
    # #         continue
        
    # #     if not by_year_graph_loaded:
    # #         # logging.error(f'Citation by year chart missing, skipping author {author_id}, paper {paper_id}, url {paper_url}')
    # #         mark_paper_done(author_id, paper_id, error=True)
    # #         continue

    # #     # updated paper html is stored in folder named data_citation_details, with prefix paper_
    # #     filename = f'{DATA_FOLDER}//paper_{author_id}_{paper_id}.html'
    # #     save_citation_page(browser, filename)

    # #     done = download_cited_by_pages(browser, author_id, paper_id)
    # #     if not done:
    # #         logging.warning(f'{author_id}, {paper_id} citations pages not fully downloaded. Paper URL: {paper_url}')

    # #     mark_paper_done(author_id, paper_id, complete=done)
    
    # #Extracting citation data from scraped bar graphs

        # res2 = extract_paper_names(author_id, paper_id)
        # check.at[index, 'name_check'] =res2
    #Change updated ids back to previous to facilitate merge later.
    # for i in range(len(old_ids)):
    #     for j in ids:
    #         j = j.replace(new_ids[i], old_ids[i])
        
    # citaiton_final_df = compile_final_df()
    # final_df = pd.merge(citaiton_final_df, df[['author_id_paper_id1', 'paper_title1', 'author_id_paper_id2', 'paper_title2']], how = 'left', left_on = 'author_id_paper_id', right_on = 'author_id_paper_id2', indicator = True)
    # final_df = final_df[['author_id_paper_id1', 'paper_title1', 'author_id_paper_id2', 'paper_title2', 'year', 'citation_count']]
    # final_df = final_df.rename(columns = {'author_id_paper_id1':'author_id_paper_id', 'paper_title1': 'paper_title'})