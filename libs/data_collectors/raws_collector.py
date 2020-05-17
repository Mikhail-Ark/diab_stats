from datetime import datetime as dt
import pickle
import re
import requests
import sys

sys.path.append('.')
from libs.data_collectors.shops import shops_list
from libs.db import DataBase
from libs.determinator import add_good_id_to_raws


def collect_info(shops_list):
    shops_list = [x() for x in shops_list]
    all_raws = list()
    for i, shop in enumerate(shops_list):
        print(i + 1, shop.shop_name, end='\t', sep='\t')
        raws = shop.get_goods(raw_format=True)
        print(len(raws))
        all_raws.extend(raws)
    return all_raws


def update_db_raws(raws):
    db = DataBase()
    db.insert_raws(raws)


def form_raw_dict(r):
    rd = {
        "title": r[0],
        "shop_name": r[1],
        "price": r[2],
        "ship_price": r[3],
        "url": r[4],
    }
    return rd


def get_filter_groups_map():
    db = DataBase()
    with db.create_connection() as conn:
        cur = conn.cursor()
        res = cur.execute("SELECT id, title, group_id from goods;").fetchall()
    return {r[0]: r[1:] for r in res}


def form_goods_cache(raws, fg_map=None, manual=True, search_cache=False):
    if fg_map is None:
        fg_map = get_filter_groups_map()
    new_good_id = 100000
    cache = dict()
    for r in raws:
        if not r[5]:
            continue
        rd = form_raw_dict(r)
        good_id = r[7]
        if good_id not in cache:
            if not good_id or (good_id != good_id):
                good_id = new_good_id
                new_good_id += 1
                fg_map[good_id] = (r[0], 15)
            cache[good_id] = {
                "group_name": fg_map[good_id][0],
                "fg_id": fg_map[good_id][1],
                "items": list()
            }
        cache[good_id]["items"].append(rd)
    for v in cache.values():
        v["items"].sort(key=lambda x : x["price"])

    if not search_cache:
        if manual:
            return cache
        else:
            with open("info/goods_cache", "wb") as f:
                pickle.dump(cache, f)
    else:
        scache = form_search_cache(cache)
        if manual:
            return cache, scache
        else:
            with open("info/goods_cache", "wb") as f:
                pickle.dump(cache, f)
            with open("info/search_cache", "wb") as f:
                pickle.dump(scache, f)


def grams(s, n=3):
    ns = "".join(re.findall(r"\w", s))[:90].lower()
    grams = set()
    if len(ns) < 3:
        return grams
    for i in range(n, len(ns) + 1):
        gram = ns[i - n : i]
        grams.add(gram)
    return grams


def form_search_cache(gcache):
    scache = dict()
    for k, v in gcache.items():
        good_grams = grams(v["group_name"])
        for item in v["items"]:
            good_grams.update(grams(item['title']))
        for gram in good_grams:
            scache.setdefault(gram, set()).add(k)
    return scache


def inform_server():
    requests.get("http://localhost:3010/api/v1/update_goods")

if __name__ == "__main__":
    print(str(dt.now()))
    raws = collect_info(shops_list)
    print(len(raws))
    raws = add_good_id_to_raws(raws)
    update_db_raws(raws)
    print("forming_goods_cache", end=': ')
    form_goods_cache(raws, manual=False, search_cache=True)
    print('ok')
    print("informing_server", end=': ')
    inform_server()
    print('ok')
    print(str(dt.now()))
    print()
