from re import sub
import pickle


def determine_good_id(s):
    ns = weak_unification(s)
    if not ns:
        return None
    model = get_model()
    return model.get(ns, None)


def weak_unification(s):
    ns = s.strip().lower()
    ns = sub(r"\W", ' ', ns)
    ns = sub(r" {2,}", ' ', ns).strip()
    return ns


def get_model():
    with open("info/match_dict", "rb") as f:
        model = pickle.load(f)
    return model


def add_good_id_to_raws(raws):
    for i, row in enumerate(raws):
        raws[i] = row + (determine_good_id(row[0]),)
    return raws
