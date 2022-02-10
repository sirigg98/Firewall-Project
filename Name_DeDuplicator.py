# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 15:36:27 2021

@author: F0064WK
"""
#Dataframe stuff:
import csv
import pandas as pd
import re
import os
from tqdm import tqdm
#Similarity ratio for author names
from difflib import SequenceMatcher 
from whoswho import who
#Match version of chrome driver and chrome
from webdriver_manager.chrome import ChromeDriverManager
#Selenium stuff
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import _find_element
from selenium.common.exceptions import NoSuchElementException
#HTML Parser
from bs4 import BeautifulSoup
#For threads:
import concurrent.futures 
from concurrent.futures import wait, ALL_COMPLETED
#Misc
import time
import os
from random import sample, seed
import numpy as np

os.chdir("D:/git repo/Firewall-Project")

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

def extract_allauthors(df):
    #Splitting by commas
    # new = df['co-authors'].str.split(", ",expand = True)
    # return new
    ls = []
    print("Extracting all coauthor names as a from the full dataset...")
    time.sleep(1)
    #append all columns into one list
    for i in tqdm(range(df.shape[1])):
        for item in list(df.iloc[:, i]):
            ls.append(item)
    unique_ls = []
    #scan for duplicates
    for x in ls:
        if x not in unique_ls:
            unique_ls.append(x)
    return unique_ls

def case_sim(ls):
    #Removing names that are only different by case. Returns a list wiht only lower case names.
    
    ls2 = [x.lower() for x in ls]
    set1 = set(ls2)
    return list(set1) 

# just checks if the last name first name is a match
def who_ratio(author1, author2):
    res1 = who.ratio(author1, author2)
    
    author1_ls = author1.split(" ")
    if len(author1_ls) == 2:
        author1 = author1_ls[-1] + " " + author1_ls[0]

    res2 = who.ratio(author1, author2)
    return np.maximum(res1, res2)


# def similaritymatching_text(author1, author2):
#     similarity_ratio = 0
#     MATCH = False
#     PARTIAL_MATCH = False
    
#     #Count number of spaces
#     n1 = author1.count(" ")
#     n2 = author2.count(" ")
    
    
#     author1_ls = author1.split()
#     # check author name match
#     author2_ls = author2.split()
    
#     #No match if middle initials differ.
#     if n1 > 1 and n2 > 1:
#         author1_midd = author1.split(" ", 1)[1].rsplit(" ", 1)[0]
#         author2_midd = author2.split(" ", 1)[1].rsplit(" ", 1)[0]
#         if author1_midd.lower() != author2_midd.lower():
#             return MATCH, PARTIAL_MATCH, 0
    
#     if author1_midd.lower() and author2_midd.lower() == 2:
#         if author1_ls[1] + " " + author1_ls[0] == author2_ls[1] + " " + author2_ls[0]:
#             MATCH = True
#             return MATCH, PARTIAL_MATCH, 1
#     else:
#         if str(author1_ls[1] + " " + author1_ls[0] + " " + author1_midd).lower() == (author2_ls[1] + " " + author2_ls[0] + author2_midd).lower():
#             if len(author1_midd) == 1:
#                 author2_midd = author2_midd[0]
#             if len(author2_midd) == 1:
#                 author1_midd = author1_midd[0]
            
#             MATCH = True
#             return MATCH, PARTIAL_MATCH, 1
            
    
#     if len(author1_ls[0]) == 1 or len(author2_ls[0]) == 1:
#         if len(author1_ls[0]) == 1:
#              author2 = author2_ls[0][0]
#              for i in range(1, n2+1):
#                  author2 = author2 + " " + author2_ls[i]
#         else:
#              author1_ls[0] = author1_ls[0][0]
#              for i in range(n1+1):
#                  author1 = author1 + " " + author1_ls[i]
#     #Need perfect match if one is first initial, last name format    
#         if (similarity_ratio := SequenceMatcher(None, author1.lower(), author2.lower()).ratio()) == 1:
#             MATCH = True
#         elif similarity_ratio > 0.90:
#             PARTIAL_MATCH = True
        
#         print(author1 + ", " + author2 + " " + str(similarity_ratio))
#         return MATCH, PARTIAL_MATCH, similarity_ratio
        
             
#     similarity_ratio = SequenceMatcher(None, author1.lower(), author2.lower()).ratio()
#     #On average accounts for 1 spelling mistakes if strings are of equal size. Average length for names in df is ~14
#     if similarity_ratio > 0.90:
#         MATCH = True 
#     #Upto 2 on average for partial match. Maybe better to revisit these guys.
#     elif similarity_ratio > 0.85:
#         PARTIAL_MATCH = True
#     print(author1 + ", " + author2 + " " + str(similarity_ratio))
#     return MATCH, PARTIAL_MATCH, similarity_ratio

#Whoswho module already deals with most of what I am coding for above (cases, middle initials, etc)
def similaritymatching_text_who(author1, author2):
    similarity_ratio = 0
    MATCH = False
    PARTIAL_MATCH = False
    
    WHO = False
    
    
    author1_ls = author1.split()
    author2_ls = author2.split()
    
    #If both not first ini, last name format, check who ratio
    if len(author1_ls[0]) > 1 and len(author2_ls[0]) > 1:
        if len(author1_ls) != len(author2_ls):
            similarity_ratio = SequenceMatcher(None, author1, author2).ratio()*100
        else:
            similarity_ratio = who_ratio(author1, author2)
            WHO = True
        
    #If one first ini, last name, then test only if both names have a middle initial. Otherwise run the sequence matcher ratio
    elif len(author1_ls[0]) > 1 or len(author2_ls[0]) > 1:
        if (len(author1_ls) > 1 and len(author2_ls) > 2):
            similarity_ratio = who_ratio(author1, author2)
            WHO = True
        else:
            similarity_ratio = SequenceMatcher(None, author1, author2).ratio()*100
    
    # if both first ini, then who ratio if both have the same number of "words" in name (spaces, too i guess).
    elif len(author1_ls[0]) == 1 or len(author2_ls[0]) == 1:
        if (len(author1_ls) == len(author2_ls)):
            similarity_ratio = who_ratio(author1, author2)
            WHO = True
        else:
            similarity_ratio = SequenceMatcher(None, author1, author2).ratio()*100
        
    if WHO:
        if similarity_ratio  == 100:
            MATCH = True
        elif similarity_ratio > 96:
            PARTIAL_MATCH = True
            
    else:
        if similarity_ratio > 93:
            MATCH = True
        elif similarity_ratio > 88:
            PARTIAL_MATCH = True
    
    return MATCH, PARTIAL_MATCH, similarity_ratio

# This Takes too long. Maybe thread?
def similarity_elementslist(authors):
    final_ls = []
    final_ratio = []
    n_ls = []
    comp_matches = []
    authors_temporary = authors
    time.sleep(1)
    for i in tqdm(authors_temporary, desc = "Grouping names based on similarity..."):
        if i in comp_matches:
            continue
        n = 0
        ls_temp = [(i, 100)]
        for j in range(authors.index(i), len(authors)-1):
            if i == authors[j]:  
                continue
            n += 1
            results = similaritymatching_text_who(str(i), str(authors[j]))
            if results[0]:
                res = authors[j], results[2]
                ls_temp.append(res)
                comp_matches.append(authors[j]) #Add to list of complete matches, not returned by this function anymore though.
                
            elif results[1]:
                res = authors[j], results[2]
                ls_temp.append(res)
            else: 
                continue
        final_ls.append(ls_temp)
        n_ls.append(n)
    return final_ls # Returns a list of tuples (name, ratio). Ratio might come in handy later

# df = pd.read_csv(r"C:\Users\F0064WK\Downloads\fullsample (2).csv", encoding="utf-8")


# Main search word is the first name in list,
# but if first name is in initial, name format, then one that is firstname lastname, 
# or if already in firstname lastname, but there is another name wiht middle initial, then use that
# Only names that fit optimal is in new list
def extract_keywordname(ls):

    if isinstance(ls[0], float):
        return
    if len(ls) == 1:
        result = ls[0]
        return result
    #Legend:
        #1: F M L; 2:F Mi L; 3:Fi M L; 4: Fi Mi L; 5: F L; 6: Fi L; 7: else
    for i in ls:
        if len(ls) > 1:
            i_sp = i.split(" ")
        if len(i_sp) > 2:
            if len(i_sp[0]) > 1:
                if len(i_sp[1]) > 1:
                    i_type = 1
                else:
                    i_type = 2
            else:
                if len(i_sp[1]) > 1:
                    i_type = 3
                else:
                    i_type = 4
        elif len(i_sp) == 2:
            if len(i_sp[0]) > 1:
                i_type = 5
            else:
                i_type = 6
        else:
            i_type = 7
        
        if ls.index(i) == 0:
            result = i
            res_type = i_type
            continue
        
        if res_type > i_type:
            result = i 
            res_type = i_type
    return result
        

##Scrape author institutions from repec. Note: Doesn't work well esp. when coauthor names start with first initial.
# def author_institution(browser, author):
#     ini = False  # Caveat for when you use institution for google search
#     mid = False
#     reg = False # Registered on Repec?
#     author_ls = author.split()
#     if len(author_ls[0]) == 1:
#         ini = True
        
#     if len(author_ls) > 2:
#         mid = True
    
#     initial = author_ls[-1][0].lower()
#     if not browser.current_url.startswith(f"https://ideas.repec.org/i/e{initial}.html"):
#         browser.get(f"https://ideas.repec.org/i/e{initial}.html")
    
#     if len(author_ls) == 2:
#         name_key = author_ls[-1] + ", " + author_ls[0]
#     elif len(author_ls) > 2:
#         name_key = author_ls[-1] + ", " + author_ls[0] + " " + author_ls[1][0] + "."
#     else: 
#         return [author, " ", reg]
    
#     try:
#         element = browser.find_element_by_partial_link_text(name_key)
#     except NoSuchElementException as NA:
#         return [author, " ", reg]
    
#     element.click()
    
#     # if browser.current_url.startswith(f"https://ideas.repec.org/i/e{initial}.html"):
#     #     select = Select(browser.find_element_by_css_selector("#wf-select"))
#     #     select.select_by_value("000F") #Select Author from drop down menu
    
#     # search = browser.find_element_by_css_selector("#content-block > div > form > div:nth-child(4) > div.col-12.col-md > input")
#     # search.send_keys(author)
    
#     # search.send_keys(Keys.RETURN)
    
#     # NORESULTS_REPEC = re.compile(".*Found 0 result for .*")
    
#     # search_desc = browser.find_element_by_css_selector("#content-block > p").text.strip()
#     # #If no results, return empty for affiliation
#     # if NORESULTS_REPEC.match(search_desc):
#     #     return author, ""
    
#     # #Only one result    
#     # elif (element := browser.find_element_by_css_selector("#content-block > ol:nth-child(4) > li > a")):
#     #     element.click()
    
#     # #Multiple cases
#     # else:
#     #     element = browser.find_elements_by_css_selector("#content-block > ol:nth-child(4) > li")
#     #     author_lastnames = []
#     #     author_firstnames = []
#     #     for i in range(len(element)):
#     #         name = browser.find_elements_by_css_selector(f"#content-block > ol:nth-child(4) > li:nth-child({i}) > a").text.strip()
#     #         name.split(", ")
#     #         author_lastnames.append(name[0])
#     #         author_firstnames.append(name[1])
        
#     #     ratios = []
#     #     for i in range(len(element)):
#     #         link_author = author_firstnames[i] + " " + author_lastnames[i]
#     #         ratio = similaritymatching_text(link_author, author)[2]
#     #         ratios.append(ratio)
#     #     if (max_val:= max(ratios)) < 0.85:
#     #         return author, ""
#     #     else:
#     #         i = ratios.index(max_val)
#     #         browser.find_elements_by_css_selector(f"#content-block > ol:nth-child(4) > li:nth-child({i}) > a").click()
#     try:
#         browser.find_element_by_css_selector("#affiliation-tab").click()
#     except NoSuchElementException:
#         return [author, " ", reg]  
    
#     try:
#         affiliation = browser.find_element_by_css_selector("#affiliation > h3").get_attribute("innerHTML").replace("<br>", ", ").replace("\n", " ")
#     except NoSuchElementException:
#         affiliation = browser.find_element_by_css_selector("#myTabContent > h3").get_attribute("innerHTML").replace("<br>", ", ")
        
#     reg = True
#     return [author, affiliation, reg]

# #Implementing threads for author institution lookup
# def author_institution_threads(browser, ls, num_threads = 5):
#     res = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers = num_threads) as executor:
#         results = [executor.submit(author_institution, browser, i) for i in ls]
#         concurrent.futures.wait(results, return_when=ALL_COMPLETED)
#         for f in concurrent.futures.as_completed(results):
#             res.append(f.result())
#     return res

def thread_fun_clean(ls, i):
    p = []
    print(i)
    for j in range(i + 1, len(ls)):
        if set(ls[j]).issubset(set(ls[i])):
            p.append(j)
    return p
        
    
def ini_cleaner(authors_df):
    authors_ls = []
    #Takes df, groups rows into lists and stores them in lists.
    for i in range(authors_df.shape[0]):
        ls = list(authors_df.iloc[i])
        del ls[0]
        authors_ls.append(ls)
    # Within each sublist, drops the nans
    authors_clean = []
    for i in authors_ls:
        print(i)
        temp = []
        for j in i:
            if str(j) != 'nan':
                temp.append(j)
        authors_clean.append(temp)
        
    temp = authors_clean
    # If one sublist is a subset of another sublist, drops the sublist, returns final list. Threads used. 
    res = []
    with concurrent.futures.ProcessPoolExecutor(max_workers = 15) as executor:
        results = [executor.submit(thread_fun_clean, temp, i) for i in range(len(temp))]
        concurrent.futures.wait(results, return_when=ALL_COMPLETED)
        for f in concurrent.futures.as_completed(results):
            res = res + f.result()
            
    res = sorted(list(set(res)), reverse = True)
    for i in res:
        del temp[i]
    
    return temp



if __name__ == "__main__":
    
    # authors = pd.read_csv(r"data\authorsonly.csv", low_memory = False).iloc[:,0]
    # authors_ls = list(authors)

    # #Grouping coauthor names. First element in sublist is the reference. elements are tuples with (name, similarity ratio)
    # results = similarity_elementslist(authors_ls)
    # # Filtering for elements with mathces, i.e. grouped coauthors
    # dup_authors = [x for x in results if len(x) > 1]
    
    # #storing this list as a df as it takes too long to run everytime I run the script
    # who_dedup_df = pd.DataFrame(results)
    # who_dedup_df.to_csv("data/names_who.csv")
    
    
    authors_df = pd.read_csv("data/names_who.csv", low_memory=False)
    authors_ls = []
    #Takes df, groups rows into lists and stores them in lists.
    for i in tqdm(range(authors_df.shape[0]), desc = "Converting dataframe to list form..."):
        ls = list(authors_df.iloc[i])
        del ls[0]
        authors_ls.append(ls)
        
    # Within each sublist, drops the nan
    authors_clean = []
    for i in tqdm(authors_ls, desc = "Dropping NA list elements..."):
        temp = []
        for j in i:
            if str(j) != 'nan':
                temp.append(j)
        authors_clean.append(temp)
        
    temp = authors_clean
    

    print("Removing Ratios...")
    #extracting only names, removing ratios
    for i in temp:
        ls_temp = []
        for j in i:
            ls_temp.append(j.split("'")[1])
        i = ls_temp
        
    l_group = [x for x in temp if len(x) > 1]
    l_solo = [x for x in temp if len(x) == 1]
    
    names_solo = []
    for x in l_solo:
        x[0] = x[0].replace('"', "'")
        sp = x[0].split("'")
        if len(sp) > 3:
            names_solo.append([str(sp[1] + sp[2])])
            continue
        names_solo.append([sp[1]])
    
    
    names_group = []
    for x in l_group:
        temp = []
        for y in x:
            y = y.replace('"', "'")
            sp = y.split("'")
            if len(sp) > 3:
                temp.append(str(sp[1] + sp[2]))
                continue
            temp.append(sp[1])
        names_group.append(temp)
        
    
    #Removing matched names for names_solo
    for x in tqdm(names_solo, desc = "Removing singletons that appear in groups"):
        for y in names_group:
            if x[0] in y:
                names_solo.remove(x)
                break
            
    names = names_solo + names_group
    
    #Currently, if a name is matched, it will be used as a reference name. If there is an intersection between two groups, it appends one to the other. Brainstorm ways to improve this.
    names_dedup_who = []
    dup = []
    for x in tqdm(names, desc = "Taking unions of lists with intersections..."):
        for i in range(names.index(x) + 1, len(names)):
            if set(x).intersection(set(names[i])):
                x = list(set(x).union(set(names[i])))
                dup.append(names[i])
        names_dedup_who.append(x)
    
    for i in dup:
        if i in names_dedup_who:
            names_dedup_who.remove(i)
                
    key = []
    for i in tqdm(names, desc = "Extracting keywords from coauthor groups..."):
        key.append(extract_keywordname(i))
    
