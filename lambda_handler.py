import logging
import json
import requests
import re
import os
from prcommands import *

log = logging.getLogger()
log.setLevel(log_level)


def validate_request(event):
    if 'content-type' not in event['headers'] or event['headers']['content-type'] != 'application/json':
        raise ValidationError("Content type is not 'application/json'")
    if 'X-Hub-Signature' not in event['headers']:
        raise ValidationErroor("No X-Hub-Signature in request headers")
    signature = event['headers']['X-Hub-Signature'].split('=', 1)[1]
    payload = event['body']
    return validate_github_request(signature, payload)


def handler(event, context):
    validate_request(event)
    data = json.loads(event['body'])
    if data['action'] not in ['created', 'edited']:
        log.error('Skipping action: %s', data['action'])
        return {
            'statusCode': 201,
            'body': ''
        }
    for cmd in parse_body(data['comment']['body']):
        run_cmd(cmd, data['issue']['number'])
    return {
        'statusCode': 201,
        'body': ''
    }
