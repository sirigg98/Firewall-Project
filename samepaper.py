# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 11:00:49 2022

@author: f0064wk
"""

from rapidfuzz import fuzz
import pandas as pd
from tqdm import tqdm
import random
import warnings
import re
import os
import numpy as np
import time
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
import sparse_dot_topn.sparse_dot_topn as ct
warnings.filterwarnings("ignore")
os.chdir('D:\git repo\Firewall-Project\data')

cols = ['main_paper', 'main_paper_id', 'main_paper_cites', 'group', 'ids']

authors = pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1')
papers_v2_full = pd.read_csv('final data/papers_v2_rank_ALL.csv', encoding = 'utf-8')

for index, row in papers_v2_full.iterrows():
    if isinstance(row['paper_google_id'],str) and row['paper_google_id'].startswith("'"):
        papers_v2_full.at[index, 'paper_google_id'] = row['paper_google_id'].replace("'", "")
        
papers_v2_full['author_id_paper_id'] = papers_v2_full['author_google_id'] + "_" + papers_v2_full['paper_google_id']

papers_v2_full = papers_v2_full.drop_duplicates('author_id_paper_id')






def correct_parse_errs(df):
    correct_id = list(pd.read_csv(r"papers_parsing_err1.csv", encoding = 'utf-8').iloc[:,0])
    correct_name = list(pd.read_csv(r"papers_parsing_err1.csv", encoding = 'utf-8').iloc[:,9])
    for index, row in tqdm(df.iterrows(), total = df.shape[0], desc = "Correcting parsing Errs"):
        author_id_paper_id = row['author_id_paper_id']
        if author_id_paper_id in correct_id:
            ind = correct_id.index(author_id_paper_id)
            new_name = correct_name[ind]
            if not isinstance(new_name, float):
                df.at[index, 'paper_title'] = new_name
    return df
    

def within_author(df, author_ids):
    within = pd.DataFrame(columns = ['main_paper', 'main_paper_id', 'main_paper_cites', 'group', 'ids'])
    uniques = []
    for author_id in tqdm(author_ids, total = len(author_ids), desc = 'Within Author matching'):    
        df_author = df[df['author_google_id'] == author_id].copy()
        ret_df = pd.DataFrame(columns = cols)
        for index, row in df_author.iterrows():
            paper_id = row['author_id_paper_id']
            paper = row['paper_title']
            cites = row['total_citation_count']
            uniques.append(paper_id)
            ls = [paper, paper_id, cites, [paper], [paper_id]]
            temp_row = pd.DataFrame([ls], columns = cols)
            max_cite = cites
            for index, row in df_author.iterrows():
                candidate_id = row['author_id_paper_id']
                if candidate_id == paper_id:
                    continue
                candidate_paper = row['paper_title']
                candidate_cites = row['total_citation_count']
                if (fuzz.ratio(paper.lower(), candidate_paper.lower()) > 85):
                    ls[3].append(candidate_paper)
                    ls[4].append(candidate_id)
                    uniques.append(candidate_id)
                    if max_cite < candidate_cites:
                        ls[0] = candidate_paper
                        ls[1] = candidate_id
                        ls[2] = candidate_cites
                        max_cite = candidate_cites
                    df_author.drop(index, inplace = True)
            temp_row = pd.DataFrame([ls], columns = cols)
            ret_df = ret_df.append(temp_row)
        within = within.append(ret_df)
    return within


def assign_final_mains(df):   
    final_papers = []
    final_paper_ids = []
    final_paper_cites = []
    rel_main_ids = [] 
    rel_mains = []
    rel_main_cites = []
    df_ret = df.copy()
    for index, row in tqdm(df_ret.iterrows(), total = df_ret.shape[0]):
        max_cites = row['main_paper_cites']
        main_papers = row['across_matches']
        if isinstance(main_papers, float):
            continue
        main_paper_id = row['main_paper_id']

        if main_paper_id in rel_main_ids:
            ind = rel_main_ids.index(main_paper_id)
            if final_paper_cites[ind] == max_cites:
                df_ret.at[index, 'main_paper'] = final_papers[ind]
                df_ret.at[index, 'main_paper_id'] = final_paper_ids[ind]   
                df_ret.at[index, 'main_paper_cites'] = final_paper_cites[ind]   
                continue

        # rel_mains.append(row['main_paper'])
        # rel_main_ids.append(main_paper_id)
        # rel_main_cites.append(max_cites)
        for paper in main_papers:
            rel_mains.append(paper[0])
            rel_main_ids.append(paper[1]) 
            rel_main_cites.append(paper[2])
            if paper[2] > max_cites:
                max_cites = paper[2]
                df_ret.at[index, 'main_paper'] = paper[0]
                df_ret.at[index, 'main_paper_id'] = paper[1]
                df_ret.at[index, 'main_paper_cites'] = paper[2]
                
        # for _ in range(len(main_papers) + 1):
        for _ in range(len(main_papers)):
            final_papers.append(row['main_paper'])
            final_paper_ids.append(row['main_paper_id'])
            final_paper_cites.append(row['main_paper_cites'])
    return df_ret


def across_authors(df):
#     pass
    
    def across_authors_mini(df, other_author_id, paper_name):
        df_sub = df[df['author_google_id'] == other_author_id]
        ls = []
        for index, row in df_sub.iterrows():
            candidate_paper = row['main_paper']
            candidate_paper_id = row['main_paper_id']
            candidate_cites = row['main_paper_cites']
            if isinstance(candidate_paper, float) or isinstance(paper_name, float):
                continue
            if (fuzz.ratio(str(paper_name).lower(), str(candidate_paper).lower()) > 80):
                ls.append([candidate_paper, candidate_paper_id, candidate_cites, row['group'], row['ids']])
        
        return ls

    
    
    df['across_matches'] = [[] for _ in range(df.shape[0])]
    for index, row in tqdm(df.iterrows(), total = df.shape[0], desc = ''):
        other_authors = row['top_50_authors']
        paper_name = row['main_paper']
        total_cites = row['main_paper_cites']
        
        if not other_authors:
            continue
        
        for other_author in other_authors:
            res = across_authors_mini(df, other_author[1], paper_name)
            if res:
                for i in res:
                    df.at[index, 'group'] = row['group'] + i[3]
                    df.at[index, 'ids'] = row['ids'] + i[4]
                    row['across_matches'].append([i[0], i[1], i[2]])
        
    df = assign_final_mains(df)
    return df
    
    

def ngrams(string, n=3):
    string = re.sub(r'[,-./]|\sBD',r'', string)
    ngrams = zip(*[string[i:] for i in range(n)])
    return [''.join(ngram) for ngram in ngrams]


def awesome_cossim_top(A, B, ntop, lower_bound=0):
    # force A and B as a CSR matrix.
    # If they have already been CSR, there is no overhead
    A = A.tocsr()
    B = B.tocsr()
    M, _ = A.shape
    _, N = B.shape
 
    idx_dtype = np.int32
 
    nnz_max = int(M*ntop)
 
    indptr = np.zeros(M+1, dtype=idx_dtype)
    indices = np.zeros(nnz_max, dtype=idx_dtype)
    data = np.zeros(nnz_max, dtype=A.dtype)
    ct.sparse_dot_topn(
            M, N, np.asarray(A.indptr, dtype=idx_dtype),
            np.asarray(A.indices, dtype=idx_dtype),
            A.data,
            np.asarray(B.indptr, dtype=idx_dtype),
            np.asarray(B.indices, dtype=idx_dtype),
            B.data,
            ntop,
            lower_bound,
            indptr, indices, data)
    return csr_matrix((data,indices,indptr),shape=(M,N))

def get_matches_df(sparse_matrix, name_vector):
    non_zeros = sparse_matrix.nonzero()
    
    sparserows = non_zeros[0]
    sparsecols = non_zeros[1]
    

    nr_matches = sparsecols.size
    
    left_side = np.empty([nr_matches], dtype=object)
    right_side = np.empty([nr_matches], dtype=object)
    similairity = np.zeros(nr_matches)
    
    for index in range(0, nr_matches):
        left_side[index] = name_vector[sparserows[index]]
        right_side[index] = name_vector[sparsecols[index]]
        similairity[index] = sparse_matrix.data[index]
    
    return pd.DataFrame({'left_side': left_side,
                          'right_side': right_side,
                           'similarity': similairity})



def multiple_top50_authors(df):
    author_names = list(pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1').iloc[:,1])
    author_ids = list(pd.read_csv(r"C:\Users\F0064WK\Downloads\profiles_final_with_count_and_scores_rev.csv", encoding ='latin-1').iloc[:,5])
    authors = []
    for i in range(len(author_names)):
        authors.append([author_names[i], author_ids[i]])
    
    
    author_regex = []
    for author in authors:
        try:
            author_ls = author[0].lower().replace("?", "").strip().split(" ")
        except AttributeError:
            continue
        if isinstance(author[0], float) or isinstance(author[1], float):
            continue
        author_regex.append([author[0], author[1], '(^|\s)' + author_ls[0][0] + '[^,]* [^,]*[\s]?' + author_ls[-1]])
    
    df['top_50_authors'] = [[] for _ in range(len(df))]
    for index, row in tqdm(df.iterrows(), total = df.shape[0], desc = 'Identifying papers with multiple Top50 authors'):       
        author = row['author']
        author_id = row['author_google_id']
        try:
            coauthors = row['co-authors'].replace(".", "").lower()
        except AttributeError:
            continue
        
        for i in author_regex:
            if author_id == i[1]:
                continue
            COAUTHOR_RE = re.compile(i[2])
            if COAUTHOR_RE.search(coauthors):
                row['top_50_authors'].append([i[0], i[1]])
    
    return df

            
def samepaperid2(df):
    
    def samepaperid_mini(df_mini, main_paper, main_paper_id, main_paper_cites):
        temp = df_mini[df_mini['main_paper'] == main_paper].copy()
        max_cite = 0
        ret_id = main_paper_id
        ret_name = main_paper
        ret_cites = main_paper_cites
        for index, row in temp.iterrows():
            
            if row['main_paper_cites'] > max_cite:
                max_cite = row['main_paper_cites']
                ret_id = row['main_paper_id']
                ret_name = row['main_paper']
                ret_cites = row['main_paper_cites']
        
        return [ret_id, ret_name, ret_cites]
    

    ret_df = df.copy()
    for index, row in tqdm(ret_df.iterrows(), total = ret_df.shape[0]):
        main_paper = row['main_paper']
        main_paper_id = row['main_paper_id']
        main_paper_cites = row['main_paper_cites']
        res = samepaperid_mini(ret_df, main_paper, main_paper_id, main_paper_cites)
        ret_df.at[index, 'main_paper_id'] = res[0]
        ret_df.at[index, 'main_paper'] = res[1]
        ret_df.at[index, 'main_paper_cites'] = res[2]
    return ret_df
        


def samepaperid1(df):
    
    def samepaperid_mini(df_mini, paper, cites):
        temp = df_mini.query('main_paper == @paper & main_paper_cites == @cites')
        ret_id = ''
        ret_name = ''
        ret_cites = ''
        for index, row in temp.iterrows():
            ret_id = row['main_paper_id']
            ret_name = row['main_paper']
            ret_cites = row['main_paper_cites']
            break
        
        return [ret_id, ret_name, ret_cites]
    

    ret_df = df.copy()
    ret_df['same_paper'] = ''
    ret_df['same_paper_id'] = ''
    ret_df['same_paper_cites'] = ''
    for index, row in tqdm(ret_df.iterrows(), total = ret_df.shape[0]):
        paper = row['main_paper']
        cites = row['main_paper_cites']
        res = samepaperid_mini(ret_df, paper, cites)
        ret_df.at[index, 'same_paper_id'] = res[0]
        ret_df.at[index, 'same_paper'] = res[1]
        ret_df.at[index, 'same_paper_cites'] = res[2]
    return ret_df 
        
def version1(papers_v2_full):
    t1 = time.time()
    
    correct_papers = correct_parse_errs(papers_v2_full)
    author_ids = list(set(correct_papers.iloc[:, 3]))
    # test = random.sample(authors, 10)
    


    within = within_author(correct_papers, author_ids)
    
    #Exploding list of matched_ids to rows
    rows = []
    _ = within.apply(lambda row: [rows.append([row['main_paper'], row['main_paper_id'], row['main_paper_cites'], row['group'], row['ids'], nn]) 
                                  for nn in row.ids], axis=1)
    
    within_new = pd.DataFrame(rows, columns = ['main_paper', 'main_paper_id', 'main_paper_cites', 'group', 'ids', 'matched_id']).drop_duplicates('matched_id')
    

    t2 = time.time()
    print("Time to run within author dedup:" + str(t2-t1))
    
    # new = multiple_top50_authors(correct_papers)
    # new.to_csv(r'w_top50_authors.csv', encoding = 'utf-8')
    t3 = time.time()
    # print("Time to identify papers with multiple top50 authors:" + str(t3-t2))
    
    new = pd.read_csv('w_top50_authors.csv', encoding = 'utf-8').drop_duplicates('author_id_paper_id')
    NAN_MATCH = r"[,]?[\s]?\['[^']+', nan\]"
    for index, row in new.iterrows():
        if isinstance(row['top_50_authors'], str):
            authors = row['top_50_authors']
            authors = re.sub(NAN_MATCH, "", authors)
            authors = authors.replace("[, ", "[")
            new.at[index, 'top_50_authors'] = literal_eval(authors)
    
    temp = pd.merge(new, within_new[['main_paper', 'main_paper_id', 'main_paper_cites', 'group', 'ids', 'matched_id']], right_on = 'matched_id', left_on = 'author_id_paper_id', how = 'left')
    print(len(temp['main_paper_id'].unique()))
    final = across_authors(temp)
    print(len(final['main_paper_id'].unique()))
    t4 = time.time()
    print("Time to run across author dedup:" + str(t4-t2))
    print("Total runtime:" + str(t4-t1))
    
    final_df = samepaperid1(final)
    return final_df
    






def version2(papers_v2_full):
    t1 = time.time()
    correct_papers = correct_parse_errs(papers_v2_full)
    author_ids = list(set(correct_papers.iloc[:, 3]))

    within = within_author(correct_papers, author_ids)
    
    #Exploding list of matched_ids to rows
    rows = []
    _ = within.apply(lambda row: [rows.append([row['main_paper'], row['main_paper_id'], row['main_paper_cites'], row['group'], row['ids'], nn]) 
                                  for nn in row.ids], axis=1)
    
    within_new = pd.DataFrame(rows, columns = ['main_paper', 'main_paper_id', 'main_paper_cites', 'group', 'ids', 'matched_id']).drop_duplicates('matched_id')
    
    
    final_within = pd.merge(correct_papers, within_new, left_on = 'author_id_paper_id', right_on = 'matched_id', how = 'left')
    t2 = time.time()
    
    print("Within Author Deduplication:" + str(t2-t1))
    paper_names = within['main_paper'].unique()
    cross = []
    names = list(within.iloc[:,0])
    ids = list(within.iloc[:,1])
    cites = list(within.iloc[:,2])
    for i in range(len(names)):
        cross.append([names[i], ids[i], cites[i]])    
        
    ids_unique_names = []
    cites_unique_names = []
    for i in tqdm(paper_names):
        for j in cross:
            if i == j[0]:
                ids_unique_names.append(j[1])
                cites_unique_names.append(j[2])
                break
            
    cross2 = []
    for i in range(len(paper_names)):
        cross2.append([paper_names[i], ids_unique_names[i], cites_unique_names[i]])    
        
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams)
    tf_idf_matrix = vectorizer.fit_transform(paper_names)
    matches = awesome_cossim_top(tf_idf_matrix, tf_idf_matrix.transpose(), 500, 0.80)

            
    
    match_df = get_matches_df(matches, np.array(ids_unique_names))
    
    match_df= match_df[match_df['left_side'] != match_df['right_side']]
    match_df = match_df.groupby('left_side')['right_side'].apply(list).reset_index().rename(columns = {"right_side": "across_matches"})
    
    for index, row in tqdm(match_df.iterrows()):
        main_papers = row['across_matches']
        ls = []
        for paper in main_papers:
            ind = ids_unique_names.index(paper)
            ls.append(cross2[ind])
        match_df.at[index, 'across_matches'] = ls

    
    correct_papers_new = pd.merge(final_within, match_df, left_on = "main_paper_id", right_on = "left_side", how = "left")
    for index, row in correct_papers_new.iterrows():
        if isinstance(row['across_matches'], list):        
            for paper in row['across_matches']:
                row['group'].append(paper[0])     
                row['ids'].append(paper[1])  
    print(len(correct_papers_new['main_paper_id'].unique()))
    correct_papers_new = assign_final_mains(correct_papers_new)
    print(len(correct_papers_new['main_paper_id'].unique()))
    
    final_df = samepaperid2(correct_papers_new)
    # print("At-scale Deduplication:" + str(t3-t2))
    # print("Total time:" + str(t3-t1))
    return final_df
        
        

        
            