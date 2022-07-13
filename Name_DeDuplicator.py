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
from thefuzz import fuzz
#Misc
import time
import os
from random import sample, seed
import numpy as np
import unidecode

os.chdir("D:/git repo/Firewall-Project")

# papers = pd.read_excel('data/mains.xlsx')
# coauths_ls = []
# for index, row in tqdm(papers.iterrows()):
#     coauths = row['co-authors']
#     if isinstance(coauths, str):
#         temp =  re.split(",|&", coauths)
#     for i in temp:
#         coauths_ls.append(i.strip())
# coauths_ls = list(set(coauths_ls))

def sort_ls(ls):
    return sorted(ls, key = lambda x: name_type(x[0]))    

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



                
def same_mid(name1, name2):
    try:
        midini1 = name1.split(' ', 1)[-1].rsplit(' ',1)[0][0]
        midini2 = name2.split(' ', 1)[-1].rsplit(' ',1)[0][0]
    
        if midini1.lower() == midini2.lower():
            return True
    except IndexError:
        return

def fuzzy_fun(i, j, cutoff = 90):
    if fuzz.ratio(i.lower(), j.lower()) > cutoff:
        return True
    
def name_type(name):
    i_sp = name.split(" ")
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
    return i_type
    
pinyin_countries = ['Singapore', 'China', 'Province of China', 'Hong Kong', 'Taiwan', 'Malaysia']
from names_dataset import NameDataset
nd = NameDataset()

def final_fun(ls):
    def clean_name(name):
        name = unidecode.unidecode(name)
        name_ls1 = name.split(' ', 1)
        name_ls3 = name.split(' ')
        try:
            #PR Milgrom to P R Milgrom
            if len(name_ls1[0]) > 1 and name_ls1[0].upper() == name_ls1[0]:
                ret =  name_ls1[0][0] + ' ' + name_ls1[0][1:] + ' ' + name_ls1[-1]
            #Milgrom, Paul R. to Paul R. Milgrom
            elif ',' in name:
                name_ls2 = name.split(',')
                ret = name_ls2[-1].strip() + ' '  + name_ls2[0].strip()
            #Paul RObert Milgrom to Paul R milgrom. Gianmarco IP Ottaviano is left as is, since mid name is already abbreviated
            elif len(name_ls3) > 2:
                midname = name_ls3[1:-1]
                if len(midname[0]) > 1 and midname[0] == midname[0].upper():
                    return name
                ret = name_ls3[0] + ' '
                for mid in midname:
                    ret += mid[0]
                ret += ' ' + name_ls3[-1]
            else:
                ret = name
        except IndexError:
            return name.replace('Mr', '').replace('Ms', ''). replace('Mrs', '').strip()
        
        return ret.replace('Mr', '').replace('Ms', ''). replace('Mrs', '').strip()
        
    done = set()
    ret_ls = []
    for i in tqdm(ls, total = len(ls)):
        temp_ls = []
        name1 = i[0]
        if name1 in done:
            continue
        name1 = clean_name(name1)
        done.add(i[0])
        temp_ls.append(i[0])
        for j in ls:
            name2 = j[0]
            if name2 in done:
                continue
            name2 = clean_name(name2)
            if i[1] != j[1]:
                continue
            if j[1] == 1:
                cutoff = 100
            else:
                cutoff = 90
            if name_type(i[0]) in {1, 2, 3, 4} and name_type(name2) in {1, 2, 3, 4}:
                if not same_mid(name1, name2):
                    continue
            if fuzzy_fun(name1, name2, cutoff = cutoff):
                done.add(j[0])
                temp_ls.append(j[0])
        ret_ls.append(temp_ls)
    return ret_ls

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
    for i in ls:
        i_type = name_type(i)
        
        if ls.index(i) == 0:
            result = i
            res_type = i_type
            len_res = len(i)
            continue
        
        if res_type > i_type or (res_type == i_type and len_res < len(i)):
            result = i 
            res_type = i_type
            len_res = len(i)
    return result
        
def deduplicator(papers_df):
    def is_pinyin(name):
        try:
            ls = nd.search(name.split()[-1])['last_name']['country'].keys()
        except (IndexError, TypeError):
            return False
        c = 0
        for i in ls:
            if i in pinyin_countries:
                c += 1
                if c == 3:
                    return True
                    
        return False
    authors = []
    for index, row in tqdm(papers_df.iterrows()):
        coauths = row['coauthors_clean']
        author = row['author_google_name']
        if not isinstance(coauths, str):
            continue
        auths_ls = re.split(',|&|\sand', coauths)
        auths_ls.append(author)
        for auth in auths_ls:
            authors.append(auth.strip())
    
    authors = list(set(authors))
    
    authors_ls = []
    
    for i in authors:
        if name_type(i) == 7:
            continue
        if is_pinyin(i):
            authors_ls.append([i, 1])
        else:
            authors_ls.append([i, 0])
    for_dedupe_ls = sort_ls(authors_ls)
    final_ls1 = final_fun(for_dedupe_ls)
    
    ret_ls = []
    for i in final_ls1:
        key = extract_keywordname(i)
        ret_ls.append([key, unidecode.unidecode(key.split()[-1].lower())]+i)
        
    ret_df = pd.DataFrame(ret_ls)
    return ret_df
    

if __name__ == "__main__":
    papers_df = pd.read_excel(r"D:\git repo\Firewall-Project\Data\mains_v3.xlsx")
    pass

