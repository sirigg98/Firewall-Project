
from names_dataset import NameDataset
nd = NameDataset()

pinyin_countries = {'Singapore', 'China', 'Province of China', 'Hong Kong', 'Taiwan', 'Malaysia'}
#Pinyin name classifier. Requires last name to appear after last space in name.
def is_pinyin(name):
    try:
        # Use names dataset to generate a lisst of 10 countries in which the last name is most popular
        top10 = set(nd.search(name.split()[-1])['last_name']['country'].keys())
    except (IndexError, TypeError):
        return False
    # If three of the 10 countries are in the set pinyin_countries, then classify as pinyin name.
    
    if len(top10.intersection(pinyin_countries)) > 2:
        return True
    
    return False