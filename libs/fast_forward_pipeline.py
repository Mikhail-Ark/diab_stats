import itertools
import pickle
import re
from collections import Counter

from libs.data_collectors.raws_collector import grams


def find_grouped_info(query, scache=None, gcache=None):
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    if gcache is None:
        with open("info/goods_cache", "rb") as f:
            gcache = pickle.load(f)
    relevant_cats = choose_cats(query, scache)
    answer = [gcache[cat] for cat in relevant_cats]
    return answer


def word_cat(word, words_cat):
    cats = list()
    for words in words_cat:
        if word in words:
            cats.append(words_cat[words])
    return cats


def choose_cats(query, scache=None, min_n=20):
    if not query:
        return list()
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    query_grams = grams(query)
    c = Counter()
    for gram in query_grams:
        gcats = scache.get(gram, False)
        if gcats:
            c.update(gcats)
    rel_cats = list()
    min_val = len(query_grams)
    for cat, val in c.most_common():
        if (len(rel_cats) >= min_n) and (val < min_val):
            break
        rel_cats.append(cat)
        min_val = val
    return rel_cats
