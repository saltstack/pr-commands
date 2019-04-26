from flask import Flask, request
from prcommands import *

app = Flask(__name__)
log = app.logger

def validate_request(event):
    if 'X-Hub-Signature' not in request.headers:
        return False
    signature = request.headers['X-Hub-Signature'].split('=', 1)[1]
    payload = request.text
    return validate_github_request(signature, payload)


@app.route('/', methods=['POST'])
def root():
    data = request.get_json()
    if data['action'] not in ['created', 'edited']:
        log.error('Skipping action: %s', data['action'])
        return '', 201
    for cmd in parse_body(data['comment']['body']):
        run_cmd(cmd, data['issue']['number'])
    return '', 201


if __name__ == '__main__':
    app.run('0.0.0.0')
else:
    application = app
