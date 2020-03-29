import itertools
import re
from collections import Counter


def find_grouped_info(s, words_cat, answers):
    relevant_cats = choose_cats(s, words_cat)
    answer = [answers[cat] for cat in relevant_cats]
    return answer


def split(s):
    return re.findall(r"\w+", s.lower())


def word_cat(word, words_cat):
    cats = list()
    for words in words_cat:
        if word in words:
            cats.append(words_cat[words])
    return cats


def choose_cats(s, words_cat):
    words = split(s)
    if len(words) == 0:
        return list()
    elif len(words) == 1:
        return word_cat(words[0], words_cat)
    else:
        counter = Counter(itertools.chain.from_iterable(map(lambda x: word_cat(x, words_cat), words)))
        rel_cats = list()
        mc = counter.most_common()
        m = mc[0][1]
        for val, n in mc:
            if n == m:
                rel_cats.append(val)
        return rel_cats
