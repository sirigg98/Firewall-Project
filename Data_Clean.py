# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 11:51:17 2021

@author: f0064wk
"""

import csv
import pandas as pd
import re
import os
import math
#Match version of chrome driver and chrome
from webdriver_manager.chrome import ChromeDriverManager
#Selenium stuff
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import _find_element
#Requests
import requests
from urllib.error import HTTPError
import ssl
#Misc
from tqdm import tqdm
import random
from random import sample
import numpy as np
import json
import urllib.request
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException, NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
import warnings
from difflib import SequenceMatcher 
import difflib
from fuzzywuzzy import fuzz
import unidecode
#surpressing warnings
warnings.filterwarnings("ignore")


os.chdir('D:\git repo\Firewall-Project\Data\PageSource')

GOOGLESITE_MATCH = re.compile('^http[s]?:\/\/sites\.google\.com\/')

def irrelevant_website(link):
    if "yahoo" in link or "wikipedia" in link or "cnn" in link or "bbc" in link or "nytimes" in link or "nypost" in link or "issuu" in link or "voxeu" in link or "dailycal" in link or "voxdev" in link or "theguardian" in link or "magazine" in link or "jstor" in link or "washingtonpost" in link:
        return True
    if "phd" in link or "grad" in link or "alumni" in link or "blog" in link or "reddit" in link or "linkedin" in link or "twitter" in link or "facebook" in link:
        return True
    if "article" in link or "igc" in link or "econometricsociety" in link or "repec" in link or "nobelprize" in link or "amazon" in link or "yumpu" in link or "equitablegrowth" in link:
        return True
    if "elsevier" in link or "investopedia" in link or "typepad" in link or "bloomberg" in link or "interview" in link:
        return True
    if "scholar.google.com" in link or "researchgate" in link or "hetwebsite" in link or "studylib" in link:
        return True
    if "curriculum" in link or "vitae" in link or "fed" in link or "chegg" in link or "ask.fm" in link:
        return True

def openbrowser():
    global browser

    capabilities = dict(DesiredCapabilities.CHROME)
    capabilities['loggingPrefs'] = { 'browser':'ALL' }

    options = webdriver.ChromeOptions()
    for arg in open('D:/git repo/scholar-scrape/config/account.txt').readlines():
        options.add_argument(arg)
    #Downloads chrome driver to match the version of chrome you use.
    browser = webdriver.Chrome(ChromeDriverManager().install(), desired_capabilities=capabilities, options=options)
    return browser

def extract_page_source_othersites(ls):

    for i in ls:
        othersites = i[15]
        author = i[0]
        for x in othersites:
            try:
                req = requests.get(x, 'html.parser',verify=False)
            except:
                continue
            with open(f"{author}_{othersites.index(x)}_other.txt", 'w', encoding="utf-8") as f:
                f.write(req.text)


def extract_page_source_personalsites(ls):
    for i in ls:
        personalsites = i[11]
        author = i[0]
        for y in personalsites:
            try:
                req = requests.get(y, 'html.parser', verify=False) #Not great practice in software dev to put verify = false, but acceptable for smaller scripts
            except:
                continue
            with open(f"{author}_{personalsites.index(y)}_pers.txt", 'w', encoding="utf-8") as f:
                f.write(req.text)       

#Usually these sites have a marker at the bottom with powered by Google Sites. Else there is a copyright by Google in the page source that works too.        
def google_site(pagesource):
    GOOGLECOPYRIGHT = re.compile("^Copyright [0-9]+ Google[ LLC]?.")
    if "Google Sites" in pagesource:
        return True
    if GOOGLECOPYRIGHT.match(pagesource):
        return True
    
    
def weebly_site(pagesource):

    if "powered by" in pagesource.lower()  and "weebly" in pagesource.lower():
        return True
    if "weebly.com" in pagesource:
        return True
  #  if or weebly.com somewhaere:
   #     return True
   
def wix_site(pagesource):
    if "wix.com website builder" in pagesource.lower():
        return True
   
def wordpress_site(pagesource):
    if "wordpress.com" in pagesource.lower():
        return True
   
    
    
def other_sitecheck(ls):
    sourcecode_sites = []
    for i in ls:
        othersites = i[15]
        author = i[0]
        indices = []
        
        if not i[15]:
            continue
        

        for x in range(len(othersites)):
            try: 
                with open(f"{author}_{x}_other.txt", "r", encoding="utf-8") as text:
                    pagesource = text.read()
            except FileNotFoundError:
                continue
            if google_site(pagesource):
                i[1].append(othersites[x])
                sourcecode_sites.append(othersites[x])
                indices.append(x)
                continue
            if weebly_site(pagesource):
                i[5].append(othersites[x])
                sourcecode_sites.append(othersites[x])
                indices.append(x)
                continue
            if wix_site(pagesource):
                i[7].append(othersites[x])
                sourcecode_sites.append(othersites[x])
                indices.append(x)
                continue
            if wordpress_site(pagesource):
                i[9].append(othersites[x])
                sourcecode_sites.append(othersites[x])
                indices.append(x)
                continue
            
        for ind in indices:
            try:
                del othersites[ind]
            except IndexError:
                pass
        i[15] = othersites
        
    return ls, sourcecode_sites
        
def pers_sitecheck(ls):
    sourcecode_sites = []
    for i in ls:
        personalsites = i[11]
        author = i[0]
        indices = []
        
        if not i[5]:
            continue
        
        for y in range(len(personalsites)):
            try:
                with open(f"{author}_{y}_pers.txt", "r", encoding="utf-8") as text:
                    pagesource = text.read()    
            except FileNotFoundError:
                extract_page_source_personalsites([i])
                with open(f"{author}_{y}_pers.txt", "r", encoding="utf-8") as text:
                    pagesource = text.read()  
            if google_site(pagesource):
                i[1].append(personalsites[y])
                sourcecode_sites.append(personalsites[y])
                indices.append(y)
                continue
            if weebly_site(pagesource):
                i[5].append(personalsites[y])
                sourcecode_sites.append(personalsites[y])
                indices.append(y)
                continue
            if wix_site(pagesource):
                i[7].append(personalsites[y])
                sourcecode_sites.append(personalsites[y])
                indices.append(y)
                continue
            if wordpress_site(pagesource):
                i[9].append(personalsites[y])
                sourcecode_sites.append(personalsites[y])
                indices.append(y)
                continue

            
        for ind in indices:
            try:
                del personalsites[ind]
            except IndexError:
                print(ls.index(i))
        i[11] = personalsites
    return ls, sourcecode_sites

#Testing screens for googlse, weebly, wix and wordpress sites.
def test_fun(list_url):
    
    for i in list_url:
        try:
            req = requests.get(i, 'html.parser',verify=False)
        except:
            continue
        with open(f"test_{list_url.index(i)}.txt", 'w', encoding="utf-8") as f:
            f.write(req.text)
            
        with open(f"test_{list_url.index(i)}.txt", "r", encoding="utf-8") as text:
            pagesource = text.read()
        
        if google_site(pagesource):
            continue
        if weebly_site(pagesource):
            continue
        if wix_site(pagesource):
            continue
        if wordpress_site(pagesource):
            continue
        
#only keep own google, wix, weebly and wordpress sites:
def remove_notown_sites(ls):
    
    for i in ls:
        author = i[0]
        author_ls = author.lower().replace("-", "").replace(".", "").replace("'", "").split()
        lastfive = ""
        for l in range(5): # People abbv last names if they're very long. Using teh first five letters
            try:
                lastfive = lastfive + author_ls[-1][l]
            except IndexError:
                lastfive = author_ls[-1]
                
        firstthree = ""
        for l in range(3): # People abbv first names if they're very long. Using teh first 
            try:
                firstthree = firstthree + author_ls[0][l]
            except IndexError:
                firstthree = author_ls[0]
              
        NAME_MATCH_EXACT1 = re.compile(f".*\/{author_ls[0]}[-]?{author_ls[-1]}.*")
        NAME_MATCH_EXACT2 = re.compile(f".*\/{author_ls[-1]}[-]?{author_ls[0]}.*")
        NAME_MATCH_EXACT3 = re.compile(f".*\/{author_ls[0][0]}{lastfive}\w*.*")
        NAME_MATCH_EXACT4 = re.compile(f".*\/{author_ls[0]}.*")
        NAME_MATCH_EXACT5 = re.compile(f".*\/{author_ls[-1]}.*")
        NAME_MATCH1 = re.compile(f".*\/\w*{firstthree}\w*[-]?{lastfive}\w*.*")
        NAME_MATCH2 = re.compile(f".*\/{author_ls[0][0]}\w*{lastfive}\w*.*")
        NAME_MATCH3 = re.compile(f".*\/\w*{lastfive}\w*{author_ls[0][0]}\w*.*")
        NAME_MATCH4 = re.compile(f".*\/{lastfive}\w*\/.*")
        sites = [1, 5, 7, 9]
        for x in sites:
            for link in i[x]:
                if x == 1:
                    MATCH = GOOGLESITE_MATCH
                elif x == 5:
                    MATCH = WEEBLYSITE_MATCH
                elif x == 7:
                    MATCH = WIXSITE_MATCH1
                elif x == 9:
                    MATCH = WORDPRESSSITE_MATCH
                    
                own = False
                count = 0
                for name in author_ls:
                    if name in link:
                        own = True
                        count += 1
                if not own:
                    i[x].remove(link)
                    continue
                if count == len(author_ls):
                    continue
                if MATCH.match(link):
                    if NAME_MATCH_EXACT1.match(link) or NAME_MATCH_EXACT2.match(link) or NAME_MATCH_EXACT3.match(link) or NAME_MATCH_EXACT4.match(link) or NAME_MATCH_EXACT5.match(link):
                        continue    
                    if NAME_MATCH1.match(link) or NAME_MATCH2.match(link) or NAME_MATCH3.match(link) or NAME_MATCH4.match(link):    
                        continue     
                    if len(author_ls) > 2:
                        NAME_MATCH5 = re.compile(f".*\/{author_ls[0][0]}{author_ls[1][0]}{author_ls[-1][0]}\w*.*")
                        NAME_MATCH6 = re.compile(f".*\/{author_ls[1]}[-]?{author_ls[-1]}\w*.*")
                        if NAME_MATCH5.match(link) or NAME_MATCH6.match(link):
                            continue 
                    
                i[x].remove(link)
                    
    return ls


def recalc_num_sites(ls):
    for i in ls:
        i[2] = len(i[1])
        i[6] = len(i[5])
        i[8] = len(i[7])
        i[10] = len(i[9])
        i[12] = len(i[11])
        i[14] = len(i[13])
        i[16] = len(i[15])
        
    ls_no = [x for x in ls if x[2] == 0 and x[4] == 0 and x[6] == 0 and x[8] == 0 and x[10] == 0 and x[12] == 0 and x[14] == 0 and x[16] == 0]
    print("-----------------------------------------------------------------------")
    print("# Authors with no sites:" + str(len(ls_no)))
    print("# Authors with Google Sites:" + str(len([x for x in ls if x[2] > 0])))
    print("# Authors with GitHub Sites:" + str(len([x for x in ls if x[4] > 0])))
    print("# Authors with Weebly Sites:" + str(len([x for x in ls if x[6] > 0])))
    print("# Authors with Wix Sites:" + str(len([x for x in ls if x[8] > 0])))
    print("# Authors with Wordpress Sites:" + str(len([x for x in ls if x[10] > 0])))
    print("# Authors with Personal Sites:" + str(len([x for x in ls if x[12] > 0])))
    print("# Authors with Academic Sites:" + str(len([x for x in ls if x[14] > 0])))
    print("# Authors with Other Sites:" + str(len([x for x in ls if x[16] > 0])))
    print("-----------------------------------------------------------------------")
    return ls, ls_no

#This is so inefficient... Need to use map() or sth to make this faster/cleaner
def build_df_from_ls(ls):
    df = pd.DataFrame(columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite'])
    for author in ls:
        maximum_num = max(author[2], author[4], author[6],author[8], author[10], author[12], author[14], author[16])
        for i in range(maximum_num):
            try:
                df = df.append(pd.DataFrame([[author[0], author[1][i], 1, 0, 0, 0, 0, 0, 0, 0]], columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[3][i], 0, 1, 0, 0, 0, 0, 0, 0]],columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[5][i], 0, 0, 1, 0, 0, 0, 0, 0]],columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[7][i], 0, 0, 0, 1, 0, 0, 0, 0]],columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[9][i], 0, 0, 0, 0, 1, 0, 0, 0]], columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[11][i], 0, 0, 0, 0, 0, 1, 0, 0]],columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[13][i], 0, 0, 0, 0, 0, 0, 1, 0]], columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
            try:
                df = df.append(pd.DataFrame([[author[0], author[15][i], 0, 0, 0, 0, 0, 0, 0, 1]], columns = ['Author', 'Website', 'googlesite', 'gitsite', 'weeblysite', 'wixsite', 'wordpresssite', 'personalsite', 'academicsite', 'othersite']), ignore_index=True)
            except IndexError:
                pass
    return df
   
# Final screens for each of the websites 
# def screen_googlesites(df):
#     #First, only do for google sites
#     google_df = df[df['googlesite'] == 1]
#     google_df['googlesite_dblcheck'] = 0
#     # browser = openbrowser()
#     cntr = 0
#     # wait = WebDriverWait(browser, 10)
#     google_df = google_df.reset_index()
#     for i in range(0, google_df.shape[0]):
#         author = google_df['Author'][i]
#         url = google_df['Website'][i]
#         # main_author = google_df['author'][i]
#         # main_author_paper = google_df['paper_title'][i]
#         author_ls = author.split(" ")
#         if author_ls[0].upper() == author_ls[0]:
#             try:
#                 first_ini = author_ls[0][0]
#                 mid = author_ls[0][1:]
#                 last = author_ls[-1]
#                 author_ls[0] = first_ini
#                 author_ls[-1] = author_ls[-1]
#                 author_ls.append(last)
#             except IndexError:
#                 pass
            
            
#         author = google_df['Author'][i].lower()
#         author_ls = author.split(" ")
        
            
#         if len(author_ls) == 1:
#             continue
#         firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
#         lastfive = author_ls[-1][0:5]
#         name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
#         try:
#             name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
#         except IndexError:
#             continue
#         name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
#         try:
#             name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
#         except IndexError:
#             continue
#         name_pat5 = re.compile(f".*{lastfive}.*")
#         name_pat6 = re.compile(f".*{firstfour}.*")
#         if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
#         # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
#             google_df.at[i, 'googlesite_dblcheck'] = 1
#             cntr += 1
#             continue
#         elif name_pat5.match(url) or name_pat6.match(url): # If only first or last name matches, do a deeper search into sourcecode   
#             print('Checking sourcecode for ' + author)
#             req = requests.get(url, 'html.parser',verify=False)
#             source_code = re.split("<|>", req.text.lower())
#             source_name_pat1 = re.compile(f".*{firstfour}[\D]* {lastfive}.*")
#             source_name_pat2 = re.compile(f".*{lastfive}[\D]* {firstfour}.*")
#             for j in source_code:
#                 if source_name_pat1.match(j) or source_name_pat2.match(j):
#                     google_df.at[i, 'googlesite_dblcheck'] = 1 
#                     print("Matched with: " + url)
#                     print('-------------------')
#                     break
#     google_df['googlesite'] = google_df['googlesite_dblcheck']
#     google_df = google_df.drop('googlesite_dblcheck', 1)
#     google_df = google_df.drop('index', 1)
#     df1 = df[df['googlesite'] == 0]
#     df1 = df1.append(google_df)
#     return df1
            

def activeresearch_links(browser, url, author, website_num, paper_names):
    
    google_redirect = 0
    other_redirect = 0 
    git_redirect = 0 
    weebly_redirect = 0 
    wix_redirect = 0 
    wordpress_redirect = 0 
    other_redirect = 0
    personal_redirect = 0
    
    col_names = ['Author', 'Website', 'website_num', 'paper', 'academicsite', 'academicsite_own',
                 'redirect_google', 'redirect_git', 'redirect_weebly', 'redirect_wix', 
                 'redirect_wordpress', 'redirect_personal', 'redirect_other', 'researchlink_own', 'researchlink_ext']
    
    temp_df = pd.DataFrame(columns = col_names)
    
    browser.get(url)
    #Find element is not case insensitive :(
    elements = browser.find_elements_by_partial_link_text("Research")
    elements += browser.find_elements_by_partial_link_text("RESEARCH")
    elements += browser.find_elements_by_partial_link_text("research")
    elements += browser.find_elements_by_partial_link_text("Papers")
    elements += browser.find_elements_by_partial_link_text("papers")
    elements += browser.find_elements_by_partial_link_text("PAPERS")
    elements += browser.find_elements_by_partial_link_text("Publications")
    elements += browser.find_elements_by_partial_link_text("publications")
    elements += browser.find_elements_by_partial_link_text("PUBLICATIONS")
    elements += browser.find_elements_by_partial_link_text("Website")
    elements += browser.find_elements_by_partial_link_text("WEBSITE")
    elements += browser.find_elements_by_partial_link_text("website")
    elements += browser.find_elements_by_partial_link_text("site")
    elements += browser.find_elements_by_partial_link_text("SITE")
    elements += browser.find_elements_by_partial_link_text("Site")
    elements += browser.find_elements_by_partial_link_text("page")
    elements += browser.find_elements_by_partial_link_text("PAGE")
    elements += browser.find_elements_by_partial_link_text("Page")
        
    
    samedom_links = [browser.current_url]
    other_links = []
    DOMAIN_MATCH = re.compile('^http[s]?:\/\/(www\.)?([\D]+)\.[a-z]{2,3}\/.*')
    ACTIVELINK_MATCH = re.compile('a href="([^"]*)"')
    
    row = pd.DataFrame([[author, url, website_num, '', 1, 0, google_redirect,
                             git_redirect, wix_redirect, weebly_redirect, wordpress_redirect, 
                             personal_redirect, other_redirect, [],[]]], columns = col_names)
    
    try:
        url_domain = DOMAIN_MATCH.match(url).group(2)
    except AttributeError:
        temp_df = temp_df.append(row)
        return temp_df
    for i in elements:
        try:
            if i.is_enabled():
                link = i.get_attribute('href')
                if link is None:
                    continue
                try:
                    link_domain = DOMAIN_MATCH.match(link).group(2)
                except AttributeError:
                    continue
                link_domain_split = link_domain.split(".")
                url_domain_split = url_domain.split(".")
                if link_domain == url_domain: #i.e. the domain is the same
                    samedom_links.append(link)
                    #Yale for eg has the academic site on 
                elif link_domain_split[-1] in url_domain or url_domain_split[-1] in link_domain:
                    samedom_links.append(link)
                else:
                    other_links.append(link) 
        except StaleElementReferenceException:
            continue
                
    firstfour = author.split()[0][0:4].lower()
    lastfive = author.split()[-1][0:5].lower()
    GOOGLESITE_MATCH = re.compile('^http[s]?:\/\/sites\.google\.com\/')
    GITSITE_MATCH1 = re.compile('^.*\.github\.io\/$')
    GITSITE_MATCH2 = re.compile('^.*\.github\.io\/.*')
    WEEBLYSITE_MATCH = re.compile('^http[s]?:\/\/.*\.weebly\.com\/$')
    WORDPRESSSITE_MATCH = re.compile('^http[s]?:\/\/.*\.wordpress\.com.*')
    WIXSITE_MATCH1 = re.compile('^http[s]?:\/\/.*\.wixsite\.com.*')
    WIXSITE_MATCH2 = re.compile('^http[s]?:\/\/.*\.wix\.com.*')
    PERSONALSITE_MATCH1 = re.compile(f'^http[s]?:\/\/(www.)?{firstfour}.*{lastfive}.*\..*')
    PERSONALSITE_MATCH2 = re.compile(f'^http[s]?:\/\/(www.)?[a-z]*.*{firstfour[0]}[a-z]*{lastfive}.*\..*')
    PERSONALSITE_MATCH3 = re.compile(f'^http[s]?:\/\/(www.)?{lastfive}.*{firstfour}.*\..*')
    PERSONALSITE_MATCH4 = re.compile(f'http[s]?:\/\/(www.)?{lastfive}.*.*')

    for x in other_links:
        if GOOGLESITE_MATCH.match(x):
            google_redirect = 1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
        elif GITSITE_MATCH1.match(x) or GITSITE_MATCH2.match(x):
            git_redirect = 1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
            
        elif WEEBLYSITE_MATCH.match(x):
            weebly_redirect = 1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
            
        elif WIXSITE_MATCH1.match(x) or WIXSITE_MATCH2.match(x):
            wix_redirect =1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
            
        elif WORDPRESSSITE_MATCH.match(x):
            wordpress_redirect = 1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
        
        elif PERSONALSITE_MATCH1.match(x) or PERSONALSITE_MATCH2.match(x) or PERSONALSITE_MATCH3.match(x) or PERSONALSITE_MATCH4.match(x):
            personal_redirect = 1
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
            
        elif irrelevant_website(x):
            try:
                other_links = other_links.remove(x)
            except AttributeError:
                continue
            
    try:  
        if len(other_links) > 0:
            other_redirect = 1
    except TypeError:
        pass
    #Look at only unique links
    # for j in list(set(samedom_links)):
    #     try:
    #         req = requests.get(j, 'html.parser',verify=False)   
    #     except:
    #         continue
        
    #     source_code = re.split("<|>", req.text
    for i in range(len(paper_names)):
        temp_row = pd.DataFrame([[author, url, website_num, paper_names[i], 1, 1, google_redirect,
                             git_redirect, wix_redirect, weebly_redirect, wordpress_redirect, 
                             personal_redirect, other_redirect, [],[]]], columns = col_names)
        
        temp_row.at[0, 'paper'] = paper_names[i]
        
        for j in list(set(samedom_links)):
            try:
                req = requests.get(j, 'html.parser',verify=False)   
            except:
                continue
    
            source_code = re.split("<|>", req.text)

            for sourcecode_text in source_code: 
                if sourcecode_text == '' or isinstance(paper_names[i], float):
                    continue
                similarity_ratio = SequenceMatcher(None, paper_names[i].lower(), sourcecode_text.lower()).ratio()
                if similarity_ratio > 0.8:
                    index = source_code.index(sourcecode_text)
                    for ind in range(0,30):
                        #Checks for href 2 items before and 4 items after the item with paper name match
                        if (match:= ACTIVELINK_MATCH.match(source_code[index-5+ind])):
                            paper_link = match.group(1)
                            if url_domain in paper_link or not paper_link.startswith('http') or paper_link.startswith('/'):
                                # print(temp_df['researchlink_own'][index])
                                temp_row['researchlink_own'][0].append(paper_link)
                                break

                            else:    
                                # print(temp_df['researchlink_ext'][index])
                                temp_row['researchlink_ext'][0].append(paper_link)
                                break
                    else:
                        continue
                    break
        temp_df = temp_df.append(temp_row)
    # return True, False, google_redirect, git_redirect, weebly_redirect, wix_redirect, wordpress_redirect, other_redirect
    return temp_df.reset_index(drop = True)


def screen_academicsites(df):
    try:
        DOMAIN_MATCH = re.compile('^http[s]?:\/\/(www\.)?([\D]+)\.[a-z]{2,3}\/.*')
        
        df['website_num'] = (df.groupby('Author').cumcount()+1).apply(str)
        df.drop(['googlesite', 'gitsite', 'weeblysite', 'wixsite', 
                 'wordpresssite', 'personalsite', 'othersite'], axis = 1)
        
        #First, only do for google sites
        aca_df = df[df['academicsite'] == 1]
        
        
        col_names = ['Author', 'Website', 'website_num', 'paper', 'academicsite', 'academicsite_own',
                     'redirect_google', 'redirect_git', 'redirect_weebly', 'redirect_wix', 
                     'redirect_wordpress', 'redirect_personal', 'redirect_other', 'researchlink_own', 
                     'researchlink_ext']
        
        ret_df = pd.DataFrame(columns = col_names)
        
        
        # browser = openbrowser()
        # wait = WebDriverWait(browser, 10)
        aca_df = aca_df.reset_index()
        browser = openbrowser()
        for i in tqdm(range(0, aca_df.shape[0]), desc = "Screening academic sites"): 
            
            if i < 1285:
                continue
            
    
            author = aca_df['Author'][i]
            url = aca_df['Website'][i]
            paper_names = aca_df['paper_title'][i]
            website_num = aca_df['website_num'][i]
            url_domain = DOMAIN_MATCH.match(url)
            
            row = pd.DataFrame([[author, url, website_num, '', 1, 0, 0, 0, 0, 0, 0, 0, 0, [],[]]], columns = col_names)
            
            
            if ".pdf" in url or "scholar.google" in url:
                continue
            
            author_ls = author.split(" ")
            if author_ls[0].upper() == author_ls[0]:
                try:
                    first_ini = author_ls[0][0]
                    last = author_ls[-1]
                    author_ls[0] = first_ini
                    author_ls[-1] = author_ls[-1]
                    author_ls.append(last)
                except IndexError:
                    pass
                
                
            author = aca_df['Author'][i].lower()
            author_ls = author.split(" ")
            
                
            if len(author_ls) == 1:
                continue
            firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
            lastfive = author_ls[-1][0:5]
            name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
            try:
                name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
            except IndexError:
                ret_df = ret_df.append(row)
                continue
            name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
            try:
                name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
            except IndexError:
                ret_df = ret_df.append(row)
                continue
            # name_pat5 = re.compile(f".*{lastfive}.*")
            # name_pat6 = re.compile(f".*{firstfour}.*")
            # name_pat7 = re.compile(f".*{firstfour[0]}{lastfive[0]}.*")
            if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
            # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
    
    
                try:
                    req = requests.get(url, 'html.parser',verify=False)
                    source_code = re.split("<|>", req.text.lower())
                except:
                    continue
                
                results = activeresearch_links(browser, url, author, website_num, paper_names)
                ret_df = ret_df.append(results)
                
            else: # If only first or last name matches, do a deeper search into sourcecode   
                try:    
                    req = requests.get(url, 'html.parser',verify=False)
                except:
                    continue
                source_name_pat = re.compile(f".*{firstfour}[a-z]* {lastfive}.*")
                source_code = re.split("<|>", req.text.lower())
                source_name_pat = re.compile(f".*{firstfour}[\D]* {lastfive}.*")
                first = 1000000000
                last = 10000000
                for j in source_code:
                    if source_name_pat.match(j.lower()):
                        results = activeresearch_links(browser, url, author, website_num, paper_names)
                        ret_df = ret_df.append(results)
                        break
                #Sometimes names are broken up in the html code for presentation. See Slesh A Shrestha
                    else:
                        if firstfour.lower() in j:
                            first = source_code.index(j)
                        if lastfive.lower() in j:
                            last = source_code.index(j)
                        if abs(first - last) < 20:
                            results = activeresearch_links(browser, url, author, website_num, paper_names)
                            ret_df = ret_df.append(results)
                            break
                else:
                    ret_df = ret_df.append(row)
    except:
        return ret_df

        
                            
    # aca_df['academicsite'] = google_df['academicsite_dblcheck']
    # aca_df.drop('academicsite_dblcheck', 'index', 1)
    return ret_df


def screen_googlesites(df):
    #Only do for google sites
    google_df = df[df['googlesite'] == 1]
    google_df['own_dblcheck'] = 0
    google_df = google_df.reset_index()
    c_perf = 0
    c_potential = 0
    c_false = 0
    for index, row in tqdm(google_df.iterrows(), total = google_df.shape[0]):
        # if index < 2890:
        #     continue
        author = unidecode.unidecode(row['Author']).lower().replace('.', '').replace('-', '').replace('_', '')
        if "(" in author:
            author = author.split("(")[0].strip()
        
        url = row['Website'].replace('-', '').replace('econ', '')
        url_original = row['Website']
    # wait = WebDriverWait(browser, 10)
        # print(author + " index no. " + str(index))
        author_ls = author.split(" ") 
        if author_ls[0].upper() == author_ls[0]:
            try:
                first_ini = author_ls[0][0]
                mid = author_ls[0][1:]
                last = author_ls[-1]
                author_ls = [first_ini, mid, last]
            except IndexError:
                pass
      
        if len(author_ls) == 1:
            continue
        firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
        lastfive = author_ls[-1][0:4]
        
        name_pat1 = re.compile('{}[a-z]*[\s]*[^<]*{}[a-z]*'.format(firstfour, lastfive))
        try:
            name_pat2 = re.compile(".*{}[a-z]*[\s]*[^<]*{}[a-z]*".format(firstfour[0], lastfive))
        except IndexError:
            pass
        name_pat3 = re.compile(".*{}[a-z]*[\s]*[^<]*{}[a-z]*".format(lastfive, firstfour))
        try:
            name_pat4 = re.compile(".*{}[a-z]*[\s]*[^<]*{}[a-z]*".format(firstfour, lastfive[0]))
        except IndexError:
            pass
        name_pat5 = re.compile(f".*{lastfive}.*")
        name_pat6 = re.compile(f".*{firstfour}.*")
        if (name_pat1.search(url) or name_pat3.search(url)):
            google_df.at[index, 'own_dblcheck'] = 2
            c_perf += 1
            continue
        else: # For the rest, do a deeper search into sourcecode   
            print('Checking sourcecode for ' + author + " " + url)
            req = requests.get(url_original, 'html.parser',verify=False)
            source_code = re.split("<|>", req.text.lower())
            name_pat1 = re.compile('{}[a-z|\s]*{}[a-z]*'.format(firstfour, lastfive))
            try:
                name_pat2 = re.compile(".*{}[a-z|\s]*{}[a-z]*".format(firstfour[0], lastfive))
            except IndexError:
                pass
            name_pat3 = re.compile(".*{}[a-z|\s]*{}[a-z]*".format(lastfive, firstfour))
            try:
                name_pat4 = re.compile(".*{}[a-z|\s]*{}[a-z]*".format(firstfour, lastfive[0]))
            except IndexError:
                pass
            name_pat5 = re.compile(f".*{lastfive}.*")
            name_pat6 = re.compile(f".*{firstfour}.*")
            br = False
            for i in range(1500):
                try:
                    j = source_code[i].replace("-", "")
                except IndexError:
                    break
                if (name_pat1.search(j) or  name_pat2.search(j) or name_pat3.search(j)):
                    google_df.at[index, 'own_dblcheck'] = 2
                    c_perf += 1
                    print("Matched with: " + url)
                    print('-------------------')
                    br = True
                    break
                elif name_pat4.search(j) or name_pat5.search(j):
                    google_df.at[index, 'own_dblcheck'] = 1
                    c_potential += 1
                    print("Potentially matched with: " + url)
                    print('-------------------')
                    br = True
                    break
            if not br:
                c_false += 1
                continue

    print('Perfect Matches: {}'.format(c_perf))
    print('Potential Matches: {}'.format(c_potential))
    print('False Positives: {}'.format(c_false))
    df1 = df[df['googlesite'] == 0]
    df1 = df1.append(google_df)
    return df1     


       

def merge_googlesites(df, website_df, author_xwalk):
    google_df = website_df.groupby('Author').agg({"googlesite": "sum"}).reset_index()
    google_df = pd.merge(google_df, author_xwalk, left_on = 'Author', right_on='Key', how = 'inner')
    
    df['coauths'] = [[] for _ in range(len(df))]
    
    for index, row in df.iterrows():
        if isinstance(row['coauthors_clean'], str):
            authors = re.split(',|&|\sand', row['coauthors_clean'])
        else:
            authors = []
        authors.append(row['author_google_name'])    
        df.at[index, 'num_auths'] = len(authors)
        df.at[index, 'coauths'] = authors
    
    rows = []
    _ = df.apply(lambda row: [rows.append([row['author'], row['author_google_name'], row['author_google_id'],
                                           row['paper_google_id'], row['author_id_paper_id'], row['paper_title'],
                                           row['publication_date'], row['co-authors'], row['coauthors_clean'], row['num_auths'],
                                           row['journal'], row['publisher'], row['total_citation_count'], 
                                           row['description'], row['title_ref_china'], row['desc_ref_china'], nn.strip()]) 
                              for nn in row.coauths], axis=1)
    
    df_for_merge = pd.DataFrame(rows, columns = ['author', 'author_google_name', 'author_google_id',
                                                 'paper_google_id', 'author_id_paper_id', 'paper_title', 
                                                 'publication_date', 'co-authors', 'coauthors_clean', 'num_auths', 'journal', 
                                                 'publisher', 'total_citation_count', 'description', 'title_ref_china', 
                                                 'desc_ref_china', 'Author'])
    
    ret_df = pd.merge(google_df, df_for_merge, left_on = 'value', right_on = 'Author', how = 'inner')
    
    ret_df = ret_df.groupby('author_id_paper_id').agg({'googlesite': 'sum', 'num_auths': 'mean'}).reset_index()
    
    return ret_df
                
# def screen_academicsites(df):
#     DOMAIN_MATCH = re.compile('^http[s]?:\/\/(www\.)?([\D]+)\.[a-z]{2,3}\/.*')
    
#     df['website_num'] = (df.groupby('Author').cumcount()+1).apply(str)
#     #First, only do for google sites
#     aca_df = df[df['academicsite'] == 1]
#     aca_df['academicsite_own'] = 0
#     #If academic site redirects to googlesite
#     aca_df['google_aca_site'] = 0
#     aca_df['other_aca_site'] = 0
#     #If active research links redirect to same or other domain
#     aca_df['academicsite_research_own'] = 0
#     aca_df['academicsite_research_ext'] = 0

#     # browser = openbrowser()
#     # wait = WebDriverWait(browser, 10)
#     aca_df = aca_df.reset_index()
#     browser = openbrowser()
#     for i in tqdm(range(0, aca_df.shape[0]), desc = "Screening academic sites"):
#         # if i > 4151:
        
#         ls = []
#         author = aca_df['Author'][i]
#         url = aca_df['Website'][i]
#         paper_names = aca_df['paper_title'][i]
#         website_num = aca_df['website_num'][i]
#         url_domain = DOMAIN_MATCH.match(url)
#         if ".pdf" in url or "scholar.google" in url:
#             continue
#         filename_start = f'{author.lower()}{website_num}_researchpage_'
#         ls = [filename for filename in 
#               os.listdir('D:\git repo\Firewall-Project\Data\Research PageSource') 
#               if filename.startswith(filename_start)]
        
#         if ls:
#             aca_df.at[i, 'academicsite_own'] = 1 
#             for filename in ls:
#                 REDIRECT_MATCH = re.compile(filename_start + "([0-9])_([0-9])_([0-9])")
#                 try:
                    
#                     aca_df.at[i, 'google_aca_site'] = REDIRECT_MATCH.match(filename).group(2)
#                     aca_df.at[i, 'other_aca_site'] = REDIRECT_MATCH.match(filename).group(3)
#                 except AttributeError:
#                     continue
#                 with open(f'D:\git repo\Firewall-Project\Data\Research PageSource\{filename}', 'r', encoding = 'utf-8') as sourcecode:    
#                     source_code = re.split("<|>", sourcecode.read())
    
#                 ACTIVELINK_MATCH = re.compile('a href="(.*)"')
#                 for sourcecode_text in source_code: 
#                     for paper in paper_names:
#                         if isinstance(paper, float):
#                             continue
#                         similarity_ratio = SequenceMatcher(None, paper.lower(), sourcecode_text.lower()).ratio()
#                         if similarity_ratio > 0.6:
#                             index = source_code.index(sourcecode_text)
#                             for ind in range(0,40):
#                         #Checks for href 2 items before and 4 items after the item with paper name match
#                                 try:
#                                     if (match:= ACTIVELINK_MATCH.match(source_code[index-10+ind])):
#                                         if DOMAIN_MATCH.match(match.group(1)) == url_domain or "pdf" in match.group(1):
#                                             aca_df.at[i, 'academicsite_research_own'] = 1 
#                                         else:    
#                                             aca_df.at[i, 'academicsite_research_ext'] = 1 
                                    
#                                 except IndexError:
#                                     break

                    

#         else: 
#         # main_author = google_df['author'][i]
#         # main_author_paper = google_df['paper_title'][i]
#             author_ls = author.split(" ")
#             if author_ls[0].upper() == author_ls[0]:
#                 try:
#                     first_ini = author_ls[0][0]
#                     last = author_ls[-1]
#                     author_ls[0] = first_ini
#                     author_ls[-1] = author_ls[-1]
#                     author_ls.append(last)
#                 except IndexError:
#                     pass
                
                
#             author = aca_df['Author'][i].lower()
#             author_ls = author.split(" ")
            
                
#             if len(author_ls) == 1:
#                 continue
#             firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
#             lastfive = author_ls[-1][0:5]
#             name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
#             try:
#                 name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
#             except IndexError:
#                 continue
#             name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
#             try:
#                 name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
#             except IndexError:
#                 continue
#             # name_pat5 = re.compile(f".*{lastfive}.*")
#             # name_pat6 = re.compile(f".*{firstfour}.*")
#             # name_pat7 = re.compile(f".*{firstfour[0]}{lastfive[0]}.*")
#             if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
#             # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
#                 aca_df.at[i, 'academicsite_own'] = 1 
#                 try:
#                     req = requests.get(url, 'html.parser',verify=False)
#                     source_code = re.split("<|>", req.text.lower())
#                 except:
#                     continue
#                 source_name_pat = re.compile(f".*{firstfour}[a-z]* {lastfive}.*")
#                 for j in source_code:
#                     if isinstance(paper_names, list):
#                         if activeresearch_links(browser, url, author, website_num, paper_names):
#                             aca_df.at[i, 'academicsite_research'] = 1 
#                     break
#                 continue
#             else: # If only first or last name matches, do a deeper search into sourcecode   
#                 try:    
#                     req = requests.get(url, 'html.parser',verify=False)
#                 except:
#                     continue
#                 source_code = re.split("<|>", req.text.lower())
#                 source_name_pat = re.compile(f".*{firstfour}[\D]* {lastfive}.*")
#                 first = 1000000000
#                 last = 10000000
#                 for j in source_code:
#                     if source_name_pat.match(j):
#                         aca_df.at[i, 'academicsite_own'] = 1 
#                         if isinstance(paper_names, list):
#                             if activeresearch_links(browser, url, author, website_num, paper_names):
#                                 aca_df.at[i, 'academicsite_research'] = 1 
#                         break
#                 #Sometimes names are broken up in the html code for presentation. See Slesh A Shrestha
#                     if firstfour.lower() in j:
#                         first = source_code.index(j)
#                     if lastfive.lower() in j:
#                         last = source_code.index(j)
#                     if abs(first - last) < 20:
#                         aca_df.at[i, 'academicsite_own'] = 1 
#                         if isinstance(paper_names, list):
#                             results = activeresearch_links(browser, url, author, website_num, paper_names)
#                             if results[0]:
#                                 aca_df.at[i, 'academicsite_research_own'] = 1 
#                             elif results[1]:
#                                 aca_df.at[i, 'academicsite_research_ext'] = 1 
#                             if results[2] == int(1):
#                                 aca_df.at[i, 'google_aca_site'] = 1
#                             if results[3]==int(1):
#                                 aca_df.at[i, 'other_aca_site'] = 1
#                         break
#     # aca_df['academicsite'] = google_df['academicsite_dblcheck']
#     # aca_df.drop('academicsite_dblcheck', 'index', 1)
#     df1 = df[df['academicsite'] == 0]
#     df1['academicsite_own'] = 0
#     df1['google_aca_site'] = 0
#     df1['other_aca_site'] = 0
#     df1['academicsite_research_own'] = 0
#     df1['academicsite_research_ext'] = 0

#     df1 = df1.append(aca_df)
    
#     return df1

def get_close_matches_lev(col1, col2, cutoff = 15):
    ls1 = list(col1)
    ls2 = list(col2)
    
    matches = []
    for i in ls1:
        match = ls2[0]
        ratio = 0
        for j in ls2:
            temp_ratio = fuzz.ratio(i, j)
            if temp_ratio > cutoff and temp_ratio > ratio:
                ratio = temp_ratio
                match = j
        if ratio < cutoff:
            match = ""
        matches.append(match)
    return pd.Series(matches)
        
                

def fuzzy_merge(df1, df2):
    
    df1.reset_index()
    df2.reset_index()
    perf_match = pd.merge(df1, df2, how = 'inner', left_on = "Author", right_on = "author")
    perf_match_authors = list(perf_match['Author'])
    
    print(len(df1))
    drop1 = []
    drop2 = []
    for index, row in df1.iterrows():
        if row['Author'] in perf_match_authors:
            drop1.append( index )
            
    for index, row in df2.iterrows():
        if row['author'] in perf_match_authors:
            drop2.append( index )
            
    temp1 = df1.drop(drop1, axis = 0)
    temp2 = df2.drop(drop2, axis = 0)
    
    print(str(temp1.shape[0]))
    print("Num perf match: " + str(perf_match.shape[0]), flush = True)
    
    temp1.reset_index()
    temp2.reset_index()
    
    temp1['author_fuzz'] = temp1['Author'].apply(lambda x: difflib.get_close_matches(x, temp2['author'], cutoff = 0.7))
    
    for index, row in temp1.iterrows():
        try:
            temp1.at[index, 'author_fuzz'] = row['author_fuzz'][0]
        except IndexError:
            temp1.at[index, 'author_fuzz'] = ''
    fuzzy_match = pd.merge(temp1, temp2.filter(['author', 'paper_title']), how = "left",
                            left_on = "author_fuzz", right_on = "author")
    
    final_df = perf_match.append(fuzzy_match)
    # 
    return final_df    
    

    
def generate_final_df(website_ls):
    temp = [x for x in website_ls if x is not None]
    sourcecode_sites = []
    recalc_num_sites(temp)
    other_res = other_sitecheck(temp)
    sourcecode_sites = sourcecode_sites + other_res[1]
    
    pers_res = pers_sitecheck(other_res[0])
    
    temp1 = pers_res[0]
    sourcecode_sites = sourcecode_sites + pers_res[1]
    
    print("-----------------------------------------------------------------------")
    print("# of Google, Weebly, Wix and Wordpress Sites found through source code check: " + str(len(sourcecode_sites)))
    print("-----------------------------------------------------------------------")
    temp2 = remove_notown_sites(temp1)
    googlesite_authors = [x for x in temp2 if len(x[1])>0]
    
    
    res = recalc_num_sites(temp2)
    website_final = res[0]
    nomatches = res[1]
    df = build_df_from_ls(website_final)
    df['sourcecode_check'] = 0
    
    for i in range(df.shape[0]):
        for url in sourcecode_sites:
            if df.Website[i] == url:
                df.at[i, 'sourcecode_check'] = 1
                break
            
    return df, nomatches, googlesite_authors
        
# For coauthors, quite a few false positives particularly for google sites. Pre screen these urls by checking if various forms of their name is present in the url.



###############################################################################

results = generate_final_df(website_ls)
final_df = results[0]
final_df1 = screen_googlesites(final_df)
# nomatches_ls = results[1]
# authors_w_googlesites = results[2]


# author_df = pd.read_excel('D:\git repo\Firewall-Project\deduped_coauthors_v3.xlsx')
# author_xwalk = pd.melt(author_df, id_vars='Key', value_vars=['coauthor1', 'coauthor2', 'coauthor3', 'coauthor4', 'coauthor5', 'coauthor6', 'coauthor7', 'coauthor8', 'coauthor9', 'coauthor10'])
# author_xwalk = author_xwalk.dropna().drop('variable', axis = 1)

# paper_df = pd.read_excel('D:\git repo\Firewall-Project\Data\mains_v3.xlsx')

# website_df = pd.read_excel('D:\git repo\Firewall-Project\Data\author_websites.xlsx')







# final_df.to_csv("D:\\git repo\\SerpAPI-Call-Clean\\data\\coauthors_website_test.csv")


# # Main author academic site screening:

# df1 = pd.read_csv(r"D:\git repo\Firewall-Project\Data\final data\papers_v2_rank_ALL.csv", encoding = 'utf-8')
# df1_old =  pd.read_stata(r"D:\git repo\Firewall-Project\Data\final data\papers_v2_rank_ALL.dta")
# df1['pub_year'] = 0
# df1['publication_date'] = df1['publication_date'].str.strip()
# df1['publication_date'] = df1['publication_date'].str.split("/")

# for index, row in df1.iterrows():
#     try:
#         for i in row['publication_date']:
#             if len(i) == 4:
#                 df1.at[index, 'pub_year'] =int(i)
#     except TypeError:
#         continue

    # 
# crosswalk = pd.read_csv(r'D:\git repo\Firewall-Project\Data\final data\key_name_crosswalk.csv')
# df = df1[['author', 'author_id_paper_id', "paper_title"]].melt(id_vars = ['author_id_paper_id', 'paper_title', 'author'])
# # df_papers = df[~df['value'].isnull()].drop(columns = ["variable", "author_id_paper_id"])
# df_old = df1_old[['author', 'author_id_paper_id', "paper_title"]].melt(id_vars = ['author_id_paper_id', 'paper_title', 'author'])

# # for_merge = df2.apply(lambda x: x.sort_values('pub_year', ascending=False)).reset_index(drop = True)

# for_merge = df1[~df1['paper_title'].isna()]
# for_merge = for_merge.filter(['author', 'paper_title'])
# for_merge = for_merge.groupby('author')['paper_title'].apply(list).reset_index()

# for_merge_old = df1_old[~df1_old['paper_title'].isna()]
# for_merge_old = for_merge_old.filter(['author', 'paper_title'])
# for_merge_old = for_merge_old.groupby('author')['paper_title'].apply(list).reset_index()

# final_df2_old = fuzzy_merge(final_df1, for_merge_old)
# final_df2 = fuzzy_merge(final_df1, for_merge)

# new_obs = []
# for index, row in final_df2_old.iterrows():
#     new_obs.append([row['Author'], row['Website']])
    
# for index, row in final_df2.iterrows():
#     if [row['Author'], row['Website']] not in new_obs:
#         final_df2.drop(index, inplace = True)
#         final_df2 = final_df2.append(row)

# return_df = screen_academicsites(final_df2)
# final_df_app.append(return_df)
# final_df_app.to_csv(r"D:\git repo\Firewall-Project\Data\author_based.csv")


# def name_info_type(name):
#     i_sp = name.split()
#     if len(i_sp) > 2:
#         if len(i_sp[0]) > 1:
#             if len(i_sp[1]) > 1:
#                 i_type = 1
#             else:
#                 i_type = 2
#         else:
#             if len(i_sp[1]) > 1:
#                 i_type = 3
#             else:
#                 i_type = 4
#     elif len(i_sp) == 2:
#         if len(i_sp[0]) > 1:
#             i_type = 5
#         else:
#             i_type = 6
#     else:
#         i_type = 7
        
#     return i_type

# # # < 3 17112
# # # 3 or 4 1029
# # # < 5 18151
# # # 5 43013
# # # 6 6371
# # # 7 200

# # # Tot: 67735

# def fun(df):
#     df['num_changes'] = 0
#     c = 0
#     m = []
#     ls = []
#     coauths = []
#     for index, row in tqdm(df.iterrows()):
#         id_paper = row['author_id_paper_id'] 
#         try:
#             coauthors = row['coauthors_y']
#         except AttributeError:
#             continue
#         n = 0
#         for i in range(1, 163):
#             if isinstance(row[f'coauthors{i}'], str):
#                 coauths.append(row[f'coauthors{i}'].lower())
#             try:
#                 author = row[f'coauthors{i}']
#                 author_split = author.lower().split()
#             except AttributeError:
#                 break
#             try:
#                 AUTHOR_MATCH = re.compile(f'({author_split[0][0]}[\D]* {author_split[-1]})')            
#                 for coauthor in coauthors:
#                     if coauthor == '':
#                         if coauthors[coauthors.index(coauthor)-1] == "":
#                             break
#                         continue
#                     if name_info_type(coauthor) == 7:
#                         m.append(coauthor.lower())
#                         continue
#                     if AUTHOR_MATCH.match(coauthor.lower())  and name_info_type(author.lower().replace(".", "")) > name_info_type(AUTHOR_MATCH.match(coauthor.lower()).group(1).replace(".", "")):
#                         new_author = AUTHOR_MATCH.match(coauthor.lower()).group(1) 
#                         ls.append([id_paper, author, new_author])
#                         df.at[index, f'coauthors{i}'] = new_author
#                         c += 1 
#                         n += 1
#                         break
#             except:
#                 continue
            
#         df.at[index, 'num_changes'] = n
        
#     print(len(set(coauths)))
#     print(c, flush = True)
    
#     return df, ls, list(set(coauths)), list(set(m))

# df1 = pd.read_csv(r'C:\Users\F0064WK\Downloads\fullsample.csv')
# new_coauthos = pd.read_csv(r"C:\Users\F0064WK\Downloads\repec_authors.csv")
# merged = pd.merge(df1, new_coauthos, how = "left", left_on = "author_id_paper_id", right_on = "author_id_paper_id")
# merged['coauthors_y'] = merged['coauthors_y'].str.split(", ")
# res = fun(merged)
# res_df = res[0]
# res_ls = res[1] 
# res_coauths = res[2] 


# # citations = pd.read_csv(r"C:\Users\F0064WK\Downloads\citaions_v2.csv")
# # test = pd.merge(df1, citations, on ="author_id_paper_id", how = "inner")

# # cols = [i for i in test if i.startswith('coauthors')]

# # test = test[['author_id_paper_id', 'author', 'year', 'citation_count'] + cols].drop('coauthors', axis = 1).melt(id_vars = ['author_id_paper_id', 'author', 'year', 'citation_count'])
            
# # test = test[test['value'].notna()]     

# # test['type'] = 0
# # for index, row in tqdm(test.iterrows()):
# #     name_type = name_info_type(row['value'])
# #     if name_type in [1, 2]:
# #         test.at[index, 'type'] = 1
# #     elif name_type in [3, 4]:
# #         test.at[index, 'type'] = 3
# #     else:
# #         test.at[index,'type'] = name_type
# # ## Coauthor academic site screening:
    
# from PyPDF2 import PdfFileReader

# def extract_information(pdf_path):
#     with open(pdf_path, 'rb') as f:
#         pdf = PdfFileReader(f)
#         information = pdf.getDocumentInfo()
#         number_of_pages = pdf.getNumPages()
#         text = pdf.getPage(0).extractText()

#     txt = f"""
#     Information about {pdf_path}: 

#     Author: {information.author}
#     Creator: {information.creator}
#     Producer: {information.producer}
#     Subject: {information.subject}
#     Title: {information.title}
#     Number of pages: {number_of_pages}
#     """

#     print(txt)
#     return text

# txt = extract_information(r'C:/Users/F0064WK/Downloads/192.pdf')