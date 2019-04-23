import os
import json
import re
import requests
import pprint
from flask import Flask, request

app = Flask(__name__)
log = app.logger


uri = os.environ.get('JENKINS_URI', 'https://jenkinsci.saltstack.com/api/json')
user = os.environ['JENKINS_USER']
password = os.environ['JENKINS_PASS']


def parse_body(body):
    '''
    Parse the body of a github issue comment and look for 're-run' test
    commands
    '''
    for line in body.lower().split('\n'):
        words = line.split()
        try:
            idx = words.index('re-run')
        except ValueError:
            continue
        if words[idx+1] == 'full':
            yield words[idx:idx+3]
        else:
            yield words[idx:idx+2]


def get_pr_jobs():
    '''
    Get all Jenkins jobs associated with pull requests
    '''
    res = requests.get(
        'https://jenkinsci.saltstack.com/view/Pull%20Requests/api/json',
            headers={'accept': 'application/json'},
            auth=requests.auth.HTTPBasicAuth(user, password),
        )
    if res.status_code != 200:
        raise RuntimeError("Received non 200 status code from jenkins")
    data = res.json()
    for job in data['jobs']:
        yield job


def job_has_params(job_url):
    '''
    Determin weather a Jenkins job accepts build parameters
    '''
    res = requests.get(
        '{}/api/json'.format(job_url.rstrip('/'))
    )
    if res.status_code != 200:
        raise RuntimeError("Received non 200 status code from jenkins")
    data = res.json()
    data['jobs'][-1]['url']
    res = requests.get(
        '{}/api/json'.format(data['jobs'][-1]['url'])
    )
    if res.status_code != 200:
        raise RuntimeError("Received non 200 status code from jenkins")
    data = res.json()
    for d in data['property']:
        if d['_class'] == 'hudson.model.ParametersDefinitionProperty':
            return True
    return False


def filter_jobs(jobs, on):
    '''
    Filter jobs by a keyword
    '''
    for job in jobs:
        if job['name'].find(on) != -1:
            yield job


def build_job(job_url, pr_number, run_full, has_params):
    '''
    Request jenkins to build a job
    '''
    if has_params:
        pr_url = '{}/job/PR-{}/buildWithParameters?runFull={}'.format(
            job_url.rstrip('/'),
            pr_number,
            'true' if run_full else 'false'
        )
    else:
        pr_url = '{}/job/PR-{}/build'.format(
            job_url.rstrip('/'),
            pr_number,
        )
    res = requests.get(
        'https://jenkinsci.saltstack.com/crumbIssuer/api/json',
        auth=requests.auth.HTTPBasicAuth(user, password),
    )
    if res.status_code != 200:
        raise Exception("Jenkins returned non 200 response")
    data = res.json()
    res = requests.post(
        pr_url,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            data['crumbRequestField']: data['crumb']
        },
        auth=requests.auth.HTTPBasicAuth(user, password),
    )
    if res.status_code == 201:
        log.error("Build started: %s", pr_url)
    else:
        log.error("Build request received non 201 status: %s", res.status_code)


def run_cmd(cmd, pr_number):
    '''
    Run a PR command
    '''
    for job in filter_jobs(get_pr_jobs(), cmd[-1]):
        has_params = job_has_params(job['url'])
        if cmd[1] == 'full':
           run_full = True
        else:
           run_full = False
        build_job(job['url'], pr_number, run_full, has_params)


@app.route('/', methods=['POST'])
def root():
    data = request.get_json()
    if data['action'] != 'created':
        log.error('Skipping action: %s', data['action'])
        return '', 200
    for cmd in parse_body(data['comment']['body']):
        run_cmd(cmd, data['issue']['number'])
    return '', 200


if __name__ == '__main__':
    app.run('0.0.0.0')
else:
    application = app
