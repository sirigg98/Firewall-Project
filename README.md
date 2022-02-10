# Firewall-Project
- Name_DeDuplicator.py: Groups similar coauthor names.
- SerpAPI-Call.py: API call to retrive search results for "{Name} Economics Website". Does initial classifying of search results by domain.
- Data-Clean.py: Improves classificiation of websites by adding source code checks for company watermarks and copyright notices. Also improves on the regex used for classification in initial screen.
- Scrape-Citation-Details.py: Scrapes google scholar citation graphs by year for each author_id_paper_id. Also extracts citation data from the source code of these graphs. Captchas pop up every 100-150 iterations.
