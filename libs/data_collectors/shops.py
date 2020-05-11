from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime as dt
import json
import pandas as pd
import re
import requests
from time import perf_counter


def get_soup(url, simple_encoding=False):
    for _ in range(3):
        try:
            req = requests.get(url)
            break
        except:
            pass
    else:
        return list()
    if not simple_encoding:
        req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    return soup


class Shop(ABC):
    def __init__(self):
        self.shop_name = ""
        self.shop_id = 0
        self.page_list = {}

    def get_goods(self, good_type='all', raw_format=False):
        res = list()
        un_goods = set()
        for url, good_type in self.prep_url_gtype_pairs(good_type):
#             print(url)
            parsed_blocks = self.parse_page(url)
            for parsed_block in parsed_blocks:
                key = (parsed_block.get('title', ''), parsed_block.get('price', 0))
                if key[0] and (key not in un_goods):
                    un_goods.add(key)
                    parsed_block['good_type'] = good_type
                    parsed_block['shop_name'] = self.shop_name
                    parsed_block['date'] = dt.now()
                    parsed_block['shop_id'] = self.shop_id
                    if ('description' in parsed_block) and (
                            (not isinstance(parsed_block['description'], str)) or (not parsed_block['description'])
                        ):
                        del parsed_block['description']
                    if raw_format:
                        parsed_block = self.ensure_raws_format(parsed_block)
                    res.append(parsed_block)
        return res

    def prep_url_gtype_pairs(self, good_type='all'):
        res = list()
        if good_type == 'all':
            for good_type, url_list in self.page_list.items():
                for url in url_list:
                    res.append((url, good_type))
        else:
            assert good_type in self.page_list, 'Нет ссылок на данный тип товара'
            for url in self.page_list[good_type]:
                res.append((url, good_type))
        return res

    def parse_page(self, url):
        soup = get_soup(url)
        if not soup:
            return list()
        blocks = self.det_blocks(soup)
        res = list()
        if blocks:
            for block in blocks:
                parsed = self.parse_block(block)
                res.append(parsed)
        return res
        
    @abstractmethod
    def det_blocks(self, soup):
        assert False, 'Not implemented'
    
    @abstractmethod
    def parse_block(self, block):
        assert False, 'Not implemented'

    def price_str_to_float(self, s):
        if "звонит" in s.lower():
            return 0
        s = s.translate({44: 46})
        s = re.sub(r"[^\d\.]", "", s).strip(".")
        s = re.sub(r"\.(?=.*\.)", "", s)
        search = re.search(r"\d+(?:[,.]\d+)?", s)
        if search:
            return float(search[0])
        else:
            return 0
        
    @staticmethod
    def ensure_raws_format(row):
        price = row.get('price', 0)
        if (price != price) or (not price):
            price = 0
        ship_price = row.get('ship_price', price)
        if (ship_price != ship_price) or (not ship_price):
            ship_price = price
        if not (price or ship_price):
            available = 0
        else:
            available = int(row.get('available', 1))
        return (
            row['title'],
            row['shop_id'],
            price,
            ship_price,
            row['url'],
            available,
            row['date']
        )


class MedMag(Shop):
    def __init__(self):
        self.shop_name = "МедМаг"
        self.shop_id = 1
        self.page_list = {
            'глюкометр': ('https://www.medmag.ru/index.php?categoryID=134&show_all=yes',),
            'полоска': (
                'https://www.medmag.ru/index.php?categoryID=135&show_all=yes',
                'https://www.medmag.ru/index.php?categoryID=1&show_all=yes',
            ),
            'анализатор': ('https://www.medmag.ru/index.php?categoryID=236&show_all=yes',),
            'ланцет': ('https://www.medmag.ru/index.php?categoryID=28&show_all=yes',),
            'ручка': ('https://www.medmag.ru/index.php?categoryID=24&show_all=yes',),
            'чехол': ('https://www.medmag.ru/index.php?categoryID=251&show_all=yes',),
            'помпа': ('https://www.medmag.ru/index.php?categoryID=2&show_all=yes',),
            'разное': ('https://www.medmag.ru/index.php?categoryID=18&show_all=yes',),
            'литература': ('https://www.medmag.ru/index.php?categoryID=15&show_all=yes',),
            'мониторинг': ('https://www.medmag.ru/index.php?categoryID=300&show_all=yes',),
            'бинт': ('https://www.medmag.ru/index.php?categoryID=21&show_all=yes',),
            'еда': ('https://www.medmag.ru/index.php?categoryID=296&show_all=yes',),
            'тонометр': ('https://www.medmag.ru/index.php?categoryID=27&show_all=yes',),
            'ингалятор': ('https://www.medmag.ru/index.php?categoryID=3&show_all=yes',),
            'ирригатор': ('https://www.medmag.ru/index.php?categoryID=338&show_all=yes',),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "products1"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        title = block.find("span")
        if not title:
            return res
        res['title'] = title.text
        res['url'] = 'https://www.medmag.ru/' + block.find("a").attrs['href']
        try:
            price_s = block.find("font", {"class": "price_special"}).text
            res['orig_price'] = price_s
        except AttributeError:
            price = 0
        else:
            price = self.price_str_to_float(price_s)
        res['price'] = price
        
        try:
            shipping_price_s = block.find("font", {"class": "price"}).text
            res['orig_ship_price'] = shipping_price_s
        except AttributeError:
            shipping_price = 0
        else:
            shipping_price = self.price_str_to_float(shipping_price_s)
        res['ship_price'] = shipping_price
        
        try:
            res['description'] = block.find("div", {"class": "text1"}).text.strip()
        except AttributeError:
            pass
        
        return res


class TestPoloska(Shop):
    def __init__(self):
        self.shop_name = "Тест-полоска"
        self.shop_id = 1
        self.page_list = {
            'анализатор': (
                'http://www.test-poloska.ru/catalog/bloodmeters/cholesterolmeters/',
                'http://www.test-poloska.ru/catalog/laboratory/',
                'http://www.test-poloska.ru/catalog/laboratory/bioteststrips/'
            ),
            'бинт': (
                'http://www.test-poloska.ru/catalog/smithandnephew/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/pico/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/diabetic_problems/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/diabetic_step/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/prolejnies/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/fireburns/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/postoperationperiod/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/odds/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/fixs/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/scarsremovers/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/skinwounds/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/fixcateters/',
                'http://www.test-poloska.ru/catalog/smithandnephew/smith_and_nephew/versajet/',
                'http://www.test-poloska.ru/catalog/smithandnephew/gigiene_invalid/',
                'http://www.test-poloska.ru/catalog/smithandnephew/cutanplast/',
                'http://www.test-poloska.ru/catalog/smithandnephew/hartmann/'
                ),
            'витамин': (
                'http://www.test-poloska.ru/catalog/baaddons/',
                'http://www.test-poloska.ru/catalog/baaddons/biological/',
                'http://www.test-poloska.ru/catalog/baaddons/vitaminy_dlya_diabetikov/',
                'http://www.test-poloska.ru/catalog/baaddons/liquidvitamins/',
                'http://www.test-poloska.ru/catalog/baaddons/p2pills/'
           ),
            'глюкометр': (
                'http://www.test-poloska.ru/catalog/bloodmeters/',
            ),
            'еда': (
                'http://www.test-poloska.ru/catalog/saluta/diabeticfood/',
            ),
            'ингалятор': (
                'http://www.test-poloska.ru/catalog/ingalator/',
                'http://www.test-poloska.ru/catalog/ingalator/omronspare/'
            ),
            'ланцет': (
                'http://www.test-poloska.ru/catalog/needles/',
                'http://www.test-poloska.ru/catalog/needles/isulinpens_needles/'
            ),
            'косметика': (
                'http://www.test-poloska.ru/catalog/ecocosmetics/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_food/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_lips/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_eyes/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_man/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_hair/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_oils/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_soap/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmtics_legs/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_baby/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/diabet_mouth_cleaning/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_hands/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_face/',
                'http://www.test-poloska.ru/catalog/ecocosmetics/cosmetics_bodycare/',
            ),
            'литература': (
                'http://www.test-poloska.ru/catalog/books/',
            ),
            'полоска': (
                'http://www.test-poloska.ru/catalog/teststripes/',
                'http://www.test-poloska.ru/catalog/teststripes/visual/',
                'http://www.test-poloska.ru/catalog/teststripes/visual/100pscinapack/'
            ),
            'помпа': (
                'http://www.test-poloska.ru/catalog/insulinpump/',
                'http://www.test-poloska.ru/catalog/insulinpump/danainsulinpumps/',
                'http://www.test-poloska.ru/catalog/insulinpump/roche/',
                'http://www.test-poloska.ru/catalog/insulinpump/',
                'http://www.test-poloska.ru/catalog/insulinpump/roche/flexlinkseria/',
                'http://www.test-poloska.ru/catalog/insulinpump/roche/tenderlinkseria/',
                'http://www.test-poloska.ru/catalog/insulinpump/roche/rapiddlinkseria/',
                'http://www.test-poloska.ru/catalog/insulinpump/roche/accuchekinsulinepumpcases/',
                'http://www.test-poloska.ru/catalog/insulinpump/medtronic/',
                'http://www.test-poloska.ru/catalog/insulinpump/medtronic/medtronic_seventh_series/',
                'http://www.test-poloska.ru/catalog/insulinpump/medtronic/medtronic_fifth_seria/',
                'http://www.test-poloska.ru/catalog/insulinpump/medtronic/medtronicinsulinpumpscases/'
            ),
            'разное': (
                'http://www.test-poloska.ru/catalog/specialoffers/',
                'http://www.test-poloska.ru/catalog/needles/cleaningproducts/',
                'http://www.test-poloska.ru/catalog/saluta/coughing/',
                'http://www.test-poloska.ru/catalog/saluta/',
                'http://www.test-poloska.ru/catalog/saluta/numismed/',
                'http://www.test-poloska.ru/catalog/saluta/teas_for_diabetes/',
                'http://www.test-poloska.ru/catalog/saluta/sugar_risers_category/',
                'http://www.test-poloska.ru/catalog/medical_equipment/',
                'http://www.test-poloska.ru/catalog/medical_equipment/thermometers/',
                'http://www.test-poloska.ru/catalog/medical_equipment/medical_all_kinds/',
                'http://www.test-poloska.ru/catalog/medical_equipment/medical_all_kinds/toothbrushesspareparts/',
                'http://www.test-poloska.ru/catalog/medical_equipment/medical_all_kinds/irrigatorsspateparts/',
                'http://www.test-poloska.ru/catalog/medical_equipment/children/',
                'http://www.test-poloska.ru/catalog/medical_equipment/stepsmonitors/',
                'http://www.test-poloska.ru/catalog/medical_equipment/floorweight/',
                'http://www.test-poloska.ru/catalog/medical_equipment/airpurifiers/',
                'http://www.test-poloska.ru/catalog/medical_equipment/alcometers_and_alcotesters/',
                'http://www.test-poloska.ru/catalog/medical_equipment/almagcategory/',
                'http://www.test-poloska.ru/catalog/ortipedic/',
                'http://www.test-poloska.ru/catalog/ortipedic/bandages/',
                'http://www.test-poloska.ru/catalog/ortipedic/o_compression/',
                'http://www.test-poloska.ru/catalog/ortipedic/stephelpers/',
                'http://www.test-poloska.ru/catalog/ortipedic/slipsole/',
                'http://www.test-poloska.ru/catalog/disability/',
                'http://www.test-poloska.ru/catalog/disability/diable_mechanic/',
                'http://www.test-poloska.ru/catalog/disability/sanitary/',
                'http://www.test-poloska.ru/catalog/medical_equipment/',
                'http://www.test-poloska.ru/catalog/other/',
                'http://www.test-poloska.ru/catalog/other/batteries/',
                'http://www.test-poloska.ru/catalog/other/thermocases/',
                'http://www.test-poloska.ru/catalog/other/pillorganizer/'
            ),
            'раствор': (
                'http://www.test-poloska.ru/catalog/bloodmeters/controlsolutions/',
            ),
            'ручка': (
                'http://www.test-poloska.ru/catalog/syringepens/',
                'http://www.test-poloska.ru/catalog/syringepens/insulinpen_needles_universal/'
            ),
            'тест': (
                'http://www.test-poloska.ru/catalog/teststripes/infections_markers/',
                'http://www.test-poloska.ru/catalog/teststripes/pregancy/',
                'http://www.test-poloska.ru/catalog/teststripes/drugstests/',
                'http://www.test-poloska.ru/catalog/teststripes/drugstests/factormediha/',
                'http://www.test-poloska.ru/catalog/teststripes/alcoholtests/',
                'http://www.test-poloska.ru/catalog/teststripes/oftalmology/',
                'http://www.test-poloska.ru/catalog/teststripes/cardiomarkers/',
                'http://www.test-poloska.ru/catalog/teststripes/cancermarkers/',
                'http://www.test-poloska.ru/catalog/teststripes/cholesterolstrips/'
            ),
            'тонометр': (
                'http://www.test-poloska.ru/catalog/tonometers/',
                'http://www.test-poloska.ru/catalog/tonometers/automatic_bloodpressure_meters/',
                'http://www.test-poloska.ru/catalog/tonometers/wristbloodpressuremonitors/',
                'http://www.test-poloska.ru/catalog/tonometers/semiautomatic/',
                'http://www.test-poloska.ru/catalog/tonometers/mechanicalbloodpressuremonitors/',
                'http://www.test-poloska.ru/catalog/tonometers/stetoskopes/',
                'http://www.test-poloska.ru/catalog/tonometers/cuffs_and_adapters/'
            ),
            'чехол': (
                'http://www.test-poloska.ru/catalog/bloodmeters/bloodmetercases/',
            ),
        }

    def det_blocks(self, soup):
        pl = soup.find("table", {"class": "productList"})
        if not pl:
            return list()
        blocks = pl.find_all("td", {"style": "padding-left:10px;"})
        return blocks

    def parse_block(self, block):
        res = dict()
        info = block.find_all("b")
        try:
            if len(info) not in (2, 3, 4):
                return res
        except TypeError:
            return res
        res['title'] = info[0].text
        res['url'] = 'http://www.test-poloska.ru' + block.find('a').attrs['href']
        if len(info) != 2:
            res['orig_manuf'] = info[1].text
        price_s = info[-1].text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        try:
            res['description'] = list(block.children)[max(7, len(info) + 4)]
        except IndexError:
            pass
        return res


class DiaCatalog(Shop):
    def __init__(self):
        self.shop_name = "ДиаКаталог"
        self.shop_id = 3
        self.page_list = {
            'анализатор': (
                'https://diacatalog.ru/product-category/%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D1%8B-%D0%BC%D0%BD%D0%BE/%D0%BA%D0%BE%D0%B0%D0%B3%D1%83%D1%87%D0%B5%D0%BA-%D0%B8%D0%BA%D1%81-%D1%8D%D1%81/',
                'https://diacatalog.ru/product-category/%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D1%8B-%D0%BC%D0%BD%D0%BE/%D0%BA%D1%83%D0%BB%D0%B0%D0%B1%D1%81-%D1%8D%D0%BB%D0%B5%D0%BA%D1%82%D1%80%D0%BE%D0%BC%D0%B5%D1%82%D1%80/',
                'https://diacatalog.ru/product-category/%D0%B1%D0%B8%D0%BE%D1%85%D0%B8%D0%BC%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D1%8B13/%D0%B0%D0%BA%D0%BA%D1%83%D1%82%D1%80%D0%B5%D0%BD%D0%B4-%D0%BF%D0%BB%D1%8E%D1%81-accutrend-plus26/',
                'https://diacatalog.ru/product-category/%D0%B1%D0%B8%D0%BE%D1%85%D0%B8%D0%BC%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D1%8B13/%D0%BA%D0%B0%D1%80%D0%B4%D0%B8%D0%BE%D1%87%D0%B5%D0%BA-cardiochek25/',
                'https://diacatalog.ru/product-category/%D0%B1%D0%B8%D0%BE%D1%85%D0%B8%D0%BC%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D1%8B13/%D0%BC%D1%83%D0%BB%D1%8C%D1%82%D0%B8%D0%BA%D1%8D%D0%B9%D1%80%D0%B8%D0%BD-multicare-in18/',
                'https://diacatalog.ru/product-category/%D0%B3%D0%BB%D0%B8%D0%BA%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9-%D0%B3%D0%B5%D0%BC%D0%BE%D0%B3%D0%BB%D0%BE%D0%B1%D0%B85/a1cnow74/',
                'https://diacatalog.ru/product-category/%D0%B3%D0%BB%D0%B8%D0%BA%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9-%D0%B3%D0%B5%D0%BC%D0%BE%D0%B3%D0%BB%D0%BE%D0%B1%D0%B85/%D0%B0%D1%84%D0%B8%D0%BD%D0%B8%D0%BE%D0%BD-afinion-as10067/',
                'https://diacatalog.ru/product-category/%D0%B3%D0%BB%D0%B8%D0%BA%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9-%D0%B3%D0%B5%D0%BC%D0%BE%D0%B3%D0%BB%D0%BE%D0%B1%D0%B85/%D0%B3%D0%BB%D0%B8%D0%BA%D0%BE%D0%B3%D0%B5%D0%BC%D0%BE%D1%82%D0%B5%D1%81%D1%8265/',
                'https://diacatalog.ru/product-category/%D0%B3%D0%BB%D0%B8%D0%BA%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9-%D0%B3%D0%B5%D0%BC%D0%BE%D0%B3%D0%BB%D0%BE%D0%B1%D0%B85/%D0%BD%D0%B8%D0%BA%D0%BE%D0%BA%D0%B0%D1%80%D0%B4nbsp%D1%80%D0%B8%D0%B4%D0%B5%D1%80nbspii-nycocardnbspreadernbsp68/'
            ),
            'бинт': (
                'https://diacatalog.ru/product-category/%D1%80%D0%B0%D0%BD%D0%BE%D0%B7%D0%B0%D0%B6%D0%B8%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B8-%D1%84%D0%B8%D0%BA%D1%81%D0%B0%D1%8616/%D1%80%D1%83%D0%BB%D0%BE%D0%BD%D0%BD%D1%8B%D0%B5-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B8-%D0%BF%D0%BE%D0%B2%D1%8F%D0%B7%D0%BA%D0%B8-%D0%B1%D0%B8%D0%BD%D1%82%D1%8B72/',
                ),
            'глюкометр': (
                'https://diacatalog.ru/product-category/%D0%B3%D0%BB%D1%8E%D0%BA%D0%BE%D0%BC%D0%B5%D1%82%D1%80%D1%8B2/',
            ),
            'ланцет': (
                'https://diacatalog.ru/product-category/%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B810/%D0%B0%D0%B2%D1%82%D0%BE%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D1%81%D0%BA%D0%B0%D1%80%D0%B8%D1%84%D0%B817/',
                'https://diacatalog.ru/product-category/%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B810/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA-%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B859/',
                'https://diacatalog.ru/product-category/%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B810/%D0%B2%D0%B0%D0%BD-%D1%82%D0%B0%D1%87-onetouch-%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%B8-%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B863/',
                'https://diacatalog.ru/product-category/%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%BF%D1%80%D0%BE%D0%BA%D0%B0%D0%BB%D1%8B%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B810/%D1%83%D0%BD%D0%B8%D0%B2%D0%B5%D1%80%D1%81%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D0%BB%D0%B0%D0%BD%D1%86%D0%B5%D1%82%D1%8B-%D0%B8%D0%B3%D0%BB%D1%8B%D0%BF%D1%80%D0%BE%D0%BA62/',
            ),
            'косметика': (
                'https://diacatalog.ru/product-category/%D0%BA%D0%BE%D1%81%D0%BC%D0%B5%D1%82%D0%B8%D0%BA%D0%B011/',
            ),
            'литература': (
                'https://diacatalog.ru/product-category/%D0%BA%D0%BD%D0%B8%D0%B37/%D0%B4%D0%B8%D0%B0%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B853/',
                'https://diacatalog.ru/product-category/%D0%BA%D0%BD%D0%B8%D0%B37/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B8-%D0%B0%D1%80%D1%82%D0%B1%D0%B8%D0%B7%D0%BD%D0%B5%D1%81%D1%86%D0%B5%D0%BD%D1%82%D1%8054/',
                'https://diacatalog.ru/product-category/%D0%BA%D0%BD%D0%B8%D0%B37/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B8-%D0%BF%D0%BE-%D0%B4%D0%B8%D0%B0%D0%B1%D0%B5%D1%82%D1%83/'
            ),
            'полоска': (
                'https://diacatalog.ru/product-category/%D1%82%D0%B5%D1%81%D1%82-%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA%D0%B81/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B8%D0%B7%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D1%82%D0%B5%D1%81%D1%82%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA6/%D0%B1%D0%B8%D0%BE%D1%81%D0%B5%D0%BD%D1%81%D0%BE%D1%80-%D0%B0%D0%BD-%D1%82%D0%B5%D1%81%D1%82%D1%8B-%D0%BC%D0%BE%D1%87%D0%B8-%D1%81%D0%BB%D1%8E%D0%BD%D1%8B-%D1%80%D0%BD19/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B8%D0%B7%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D1%82%D0%B5%D1%81%D1%82%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA6/%D1%82%D0%B5%D1%81%D1%82-%D0%BF%D0%BE%D0%B4%D1%82%D0%B5%D0%BA%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BE%D0%BA%D0%BE%D0%BB%D0%BE%D0%BF%D0%BB%D0%BE%D0%B4%D0%BD%D1%8B%D1%85-%D0%B2%D0%BE51/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B8%D0%B7%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D1%82%D0%B5%D1%81%D1%82%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA6/%D1%82%D0%B5%D1%81%D1%82%D1%8B-%D0%BA%D1%80%D0%BE%D0%B2%D0%B827/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B8%D0%B7%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D1%82%D0%B5%D1%81%D1%82%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA6/%D1%82%D0%B5%D1%81%D1%82%D1%8B-%D0%BC%D0%BE%D1%87%D0%B828/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B8%D0%B7%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5-%D1%82%D0%B5%D1%81%D1%82%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D0%BA6/%D1%82%D0%B5%D1%81%D1%82-%D0%BD%D0%B0%D0%B1%D0%BE%D1%80%D1%8B-%D0%BD%D0%B0-%D0%B2%D1%8B%D1%8F%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F-%D0%B2%D0%B8%D1%80%D1%83%D1%81%D0%BE%D0%B2-%D0%B3%D1%80%D0%B8%D0%BF/',
            ),
            'помпа': (
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D0%BA%D0%B0%D1%80%D1%82%D1%80%D0%B8%D0%B4%D0%B6%D0%B8-%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D0%BD%D1%8B%D0%B5-%D0%BD%D0%B0%D0%B1%D0%BE%D1%80%D1%8B/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D1%80%D0%B5%D0%BF%D0%B8%D0%B4-%D0%B4-%D0%BB%D0%B8%D0%BD%D0%BA-rapid-d-link/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D1%82%D0%B5%D0%BD%D0%B4%D0%B5%D1%80-%D0%BB%D0%B8%D0%BD%D0%BA-tenderlink/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D1%84%D0%BB%D0%B5%D0%BA%D1%81-%D0%BB%D0%B8%D0%BD%D0%BA-flexlink/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D1%84%D0%BB%D0%B5%D0%BA%D1%81-%D0%BB%D0%B8%D0%BD%D0%BA-%D0%BF%D0%BB%D1%8E%D1%81-flexlink-plus/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA/%D0%B0%D0%BA%D0%BA%D1%83%D1%87%D0%B5%D0%BA-%D1%87%D0%B5%D1%85%D0%BB%D1%8B-%D0%BA%D0%BB%D0%B8%D0%BF%D1%81%D1%8B82/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D1%83%D0%B0%D1%80%D1%8B-%D0%BA%D0%BE%D0%BB%D0%BF%D0%B0%D1%87%D0%BA%D0%B8-%D0%BA%D0%BB%D1%8E%D1%87-%D0%B1%D0%B5%D0%B7%D0%BE%D0%BF%D0%B0%D1%81%D0%BD%D0%BE%D1%81/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D0%BA%D0%B2%D0%B8%D0%BA-%D1%81%D0%B5%D1%82-quick-set/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D0%BC%D0%B8%D0%BE-minimed-mio/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D1%81%D0%B8%D0%BB%D1%83%D1%8D%D1%82-silhouette/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D1%88%D1%83%D0%B0-%D1%82%D0%B8-sure-t/',
                'https://diacatalog.ru/product-category/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B0%D0%BA8/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D0%BF%D0%BE%D0%BC%D0%BF%D1%8B-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA%D0%B879/%D0%BC%D0%B5%D0%B4%D1%82%D1%80%D0%BE%D0%BD%D0%B8%D0%BA-%D1%87%D0%B5%D1%85%D0%BB%D1%8B-%D0%BA%D0%BB%D0%B8%D0%BF%D1%81%D1%8B77/'
            ),
            'разное': (
                'https://diacatalog.ru/sale/',
                'https://diacatalog.ru/product-category/%D0%B2%D0%B5%D1%81%D1%8B-%D0%B4%D0%B8%D0%B0%D0%B1%D0%B5%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B548/',
                'https://diacatalog.ru/product-category/%D0%B3%D0%B8%D0%BF%D0%BE%D0%B3%D0%BB%D0%B8%D0%BA%D0%B5%D0%BC%D0%B8%D0%B8-%D0%BD%D0%B5%D1%8221/',
                'https://diacatalog.ru/product-category/%D0%B4%D0%B5%D0%B7%D0%B8%D0%BD%D1%84%D0%B5%D0%BA%D1%86%D0%B814/',
                'https://diacatalog.ru/product-category/%D0%BC%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3-%D0%B3%D0%BB%D1%8E%D0%BA%D0%BE%D0%B7%D1%8B/%D0%BC%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3-%D0%B3%D0%BB%D1%8E%D0%BA%D0%BE%D0%B7%D1%8B-%D0%B2-%D0%BA%D1%80%D0%BE%D0%B2%D0%B8-%D0%BC%D0%B5%D0%B4%D1%8258/',
                'https://diacatalog.ru/product-category/%D0%BC%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3-%D0%B3%D0%BB%D1%8E%D0%BA%D0%BE%D0%B7%D1%8B/%D1%84%D1%80%D0%B8%D1%81%D1%82%D0%B0%D0%B9%D0%BB-%D0%BB%D0%B8%D0%B1%D1%80%D0%B5-freestyle-libre-flash/',
                'https://diacatalog.ru/product-category/%D0%BE%D0%BB%D1%8C%D1%84%D0%B0%D0%BA%D1%82%D0%BE%D0%BC%D0%B5%D1%82%D1%80%D0%B8%D1%8F-%D0%B7%D0%B0%D1%89%D0%B8%D1%82%D0%B0-%D0%B3%D0%BB%D0%B0%D0%B7%D0%B095/',
                'https://diacatalog.ru/product-category/%D0%BF%D1%80%D0%BE%D1%84%D0%B8%D0%BB%D0%B0%D0%BA%D1%82%D0%B8%D0%BA%D0%B0-%D0%BF%D0%BE%D0%BB%D0%BE%D1%81%D1%82%D0%B8-%D1%80%D1%82%D0%B039/',
                'https://diacatalog.ru/product-category/%D1%80%D0%B0%D0%BD%D0%BE%D0%B7%D0%B0%D0%B6%D0%B8%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B8-%D1%84%D0%B8%D0%BA%D1%81%D0%B0%D1%8616/%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B871/',
                'https://diacatalog.ru/product-category/%D1%80%D0%B0%D0%BD%D0%BE%D0%B7%D0%B0%D0%B6%D0%B8%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B8-%D1%84%D0%B8%D0%BA%D1%81%D0%B0%D1%8616/%D1%80%D0%B0%D0%BD%D0%BE%D0%B7%D0%B0%D0%B6%D0%B8%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B570/',
                'https://diacatalog.ru/product-category/%D1%80%D0%B0%D0%BD%D0%BE%D0%B7%D0%B0%D0%B6%D0%B8%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D0%B8-%D1%84%D0%B8%D0%BA%D1%81%D0%B0%D1%8616/%D1%83%D0%B4%D0%B0%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D1%84%D0%B8%D0%BA%D1%81%D0%B0%D1%86%D0%B8%D1%8F-%D0%BF%D0%BB%D0%B0%D1%81%D1%82%D1%8B%D1%80%D1%8F-%D0%B1%D0%B5%D0%B7-73/',
                'https://diacatalog.ru/product-category/%D1%81%D1%82%D0%B5%D0%B2%D0%B8%D1%8F76/',
                'https://diacatalog.ru/product-category/%D1%85%D0%BE%D0%BB%D0%BE%D0%B4%D0%B8%D0%BB%D1%8C%D0%BD%D0%B8%D0%BA%D0%B8-%D1%82%D0%B5%D1%80%D0%BC%D0%BE%D1%87%D0%B5%D1%85%D0%BB%D1%8B-%D1%8D%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%8247/',
            ),
            'ручка': (
                'https://diacatalog.ru/product-category/%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%BA%D0%B8-%D0%B8%D0%B3%D0%BB%D1%8B-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%8B3/%D0%B0%D0%B2%D1%82%D0%BE%D0%B8%D0%BD%D1%8A%D0%B5%D0%BA%D1%82%D0%BE%D1%80%D1%8B/',
                'https://diacatalog.ru/product-category/%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%BA%D0%B8-%D0%B8%D0%B3%D0%BB%D1%8B-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%8B3/%D0%B8%D0%B3%D0%BB%D1%8B-%D0%B4%D0%BB%D1%8F-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%B5%D0%BA85/',
                'https://diacatalog.ru/product-category/%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%BA%D0%B8-%D0%B8%D0%B3%D0%BB%D1%8B-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%8B3/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%BA%D0%B887/',
                'https://diacatalog.ru/product-category/%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%80%D1%83%D1%87%D0%BA%D0%B8-%D0%B8%D0%B3%D0%BB%D1%8B-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%8B3/%D0%B8%D0%BD%D1%81%D1%83%D0%BB%D0%B8%D0%BD%D0%BE%D0%B2%D1%8B%D0%B5-%D1%88%D0%BF%D1%80%D0%B8%D1%86%D1%8B94/',
            ),
            'тонометр': (
                'https://diacatalog.ru/product-category/%D1%82%D0%BE%D0%BD%D0%BE%D0%BC%D0%B5%D1%82%D1%80%D1%8B-%D0%BC%D0%B0%D0%BD%D0%B6%D0%B5%D1%82%D1%8B34/',
            ),
        }
        
    def det_blocks(self, soup):
        titles = [x.text for x in soup.find_all("span", {"class": "h7"})]
        urls = [x.attrs['href'] for x in soup.find_all('a', {"class": "full-outer"})]
        orig_prices = list()
        for p in soup.find_all("span", {"class": "price"}):
            price_tag = p.find("ins")
            if not price_tag:
                price_tag = p
            if len(price_tag.find_all("span", {"class": "woocommerce-Price-amount amount"})) == 2:
                price_tag = price_tag.find_all("span", {"class": "woocommerce-Price-amount amount"})[1]
            orig_prices.append(price_tag.text)
        return list(zip(titles, orig_prices, urls))

    def parse_block(self, block):
        res = dict()
        res['title'] = block[0]
        res['url'] = block[2]
        price_s = block[1]
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class Glukometr(Shop):
    def __init__(self):
        self.shop_name = "Глюкометр"
        self.shop_id = 4
        self.page_list = {
            'разное': (
                'https://glucometr.com/score/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "t776__textwrapper"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res["title"] = block.find("div").text
        res["url"] = 'https://glucometr.com/score/'
        price_s = block.find("div", {"class": "t776__price-value"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class DaibetControl(Shop):
    def __init__(self):
        self.shop_name = "Диабет-контроль"
        self.shop_id = 5
        self.page_list = {
            'бинт': (
                'https://diabet-control.ru/category/sredstva-po-ukhodu/plastyri-i-kinezioteypy/',
                ),
            'витамин': (
                'https://diabet-control.ru/category/pitanie/vitaminy-dlya-diabetikov/',
           ),
            'глюкометр': (
                'https://diabet-control.ru/category/glyukometr-i-analizatory/neinvazivnyy-glyukometr/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/glyukometr-diakont-diacont/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/accu-chek-active/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/easy-touch/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/one-touch-glyukometr/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/glyukometr-kontur-ts/',
                'https://diabet-control.ru/category/glyukometr-i-analizatory/glyukometr-satellit/',
            ),
            'еда': (
                'https://diabet-control.ru/category/pitanie/pitanie-pri-diabete/',
                'https://diabet-control.ru/category/pitanie/zameniteli-sakhara/',
                'https://diabet-control.ru/category/pitanie/sredstva-pri-gipoglikemii/',
                'https://diabet-control.ru/category/pitanie/fitochai/',
            ),
            'ланцет': (
                'https://diabet-control.ru/category/lantsety-i-prokalyvateli/',
            ),
            'косметика': (
                'https://diabet-control.ru/category/sredstva-po-ukhodu/ukhod-za-kozhey-krema-dlya-nog-ruk-i-tela/',
            ),
            'литература': (
                'https://diabet-control.ru/category/saharnyj-diabet/',
            ),
            'полоска': (
                'https://diabet-control.ru/category/test-poloski/vizualnye-test-poloski/',
                'https://diabet-control.ru/category/test-poloski/aychek-ichek/',
                'https://diabet-control.ru/category/test-poloski/akku-chek-aktiv-test-poloski/',
                'https://diabet-control.ru/category/test-poloski/bayer-bayer/',
                'https://diabet-control.ru/category/test-poloski/one-touch-select-test-poloski/',
                'https://diabet-control.ru/category/test-poloski/diakont-diacont/',
                'https://diabet-control.ru/category/test-poloski/izi-tach-easy-touch/',
                'https://diabet-control.ru/category/test-poloski/test-poloski-one-touch-ultra/',
                'https://diabet-control.ru/category/test-poloski/ebbot-abbott/',
                'https://diabet-control.ru/category/test-poloski/yunistrip-unistrip/',
            ),
            'помпа': (
                'https://diabet-control.ru/category/insulinovye-pompa/akku-chek/',
                'https://diabet-control.ru/category/insulinovye-pompa/medtronik/',
            ),
            'разное': (
                'https://diabet-control.ru/category/aksessuary-i-chekhly/braslety/',
                'https://diabet-control.ru/category/aksessuary-i-chekhly/medtronik/',
                'https://diabet-control.ru/category/aksessuary-i-chekhly/akku-chek/',
                'https://diabet-control.ru/category/aksessuary-i-chekhly/insula--poyas-dlya-nosheniya-insulinovoy-pompy/',
                'https://diabet-control.ru/category/insulinovye-pompa/monitoring-glyukozy/',
                'https://diabet-control.ru/category/infuzionnye-port-sistemy-dlya-khimioterapii/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/vesy/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/termometry/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/shagomery/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/ingalyatory/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/obluchateli/',
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/massazhery/',
                'https://diabet-control.ru/category/infuzionnyj-nabor/medtronik-medtronic/',
                'https://diabet-control.ru/category/infuzionnyj-nabor/akku-chek-accu-chek/',
                'https://diabet-control.ru/category/ruchki-i-igly/shpritsy-insulinovye/',
                'https://diabet-control.ru/category/sredstva-po-ukhodu/dezinfitsiruyushchie-sredstva/',
                'https://diabet-control.ru/category/sredstva-po-ukhodu/diabeticheskaya-stopa/',
                'https://diabet-control.ru/category/sredstva-po-ukhodu/ukhod-za-polostyu-rta/',
                'https://diabet-control.ru/category/uvlazhniteli-vozdukhoochistiteli/',
            ),
            'ручка': (
                'https://diabet-control.ru/category/ruchki-i-igly/shprits-ruchki/',
                'https://diabet-control.ru/category/ruchki-i-igly/shpric-ruchka/',
            ),
            'тонометр': (
                'https://diabet-control.ru/category/meditsinskaya-tekhnika/tonometry/',
            ),
            'чехол': (
                'https://diabet-control.ru/category/aksessuary-i-chekhly/dlya-shprits-ruchek/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "pl-item-info"})
        return blocks

    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("span", {"itemprop": "name"}).text
        res['url'] = 'https://diabet-control.ru' + block.find('a').attrs['href']
        price_s = block.find("span", {"class": "price"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        desc = block.find("div", {"itemprop": "description"})
        if desc:
            res['description'] = desc.text
        return res


class DiaCheck(Shop):
    def __init__(self):
        self.shop_name = "Диачек"
        self.shop_id = 6
        self.page_list = {    
            'анализатор': (
                'https://www.diacheck.ru/collection/biohimicheskie-analizatory-i-mno',
            ),
            'бинт': (
                'https://www.diacheck.ru/collection/povyazki-i-plastyri',
            ),
            'витамин': (
                'https://www.diacheck.ru/collection/vitaminy-dlya-diabetikov',
            ),
            'глюкометр': (
                'https://www.diacheck.ru/collection/glyukometry',
                'https://www.diacheck.ru/collection/glyukometry-clever-chek',
                'https://www.diacheck.ru/collection/glyukometry-one-touch',
                'https://www.diacheck.ru/collection/glyukometr-accu-chek',
                'https://www.diacheck.ru/collection/glyukometry-freestyle',
                'https://www.diacheck.ru/collection/glyukometry-sensocard',
                'https://www.diacheck.ru/collection/glyukometry-bionime',
            ),
            'еда': (
                'https://www.diacheck.ru/collection/dieticheskie-produkty',
                'https://www.diacheck.ru/collection/varenie-i-dzhemy',
                'https://www.diacheck.ru/collection/bakaleya',
                'https://www.diacheck.ru/collection/pechenie-konfety',
                'https://www.diacheck.ru/collection/saharozameniteli',
            ),
            'ингалятор': (
                'https://www.diacheck.ru/collection/ingalyatory',
                'https://www.diacheck.ru/collection/zapasnye-chasti',
            ),
            'ланцет': (
                'https://www.diacheck.ru/collection/prokalyvateli-i-lantsety',
                'https://www.diacheck.ru/collection/lantsety',
                'https://www.diacheck.ru/collection/lantsety-accu-chek',
                'https://www.diacheck.ru/collection/lantsety-one-touch',
                'https://www.diacheck.ru/collection/prokalyvateli',
            ),
            'косметика': (
                'https://www.diacheck.ru/collection/uhod-za-stopoy',
                'https://www.diacheck.ru/collection/krema',
            ),
            'литература': (
                'https://www.diacheck.ru/collection/literatura',
            ),
            'полоска': (
                'https://www.diacheck.ru/collection/test-poloski-dlya-analizatorov',
                'https://www.diacheck.ru/collection/test-poloski-accutrend',
                'https://www.diacheck.ru/collection/test-poloski-coaguchek',
                'https://www.diacheck.ru/collection/test-poloski-multicare-in',
                'https://www.diacheck.ru/collection/test-poloski-easy-touch',
                'https://www.diacheck.ru/collection/test-poloski',
                'https://www.diacheck.ru/collection/vizualnye_test_poloski',
                'https://www.diacheck.ru/collection/test-poloski-dlya-opredeleniya-ketonov-v-moche',
                'https://www.diacheck.ru/collection/test-poloski-na-belok-v-moche',
                'https://www.diacheck.ru/collection/test-poloski-na-sahar-v-krovi',
                'https://www.diacheck.ru/collection/test-poloski-na-troponin',
                'https://www.diacheck.ru/collection/test-poloski-dlya-opredeleniya-glyukozy-v-moche',
                'https://www.diacheck.ru/collection/test-poloski-na-opredelenie-alkogolya-po-slyune',
                'https://www.diacheck.ru/collection/test_poloski_dlya_glyukometra',
                'https://www.diacheck.ru/collection/test-poloski-icheck',
                'https://www.diacheck.ru/collection/test-poloski-one-touch-select',
                'https://www.diacheck.ru/collection/test-poloski-one-touch-select-plus',
                'https://www.diacheck.ru/collection/test-poloski-one-touch-ultra',
                'https://www.diacheck.ru/collection/test-poloski-one-touch-verio',
                'https://www.diacheck.ru/collection/test-poloski-accu-chek-active',
                'https://www.diacheck.ru/collection/test-poloski-accu-chek-performa',
                'https://www.diacheck.ru/collection/test-poloski-satellit',
                'https://www.diacheck.ru/collection/test-poloski-satellit-plyus',
                'https://www.diacheck.ru/collection/test-poloski-contour-ts',
                'https://www.diacheck.ru/collection/test-poloski-klever-chek',
            ),
            'помпа': (
                'https://www.diacheck.ru/collection/insulinovye-pompy',
                'https://www.diacheck.ru/collection/tovary-dlya-insulinovyh-pomp',
                'https://www.diacheck.ru/collection/rashodnye-materialy-dlya-insulinovyh-pomp',
                'https://www.diacheck.ru/collection/rashodnye-materialy-dlya-pompy-medtronic',
                'https://www.diacheck.ru/collection/rashodnye-materialy-dlya-pompy-accu-chek',
                'https://www.diacheck.ru/collection/insulinovye-pompy-medtronic',
                'https://www.diacheck.ru/collection/insulinovye-pompy-accu-chek',
            ),
            'разное': (
                'https://www.diacheck.ru/collection/aktsii',
                'https://www.diacheck.ru/collection/rasprodazha',
                'https://www.diacheck.ru/collection/spets-tsena',
                'https://www.diacheck.ru/collection/vpityvayuschee-belie',
                'https://www.diacheck.ru/collection/pelenki',
                'https://www.diacheck.ru/collection/podguzniki-dlya-vzroslyh',
                'https://www.diacheck.ru/collection/podguzniki-dlya-detey',
                'https://www.diacheck.ru/collection/urologicheskie-prokladki',
                'https://www.diacheck.ru/collection/diabeticheskaya-stopa',
                'https://www.diacheck.ru/collection/gelevye-prisposobleniya',
                'https://www.diacheck.ru/collection/reabilitatsionnaya-obuv',
                'https://www.diacheck.ru/collection/ortopedicheskaya-obuv',
                'https://www.diacheck.ru/collection/diabeticheskie-noski',
                'https://www.diacheck.ru/collection/protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/kolgotki',
                'https://www.diacheck.ru/collection/i-klass-kompressiya-18-21-mm-rtst-kolgotki-protivovarikoznyy-trikotazh-tovary-dlya-beremennyh',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-23-25-mm-rtst-kolgotki-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-26-32-mm-rtst-kolgotki-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/iii-klass-kompressiya-34-46-mm-rtst-kolgotki',
                'https://www.diacheck.ru/collection/golfy',
                'https://www.diacheck.ru/collection/i-klass-kompressiya-18-21-mm-rtst-golfy-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-23-25-mm-rtst-golfy-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-26-32-mm-rtst-golfy-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/iii-klass-kompressiya-34-46-mm-rtst-golfy',
                'https://www.diacheck.ru/collection/chulki',
                'https://www.diacheck.ru/collection/i-klass-kompressiya-18-21-mm-rtst-chulki',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-23-25-mm-rtst-chulki-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/ii-klass-kompressiya-26-32-mm-rtst-chulki-protivovarikoznyy-trikotazh',
                'https://www.diacheck.ru/collection/iii-klass-kompressiya-34-46-mm-rtst-chulki',
                'https://www.diacheck.ru/collection/diaksessuary',
                'https://www.diacheck.ru/collection/drugie-tovary',
                'https://www.diacheck.ru/collection/batareyki',
                'https://www.diacheck.ru/collection/vesy',
                'https://www.diacheck.ru/collection/diagnosticheskie-kompleksy',
                'https://www.diacheck.ru/collection/zvukovye-zubnye-schetki',
                'https://www.diacheck.ru/collection/irrigatory',
                'https://www.diacheck.ru/collection/massazhery',
                'https://www.diacheck.ru/collection/retsirkulyatory',
                'https://www.diacheck.ru/collection/solevye-grelki',
                'https://www.diacheck.ru/collection/stetoskopy',
                'https://www.diacheck.ru/collection/aerodivany',
                'https://www.diacheck.ru/collection/izdeliya-iz-verblyuzhiey-shersti',
                'https://www.diacheck.ru/collection/miniholodilniki-dlya-lekarstv',
                'https://www.diacheck.ru/collection/noski-dlya-diabetikov',
                'https://www.diacheck.ru/collection/ortopedicheskie-izdeliya',
                'https://www.diacheck.ru/collection/ortopedicheskie-izdeliya-ortopedicheskie-stelki',
                'https://www.diacheck.ru/collection/gelevye-prisposobleniya-dlya-stopy',
                'https://www.diacheck.ru/collection/gelevye-prisposobleniya-dlya-stopy',
                'https://www.diacheck.ru/collection/navolochki-dlya-ortopedicheskih-podushek',
                'https://www.diacheck.ru/collection/izdeliya-dlya-sustavov',
                'https://www.diacheck.ru/collection/kolennyy-sustav',
                'https://www.diacheck.ru/collection/izdeliya-dlya-sustavov-luchezapyastnyy-sustav-ortopedicheskie-izdeliya',
                'https://www.diacheck.ru/collection/pyastno-falangovyy-sustav',
                'https://www.diacheck.ru/collection/sustavy-stopy',
                'https://www.diacheck.ru/collection/izdeliya-dlya-pozvonochnika',
                'https://www.diacheck.ru/collection/sheynyy-otdel',
                'https://www.diacheck.ru/collection/gimnasticheskie-myachi',
                'https://www.diacheck.ru/collection/meditsinskie-i-profilakticheskie-bandazhi',
                'https://www.diacheck.ru/collection/bandazhi-na-grudnuyu-kletku-meditsinskie-i-profilakticheskie-bandazhi',
                'https://www.diacheck.ru/collection/bandazhi-na-bryushnuyu-stenku-meditsinskie-i-profilakticheskie-bandazhi',
                'https://www.diacheck.ru/collection/bandazhi-gryzhevye-meditsinskie-i-profilakticheskie-bandazhi',
                'https://www.diacheck.ru/collection/sportivnye-ortezy',
                'https://www.diacheck.ru/collection/massazhnye-podushki-i-trenazhery',
                'https://www.diacheck.ru/collection/sredstva-dlya-dezinfektsii',
                'https://www.diacheck.ru/collection/sredstva-reabilitatsii',
                'https://www.diacheck.ru/collection/kresla-kolyaski',
                'https://www.diacheck.ru/collection/hodunki-i-trosti',
                'https://www.diacheck.ru/collection/sanitarnoe-osnaschenie',
                'https://www.diacheck.ru/collection/funktsionalnye-krovati',
                'https://www.diacheck.ru/collection/protivoprolezhnevye-sistemy',
                'https://www.diacheck.ru/collection/sredstva-dlya-uhoda-za-polostyu-rta',
                'https://www.diacheck.ru/collection/sredstva-vvedeniya-insulina',
                'https://www.diacheck.ru/collection/insulinovye-shpricy',
                'https://www.diacheck.ru/collection/sredstva-kupirovaniya-gipoglikemii',
                'https://www.diacheck.ru/collection/termometry',
                'https://www.diacheck.ru/collection/tovary-dlya-beremennyh',
                'https://www.diacheck.ru/collection/tovary-dlya-malyshey',
                'https://www.diacheck.ru/collection/shagomery'
            ),
            'раствор': (
                'https://www.diacheck.ru/collection/kontrolnye-rastvory',
            ),
            'ручка': (
                'https://www.diacheck.ru/collection/shprits-ruchki',
                'https://www.diacheck.ru/collection/igly',
            ),
            'тест': (
                'https://www.diacheck.ru/collection/testy_na_vich',
                'https://www.diacheck.ru/collection/test_na_beremennost',
                'https://www.diacheck.ru/collection/struynye-testy-na-beremennost',
                'https://www.diacheck.ru/collection/ekspress_testy_na_infektsii',
                'https://www.diacheck.ru/collection/ekspress-testy-na-gripp',
                'https://www.diacheck.ru/collection/ekspress-testy-na-sifilis',
                'https://www.diacheck.ru/collection/testy-na-gepatit',
                'https://www.diacheck.ru/collection/test_na_ovulyatsiyu',
                'https://www.diacheck.ru/collection/testy_na_narkotiki',
                'https://www.diacheck.ru/collection/testy-na-barbituraty',
                'https://www.diacheck.ru/collection/testy-na-marihuanu',
            ),
            'тонометр': (
                'https://www.diacheck.ru/collection/tonometry',
                'https://www.diacheck.ru/collection/avtomaticheskie-tonometry',
                'https://www.diacheck.ru/collection/poluavtomaticheskie-tonometry',
                'https://www.diacheck.ru/collection/zapyastnye-tonometry',
                'https://www.diacheck.ru/collection/mehanicheskie-tonometry',
                'https://www.diacheck.ru/collection/fonendoskopy',
                'https://www.diacheck.ru/collection/manzhety',
            ),
            'услуга': (
                'https://www.diacheck.ru/collection/uslugi',
            ),
            'чехол': (
                'https://www.diacheck.ru/collection/chehly-dlya-glyukometrov',
                'https://www.diacheck.ru/collection/chehly-frio',
            ),
        }
    
    def det_blocks(self, soup):
        blocks = soup.find_all('div', {"class": "product-card-inner"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("a", {"class": "product-link"}).text.strip()
        res['url'] = 'https://www.diacheck.ru' + block.find('link').attrs['href']
        price_s = block.find("div", {"class": "price in-card"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class DiabeticShop(Shop):
    def __init__(self):
        self.shop_name = "Diabetic Shop"
        self.shop_id = 7
        self.page_list = {
            'витамин': (
                'https://diabetic-shop.ru/vitaminy',
            ),
            'глюкометр': (
                'https://diabetic-shop.ru/glyukometry',
            ),
            'еда': (
                'https://diabetic-shop.ru/produkty-dlya-diabetikov',
                'https://diabetic-shop.ru/nizkouglevodnaya-eda',
            ),
            'ланцет': (
                'https://diabetic-shop.ru/lantsety-ruchki-dlya-prokalyvaniya',
            ),
            'косметика': (
                'https://diabetic-shop.ru/kosmetika',
            ),
            'полоска': (
                'https://diabetic-shop.ru/test-poloski',
                'https://diabetic-shop.ru/vizualnye-test-poloski',
            ),
            'помпа': (
                'https://diabetic-shop.ru/insulinovye-pompy-i-raskhodnye-materialy-aksessuary',
            ),
            'разное': (
                'https://diabetic-shop.ru/dezinfektsiya',
                'https://diabetic-shop.ru/aksessuary',
                'https://diabetic-shop.ru/sredstva-pri-gipoglikemii',
                'https://diabetic-shop.ru/tovary-dlya-doma',
                'https://diabetic-shop.ru/novinki',
                'https://diabetic-shop.ru/rasprodazha',
            ),
            'ручка': (
                'https://diabetic-shop.ru/shprits-ruchki-igly-shpritsy',
            ),
            'чехол': (
                'https://diabetic-shop.ru/termochekhly-dlya-insulina',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "block_product"})
        if len(blocks) > 0:
            pagination = soup.find("li", {"class": "pagination-next"})
            if pagination:
                pagination = pagination.find("a")
                if pagination:
                    try:
                        pag_href = 'https://diabetic-shop.ru' + pagination.attrs['href']
                        next_soup = get_soup(pag_href)
                        blocks += self.det_blocks(next_soup)
                    except:
                        pass
        return blocks
    
    def parse_block(self, block):
        res = dict()
        name_block = block.find("div", {"class": "name"}).find("a")
        res['title'] = name_block.text.strip()
        res['url'] = "https://diabetic-shop.ru" + name_block.attrs['href']
        price_s = block.find("div", {"class": "jshop_price"}).text.strip()
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = not bool(block.find("div", {"class": "not_available"}).text.strip())
        man_block = block.find("div", {"class": "manufacturer_name"})
        if man_block:
            res["manuf"] = man_block.find("span").text.strip()
        return res
        

class DiaLife(Shop):
    def __init__(self):
        self.shop_name = "Диалайф"
        self.shop_id = 8
        self.page_list = {    
            'анализатор': (
                'https://shop-dia.ru/catalog/analizatory/?count=200',
            ),
            'бинт': (
                'https://shop-dia.ru/catalog/plastyri-rocktape-kinezioteyp/?count=200',
                'https://shop-dia.ru/catalog/plastyri-rocktape-kinezioteyp-design/?count=200',
            ),
            'глюкометр': (
                'https://shop-dia.ru/catalog/glyukometry/?count=200',
            ),
            'еда': (
                'https://shop-dia.ru/catalog/fitochay/?count=200',
                'https://shop-dia.ru/catalog/zdorovoe-pitanie/?count=200',
                'https://shop-dia.ru/catalog/sakharozameniteli/?count=200',
            ),
            'ланцет': (
                'https://shop-dia.ru/catalog/igly-dlya-shprits-ruchek/?count=200',
            ),
            'косметика': (
                'https://shop-dia.ru/catalog/ukhazhivayushchaya-kosmetika/?count=200',
                'https://shop-dia.ru/catalog/ukhod-za-polostyu-rta/?count=200',
            ),
            'литература': (
                'https://shop-dia.ru/catalog/knigi-o-diabete/',
            ),
            'полоска': (
                'https://shop-dia.ru/catalog/test-poloski/?count=200',
                'https://shop-dia.ru/catalog/vizualnye-test-poloski/?count=200',
            ),
            'помпа': (
                'https://shop-dia.ru/catalog/insulinovye-pompy/?count=200',
                'https://shop-dia.ru/catalog/raskhodnye-materialy-k-akku-chek/?count=200',
                'https://shop-dia.ru/catalog/raskhodnye-materialy-k-medtronik/?count=200',
                'https://shop-dia.ru/catalog/aksessuary-k-akku-chek/?count=200',
                'https://shop-dia.ru/catalog/aksessuary-k-medtronik/?count=200',
            ),
            'разное': (
                'https://shop-dia.ru/catalog/aktsii-i-skidki/?count=200',
                'https://shop-dia.ru/catalog/dieticheskie-vesy/?count=200',
                'https://shop-dia.ru/catalog/sredstva-ot-gipoglikemii/?count=200',
                'https://shop-dia.ru/catalog/prochie-tovary/?count=200',
                'https://shop-dia.ru/catalog/ukhod-za-kozhey/?count=200',
                'https://shop-dia.ru/catalog/nakleyki/?count=200',
            ),
            'ручка': (
                'https://shop-dia.ru/catalog/shprits-ruchki/?count=200',
            ),
            'тонометр': (
                'https://shop-dia.ru/catalog/tonometry/?count=200',
            ),
            'чехол': (
                'https://shop-dia.ru/catalog/chekhly-dlya-shprits-ruchek/?count=200',
            ),
            'мониторинг': (
                'https://shop-dia.ru/catalog/sistemy-monitorirovaniya/?count=200',
            ),
        }


    def det_blocks(self, soup):
        return soup.find_all("div", {"class": "listing"})
    
    def parse_block(self, block):
        res = dict()
        cb = block.find("div", {"class": "contm"})
        res['title'] = cb.find("h3").text.strip()
        res['url'] = "https://shop-dia.ru" + cb.find("a").attrs["href"]
        price_b = cb.find("span", {"class": "num"})
        if price_b:
            price_s = cb.find("span", {"class": "num"}).text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        else:
            res['available'] = False
        desc = cb.find("div", {"class": "p"})
        if desc:
            res['description'] = desc.text.strip()
        return res


class DiabetCare(Shop):
    def __init__(self):
        self.shop_name = "Diabet Care"
        self.shop_id = 9
        self.page_list = {    
            'анализатор': (
                'https://diabet-ural.ru/catalog/Portativnye-analizatory',
            ),
            'бинт': (
                'https://diabet-ural.ru/catalog/Septiki-i-fiksaciya',
            ),
            'витамин': (
                'https://diabet-ural.ru/catalog/Vitaminy',
            ),
            'глюкометр': (
                'https://diabet-ural.ru/catalog/Glyukometry-i-test-poloski',
            ),
            'еда': (
                'https://diabet-ural.ru/catalog/Vitaminy-zameniteli-sahara-3',
                'https://diabet-ural.ru/catalog/Zdorovoe-pitanie',
            ),
            'ланцет': (
                'https://diabet-ural.ru/catalog/Prokalyvateli-lancety',
            ),
            'косметика': (
                'https://diabet-ural.ru/catalog/Uhod-za-kozhej',
                'https://diabet-ural.ru/catalog/Uhod-za-polostyu-rta',
                'https://diabet-ural.ru/catalog/Intimnaya-gigiena',
            ),
            'литература': (
                'https://diabet-ural.ru/catalog/Literatura',
            ),
            'мониторинг': (
                'https://diabet-ural.ru/catalog/Sutochnyj-monitoring',
            ),
            'полоска': (
                'https://diabet-ural.ru/catalog/Test-poloski',
                'https://diabet-ural.ru/catalog/Vizualnye-test-poloski',
            ),
            'помпа': (
                'https://diabet-ural.ru/catalog/Insulinovye-pompy-3',
                'https://diabet-ural.ru/catalog/Akku-chek',
                'https://diabet-ural.ru/catalog/Medtronik',
            ),
            'разное': (
                'https://diabet-ural.ru/catalog/Gipoglikemiya',
                'https://diabet-ural.ru/catalog/Vesy-kuhonnye',
                'https://diabet-ural.ru/catalog/Vesy-napolnye-diagnosticheskie',
                'https://diabet-ural.ru/catalog/Vesy-diagnosticheskie',
                'https://diabet-ural.ru/catalog/Priboy-po-uhodu-za-kozhej',
                'https://diabet-ural.ru/catalog/Trekery-aktivnosti',
                'https://diabet-ural.ru/catalog/Fizioterapiya',
                'https://diabet-ural.ru/catalog/Massazhery-dlya-shei-i-spiny',
                'https://diabet-ural.ru/catalog/Massazhery-dlya-nog',
            ),
            'ручка': (
                'https://diabet-ural.ru/catalog/Shpric-ruchki',
                'https://diabet-ural.ru/catalog/Igly-dlya-shpric-ruchek-i-shpricy-insulinovye',
            ),
            'тонометр': (
                'https://diabet-ural.ru/catalog/Tonometry',
            ),
            'чехол': (
                'https://diabet-ural.ru/catalog/Chehly-ohlazhdayushhie-Frio',
            ),
        }

    def det_blocks(self, soup):
        return soup.find_all("div", {"class": "product-shop"})
    
    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "product-name"})
        res['url'] = bname.find("a").attrs['href']
        res['title'] = bname.find("a").text.strip()
        
        price_s = block.find("span", {"class": "price RUB"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        desc = block.find("meta", {"itemprop": "description"}).attrs['content']
        if desc:
            res['description'] = desc
        return res


class DiabetMed(Shop):
    def __init__(self):
        self.shop_name = "Diabet Med"
        self.shop_id = 10
        self.page_list = {    
            'анализатор': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/analizator-glikirovanogo-gyemoglobina/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/kardiochek-cardiochek/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/analizator-mno/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/biokhimicheskie-analizatory_1/',
            ),
            'бинт': (
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/lechenie-ran/cetchataya-povyazka-voskopran-s-propitkoy-pchelinym-voskom/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/lechenie-ran/sterilnye-atravmaticheskie-povyazki-parapran/',
            ),
            'витамин': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/vitaminy/',
            ),
            'глюкометр': (
                'https://diabet-med.ru/category/glyukometry/',
            ),
            'еда': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/sakharosnizhayushchie-chai/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/sakharozameniteli/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/steviya/',
                'https://diabet-med.ru/category/tovary-dlya-sporta/sportivnoe-pitanie-powerup-dlya-tsiklicheskikh-i-igrovykh-vidov-sporta/',
                'https://diabet-med.ru/category/dieticheskie-produkty/dzhemy-varene-zhele/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/gotovye-blyuda/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/otrubi/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/sportivnoe-pitanie/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/superfudy-vodorosli/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/kakao-produktsiya-naturalnaya/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/naturalnye-zameniteli-sakhara/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/lnyanye-khlebtsy/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/muka-ekologicheskaya/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/khlopya-ekologicheskie-bez-termicheskoy-obrabotki/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/bakaleya-ekologicheskie-krupy/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/semena-ekologicheskie/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/miksy-semyan-idealno-dlya-salatov/',
                'https://diabet-med.ru/category/dieticheskie-produkty/krupy-zernovye-i-bobovye-kultury/miksy-dlya-prorashchivaniya-mikrozelen/',
                'https://diabet-med.ru/category/dieticheskie-produkty/smuzi-detox-bioaktivnyy-kokteyl/',
                'https://diabet-med.ru/category/dieticheskie-produkty/bakterialnye-zakvaski/'
                'https://diabet-med.ru/category/dieticheskie-produkty/vyrashchivanie-rasteniy/',
                'https://diabet-med.ru/category/dieticheskie-produkty/fitochay/',
                'https://diabet-med.ru/category/dieticheskie-produkty/chai-evalar-bio/',
                'https://diabet-med.ru/category/dieticheskie-produkty/zameniteli-sakhara-naturalnye/',
                'https://diabet-med.ru/category/dieticheskie-produkty/kletchatka/',
                'https://diabet-med.ru/category/dieticheskie-produkty/kletchatka/malenkaya-banka/',
                'https://diabet-med.ru/category/dieticheskie-produkty/kletchatka/bolshaya-banka/',
                'https://diabet-med.ru/category/dieticheskie-produkty/kletchatka/ya-dieta/',
                'https://diabet-med.ru/category/dieticheskie-produkty/kletchatka/kokteyli/',
            ),
            'ингалятор': (
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/ingalyatory-i-nebulayzery/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/ingalyatory-i-nebulayzery/kompressornye/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/ingalyatory-i-nebulayzery/ultrazvukovye/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/ingalyatory-i-nebulayzery/mesh-ingalyatory/',
            ),
            'ланцет': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/avtomaticheskie-lantsety/',
                'https://diabet-med.ru/category/lantsety//',
            ),
            'косметика': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/sredstva-po-ukhodu-za-kozhey/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/sredstva-po-ukhodu-za-polostyu-rta/',
                'https://diabet-med.ru/category/kosmetika/',
                'https://diabet-med.ru/category/kosmetika/asyepta---zdorovye-zuby-i-desny/',
                'https://diabet-med.ru/category/kosmetika/italyanskoe-mylo-ruchnoy-raboty/',
            ),
            'литература': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/literatura-po-diabetu/',
            ),
            'мониторинг': (
                'https://diabet-med.ru/category/medtronik-medtronic/nepreryvnyy-monitoring-glyukozy/',
            ),
            'полоска': (
                'https://diabet-med.ru/category/test-poloski-dlya-priborov/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/test-poloski-k-analizatoram/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/oftalmologicheskie-test-poloski/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/vizualnye-test-poloski/',
            ),
            'помпа': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/insulinovye-pompy-i-aksessuary/',
                'https://diabet-med.ru/category/medtronik-medtronic/pompovaya-insulinoterapiya/',
                'https://diabet-med.ru/category/medtronik-medtronic/sertery/',
                'https://diabet-med.ru/category/medtronik-medtronic/rezervuary/',
                'https://diabet-med.ru/category/medtronik-medtronic/raskhodnye-materialy-quick-set/',
                'https://diabet-med.ru/category/medtronik-medtronic/raskhodnye-materialy-mio/',
                'https://diabet-med.ru/category/medtronik-medtronic/ustroystva-dlya-infuzii-sure-t/',
                'https://diabet-med.ru/category/medtronik-medtronic/raskhodnye-materialy-silhouette/',
                'https://diabet-med.ru/category/medtronik-medtronic/inektsionnyy-port/',
                'https://diabet-med.ru/category/medtronik-medtronic/aksessuary/',
                'https://diabet-med.ru/category/insulinovye-pompy-akku-chyek-accu-chek/igly-dlya-pompy-akkuchek-accu-chek/',
                'https://diabet-med.ru/category/insulinovye-pompy-akku-chyek-accu-chek/nabor-infuzionnyy-akkuchek-accu-chek/',
                'https://diabet-med.ru/category/insulinovye-pompy-akku-chyek-accu-chek/raskhodnye-materialy-dlya-pomp-akku-chyek-accu-chek/',
                'https://diabet-med.ru/category/insulinovye-pompy-akku-chyek-accu-chek/udliniteli-akku-chyek-accu-chek/',
                'https://diabet-med.ru/category/insulinovye-pompy-akku-chyek-accu-chek/chekhly-dlya-pomp-akku-chyek-accu-chek/',
            ),
            'разное': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/shpritsy-insulinovye/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/dezinfektsiya/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/noski-dlya-diabetikov_1/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/sredstva-kupirovaniya-gipoglikemii/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/braslety-u-menya-diabet/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/elementy-pitaniya-dlya-glyukometrov_1/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/diabet-u-zhivotnykh/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/soputstvuyushchie-tovary/',
                'https://diabet-med.ru/category/tovary-dlya-sporta/begovye-ryukzaki-poyasa-i-zhilety/',
                'https://diabet-med.ru/category/tovary-dlya-sporta/sportivnye-poyasnye-sumki/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/bandazhi/bandazhi-pri-gryzhe/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/bandazhi/posleoperatsionnye-bandazhi/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/izdeliya-dlya-pozvonochnika/korsety/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/izdeliya-dlya-pozvonochnika/korrektory-osanki/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/izdeliya-dlya-pozvonochnika/sheynye-vorotniki/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/podushki-dlya-detey/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/podushki-pod-nogi/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/podushki-na-sidene/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/podushki-dlya-beremennykh/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/ortopedicheskie-podushki-pod-spinu/',
                'https://diabet-med.ru/category/ortopedicheskie-izdeliya_1/ortopedicheskie-podushki/ortopedicheskie-podushki-dlya-puteshestviy/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/protivoprolezhnevye-matrasy/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/prisposobleniya-dlya-vannykh-i-tualetnykh-komnat/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/kresla-tualety/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/opory-khodunki/',
                'https://diabet-med.ru/category/reabilitatsiya-i-ukhod/kresla-kolyaski/',
                'https://diabet-med.ru/category/spetsialnoe-bele/',
                'https://diabet-med.ru/category/spetsialnoe-bele/vpityvayushchee-bele/',
                'https://diabet-med.ru/category/spetsialnoe-bele/noski/',
                'https://diabet-med.ru/category/dlya-meduchrezhdeniy/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/dieticheskie/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/napolnye-elektronnye/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/kukhonnye/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/lyubaya/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/detskie/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/zhiroanalizatory/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/bezmeny-elektronnye/',
                'https://diabet-med.ru/category/profilaktika-i-kontrol/vesy/vesy-dlya-zhivotnykh/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/massazhnye-podushki/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/vakuumnye-banki/',
                'https://diabet-med.ru/category/tovary-dlya-zdorovya/domashnie-aptechki/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/gigrometry/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/ionizatsiya-vozdukha/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/uvlazhniteli-vozdukha/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/dykhatelnye-trenazhery/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/kislorodnye-kontsentratory/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/kislorodnye-podushki/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/kislorodnye-kokteylery/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/kislorodnye-ballonchiki/',
                'https://diabet-med.ru/category/tovary-dlya-dykhaniya/aromatizatory-vozdukha/',
            ),
            'раствор': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/kontrolnye-rastvory/',
            ),
            'ручка': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/avtolantsety/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/shprits-ruchki/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/igly-k-shprits-ruchkam/',
            ),
            'тест': (
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/testy-na-narkotiki/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/testy-na-zabolevaniya/',
                'https://diabet-med.ru/category/biokhimicheskie-analizatory/testy-dlya-zhenshchin/',
            ),
            'чехол': (
                'https://diabet-med.ru/category/diabeticheskie-tovary/termo-sumki-termochekhly-minikholodilniki/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/produktsiya-diabet-aksessuar/',
                'https://diabet-med.ru/category/diabeticheskie-tovary/chekhly-dlya-glyukometrov_1/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("li", {"class": "item"})
        pagination = soup.find("a", {"class": "inline-link"})
        if pagination and (pagination.text == '→'):
            url = 'https://diabet-med.ru' + pagination.attrs['href']
            blocks += self.det_blocks(get_soup(url))
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.find("a")
        res['title'] = bname.attrs['title']
        res['url'] = 'https://diabet-med.ru' + bname.attrs['href']
        price_s = block.find("span", {"class": "total"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        desc = block.find("div", {"class": "opus_block"})
        if desc:
            res['description'] = desc.text
        return res
        

class DiabetaNet(Shop):
    def __init__(self):
        self.shop_name = "Diabeta Net"
        self.shop_id = 11
        self.page_list = {
            'анализатор': (
                'http://diabeta.net.ru/shop/analizatory-krovi',
            ),
            'витамин': (
                'http://diabeta.net.ru/shop/vitaminy',
            ),
            'глюкометр': (
                'http://diabeta.net.ru/shop/onetouch-select',
                'http://diabeta.net.ru/shop/diakont',
                'http://diabeta.net.ru/shop/contour-plus',
                'http://diabeta.net.ru/shop/accu-chek',
                'http://diabeta.net.ru/shop/ajchek',
                'http://diabeta.net.ru/shop/ebsensor',
                'http://diabeta.net.ru/shop/freestyle-optium',
                'http://diabeta.net.ru/shop/satellit',
            ),
            'еда': (
                'http://diabeta.net.ru/shop/saharozameniteli',
                'http://diabeta.net.ru/shop/semena-i-poleznoe-pitanie',
                'http://diabeta.net.ru/shop/siropy-i-chajnye-nabory',
            ),
            'ингалятор': (
                'http://diabeta.net.ru/shop/ingaljatory',
            ),
            'ланцет': (
                'http://diabeta.net.ru/shop/lantsety',
            ),
            'косметика': (
                'http://diabeta.net.ru/shop/zubnye-pasty-i-opolaskivateli',
                'http://diabeta.net.ru/shop/krema-i-mylo',
            ),
            'помпа': (
                'http://diabeta.net.ru/shop/akku-chek',
                'http://diabeta.net.ru/shop/medtronik',
            ),
            'разное': (
                'http://diabeta.net.ru/shop/kosmetologija',
                'http://diabeta.net.ru/shop/obluchateli-i-apparaty-magnitoterapii',
                'http://diabeta.net.ru/shop/matrasy',
                'http://diabeta.net.ru/shop/trosti',
                'http://diabeta.net.ru/shop/massazhery',
                'http://diabeta.net.ru/shop/kontsentratory',
                'http://diabeta.net.ru/shop/vozduhoochestiteli',
                'http://diabeta.net.ru/shop/vozduhoochistiteli-uvlazhniteli',
                'http://diabeta.net.ru/shop/klimaticheskie-kompleksy',
                'http://diabeta.net.ru/shop/vozduhoochistiteli-ionizatory',
                'http://diabeta.net.ru/shop/ochistiteli-aromatizatory-vozduha',
                'http://diabeta.net.ru/shop/uvlazhniteli-vozduha',
                'http://diabeta.net.ru/shop/soljanye-lampy',
                'http://diabeta.net.ru/shop/spetsialnye-predlozhenija',
                'http://diabeta.net.ru/shop/spirtovye-salfetki_',
                'http://diabeta.net.ru/shop/hypofree',
                'http://diabeta.net.ru/shop/dekstro',
                'http://diabeta.net.ru/shop/aksessuary'
            ),
            'ручка': (
                'http://diabeta.net.ru/shop/prokalyvateli-shprits-ruchki',
            ),
            'тонометр': (
                'http://diabeta.net.ru/shop/tonometry',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "static-grid-item"})
        pagination = soup.find("div", {"class": "products-list-pagination f__s_category"})
        if pagination:
            pagination = soup.find("div", {"class": "products-list-pagination f__s_category"}).find_all("a")[1:-1]
            if pagination:
                for block in pagination:
                    blocks += get_soup(block.attrs['href']).find_all("div", {"class": "static-grid-item"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("div", {"class": "product-name"}).text
        res['url'] = block.find("a").attrs['href']
        price_s = block.find("div", {"class": "product-price"}).find_all("span")[-1].text.strip()
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class Diapuls(Shop):
    def __init__(self):
        self.shop_name = "Диа-Пульс"
        self.shop_id = 12
        self.page_list = {    
            'анализатор': (
                'https://diapuls.ru/category/biohimicheskie-analizatory/',
            ),
            'глюкометр': (
                'https://diapuls.ru/category/gljukometry/',
            ),
            'еда': (
                'https://diapuls.ru/category/zdorovoe-pitanie/',
            ),
            'ингалятор': (
                'https://diapuls.ru/category/dopolnitelnye-prinadlezhnosti-k-ingaljatoram-i-nebulajzeram-/',
                'https://diapuls.ru/category/pikfloumetry-i-prinadlezhnosti-k-nim/',
            ),
            'ланцет': (
                'https://diapuls.ru/category/avtomaticheskie-lancety/',
                'https://diapuls.ru/category/lancety-dlja-ruchek-prokalyvatelej/',
            ),
            'косметика': (
                'https://diapuls.ru/category/lechenie_gd/',
                'https://diapuls.ru/category/uhod-za-nogami/',
                'https://diapuls.ru/category/opolaskivateli/',
                'https://diapuls.ru/category/saharozameniteli-i-sredstva-dlja-snizhenija-vesa/',
            ),
            'литература': (
                'https://diapuls.ru/category/knigi/',
            ),
            'полоска': (
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=342',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=343',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=344',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=345',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=346',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=347',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=348',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=349',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=350',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=37',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=38',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=39',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=40',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=42',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=43',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=45',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=47',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=49',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=51',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=52',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=53',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=54',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=55',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=56',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=57',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=58',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=302',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=303',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=304',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=305',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=306',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=307',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=403',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=351&brand%5B%5D=404',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=353',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=360',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=363',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=364',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=367',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=368',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=369',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=370',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=371',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=373',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=375',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=377',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=378',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=380',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=381',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=382',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=384',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=385',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=386',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=387',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=390',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=391',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=392',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=393',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=394',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=396',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=397',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=398',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=399',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=400',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=401',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=405',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=407',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=408',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=409',
                'https://diapuls.ru/category/test-poloski/?chto_ishchem_ili_meryaem%5B%5D=618',
            ),
            'помпа': (
                'https://diapuls.ru/category/insulinovie-pompi/?chto_ishchem_%5B%5D=411',
                'https://diapuls.ru/category/insulinovie-pompi/?chto_ishchem_%5B%5D=412',
                'https://diapuls.ru/category/insulinovie-pompi/?chto_ishchem_%5B%5D=413',
            ),
            'разное': (
                'https://diapuls.ru/category/vesi-giroanalizator/',
                'https://diapuls.ru/category/prochie-tovary/',
                'https://diapuls.ru/category/antiseeptiki/',
                'https://diapuls.ru/category/salfetki/',
                'https://diapuls.ru/category/prinadlezhnosti-dlya-slukhovykh-apparatov/',
                'https://diapuls.ru/category/slukhovye-apparaty/',
                'https://diapuls.ru/category/zubnye-shetki/',
                'https://diapuls.ru/category/irrigatory-i-nasadki-dlya-nikh/',
                'https://diapuls.ru/category/sredstva-cupirovania-gipoglimi/',
                'https://diapuls.ru/category/stetofonendoskopy/',
                'https://diapuls.ru/category/termometry/',
                'https://diapuls.ru/category/shpric-ruchki-igli-shprici/',
                'https://diapuls.ru/category/shpric-ruchki-i-igly-k-shpric-ruchkam/',
                'https://diapuls.ru/category/shpricy/',
                'https://diapuls.ru/category/elektromassazhery-vibromassazhery/',
            ),
            'раствор': (
                'https://diapuls.ru/category/kontrolnye-rastvory/',
            ),
            'ручка': (
                'https://diapuls.ru/category/ruchki-dlja-prokalyvanija/',
            ),
            'тест': (
                'https://diapuls.ru/category/alkotestery/',
            ),
            'тонометр': (
                'https://diapuls.ru/category/dopolnitelnye-prinadlezhnosti-k-tonometram/',
                'https://diapuls.ru/category/dopolnitelnye-prinadlezhnosti-k-avtomatichekim-i-poluavtomaticheskim-tonometram/',
                'https://diapuls.ru/category/tonometry/',
            ),
            'чехол': (
                'https://diapuls.ru/category/insulinovie-pompi/?chto_ishchem_%5B%5D=410',
            ),
        }


    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "product"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "product_name"})
        res['url'] = 'https://diapuls.ru' + bname.a.attrs['href']
        res['title'] = bname.text.strip()
        price_s = block.find("span", {"class": "price"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = not ('no' in block.find("div", {"class": "stock"}).attrs['class'])       
        return res


class Diabeton(Shop):
    def __init__(self):
        self.shop_name = "Диабетон"
        self.shop_id = 13
        self.page_list = {    
            'анализатор': (
                'https://sc-diabeton.ru/store/laboratornaya-tehnika/?psize=all',
            ),
            'бинт': (
                'https://sc-diabeton.ru/store/fiksatory-sustavov/?psize=all',
            ),
            'витамин': (
                'https://sc-diabeton.ru/store/vitaminy/?psize=all',
            ),
            'глюкометр': (
                'https://sc-diabeton.ru/store/glukometry/?psize=all',
            ),
            'еда': (
                'https://sc-diabeton.ru/store/zameniteli-sahara/?psize=all',
                'https://sc-diabeton.ru/store/chai/?psize=all',
                'https://sc-diabeton.ru/store/poleznyj-perekus/?psize=all',
                'https://sc-diabeton.ru/store/bakaleya/?psize=all',
                'https://sc-diabeton.ru/store/nizkouglevodnye-sladosti/?psize=all',
            ),
            'ингалятор': (
                'https://sc-diabeton.ru/store/ingalyatory/?psize=all',
            ),
            'ланцет': (
                'https://sc-diabeton.ru/store/ustroystva-dlya-prokalyvaniya/?psize=all',
            ),
            'косметика': (
                'https://sc-diabeton.ru/store/kosmeticheskie-sredstva/?psize=all',
                'https://sc-diabeton.ru/store/detskaya-seriya/?psize=all',
            ),
            'литература': (
                'https://sc-diabeton.ru/store/knigi/?psize=all',
            ),
            'полоска': (
                'https://sc-diabeton.ru/store/test-poloski/?psize=all',
                'https://sc-diabeton.ru/store/visualnye-test-poloski/?psize=all',
            ),
            'помпа': (
                'https://sc-diabeton.ru/store/pompy/?psize=all',
            ),
            'разное': (
                'https://sc-diabeton.ru/store/dev-inject/?psize=all',
                'https://sc-diabeton.ru/store/dlya-lecheniya-gipoglikemii/?psize=all',
                'https://sc-diabeton.ru/store/massazhery/?psize=all',
                'https://sc-diabeton.ru/store/apparaty-dlya-lecheniya/?psize=all',
                'https://sc-diabeton.ru/store/tekstilnye-izdeliya/?psize=all',
                'https://sc-diabeton.ru/store/medicinskie-izdeliya/?psize=all',
                'https://sc-diabeton.ru/store/pulsometry-shagomery/?psize=all',
                'https://sc-diabeton.ru/store/vesy/?psize=all',
                'https://sc-diabeton.ru/store/termometry/?psize=all',
                'https://sc-diabeton.ru/store/applikatory/?psize=all',
                'https://sc-diabeton.ru/store/irrigatory-zubnyye-shchetki/?psize=all',
                'https://sc-diabeton.ru/store/uvlazhniteli-vozduha-ochistiteli/?psize=all',
                'https://sc-diabeton.ru/store/baktericidnye-obluchateli-lampy/?psize=all',
                'https://sc-diabeton.ru/store/lampy/?psize=all',
                'https://sc-diabeton.ru/store/grelki/?psize=all',
                'https://sc-diabeton.ru/store/ozonatory-oserebriteli/?psize=all',
                'https://sc-diabeton.ru/store/ledokhodi/?psize=all',
                'https://sc-diabeton.ru/store/darsonval/?psize=all',
                'https://sc-diabeton.ru/store/manikyurno-pedikyurnie-nabory/?psize=all',
                'https://sc-diabeton.ru/store/uhod-za-kozhej/?psize=all',
                'https://sc-diabeton.ru/store/izdeliya-dlya-stopy/?psize=all',
                'https://sc-diabeton.ru/store/kompressionnyj-trikotazh/?psize=all',
                'https://sc-diabeton.ru/store/ortopedicheskie-podushki/?psize=all',
                'https://sc-diabeton.ru/store/trosti-kostyli/?psize=all',
                'https://sc-diabeton.ru/store/korsety-bandazhi-korrekciya-osanki/?psize=all',
            ),
            'тест': (
                'https://sc-diabeton.ru/store/alkotestery/?psize=all',
                'https://sc-diabeton.ru/store/kontrol-sredy/?psize=all',
            ),
            'тонометр': (
                'https://sc-diabeton.ru/store/tonometry/?psize=all',
            ),
            'чехол': (
                'https://sc-diabeton.ru/store/termo-sumki-frio-chehly/?psize=all',
            ),
        }

    def parse_page(self, url):
        soup = get_soup(url, True)
        blocks = self.det_blocks(soup)
        res = list()
        if blocks:
            for block in blocks:
                parsed = self.parse_block(block)
                res.append(parsed)
        return res
    
    def det_blocks(self, soup):
        blocks = soup.find("ul", {"class": "store-items"}).find_all("li")
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res['title'] = block.img.attrs['title']
        res['url'] = 'https://sc-diabeton.ru' + block.a.attrs['href']
        price_s = block.strong.text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = not ('нет' in block.find("div", {"class": "submit"}).text.lower())
        return res
        

class Glukoza(Shop):
    def __init__(self):
        self.shop_name = "Глюкоза"
        self.shop_id = 14
        self.page_list = {    
            'анализатор': (
                'https://glukoza-med.ru/index.php?page=cat&cat=8',
            ),
            'бинт': (
                'https://glukoza-med.ru/index.php?page=cat&cat=27',
            ),
            'глюкометр': (
                'https://glukoza-med.ru/index.php?page=cat&cat=2',
            ),
            'еда': (
                'https://glukoza-med.ru/index.php?page=cat&cat=106',
                'https://glukoza-med.ru/index.php?page=cat&cat=21',
                'https://glukoza-med.ru/index.php?page=cat&cat=52',
                'https://glukoza-med.ru/index.php?page=cat&cat=109',
            ),
            'ингалятор': (
                'https://glukoza-med.ru/index.php?page=cat&cat=28',
            ),
            'ланцет': (
                'https://glukoza-med.ru/index.php?page=cat&cat=5',
            ),
            'косметика': (
                'https://glukoza-med.ru/index.php?page=cat&cat=100',
                'https://glukoza-med.ru/index.php?page=cat&cat=26',
            ),
            'литература': (
                'https://glukoza-med.ru/index.php?page=cat&cat=33',
            ),
            'мониторинг': (
                'https://glukoza-med.ru/index.php?page=cat&cat=46',
            ),
            'полоска': (
                'https://glukoza-med.ru/index.php?page=cat&cat=3',
                'https://glukoza-med.ru/index.php?page=cat&cat=48',
            ),
            'помпа': (
                'https://glukoza-med.ru/index.php?page=cat&cat=9',
                'https://glukoza-med.ru/index.php?page=cat&cat=34',
            ),
            'разное': (
                'https://glukoza-med.ru/index.php?page=cat&cat=12',
                'https://glukoza-med.ru/index.php?page=cat&cat=18',
                'https://glukoza-med.ru/index.php?page=cat&cat=11',
                'https://glukoza-med.ru/index.php?page=cat&cat=45',
                'https://glukoza-med.ru/index.php?page=cat&cat=43',
                'https://glukoza-med.ru/index.php?page=cat&cat=19',
                'https://glukoza-med.ru/index.php?page=cat&cat=24',
                'https://glukoza-med.ru/index.php?page=cat&cat=20',
                'https://glukoza-med.ru/index.php?page=cat&cat=85',
                'https://glukoza-med.ru/index.php?page=cat&cat=65',
                'https://glukoza-med.ru/index.php?page=cat&cat=66',
                'https://glukoza-med.ru/index.php?page=cat&cat=68',
                'https://glukoza-med.ru/index.php?page=cat&cat=116',
                'https://glukoza-med.ru/index.php?page=cat&cat=117',
                'https://glukoza-med.ru/index.php?page=cat&cat=29',
                'https://glukoza-med.ru/index.php?page=cat&cat=37',
                'https://glukoza-med.ru/index.php?page=cat&cat=54',
                'https://glukoza-med.ru/index.php?page=cat&cat=104',
                'https://glukoza-med.ru/index.php?page=cat&cat=73',
                'https://glukoza-med.ru/index.php?page=cat&cat=107',
                'https://glukoza-med.ru/index.php?page=cat&cat=108',
                'https://glukoza-med.ru/index.php?page=cat&cat=110',
                'https://glukoza-med.ru/index.php?page=cat&cat=102',
                'https://glukoza-med.ru/index.php?page=cat&cat=101',
                'https://glukoza-med.ru/index.php?page=cat&cat=31',
                'https://glukoza-med.ru/index.php?page=cat&cat=36',
                'https://glukoza-med.ru/index.php?page=cat&cat=35',
                'https://glukoza-med.ru/index.php?page=cat&cat=76',
                'https://glukoza-med.ru/index.php?page=cat&cat=90',
                'https://glukoza-med.ru/index.php?page=cat&cat=96',
                'https://glukoza-med.ru/index.php?page=cat&cat=87',
                'https://glukoza-med.ru/index.php?page=cat&cat=64',
            ),
            'раствор': (
                'https://glukoza-med.ru/index.php?page=cat&cat=7',
            ),
            'ручка': (
                'https://glukoza-med.ru/index.php?page=cat&cat=6',
                'https://glukoza-med.ru/index.php?page=cat&cat=44',
                'https://glukoza-med.ru/index.php?page=cat&cat=14',
            ),
            'тонометр': (
                'https://glukoza-med.ru/index.php?page=cat&cat=23',
            ),
        }


    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "product_wrap"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("a", {"class": "product_name"}).text.strip()
        res['url'] = 'https://glukoza-med.ru/index.php?page=cat&cat=2&idTov=' + re.search(r"\d+", block.find("span", {"class": "text-muted"}).text)[0]
        price_s = block.find("span", {"class": "font-s16"})
        if price_s:
            price_s = price_s.text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        res['available'] = not ('отс' in block.span.text.lower())
        desc = block.find("div", {"class": "product_desc"})
        if desc:
            res['description'] = desc.text
        return res
        

class Betar(Shop):
    def __init__(self):
        self.shop_name = "Бетар Компани"
        self.shop_id = 15
        self.page_list = {    
            'глюкометр': (
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/nabory/',
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/nabory/?p=1',
            ),
            'косметика': (
                'https://betarcompany.ru/katalog/kremy/diaderm/',
                'https://betarcompany.ru/katalog/kremy/diaul_traderm/',
            ),
            'мониторинг': (
                'https://betarcompany.ru/katalog/sistemy_monitorirovaniya_glyukozy_krovi/',
            ),
            'полоска': (
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/testpoloski_dlya_glyukometrov/',
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/testpoloski_dlya_glyukometrov/?p=1',
            ),
            'помпа': (
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/',
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/?p=1',
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/?p=2',
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/?p=3',
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/?p=4',
                'https://betarcompany.ru/katalog/insulinovye_pompy/diabeticheskie_tovary/?p=5',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/?p=1',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/?p=2',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/?p=3',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/?p=4',
                'https://betarcompany.ru/katalog/insulinovye_pompy/roche/?p=5',
            ),
            'разное': (
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/aksessuary/',
                'https://betarcompany.ru/katalog/glyukometry_i_analizatory_mno/aksessuary/?p=1',
                'https://betarcompany.ru/katalog/sredstva_pri_gipoglikemii/',
                'https://betarcompany.ru/katalog/sredstva_pri_gipoglikemii/?p=1',
                'https://betarcompany.ru/katalog/antisepticheskie_sredstva/',
            ),
            'чехол': (
                'https://betarcompany.ru/katalog/termo-chehly/',
                'https://betarcompany.ru/katalog/termo-chehly/?p=1',
                'https://betarcompany.ru/katalog/tovary_dlya_zdorovya/uhod_za_kozhej_nog/',
            ),
        }


    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "allitemcontent"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("div", {"class": "caption"}).text
        res['url'] = 'https://betarcompany.ru' + block.a.attrs['href']
        price_s = block.find("div", {"class": "price red"}).text.strip()
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = bool(block.find("div", {"class": "go_basket"}))
        desc = block.find("div", {"class": "info"})
        if desc:
            res['description'] = desc.text.strip()
        return res


class Diateh(Shop):
    def __init__(self):
        self.shop_name = "Диатех"
        self.shop_id = 16
        self.page_list = {    
            'глюкометр': (
                'https://diatex.net/glucometers',
            ),
            'еда': (
                'https://diatex.net/saharozameniteli',
                'https://diatex.net/superfuds',
                'https://diatex.net/chay',
            ),
            'ланцет': (
                'https://diatex.net/avtoprokalyvateli-lancets',
            ),
            'косметика': (
                'https://diatex.net/creams',
            ),
            'полоска': (
                'https://diatex.net/test-strips',
            ),
            'помпа': (
                'https://diatex.net/insulinovye-pompy-rashodnye-materialy/raskhodnye-materialy-dlya-kombo',
                'https://diatex.net/insulinovye-pompy-rashodnye-materialy/raskhodnye-materialy-dlya-medtronik',
            ),
            'разное': (
                'https://diatex.net/igly-insulinovye',
                'https://diatex.net/prochie-tovary',
            ),
            'ручка': (
                'https://diatex.net/shprits-ruchki',
            ),
        }

    def det_blocks(self, soup):
        blocks = [block.parent for block in soup.find_all("div", {"class": "name"})]
        return blocks

    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "name"})
        res['title'] = bname.text
        res['url'] = bname.a.attrs['href']
        price_s = block.find("span", {"class": "price-new"})
        if price_s:
            price_s = price_s.text.strip()
        else:
            price_s = block.find("div", {"class": "price"}).text.strip().split('\n')[0]
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = not bool(block.find("img", {"class": "outofstock"}))
        desc = block.find("div", {"class": "description"})
        if desc:
            res['description'] = desc.text
        return res


class Satellit(Shop):
    def __init__(self):
        self.shop_name = "Сателлит"
        self.shop_id = 17
        self.page_list = {    
            'анализатор': (
                'https://satellit-tsc.ru/pribor-dlya-izmereniya-kholesterina',
            ),
            'бинт': (
                'https://satellit-tsc.ru/shop/kinezio-teypy',
            ),
            'витамин': (
                'https://satellit-tsc.ru/vitaminy-1',
            ),
            'глюкометр': (
                'https://satellit-tsc.ru/glyukometry',
            ),
            'еда': (
                'https://satellit-tsc.ru/pitaniye-i-vitaminy',
            ),
            'ингалятор': (
                'https://satellit-tsc.ru/ingalyatory-1',
            ),
            'ланцет': (
                'https://satellit-tsc.ru/ustroystva-dlya-prokalyvaniya',
            ),
            'косметика': (
                'https://satellit-tsc.ru/shop/folder/kremy',
                'https://satellit-tsc.ru/zubnyye-pasty',
                'https://satellit-tsc.ru/gigiyenicheskiye-pomady',
            ),
            'литература': (
                'https://satellit-tsc.ru/literatura-1',
            ),
            'полоска': (
                'https://satellit-tsc.ru/test-poloski/dlya-glyukometra',
                'https://satellit-tsc.ru/test-poloski/vizualnyye',
                'https://satellit-tsc.ru/oftalmologicheskiye-test-poloski',
            ),
            'помпа': (
                'https://satellit-tsc.ru/insulinovyye-pompy/accu-chek',
                'https://satellit-tsc.ru/insulinovyye-pompy/medtronik',
            ),
            'разное': (
                'https://satellit-tsc.ru/diagnosticheskiye-pribory',
                'https://satellit-tsc.ru/vsya-produktsiya-accu-chek?view=simple',
                'https://satellit-tsc.ru/soputstvuyushchiye-tovary',
                'https://satellit-tsc.ru/termometry-1',
                'https://satellit-tsc.ru/vesy',
                'https://satellit-tsc.ru/noski-i-perchatki',
                'https://satellit-tsc.ru/shop/folder/sudna-i-mochepriyemniki',
                'https://satellit-tsc.ru/irrigatory-i-zubnyye-shchetki',
                'https://satellit-tsc.ru/vanny-dlya-nog',
                'https://satellit-tsc.ru/massazhery',
                'https://satellit-tsc.ru/miostimulyatory-1',
                'https://satellit-tsc.ru/tovary-magnitnoy-terapii',
                'https://satellit-tsc.ru/applikatory-1',
                'https://satellit-tsc.ru/elektricheskiye-vitaminy',
                'https://satellit-tsc.ru/scholl',
                'https://satellit-tsc.ru/domashniy-uyut-1',
                'https://satellit-tsc.ru/shop/folder/fiziopribory-domashnego-primeneniya',
                'https://satellit-tsc.ru/vitafony-1',
                'https://satellit-tsc.ru/shagomery-datchiki-aktivnosti-pulsometry',
                'https://satellit-tsc.ru/drugaya-tekhnika-dlya-zdorovya'
            ),
            'ручка': (
                'https://satellit-tsc.ru/sredstva-dlya-vvoda-insulina',
            ),
            'тест': (
                'https://satellit-tsc.ru/testy-na-narkotiki',
                'https://satellit-tsc.ru/shop/folder/testy-dlya-beremennykh',
                'https://satellit-tsc.ru/testy-na-zabolevaniya',
                'https://satellit-tsc.ru/personalnyye-alkotestery',
                'https://satellit-tsc.ru/dozimetry-testery',
            ),
            'тонометр': (
                'https://satellit-tsc.ru/tonometry',
            ),
            'чехол': (
                'https://satellit-tsc.ru/minikholodilniki-termochekhly',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("form", {"class": "shop2-product-item product-item-simple"})
        pagination = soup.find("li", {"class": "page-next"})
        if pagination:
            new_url = 'https://satellit-tsc.ru' + pagination.a.attrs['href']
            blocks += self.det_blocks(get_soup(new_url))
        return blocks
        
    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "product-name"})
        res['title'] = bname.text
        res['url'] = 'https://satellit-tsc.ru' + bname.a.attrs['href']
        price_s = block.find("div", {"class": "price-current"}).text.strip()
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        if res['price'] == 0:
            res['available'] = False
        else:
            flag = block.find("div", {"class": "product-label"})
            if flag:
                res['available'] = not ("нет" in flag.text.lower())
            else:
                res['available'] = True
        desc = block.find("div", {"class": "product-anonce"})
        if desc:
            res['description'] = desc.text.strip()
        manuf = block.find("div", {"class": "td"})
        if manuf:
            res['manuf'] = manuf.text.strip()
        return res


class DiaShop24(Shop):
    def __init__(self):
        self.shop_name = "Diashop 24"
        self.shop_id = 18
        self.page_list = {    
            'бинт': (
                'https://www.diashop24.com/product-category/aksessuary/fiksiruyushchie-povyazki/',
                'https://www.diashop24.com/product-category/aksessuary/lejkoplastyri/',
                'https://www.diashop24.com/product-category/aksessuary/zashchitnye-plyonki/',
                'https://www.diashop24.com/product-category/akciya/',
            ),
            'мониторинг': (
                'https://www.diashop24.com/product-category/monitoring/freestyle-libre/',
                'https://www.diashop24.com/product-category/dexcom/',
                'https://www.diashop24.com/product-category/monitoring/medtronic/',
                'https://www.diashop24.com/product-category/omnipod/',
            ),
            'помпа': (
                'https://www.diashop24.com/product-category/insulinovaya-terapiya/pompy/',
            ),
            'разное': (
                'https://www.diashop24.com/product-category/insulinovaya-terapiya/infuzionnye-nabory/',
                'https://www.diashop24.com/product-category/insulinovaya-terapiya/igolki/',
            ),
            'ручка': (
                'https://www.diashop24.com/product-category/insulinovaya-terapiya/insulinovye-ruchki/',
            ),
            'чехол': (
                'https://www.diashop24.com/product-category/aksessuary/chekhly/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "product-small box"})
        pagination = soup.find("a", {"class": "next"})
        if pagination:
            nurl = pagination.attrs['href']
            blocks += self.det_blocks(get_soup(nurl))
        return blocks

    def parse_block(self, block):
        res = dict()
        bname = block.find("p", {"class": "name product-title"})
        res['title'] = bname.text
        res['url'] = bname.a.attrs['href']
        price_s = block.ins
        if price_s:
            price_s = price_s.text
        else:
            price_s = block.find("span", {"class": "price"}).text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        res['available'] = not bool(block.find("div", {"class": "out-of-stock-label"}))
        return res


class DiabetServis(Shop):
    def __init__(self):
        self.shop_name = "Диабет Сервис"
        self.shop_id = 19
        self.page_list = {    
            'анализатор': (
                'https://диабетсервис.рф/catalog/3/',
            ),
            'глюкометр': (
                'https://диабетсервис.рф/catalog/1/',
            ),
            'полоска': (
                'https://диабетсервис.рф/catalog/2/',
            ),
            'помпа': (
                'https://диабетсервис.рф/catalog/5/',
            ),
            'разное': (
                'https://диабетсервис.рф/catalog/4/',
            ),
        }
        
    def parse_page(self, url):
        soup = get_soup(url, True)
        blocks = self.det_blocks(soup)
        res = list()
        if blocks:
            for block in blocks:
                parsed = self.parse_block(block)
                res.append(parsed)
        return res
    
    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "item"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.find("a", {"class": "name"})
        res['title'] = bname.text
        res['url'] = 'https://диабетсервис.рф' + bname.attrs['href']
        price_s = block.strong.text
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class Diacadem(Shop):
    def __init__(self):
        self.shop_name = "Академия Диабета"
        self.shop_id = 20
        self.page_list = {    
            'бинт': (
                'https://diacadem.com/catalog/plastyri_i_dezinfektsiya/',
            ),
            'глюкометр': (
                'https://diacadem.com/catalog/glyukometry/',
            ),
            'еда': (
                'https://diacadem.com/catalog/zdorovoe_pitanie/',
                'https://diacadem.com/catalog/zameniteli_sakhara/',
                'https://diacadem.com/catalog/ledentsy_zhivichnye_s_propolisom/',
            ),
            'ланцет': (
                'https://diacadem.com/catalog/lantsety_i_prokalyvateli_/',
            ),
            'косметика': (
                'https://diacadem.com/catalog/kosmeticheskie_sredstva/',
            ),
            'литература': (
                'https://diacadem.com/catalog/spetsializirovannaya_literatura/',
            ),
            'мониторинг': (
                'https://diacadem.com/catalog/monitoring_glyukozy/',
            ),
            'полоска': (
                'https://diacadem.com/catalog/test_poloski/',
            ),
            'помпа': (
                'https://diacadem.com/catalog/insulinovye_pompy/',
                'https://diacadem.com/catalog/aksessuary_dlya_pomp/',
            ),
            'разное': (
                'https://diacadem.com/catalog/aktsii-i-spepredlozheniya/',
                'https://diacadem.com/catalog/raskhodnye_materialy/',
                'https://diacadem.com/catalog/sredstva_pri_gipoglikemii/',
                'https://diacadem.com/catalog/vesy/',
                'https://diacadem.com/catalog/masla/',
                'https://diacadem.com/catalog/medtekhnika/',
                'https://diacadem.com/catalog/raznoe/',
                'https://diacadem.com/catalog/probiotiki/',
            ),
            'ручка': (
                'https://diacadem.com/catalog/shprits_ruchki_i_igly/',
            ),
            'чехол': (
                'https://diacadem.com/catalog/myabetic_/',
                'https://diacadem.com/catalog/termosumki_i_chekhly/',
            ),
        }


    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "catalog-item-info"})
        pagination = soup.find("li", {"class": "last"})
        if pagination:
            nurl = 'https://diacadem.com' + pagination.a.attrs['href']
            blocks += self.det_blocks(get_soup(nurl))
        return blocks


    def parse_block(self, block):
        res = dict()
        bname = block.find("a", {"class": "item-title"})
        res['title'] = bname.text.strip()
        res['url'] = 'https://diacadem.com' + bname.attrs['href']
        try:
            price_s = list(block.find("span", {"class": "catalog-item-price"}).children)[0].strip()
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        except:
            res['available'] = False
        return res
        

class DiabetCabinet(Shop):
#     pagination??
    def __init__(self):
        self.shop_name = "Диабет Кабинет"
        self.shop_id = 21
        self.page_list = {    
            'витамин': (
                'http://диабет-кабинет.рф/catalog/vitaminy-',
            ),
            'глюкометр': (
                'http://диабет-кабинет.рф/catalog/prodazha-glyukometrov',
            ),
            'еда': (
                'http://диабет-кабинет.рф/catalog/produkty-pitaniya',
                'http://диабет-кабинет.рф/catalog/batonchiki-flaks-batonchiki-myusli',
                'http://диабет-кабинет.рф/catalog/vafli',
                'http://диабет-кабинет.рф/catalog/varene',
                'http://диабет-кабинет.рф/catalog/dzhem',
                'http://диабет-кабинет.рф/catalog/kozinaki',
                'http://диабет-кабинет.рф/catalog/konfety',
                'http://диабет-кабинет.рф/catalog/ledency',
                'http://диабет-кабинет.рф/catalog/voad-mineralnaya',
                'http://диабет-кабинет.рф/catalog/makaronnye-izdeliya',
                'http://диабет-кабинет.рф/catalog/pechene',
                'http://диабет-кабинет.рф/catalog/pechene/page/2',
                'http://диабет-кабинет.рф/catalog/podushechki',
                'http://диабет-кабинет.рф/catalog/pryaniki-',
                'http://диабет-кабинет.рф/catalog/ciropy',
                'http://диабет-кабинет.рф/catalog/fruktovo-yagodnye-snehki-',
                'http://диабет-кабинет.рф/catalog/khalva',
                'http://диабет-кабинет.рф/catalog/khrumstiki',
                'http://диабет-кабинет.рф/catalog/shokolad-bes-cahara',
                'http://диабет-кабинет.рф/catalog/balzamy-lechebnye',
                'http://диабет-кабинет.рф/catalog/bezglyuten',
                'http://диабет-кабинет.рф/catalog/fitochai',
                'http://диабет-кабинет.рф/catalog/cakharozameniteli',
                'http://диабет-кабинет.рф/catalog/fit-parad',
                'http://диабет-кабинет.рф/catalog/cteviya',
                'http://диабет-кабинет.рф/catalog/cteviozid',
                'http://диабет-кабинет.рф/catalog/cukra-diet',
                'http://диабет-кабинет.рф/catalog/fruktoza',
                'http://диабет-кабинет.рф/catalog/zdorovoe-pitanie-',
                'http://диабет-кабинет.рф/catalog/kashi',
                'http://диабет-кабинет.рф/catalog/pektin-agar-',
                'http://диабет-кабинет.рф/catalog/urbech--pasta-iz-semen',
                'http://диабет-кабинет.рф/catalog/pribiotiki-',
                'http://диабет-кабинет.рф/catalog/masla-',
                'http://диабет-кабинет.рф/catalog/otrubi',
                'http://диабет-кабинет.рф/catalog/kletchatka',
                'http://диабет-кабинет.рф/catalog/kofe-zelenyjj-',
                'http://диабет-кабинет.рф/catalog/tolokno',
                'http://диабет-кабинет.рф/catalog/coevaya-produkciya',
                'http://диабет-кабинет.рф/catalog/cikorijj',
                'http://диабет-кабинет.рф/catalog/khlebcy',
                'http://диабет-кабинет.рф/catalog/zarodyshi',
                'http://диабет-кабинет.рф/catalog/talkan-',
            ),
            'ланцет': (
                'http://диабет-кабинет.рф/catalog/lancety',
                'http://диабет-кабинет.рф/catalog/avtoprokalyvateli',
            ),
            'косметика': (
                'http://диабет-кабинет.рф/catalog/credstva-po-ukhodu-za-kozhejj',
                'http://диабет-кабинет.рф/catalog/credsta',
            ),
            'литература': (
                'http://диабет-кабинет.рф/catalog/test3',
                'http://диабет-кабинет.рф/catalog/test3/page/2',
            ),
            'полоска': (
                'http://диабет-кабинет.рф/catalog/subcat',
                'http://диабет-кабинет.рф/catalog/vizualnye',
            ),
            'помпа': (
                'http://диабет-кабинет.рф/catalog/pompy',
                'http://диабет-кабинет.рф/catalog/raskhodnyjj-material',
            ),
            'разное': (
                'http://диабет-кабинет.рф/catalog/medicinskie-pribory',
                'http://диабет-кабинет.рф/catalog/raskhodnye-materialy',
                'http://диабет-кабинет.рф/catalog/batarejjki',
                'http://диабет-кабинет.рф/catalog/shpricy-insulinovye',
                'http://диабет-кабинет.рф/catalog/credstva-dlya-kupirovaniya-gipoglikemii',
            ),
            'ручка': (
                'http://диабет-кабинет.рф/catalog/shpric-ruchki',
                'http://диабет-кабинет.рф/catalog/igly-dlya-shpric-ruchek',
            ),
            'чехол': (
                'http://диабет-кабинет.рф/catalog/chekhly-dlya-pomp',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find("div", {"class": "items fix"})
        if blocks:
            blocks = blocks.find_all("div", {"class": "item"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.a
        res['title'] = bname.text
        res['url'] = 'http://диабет-кабинет.рф/' + bname.attrs['href']
        price_s = block.find("div", {"class": "price"})
        if price_s: 
            price_s = price_s.span.text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        res['available'] = not bool(block.find("p", {"class": "outofstock"}))
        return res


class JiznSDiabetom(Shop):
    def __init__(self):
        self.shop_name = "Жизнь с диабетом"
        self.shop_id = 22
        self.page_list = {    
            'глюкометр': (
                'https://diabetrus.ru/category/glyukometry/',
            ),
            'еда': (
                'https://diabetrus.ru/category/zdorovoe-pitanie/',
                'https://diabetrus.ru/category/zdorovoe-pitanie/page/2/',
            ),
            'ланцет': (
                'https://diabetrus.ru/category/avtoprokalyvateli-igly-lantsety/',
            ),
            'косметика': (
                'https://diabetrus.ru/category/kosmeticheskie-sredstva/',
            ),
            'полоска': (
                'https://diabetrus.ru/category/test-poloski/',
            ),
            'помпа': (
                'https://diabetrus.ru/category/insulinovye/',
            ),
            'разное': (
                'https://diabetrus.ru/category/soputstvuyushhie-tovary/',
            ),
            'тонометр': (
                'https://diabetrus.ru/category/tonometr/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "product-wrapper"})
        return blocks

    def parse_block(self, block):
        res = dict()
        res['title'] = block.find("div", {"class": "product-details"}).text
        res['url'] = block.a.attrs['href']
        
        price_s = block.find("span", {"woocommerce-Price-amount amount"})
        if price_s:
            price_s = price_s.text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
            res['available'] = not bool(block.find("span", {"class": "out-of-stock"}))
        else:
            res['available'] = False
        return res


class DiabetMag(Shop):
    def __init__(self):
        self.shop_name = "Diabet Mag"
        self.shop_id = 23
        self.page_list = {    
            'помпа': (
                'https://www.diabet-mag.ru/shop/insulinpompa',
            ),
            'разное': (
                'https://www.diabet-mag.ru/shop/quick-set',
                'https://www.diabet-mag.ru/shop/sure-t',
                'https://www.diabet-mag.ru/shop/silhouette',
                'https://www.diabet-mag.ru/shop/izmerenieglukozy',
                'https://www.diabet-mag.ru/shop/rashodniematerialy',
                'https://www.diabet-mag.ru/shop/prochietovary',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "spacer product-container"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "vm-product-descr-container-1"})
        if bname:
            bname = bname.a
        else:
            bname = block.find("div", {"class": "vm-product-descr-container-0"}).a
        res['title'] = bname.text
        res['url'] = 'https://www.diabet-mag.ru' + bname.attrs['href']
        
        price_s = block.find("span", {"class": "PricesalesPrice"})
        if price_s:
            price_s = price_s.text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        return res
        

class Diabetica(Shop):
    def __init__(self):
        self.shop_name = "Диабетика"
        self.shop_id = 24
        self.page_list = {    
            'глюкометр': (
                'https://thediabetica.com/category/gljukometry/',
            ),
            'еда': (
                'https://thediabetica.com/category/fitparad/',
                'https://thediabetica.com/category/mr-djemius-zero/',
            ),
            'ланцет': (
                'https://thediabetica.com/category/lancety-i-prokalyvanija/',
            ),
            'косметика': (
                'https://thediabetica.com/category/sredstva-po-uhodu/',
            ),
            'полоска': (
                'https://thediabetica.com/category/test-poloski/',
            ),
            'помпа': (
                'https://thediabetica.com/category/insulinovye-pompy/',
            ),
            'разное': (
                'https://thediabetica.com/category/rashodnye-materialy/',
                'https://thediabetica.com/category/rashodnye-materialy/?page=2',
                'https://thediabetica.com/category/ruchki-i-igly/',
                'https://thediabetica.com/category/prochie-tovary/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "prd-wrapper"})
        return blocks
    
    def parse_block(self, block):
        res = dict()
        bname = block.a
        res['title'] = bname.text.strip()
        res['url'] = 'https://thediabetica.com' + bname.attrs['href']
        price_s = block.find("meta", {"itemprop": "price"}).attrs['content']
        res['orig_price'] = price_s
        res['price'] = self.price_str_to_float(price_s)
        return res


class Diamarka(Shop):
    def __init__(self):
        self.shop_name = "Диамарка"
        self.shop_id = 25
        self.page_list = {    
            'анализатор': (
                'https://diamarka.com/analizatory/',
            ),
            'бинт': (
                'https://diamarka.com/plastyri_i_dezinfektsiya/',
                'https://diamarka.com/kinezioteypy/',
            ),
            'глюкометр': (
                'https://diamarka.com/glyukometry/',
            ),
            'еда': (
                'https://diamarka.com/zdorovoe_pitanie/',
            ),
            'ланцет': (
                'https://diamarka.com/lantsety_i_prokalyvateli/',
            ),
            'косметика': (
                'https://diamarka.com/ukhod_za_kozhey/',
                'https://diamarka.com/ukhod_za_polostyu_rta/',
            ),
            'литература': (
                'https://diamarka.com/knigi_o_diabete/',
            ),
            'мониторинг': (
                'https://diamarka.com/monitoring_glyukozy/',
            ),
            'полоска': (
                'https://diamarka.com/test_poloski/',
            ),
            'помпа': (
                'https://diamarka.com/insulinovye_pompy/',
                'https://diamarka.com/raskhodnye_materialy/',
            ),
            'разное': (
                'https://diamarka.com/aksessuary_i_chekhly/',
                'https://diamarka.com/diabeticheskaya_stopa/',
                'https://diamarka.com/sredstva_pri_gipoglikemii/',
                'https://diamarka.com/medtekhnika/',
                'https://diamarka.com/vesy/',
                'https://diamarka.com/dezinfektsiya/',
                'https://diamarka.com/bytovaya_nekhimiya/',
                'https://diamarka.com/aktsii_i_rasprodazhi/',
            ),
            'ручка': (
                'https://diamarka.com/shprits_ruchki_i_igly/',
            ),
            'чехол': (
                'https://diamarka.com/termosumki_i_chekhly/',
            ),
        }

    def det_blocks(self, soup):
        blocks = soup.find_all("div", {"class": "catalog_item main_item_wrapper item_wrap"})
        pagination = soup.find("a", {"class": "flex-next"})
        if pagination:
            nurl = 'https://diamarka.com' + pagination.attrs['href']
            blocks += self.det_blocks(get_soup(nurl))
        return blocks

    def parse_block(self, block):
        res = dict()
        bname = block.find("div", {"class": "item-title"})
        res['title'] = bname.text.strip()
        res['url'] = 'https://diamarka.com' + bname.a.attrs['href']
        price_s = block.find("span", {"class": "price_value"})
        if price_s:
            price_s = price_s.text
            res['orig_price'] = price_s
            res['price'] = self.price_str_to_float(price_s)
        else:
            res['available'] = False
        return res


shops_list = [
    MedMag, TestPoloska, DiaCatalog, Glukometr, DaibetControl,
    DiaCheck, DiabeticShop, DiaLife, DiabetCare, DiabetMed,
    DiabetaNet, Diapuls, Diabeton, Glukoza, Betar,
    Diateh, Satellit, DiaShop24, DiabetServis, Diacadem,
    DiabetCabinet, JiznSDiabetom, DiabetMag, Diabetica, Diamarka
]
