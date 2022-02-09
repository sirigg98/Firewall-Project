# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 11:51:17 2021

@author: f0064wk
"""

import csv
import pandas as pd
import re
import os
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
from random import sample
import numpy as np
import json
import urllib.request
import time
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
import warnings
#surpressing warnings
warnings.filterwarnings("ignore")


os.chdir('D:\git repo\SerpAPI-Call-Clean\Data\PageSource')

GOOGLESITE_MATCH = re.compile('^http[s]?:\/\/sites\.google\.com\/')

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
def screen_googlesites(df):
    #First, only do for google sites
    google_df = df[df['googlesite'] == 1]
    google_df['googlesite_dblcheck'] = 0
    # browser = openbrowser()
    cntr = 0
    # wait = WebDriverWait(browser, 10)
    google_df = google_df.reset_index()
    for i in range(0, google_df.shape[0]):
        author = google_df['Author'][i]
        url = google_df['Website'][i]
        # main_author = google_df['author'][i]
        # main_author_paper = google_df['paper_title'][i]
        author_ls = author.split(" ")
        if author_ls[0].upper() == author_ls[0]:
            try:
                first_ini = author_ls[0][0]
                mid = author_ls[0][1:]
                last = author_ls[-1]
                author_ls[0] = first_ini
                author_ls[-1] = author_ls[-1]
                author_ls.append(last)
            except IndexError:
                pass
            
            
        author = google_df['Author'][i].lower()
        author_ls = author.split(" ")
        
            
        if len(author_ls) == 1:
            continue
        firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
        lastfive = author_ls[-1][0:5]
        name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
        try:
            name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
        except IndexError:
            continue
        name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
        try:
            name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
        except IndexError:
            continue
        name_pat5 = re.compile(f".*{lastfive}.*")
        name_pat6 = re.compile(f".*{firstfour}.*")
        if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
        # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
            google_df.at[i, 'googlesite_dblcheck'] = 1
            cntr += 1
            continue
        elif name_pat5.match(url) or name_pat6.match(url): # If only first or last name matches, do a deeper search into sourcecode   
            print('Checking sourcecode for ' + author)
            req = requests.get(url, 'html.parser',verify=False)
            source_code = re.split("<|>", req.text.lower())
            source_name_pat = re.compile(f".*{firstfour}[a-z]* {lastfive}.*")
            for j in source_code:
                if source_name_pat.match(j):
                    google_df.at[i, 'googlesite_dblcheck'] = 1 
                    print("Matched with: " + url)
                    print('-------------------')
                    break
    google_df['googlesite'] = google_df['googlesite_dblcheck']
    google_df = google_df.drop('googlesite_dblcheck', 1)
    google_df = google_df.drop('index', 1)
    df1 = df[df['googlesite'] == 0]
    df1 = df1.append(google_df)
    return df1
            
                
                
                
def screen_gitesites(df):
    #First, only do for google sites
    git_df = df[df['gitsite'] == 1]
    git_df['gitsite_dblcheck'] = 0
    # browser = openbrowser()
    cntr = 0
    # wait = WebDriverWait(browser, 10)
    git_df = git_df.reset_index()
    for i in range(0, git_df.shape[0]):
        author = git_df['Author'][i]
        url = git_df['Website'][i]
        # main_author = google_df['author'][i]
        # main_author_paper = google_df['paper_title'][i]
        author_ls = author.split(" ")
        if author_ls[0].upper() == author_ls[0]:
            try:
                first_ini = author_ls[0][0]
                mid = author_ls[0][1:]
                last = author_ls[-1]
                author_ls[0] = first_ini
                author_ls[-1] = author_ls[-1]
                author_ls.append(last)
            except IndexError:
                pass
            
            
        author = git_df['Author'][i].lower()
        author_ls = author.split(" ")
        
            
        if len(author_ls) == 1:
            continue
        firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
        lastfive = author_ls[-1][0:5]
        name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
        try:
            name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
        except IndexError:
            continue
        name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
        try:
            name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
        except IndexError:
            continue
        name_pat5 = re.compile(f".*{lastfive}.*")
        name_pat6 = re.compile(f".*{firstfour}.*")
        if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
        # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
            git_df.at[i, 'gitsite_dblcheck'] = 1
            cntr += 1
            continue
        elif name_pat5.match(url) or name_pat6.match(url): # If only first or last name matches, do a deeper search into sourcecode   
            print('Checking sourcecode for ' + author)
            req = requests.get(url, 'html.parser',verify=False)
            source_code = re.split("<|>", req.text.lower())
            source_name_pat = re.compile(f".*{firstfour}[a-z]* {lastfive}.*")
            for j in source_code:
                if source_name_pat.match(j):
                    git_df.at[j, 'gitsite_dblcheck'] = 1 
                    print("Matched with: " + url)
                    print('-------------------')
                    break
    git_df['gitsite'] = google_df['gitsite_dblcheck']
    git_df.drop('gitsite_dblcheck', 'index', 1)
    df1 = df['gitsite' == 0]
    df1.append(google_df)
    return df1
    
                
                
def screen_wixsites(df):
    #First, only do for google sites
    wix_df = df[df['wixsite'] == 1]
    wix_df['wixsite_dblcheck'] = 0
    # browser = openbrowser()
    cntr = 0
    # wait = WebDriverWait(browser, 10)
    wix_df = wix_df.reset_index()
    for i in range(0, wix_df.shape[0]):
        author = wix_df['Author'][i]
        url = wix_df['Website'][i]
        # main_author = google_df['author'][i]
        # main_author_paper = google_df['paper_title'][i]
        author_ls = author.split(" ")
        if author_ls[0].upper() == author_ls[0]:
            try:
                first_ini = author_ls[0][0]
                mid = author_ls[0][1:]
                last = author_ls[-1]
                author_ls[0] = first_ini
                author_ls[-1] = author_ls[-1]
                author_ls.append(last)
            except IndexError:
                pass
            
            
        author = wix_df['Author'][i].lower()
        author_ls = author.split(" ")
        
            
        if len(author_ls) == 1:
            continue
        firstfour = author_ls[0][0:4] #Some ppl abbreviate names (alex = alexander, etc.)
        lastfive = author_ls[-1][0:5]
        name_pat1 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive}.*")
        try:
            name_pat2 = re.compile(f".*{author_ls[0][0]}[a-z]*[-|_]?{lastfive}.*")
        except IndexError:
            continue
        name_pat3 = re.compile(f".*{lastfive}[a-z]*[-|_]?{firstfour}.*")
        try:
            name_pat4 = re.compile(f".*{firstfour}[a-z]*[-|_]?{lastfive[0]}.*")
        except IndexError:
            continue
        name_pat5 = re.compile(f".*{lastfive}.*")
        name_pat6 = re.compile(f".*{firstfour}.*")
        if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url) or name_pat4.match(url):
        # if name_pat1.match(url) or name_pat2.match(url) or name_pat3.match(url):
            wix_df.at[i, 'wixsite_dblcheck'] = 1
            cntr += 1
            continue
        elif name_pat5.match(url) or name_pat6.match(url): # If only first or last name matches, do a deeper search into sourcecode   
            print('Checking sourcecode for ' + author)
            req = requests.get(url, 'html.parser',verify=False)
            source_code = re.split("<|>", req.text.lower())
            source_name_pat = re.compile(f".*{firstfour}[a-z]*[ ]?{lastfive}.*")
            for j in source_code:
                if source_name_pat.match(j):
                    wix_df.at[j, 'wixsite_dblcheck'] = 1 
                    print("Matched with: " + url)
                    print('-------------------')
                    break
                
    google_df['wixsite'] = google_df['wixsite_dblcheck']
    google_df.drop('wixsite_dblcheck', 'index', 1)
    df1 = df['wixsite' == 0]
    df1.append(google_df)
    return df1
                
            # try:
            #     main_author_ls = main_author.lower().split(" ")
            # except AttributeError:
            #     continue
            
            # browser.get(url)
            # time.sleep(2)
            # #list of elements with links to papers (possibly)
            # papers = []
            # try:
            #     papers1 = browser.find_elements_by_partial_link_text("Research")
            #     papers = papers + papers1
            # except NoSuchElementException:
            #     pass
            # try:
            #     papers2 = browser.find_elements_by_partial_link_text("RESEARCH")
            #     papers = papers + papers2
            # except NoSuchElementException:
            #     pass
            # try:
            #     papers3 = browser.find_elements_by_partial_link_text("Papers")
            #     papers = papers + papers3
            # except NoSuchElementException:
            #     pass
            # try:
            #     papers4 = browser.find_elements_by_partial_link_text("PAPERS")
            #     papers = papers + papers4
            # except NoSuchElementException:
            #     pass
            # try:
            #     papers5 = browser.find_elements_by_partial_link_text("Publications")
            #     papers = papers + papers5
            # except NoSuchElementException:
            #     pass
            # try:
            #     papers6 = browser.find_elements_by_partial_link_text("PUBLICATIONS")
            #     papers = papers + papers6
            # except NoSuchElementException:
            #     pass
            
            # if papers and isinstance(main_author, str):
            #     name_pat5 = re.compile(f".*{firstfour}[a-z]* {lastfive}[a-z]*.*")
                
            #     for i in papers:
            #         try:
            #             link = i.get_attribute('href')
            #         except AttributeError:
            #             continue
            #         break
                
            #     main_name_pat = re.compile(f"{main_author_ls[0]}[a-z]*? [a-z]*? {main_author_ls[-1]}[a-z]*?")
            #     try:
            #         req = requests.get(link, 'html.parser',verify=False)
            #         source_code = req.text.split(">").split("<")
            #         for i in source_code:
            #             if name_pat5.match(i) or main_name_pat.match(i):
            #                 print("Here")
            #                 for j in source_code:
            #                     fuzzy_paper_match = SequenceMatcher(None, main_author_paper.lower(), i.lower()).ratio()
            #                     if fuzzy_paper_match > 0.7:
            #                        google_df.at[i, 'googlesite_dblcheck'] = 1
            #                        print(author + " " + main_author_paper)
            #                        break
            #     except:
            #         continue
         
    # return google_df



    
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

# final_df.to_csv("D:\\git repo\\SerpAPI-Call-Clean\\data\\coauthors_website_test.csv")
