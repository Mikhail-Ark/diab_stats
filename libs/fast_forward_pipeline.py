import itertools
import pickle
import re
from collections import Counter

from libs.data_collectors.raws_collector import grams


def find_grouped_info(query, scache=None, gcache=None, fgroups=None):
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    if gcache is None:
        with open("info/goods_cache", "rb") as f:
            gcache = pickle.load(f)
    relevant_cats = choose_cats(query, scache=scache, fgroups=fgroups, gcache=gcache)
    answer = [gcache[cat] for cat in relevant_cats]
    return answer


def choose_cats(query, scache=None, fgroups=None, gcache=None, min_n=10):
    if not query:
        return list()
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    if fgroups and (gcache is None):
        with open("info/goods_cache", "rb") as f:
            gcache = pickle.load(f)
    query_grams = grams(query)
    c = Counter()
    if fgroups:
        rel_gr = {15} | set(int(x) for x in fgroups.split())
    for gram in query_grams:
        gcats = scache.get(gram, False)
        if gcats:
            if fgroups:
                gcats = [x for x in gcats if gcache.get(x, {}).get('fg_id', None) in rel_gr]
            c.update(gcats)
    rel_cats = list()
    min_val = len(query_grams)
    for cat, val in c.most_common():
        if (len(rel_cats) >= min_n) and (val < min_val):
            break
        rel_cats.append(cat)
        min_val = val
    return rel_cats


12 18 * * * /home/mikhail_ark/project/diab_stats/libs/data_collectors/raws_collector.py >> /var/log/myjob.log 2>&1