import json
from time import gmtime, strftime, perf_counter
from flask import Flask, request, jsonify
import gc
import pickle
import sys

from libs.fast_forward_pipeline import find_grouped_info

sys.path.append('.')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

started = strftime("%Y-%m-%d %H:%M:%S", gmtime())
started_time = perf_counter()

with open("info/goods_cache", "rb") as f:
    goods_cache = pickle.load(f)
with open("info/search_cache", "rb") as f:
    search_cache = pickle.load(f)


@app.route('/api/v1/goods', methods=['GET'])
def get_goods():
    query = request.args.get('query')
    if len(query) < 2:
        info = list()
    else:
        info = find_grouped_info(str(query), search_cache, goods_cache)
    return jsonify(
        status='ok',
        info=info
    )


@app.route('/api/v1/update_goods', methods=['GET'])
def update_goods():
    global goods_cache, search_cache
    with open("info/goods_cache", "rb") as f:
        goods_cache = pickle.load(f)
    with open("info/search_cache", "rb") as f:
        search_cache = pickle.load(f)
    gc.collect()
    return jsonify(
        status='ok',
    )


@app.route('/')
def status():
    diff = round(perf_counter() - started_time, 2)
    return 'Server started: %s. Operational: %s' % (started, diff)


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify(
        status='error',
        error='URL on method not found'
    )
    response.status_code = 404
    return response


@app.errorhandler(500)
def page_error(e):
    response = jsonify(
        status='error',
        error='Internal server error'
    )
    response.status_code = 500
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3010)
