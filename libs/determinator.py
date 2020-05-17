from re import sub
import pickle


def determine_good_id(s, model=None):
    ns = weak_unification(s)
    if not ns:
        return None
    if model is None:
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
    model = get_model()
    for i, row in enumerate(raws):
        raws[i] = row + (determine_good_id(row[0], model),)
    return raws
