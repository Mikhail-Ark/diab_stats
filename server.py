import json
from time import gmtime, strftime, perf_counter
from flask import Flask, request, jsonify

from info.cats import cats_list
from libs.fast_forward_pipeline import find_grouped_info

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

started = strftime("%Y-%m-%d %H:%M:%S", gmtime())
started_time = perf_counter()

with open("info/conv_table.json", "r", encoding='utf-8') as f:
    conv_table = json.load(f)


@app.route('/api/v1/goods', methods=['GET'])
def get_goods():
    data = request.get_json(silent=True)
    # started_time_local = perf_counter()

    if (not 'query' in data) or (not data['query']):
        response = jsonify(
            status='error',
            error='query not set'
        )
        response.status_code = 400
        return response

    info = find_grouped_info(str(data['query']), cats_list, conv_table)

    return jsonify(
        status='ok',
        info=info
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
