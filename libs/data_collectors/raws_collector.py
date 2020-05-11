from datetime import datetime as dt
import pickle
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


def make_conv_table(raws):
    pass


def inform_server():
    pass


if __name__ == "__main__":
    print(str(dt.now()))
    raws = collect_info(shops_list)
    print(len(raws))
    raws = add_good_id_to_raws(raws)
    update_db_raws(raws)
    make_conv_table(raws)
    inform_server()
    print(str(dt.now()))
    print()
