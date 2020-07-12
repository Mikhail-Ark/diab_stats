import itertools
import pickle
import re
from collections import Counter

from libs.data_collectors.raws_collector import grams
from libs.parser.manuf_parser import BrandDeterminator


def find_grouped_info(query, scache=None, gcache=None, fgroups=None, bdet=None):
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    if gcache is None:
        with open("info/goods_cache", "rb") as f:
            gcache = pickle.load(f)
    relevant_cats = choose_cats(query, scache=scache, fgroups=fgroups, gcache=gcache, bdet=bdet)
    answer = [gcache[cat] for cat in relevant_cats]
    fg_list = sorted(set(x["fg_id"] for x in answer))
    return answer, fg_list


def choose_cats(query, scache=None, fgroups=None, gcache=None, bdet=None):
    if not query:
        return list()
    if scache is None:
        with open("info/search_cache", "rb") as f:
            scache = pickle.load(f)
    if fgroups and (gcache is None):
        with open("info/goods_cache", "rb") as f:
            gcache = pickle.load(f)
    if bdet is None:
        bdet = BrandDeterminator()
    
    rel_brands, nquery = bdet.pull_brand_set(query)
    nquery_grams = grams(nquery)
    c = Counter()
    for gram in nquery_grams:
        gcats = scache.get(gram, False)
        if gcats:
            if len(gram) > 3:
                c.update({k: len(gram) for k in gcats})
            else:
                c.update(gcats)

    rel_cats = list()
    if not c:
        if not (rel_brands or fgroups):
            return rel_cats
        else:
            c.update(list(gcache.keys()))

    # filter
    to_del = set()
    if fgroups:
        rel_gr = {15} | set(int(x) for x in fgroups.split())
        if rel_brands:
            for k in c:
                info = gcache[k]
                if not ((info['b_id'] in rel_brands) and (info['fg_id'] in rel_gr)):
                    to_del.add(k)
        else:
            for k in c:
                info = gcache[k]
                if info['fg_id'] not in rel_gr:
                    to_del.add(k)
    elif rel_brands:
        for k in c:
            info = gcache[k]
            if info['b_id'] not in rel_brands:
                to_del.add(k)
    for k in to_del:
        del c[k]

    lower_bound = c.most_common(1)[0][1] / 2
    for cat, val in c.most_common():
        if val <= lower_bound:
            break
        rel_cats.append(cat)
    rel_cats.sort(key=lambda x: (c[x], len(gcache[x]['group_name'])))
    return rel_cats
