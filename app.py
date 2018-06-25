from json import dumps
from flask import Flask, request, jsonify, abort, Response
from sys import stderr
import hmac
import os
import requests
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
config = app.config


@app.route('/', methods=['GET'])
def hello_world():
    app.logger.info("Heimdall it's working!")
    data = {
        "msg": "Heimdall it's working!"
    }

    return Response(dumps(data), status=200, mimetype='application/json')


@app.route('/circleci/webhook', methods=['POST'])
def webhook():
    # Ping github
    event = request.headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return Response(dumps({'msg': 'pong'}), status=200, mimetype='application/json')
    elif event != 'delete':
        app.logger.warning('Event ' + event + ' not supported')
        return Response(dumps({'msg': 'Event ' + event + ' not supported'}), status=400, mimetype='application/json')

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

    # Get environment variables
    try:
        job_ci = os.environ.get('JOB_CI')
        user_token = os.environ.get('USER_TOKEN')
    except Exception:
        app.logger.error('Error to get environment variables')
        return Response(dumps({'msg': 'Error to get environment variables'}), status=400, mimetype='application/json')

    # Get config variables
    try:
        ci_url_base = config['CI_BASE_URL']
    except Exception:
        app.logger.error('Error to get config variables')
        return Response(dumps({'msg': 'Error to get config variables'}), status=400, mimetype='application/json')

    # Get data
    try:
        payload = request.get_json()
    except Exception:
        app.logger.error('Request parsing failed')
        return Response(dumps({'msg': 'Request parsing failed'}), status=400, mimetype='application/json')

    if 'ref_type' in payload:
        if payload['ref_type'] == 'branch':
            branch = payload['ref']
        else:
            app.logger.warning('ref_type not supported')
            return Response(dumps({'msg': 'ref_type not supported.'}), status=400, mimetype='application/json')
    else:
        app.logger.error('Json struct not supported. ref_type required.')
        return Response(dumps({'msg': 'Json struct not supported. ref_type required.'}), status=400, mimetype='application/json')

    try:
        repo_path = payload['repository']['full_name']
    except Exception:
        app.logger.error('Error to get repository name.')
        return Response(dumps({'msg': 'Error to get repository name.'}), status=400, mimetype='application/json')


    ci_url = ci_url_base.replace('{repo_path}', repo_path)

    data = {
        "build_parameters": {
            "CIRCLE_JOB": job_ci,
            "DELETED_BRANCH": branch
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + user_token
    }

    meta = {
        'repo': repo_path,
        'branch': branch,
        'event': event
    }

    app.logger.info('Metadata:\n{}'.format(dumps(meta)))

    try:
        response = requests.post(ci_url, data=dumps(data), headers=headers)
    except Exception:
        app.logger.error('Error to posting to CI')
        return Response(dumps({'msg': 'Error to posting to CI'}), status=400, mimetype='application/json')

    return Response(status=200)


if __name__ == '__main__':
    app.run()
