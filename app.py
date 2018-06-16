from flask import Flask
from flask import request
from flask import jsonify
from flask_restful import Resource, Api
from flask import make_response
from flask import abort
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    app.logger.info('Test info')
    app.logger.error('Test error')
    app.logger.warning('Test warning')
    response = {
        "status": "Hello World"
    }
    return make_response(jsonify(response), 200)


@app.route('/circleci/webhook', methods = ['POST'])
def webhook():
    branch = request.json['ref'] if request.json['ref_type'] == 'branch' else None
    if not branch:
        abort(403)
    trigger_type = request.headers['X-Github-Event']
    # delete_branch(trigger_type)
    # git_secret_key = os.environ.get('GIT_SECRET_KEY')
    response = {
        "Status": "CircleCI webhook working",
    }
    return make_response(jsonify(response), 200)


# def delete_branch(trigger_type):

#     return("Delete")

if __name__ == '__main__':
    app.run()
