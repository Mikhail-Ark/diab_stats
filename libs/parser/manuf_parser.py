import re

from libs.parser.kw import words_manuf, regs_manuf
from libs.determinator import weak_unification


class BrandDeterminator(object):
    def __init__(self):
        self.words = words_manuf
        self.regs = {re.compile(x[0]): x[1] for x in regs_manuf}
    
    def pull_brand_set(self, s):
        ns = weak_unification(s)
        brand_set = set()
        words = ns.split()
        used = set()
        for i, word in enumerate(words):
            res = self.words.get(word)
            if res:
                brand_set.add(res)
                used.add(i)
        if used:
            ns = " ".join(x for i, x in enumerate(words) if i not in used)
        ur_len = len(ns)
        for reg in self.regs:
            res = reg.sub("", ns).strip()
            if len(res) < ur_len:
                brand_set.add(self.regs[reg])
                ns = res
                ur_len = len(res)
        return brand_set, ns
