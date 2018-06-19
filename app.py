from flask import Flask, request, jsonify, make_response, abort
from sys import stderr
import hmac
import os
from json import dumps
# import logging
# logging.basicConfig(stream=stderr)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello_world():
    app.logger.info('Test info')
    app.logger.error('Test error')
    app.logger.warning('Test warning')
    response = {
        "status": "Its working!"
    }
    return make_response(jsonify(response), 200)


@app.route('/circleci/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        response = {"msg": "Its working!"}
        return make_response(jsonify(response), 200)

    # Ping github
    event = request.headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return make_response(jsonify({'msg': 'pong'}), 200)
    elif event != 'delete':
        app.logger.warning('Event '+ event + ' not supported')
        return make_response(jsonify({'msg': 'Event '+ event + ' not supported'}), 400)

    # Enforce secret
    secret = os.environ.get('GIT_SECRET_KEY')

    if secret:
        # Only SHA1 is supported
        header_signature = request.headers.get('X-Hub-Signature')
        if header_signature is None:
            abort(403)

        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            abort(501)

        # HMAC requires the key to be bytes, but data is string
        mac = hmac.new(str(secret), msg=request.data, digestmod='sha1')

        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            abort(403)

    # Gather data
    try:
        payload = request.get_json()
    except Exception:
        app.logger.warning('Request parsing failed')
        return make_response(jsonify({'msg': 'Request parsing failed'}), 400)

    if 'ref_type' in payload:
        if payload['ref_type'] == 'branch':
            branch = payload['ref']
        else:
            app.logger.warning('ref_type not supported')
            return make_response(jsonify({'msg': 'ref_type not supported.'}), 400)
    else:
        app.logger.warning('Json struct not supported. ref_type required.')
        return make_response(jsonify({'msg': 'Json struct not supported. ref_type required.'}), 400)

    name = payload['repository']['name'] if 'repository' in payload else None

    meta = {
        'name': name,
        'branch': branch,
        'event': event
    }

    app.logger.info('Metadata:\n{}'.format(dumps(meta)))


    # secret = request.json["hook"]["config"]["secret"]

    # app.logger.warning("secret: ########################" + request.headers.get('X-Hub-Signature'))
    # app.logger.warning("data: ########################" + str(request.data))
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
