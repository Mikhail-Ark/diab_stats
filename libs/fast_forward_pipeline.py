import re


def find_grouped_info(s, cat_names, ret_dict):
    norm_name = parse(clean(s))['norm_name']
    if not norm_name:
        ns = s
    else:
        ns = norm_name
    relevant_cats = choose_cats(ns, cat_names)
    answer = [ret_dict[str(cat)] for cat in relevant_cats]
    return answer


def clean(s):
    new_s = re.sub(r"\W+", " ", s.lower().strip())
    return new_s


def parse(s):
    big_dict = {
        "type": {
            "Глюкометр": r"\bглюкометр\b",
            "тонометр": r"тонометр",
            "чехол": r"\bчехол\b"
        },
        "name": {
            "Глюкометр iCheck": r"\b(?:ай\ ?чек|i\ ?che[cс]?k)\b",
            "Глюкометр Accu-Chek Active": r"(?:акку|accu)\ ?(?:чек|chek)\ (?:актив|active?)",
            "Глюкометр Accu-Chek Mobile": r"(?:акку|accu)\ ?(?:чек|chek)\ (?:мобайл|mobile)",
            "Глюкометр Accu-Chek Performa": r"(?:акку|accu)\ ?(?:чек|chek)\ (?:перформа|performa)(?!\ (?:нано|nano))",
            "Глюкометр Accu-Chek Performa Nano": r"(?:акку|accu)\ ?(?:чек|chek)(?:\ (?:перформа|performa))?\ (?:нано|nano)",
            "Глюкометр Ascensia Entrust": r"\b(?:энтраст|асцензия|ascensia|entrust)\b",
            "Глюкометр B.Well WG-72": r"\bb\ well\ wg\ 72\b",
            "Глюкометр Bionime Rightest": r"\b(?:(?:бионайм\ райтест|bionime\ rightest))\b",
            "Глюкометр OneTouch Verio IQ": r"(?:(?:[ву]ан\ ?тач|one\ ?touch)\ )?(?:верио|verio)\ (?:ай\ ?кью|iq)",
            "Глюкометр OneTouch Verio Pro+": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:верио|verio)\ (?:про|pro)(?:\ (?:плюс|plus))?",
            "Глюкометр OneTouch Select": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:селект|select)(?!\ (?:плюс|симпл|plus|simple))",
            "Глюкометр OneTouch Select Plus": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:селект|select)\ (?:плюс|plus)(?!\ (?:флекс|flex))",
            "Глюкометр OneTouch Select Plus Flex": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:селект|select)\ (?:плюс|plus)\ (?:флекс|flex)",
            "Глюкометр OneTouch Select Simple": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:селект|select)\ (?:симпл|simple)",
            "Глюкометр OneTouch UltraEasy": r"(?:[ву]ан\ ?тач|one\ ?touch)\ (?:ультра|ultra)\ ?(?:изи|easy)",
            "Глюкометр Глюкокард Сигма": r"\b(?:глюкокард|glucocard)\ (?:сигма|sigma)(?!\ (?:мини|mini))\b",
            "Глюкометр Глюкокард Сигма Мини": r"\b(?:глюкокард|glucocard)\ (?:сигма|sigma)\ (?:мини|mini)\b",
            "Глюкометр Diacont": r"\b(?:диаконт|diacont)(?:\ (?:стандарт|standart))?(?!(?:\ (?:(?:мини|mini)|(?:компакт|compact))))\b",
            "Глюкометр Diacont Compact": r"\b(?:диаконт|diacont)\ (?:компакт(?:ный)?|мини|compact|mini)\b",
            "Глюкометр Duo-Care": r"\b(дуо\ ?к[еэ]а|duo\ ?care)\b",
            "Глюкометр eBsensor": r"\b(?:ebsensor|(?:еб|и\ ?би?\ ?)сенсор)\b",
            "Глюкометр IME-DC": r"\b(?:ime\ dc|(?:ай|и)ме\ д(?:ц|и\ ?си))\b",
            "Глюкометр EasyTouch": r"\b(?:изи\ ?тач|easy\ ?touch)(?!\ (?:джи|g)\b)\b",
            "Глюкометр EasyTouch G": r"\b(?:изи\ ?тач|easy\ ?touch)\ (?:джи|g)\b",
            "Глюкометр Clever Chek": r"\b(?:клевер\ ?чек|clever\ ?chec?k)\b",
            "Глюкометр CareSens II": r"(?:к[еэ]а\ ?сенс|care\ ?sens)\ (?:2|ii|ll)",
            "Глюкометр CareSens N": r"(?:к[еэ]а\ ?сенс|care\ ?sens)\ [nhн]",
            "Глюкометр CareSens Pop": r"(?:к[еэ]а\ ?сенс|care\ ?sens)\ (?:поп|pop)",
            "Глюкометр Contour Plus": r"(?:контур|contour)\ (?:плюс|plus)(?!\ (?:[ув]ан|one))",
            "Глюкометр Contour Plus One": r"(?:контур|contour)\ (?:плюс|plus)\ (?:[ув]ан|one)",
            "Глюкометр Contour TS": r"(?:контур|contour)\ [tт][сcs]\b",
            "Глюкометр Омелон А-1": r"\bомелон\ [aа]\ ?1\b",
            "Глюкометр Омелон В-2": r"\bомелон\ [bв]\ ?2\b",
            "Глюкометр Optium Omega": r"\b(?:оптиум\ омега|optium\ omega)\b",
            "Глюкометр Сателлит": r"(?:элта )?сатт?елл?ит(?!\ (?:экспресс|плюс))",
            "Глюкометр Сателлит Плюс": r"(?:элта )?сатт?елл?ит\ плюс",
            "Глюкометр Сателлит Экспресс": r"(?:элта )?сатт?елл?ит\ экспресс",
            "Глюкометр СенсоКард": r"\b(?:сенсо\ ?кард|senso\ ?card)(?!\ (?:плюс|plus))\b",
            "Глюкометр СенсоКард Плюс": r"\b(?:сенсо\ ?кард|senso\ ?card)\ (?:плюс|plus)\b",
            "Глюкометр SD Check Gold": r"\b(?:си?\ ?ди?\ чек|sd\ check)\ (?:голд|gold)\b",
            "Глюкометр True Result Twist": r"\b(?:тру\ ?резалт\ ?твист|true\ ?result\ ?twist)\b",
            "Глюкометр FreeStyle Optium": r"\b((?:оптиум|optium)\ )?(?:фристайл|freestyle)(\ (?:оптиум|optium))?(?!\ (?:папиллон|papillon))\b",
            "Глюкометр FreeStyle Papillon Mini": r"(?:фристайл|freestyle)\ (?:папиллон|papillon)\ (?:мини|mini)",
        },
        "attrib": {
            "автоматический": r"\bавтоматический\b",
            "bluetooth": r"\bс\ bluetooth\b",
            "Voice": r"\b(?:говорящий|voice|во[ий]с|с\ голосовым\ сопровождением|для\ слабовидящих)\b",
            "на запястье": r"на\ запястье",
            "неинвазивный": r"неинвазивный",
            "GC": r"\bgc\b",
            "GCU": r"\bgcu\b",
            "GCHb": r"\bgchb\b",
            "GM300": r"\bgm\ ?300\b",
            "GM500": r"\bgm\ ?500\b",
            "ТD-4209": r"\b(?:[tт]d\ )?4209\b",
            "ТD-4227": r"\b(?:[tт]d\ )?4227[аa]?\b",
            "CKC-05": r"\b[cс][кk][cс]\ 05\b",
        },
#         "add": "тест-полоски": "(без\ )?тест(\ полос(?:ки|ок)?)"
    }
    
    parts = {"tailings": s}
    for gr in big_dict:
        for kw in big_dict[gr]:
            if re.search(big_dict[gr][kw], parts["tailings"]):
                parts["tailings"] = re.sub(big_dict[gr][kw], "", parts["tailings"])
                parts[gr] = parts.get(gr, set()) | {kw}
    
    for part in parts:
        if part != "tailings":
            parts[part] = " ".join(sorted(parts[part]))
    
    if parts.get("type") and "чехол" in parts["type"]:
        parts["norm_name"] = " ".join([x for x in [parts.get("type"), parts.get("name")] if x is not None])
        return parts
    if "name" in parts:
        norm_name = " ".join([x for x in [parts.get("name"), parts.get("attrib")] if x is not None])
    else:
        norm_name = False
    if norm_name:
        parts["norm_name"] = norm_name
    else:
        parts["norm_name"] = None
    return parts


def choose_cats(s, cat_names):
    ns = s.strip().lower()
    words = ns.split()
    rel_cats = set()
    if len(words) == 0:
        return set(range(len(cat_names)))
    
    elif len(words) == 1:
        word = words[0]
        for i, cn in enumerate(cat_names):
            if word in cn:
                rel_cats.add(i)
    else:
        yellow = set()
        green = set()
        for i, cn in enumerate(cat_names):
            at_least_1_in = False
            at_least_1_out = False
            for word in words:
                if word in cn:
                    at_least_1_in = True
                    if at_least_1_out:
                        break
                else:
                    at_least_1_out = True
                    if at_least_1_in:
                        break
            if at_least_1_in:
                if at_least_1_out:
                    yellow.add(i)
                else:
                    green.add(i)
        if green:
            rel_cats = green
        else:
            rel_cats = yellow

    return rel_cats
