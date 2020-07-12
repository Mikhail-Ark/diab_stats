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


def form_raw_dict(r, shop_name_map):
    rd = {
        "title": r[0],
        "shop_name": shop_name_map[r[1]],
        "price": r[2],
        "ship_price": r[3],
        "url": r[4],
    }
    return rd


def get_db_info_map():
    db = DataBase()
    with db.create_connection() as conn:
        cur = conn.cursor()
        res = cur.execute("select g.id, g.title, g.group_id, g.manuf_id, m.name from goods g left join manufs m on g.manuf_id = m.id;").fetchall()
    return {r[0]: r[1:] for r in res}


def form_goods_cache(raws, fg_map=None, manual=True, search_cache=False):
    shop_name_map = {
        1: "МедМаг",
        2: "Тест-полоска",
        3: "ДиаКаталог",
        4: "Глюкометр",
        5: "Диабет-контроль",
        6: "Диачек",
        7: "Diabetic Shop",
        8: "Диалайф",
        9: "Diabet Care",
        10: "Diabet Med",
        11: "Diabeta Net",
        12: "Диа-Пульс",
        13: "Диабетон",
        14: "Глюкоза",
        15: "Бетар Компани",
        16: "Диатех",
        17: "Сателлит",
        18: "Diashop 24",
        19: "Диабет Сервис",
        20: "Академия Диабета",
        21: "Диабет Кабинет",
        22: "Жизнь с диабетом",
        23: "Diabet Mag",
        24: "Диабетика",
        25: "Диамарка"
    }
    if fg_map is None:
        g_map = get_db_info_map()
    with open("g_map", "wb") as f:
        pickle.dump(g_map, f)
    new_good_id = 100000
    cache = dict()
    for r in raws:
        if not r[5]:
            continue
        rd = form_raw_dict(r, shop_name_map)
        good_id = r[7]
        if good_id not in cache:
            if not good_id or (good_id != good_id):
                good_id = new_good_id
                new_good_id += 1
                g_map[good_id] = (r[0], 15, 0, '')
            g_info = g_map.get(good_id, (r[0], 15, 0, ''))
            cache[good_id] = {
                "group_name": g_info[0],
                "fg_id": g_info[1],
                "b_id": g_info[2],
                "b_name": g_info[3],
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
    grams = set(x for x in s.lower().split() if len(x) > n)
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
            good_grams.update(grams(item['title'].split(" — ")[0]))
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
