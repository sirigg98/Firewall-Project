# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:46:05 2021

@author: f0064wk
"""
from serpapi import GoogleSearch
import json
import pandas as pd
#Similarity ratio for author names
from difflib import SequenceMatcher 
import os 
from os.path import exists
import re
os.chdir('D:\git repo\SerpAPI-Call-Clean\data')
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support.expected_conditions import _find_element
import unidecode



GOOGLESITE_MATCH = re.compile('^http[s]?:\/\/sites\.google\.com\/')
GITSITE_MATCH1 = re.compile('^.*\.github\.io\/$')
GITSITE_MATCH2 = re.compile('^.*\.github\.io\/.*')
WEEBLYSITE_MATCH = re.compile('^http[s]?:\/\/.*\.weebly\.com\/$')
WORDPRESSSITE_MATCH = re.compile('^http[s]?:\/\/.*\.wordpress\.com.*')
WIXSITE_MATCH1 = re.compile('^http[s]?:\/\/.*\.wixsite\.com.*')
WIXSITE_MATCH2 = re.compile('^http[s]?:\/\/.*\.wix\.com.*')

ALTNAME_FORMAT1 = re.compile("^[^0-9]+, [^0-9]+")

ALTNAME_FORMAT2 = re.compile("^[^0-9]+. [^0-9]+")

def api_call(author):
    params = {
      "q": f"{author} Economics Personal Website",
      "hl": "en",
      "gl": "us",
      "google_domain": "google.com",
      "api_key": "dc7ce51ae4f479edef778bd64922f265af96d36d1d5426a67290766c4f882378"
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    return results

def name_reorg(name):
    if ALTNAME_FORMAT1.match(name):
        name_ls = name.split(",")
        name = name_ls[-1] + name_ls[0]
    if ALTNAME_FORMAT2.match(name):
        name_ls = name.split(".")
        name = name_ls[-1] 
    return name
    

def pdf(link): 
    if "pdf" in link:
        return True
    
def no_research(link):
    if "yahoo" in link or "wikipedia" in link or "cnn" in link or "bbc" in link or "nytimes" in link or "nypost" in link or "issuu" in link or "voxeu" in link or "dailycal" in link or "voxdev" in link or "theguardian" in link or "magazine" in link or "jstor" in link or "washingtonpost" in link:
        return True
    if "phd" in link or "grad" in link or  "papers" in link or "alumni" in link or "blog" in link or "reddit" in link or "linkedin" in link or "twitter" in link or "facebook" in link:
        return True
    if "article" in link or "igc" in link or "econometricsociety" in link or "repec" in link or "nobelprize" in link or "amazon" in link or "yumpu" in link or "equitablegrowth" in link:
        return True
    if "elsevier" in link or "investopedia" in link or "typepad" in link or "bloomberg" in link or "interview" in link:
        return True
    if "scholar.google.com" in link or "researchgate" in link or "hetwebsite" in link or "studylib" in link:
        return True
    if "opportunityinsights" in link or "thedecisionlab" in link or "fed" in link:
        return True
    if "curriculum" in link or "vitae" in link or "fed" in link or "chegg" in link or "ask.fm" in link:
        return True

def download_search_results(authors):   
    counter = 0
    for author in authors:
        if not exists(f"Google Searches\Coauthors\{author}.json"):
            results = api_call(author)
            if no_result(results):
                counter += 1
            
            if authors.index(author)%100 == 0 or authors.index(author) == len(authors)-1:
                print("# of author searches completed:" + str(authors.index(author) + 1))
                prop_results = (len(authors) - counter)/len(authors)
                print(f"Prop of authors with some google search result {prop_results}")  
                print("------------------------------------------------------------")
            try:
                with open(f"Google Searches/Coauthors/{author}.json", "w") as outfile:
                    json.dump(results, outfile)
            except:
                continue #Some issue with special characters (like \\) can lead to a filenotfounderror
                

            
def openbrowser():
    global browser

    capabilities = dict(DesiredCapabilities.CHROME)
    capabilities['loggingPrefs'] = { 'browser':'ALL' }

    options = webdriver.ChromeOptions()
    for arg in open('D:/git repo/scholar-scrape/config/account.txt').readlines():
        options.add_argument(arg)

    browser = webdriver.Chrome(desired_capabilities=capabilities, options=options)
    return browser



def similaritymatching_text(author, link, link_text):
    matched = re.search('Professor (.*?) (.*?) - ', link_text, re.IGNORECASE)
    if not matched:
        matched = re.search('^(.*?) (.*?) - ', link_text, re.IGNORECASE)
        if not matched:
            return 

    author_firstname = author.split()[0]
    # check author name match
    linkauthor_firstname = matched.group(1)
    if len(author_firstname) == 1:
         linkauthor_firstname = linkauthor_firstname[0]
    
    link_author = f'{linkauthor_firstname} {matched.group(2)}'
    similarity_ratio = SequenceMatcher(None, author.lower(), link_author.lower()).ratio()

    if similarity_ratio < 0.75:
        # put first name last and try matching author name again
        link_author = f'{matched.group(2)} {matched.group(1)}'
        similarity_ratio = SequenceMatcher(None, author.lower(), link_author.lower()).ratio()
        if similarity_ratio < 0.75:
            return 
    else:
        return link

#Google Site match
def googlesite_match(author, title, link, link_text):
    authorname = author.split(",")[0].lower()
    author_ls = authorname.split()
    firstname = authorname.split()[0]
    lastname = authorname.split()[-1]
    GOOGLESITE_TITLE_NAME1 = re.compile(f"^{firstname} [a-z]* {lastname} - google sites$")
    GOOGLESITE_TITLE_NAME2 = re.compile(f"^{firstname}[a-z]*{lastname} - google sites$")
    
    firstini = authorname.split()[0][0]
    lastini = authorname.split()[-1][0]
    
    GOOGLESITE_TITLE_INI = re.compile(f"^{firstini}[^0-9]+ {lastini}[^0-9]+ - google sites$")
    
    if GOOGLESITE_MATCH.match(link):
        if not GOOGLESITE_TITLE_NAME1.match(title.lower()) and GOOGLESITE_TITLE_NAME2.match(title.lower()):     
            if not GOOGLESITE_TITLE_INI.match(title.lower()) and title != "Home - Google Sites":
                if len(author_ls) > 2:
                    midini = author_ls[1][0]
                    GOOGLESITE_TITLE_MID_INI = re.compile(f"^{firstini}[^0-9]+ {midini}[^0-9]* {lastini}[^0-9]+ - google sites$")
                    if not GOOGLESITE_TITLE_MID_INI.match(title.lower()):
                        return
                return
            
        return True

#Match for personal website (i.e. {firstname}{lastname}.com)
def personalsite_match(author, link, link_text):
    author_firstname = author.lower().split()[0]
    author_lastname = author.lower().split()[-1]
    authorname = author.split(",")[0].lower()
    firstini = authorname.split()[0][0]
    lastini = authorname.split()[-1][0]
    PERSONALSITE1_MATCH = re.compile(f'^http[s]?:\/\/(www.)?{author_firstname}.*{author_lastname}\..*')
    PERSONALSITE2_MATCH = re.compile(f'^http[s]?:\/\/(www.)?[a-z]*.*{author_firstname[0]}[a-z]*{author_lastname}\..*')
    PERSONALSITE3_MATCH = re.compile(f'^http[s]?:\/\/(www.)?{author_lastname}.*{author_firstname}\..*')
    PERSONALSITE4_MATCH = re.compile(f'http[s]?:\/\/(www.)?{author_lastname}.*')
    PERSONALSITE5_MATCH = re.compile(f'^http[s]?:\/\/(www.])?{firstini}[a-z]+.*{lastini}[a-z]*\..*')
    if no_research(link):
        return
    if ".edu" in link:
        return
    if pdf(link):
        return
    if "nber" in link:
        return
    if PERSONALSITE1_MATCH.match(link) or PERSONALSITE2_MATCH.match(link) or PERSONALSITE3_MATCH.match(link) or PERSONALSITE4_MATCH.match(link) or PERSONALSITE5_MATCH.match(link):
        return True
    if "personal" in link: 
        return True
    return 
    
def gitsite_match(author, title, link, link_text):
    if no_research(link):
        return
    author_ls = author.lower().split()
    if pdf(link):
        return 
    if GITSITE_MATCH1.match(link) or GITSITE_MATCH2.match(link):
        if author_ls[0] in title.lower() and author_ls[-1] in title.lower():
            return True
    
    
def weeblysite_match(author, title, link, link_text):
    if no_research(link):
        return
    if pdf(link):
        return
    if WEEBLYSITE_MATCH.match(link) and not pdf(link):
        author_ls = author.split()
        own = False
        if author in title:
            return True
        for i in author_ls:
            if i in link:
                own = True
        if own:
          return True  
      
        
def wordpresssite_match(author, link, link_text):
    if no_research(link):
        return
    if pdf(link):
        return
    author_ls = author.split()
    for x in author_ls:
        if f"{x}" in link and "wordpress" in link and not pdf(link):
            return True


def wixsite_match(author, link, link_text):
    if no_research(link):
        return
    if pdf(link):
        return
    if WIXSITE_MATCH1.match(link) or WIXSITE_MATCH2.match(link):
        return True
    
    
def academicsite_match(author, link, link_text):
    if no_research(link):
        return
    author_ls = author.split()
    firstthree = ""
    for i in range(3):
        try:
            firstthree = firstthree + author_ls[0][i]
        except IndexError:
            firstthree = author_ls[-1]
    lastfive = ""
    for i in range(5):
        try:
            lastfive = lastfive + author_ls[-1][i]
        except IndexError:
            lastfive = author_ls[-1]
    ACADEMICSITE1_MATCH = re.compile('^.*(www\.)?[a-z]*[.]?[a-z]*\.edu.*$')
    ACADEMICSITE2_MATCH = re.compile('^.*.uk\/.*$')
    ACADEMICSITE3_MATCH = re.compile('^.*de\/.*$') #Sites with foreign domains are academic websites
    ACADEMICSITE4_MATCH = re.compile('^.*ca\/.*$')
    ACADEMICSITE5_MATCH = re.compile('^.*it\/.*$')
    ACADEMICSITE6_MATCH = re.compile('^.*fr\/.*$')
    ACADEMICSITE7_MATCH = re.compile('^.*eu\/.*$')
    ACADEMICSITE8_MATCH = re.compile('^.*ch\/.*$')
    MITSITEALT_MATCH = re.compile('.*mit\.edu.*')
    GOOGLESCHOLAR_MATCH = re.compile('https:\/\/scholar.google.com\/.*$')
    if GOOGLESCHOLAR_MATCH.match(link) or pdf(link):
        return
    elif MITSITEALT_MATCH.match(link) or ACADEMICSITE1_MATCH.match(link) or ACADEMICSITE2_MATCH.match(link) or ACADEMICSITE3_MATCH.match(link) or ACADEMICSITE4_MATCH.match(link) or ACADEMICSITE5_MATCH.match(link) or ACADEMICSITE6_MATCH.match(link) or ACADEMICSITE7_MATCH.match(link) or ACADEMICSITE8_MATCH.match(link):
        return True
    

    
def othersite_match(author, link, link_text):
    ACADEMICSITE2_MATCH = re.compile('^.*[www\.]?[a-z]*\.[a-z]*\.[a-z]*\.[a-z]{3}.*$')
    author_lastname = author.lower().split()[-1]
    OTHERSITE2_MATCH = re.compile(f'.*(www\.)?.*{author_lastname}..*')
    GOOGLESCHOLAR_MATCH = re.compile('https:\/\/scholar.google.com\/.*$')
    
    if GOOGLESCHOLAR_MATCH.match(link) or pdf(link):
        return
    
    elif no_research(link):
        return
    
    elif ACADEMICSITE2_MATCH.match(link):
        return True
    
    elif OTHERSITE2_MATCH.match(link):
        return True
           
def no_result(result):
    try:
        search_results = result['organic_results']
        if "Google hasn't returned any results for this query" in search_results[0]:
            return True
    except KeyError:
        pass
    
    
    return

def website_search(author = "Kripa Freitas"):
    googlesite = []
    other = []
    pers = []
    git = []
    weebly = []
    wix = []
    wp = []
    aca = []
    # try:
    with open(f"Google Searches\Authors\{author}.json", "r") as jsonfile:
        search = json.load(jsonfile)
    # except FileNotFoundError:
    #     print("Redownloading: " + author)
    #     download_search_results([author])
    #     return
    try:
        search_results = search['organic_results']
    except KeyError:
        return
    for i in search_results:
        try:
            link = i['link']
            link_text = i['snippet']
            title = i['title']
        except KeyError:
            continue
        if len(googlesite) == 0:
            if googlesite_match(author, title, link, link_text):
                googlesite.append(link)
                continue
        
        if academicsite_match(author, link, link_text):
            aca.append(link)
            continue
        
        if len(git) == 0:
            if gitsite_match(author, title,  link, link_text):
                git.append(link)
                continue
        
        if weeblysite_match(author, title, link, link_text):
            weebly.append(link)
            continue
        
        if wixsite_match(author, link, link_text):
            wix.append(link)
            continue
        
        # Some wordpress domains dont follow the regular conventions
        if wordpresssite_match(author, link, link_text):
            wp.append(link)
            continue
        if len(pers) == 0:
            if personalsite_match(author, link, link_text):
                pers.append(link)
                continue
        
        if othersite_match(author, link, link_text):
            other.append(link)
            continue
        
    return [author, googlesite, len(googlesite), git, len(git), weebly, len(weebly), wix, len(wix), wp, len(wp), pers, len(pers), aca, len(aca), other, len(other)]

# download_search_results(["Yuting Huang"])
def replace_special_chars(string):
    match_dict = {"(": "", 
                  ")": "",
                  "$": "",
                  "!":"",
                  "?": "",
                  '"': "",
                  "/": "",
                  "*": "",
                  ">": "",
                  "<": "",
                  "1": "",
                  "2": "",
                  "3": "",
                  "4": "",
                  "5": "",
                  "6": "",
                  "7": "",
                  "8": "",
                  "9": ""}
    for i, j in match_dict.items():
        string = string.replace(i, j)
    return string

def txt_to_ls(filename):
    with open(f"{filename}", "r") as txtfile:
        lines = txtfile.readlines()
        authors = [replace_special_chars(unidecode.unidecode(line.rstrip())) for line in lines]
    return authors

# test_ls = [str(x[0].encode("utf-8")).replace("b'", "").replace("'", "").replace("\\", "") for x in test_coauth]

authors = txt_to_ls("scholars_top50.txt")
# download_search_results(key)

website_ls = []
cntr = 0
cntr_none = 0
for i in authors:
    print(authors.index(i))
    try:
        website_ls.append(website_search(i))
    except:
        cntr_none += 1
        continue
    cntr += 1
    
print(cntr, cntr_none)


########### Number of coauthors already downloaded
# from os.path import exists

# cntr = 0
# for i in key:
#     if exists(f"Google Searches\Coauthors\{i}.json"):
#         cntr += 1
# print(cntr)
    
    
    
    
    
    
    
    
    
    