import os


from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/')
def base():
    if 'application/json' in request.headers['Accept']:
        return jsonify({})
    return 'JSON only supported', 406


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
