from re import sub
import pickle

from info.match_dict import match_dict


def determine_good_id(s):
    ns = weak_unification(s)
    if not ns:
        return None
    return match_dict.get(ns, None)


def weak_unification(s):
    ns = s.strip().lower()
    ns = sub(r"\W", ' ', ns)
    ns = sub(r" {2,}", ' ', ns).strip()
    return ns


def add_good_id_to_raws(raws):
    for i, row in enumerate(raws):
        raws[i] = row + (determine_good_id(row[0]),)
    return raws
