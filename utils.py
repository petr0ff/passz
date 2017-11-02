import hashlib
import jwt
import time
import yaml

import requests

config = yaml.safe_load(open("config.yml"))

BASE_JIRA_URL = config.get("jira")
ZAPI_URL = config.get("zapi")
ZAPI_VERSION = config.get("zapi_version")
LOGIN = config.get("login")
ACCESS_KEY = config.get("access_key")
SECRET_KEY = config.get("secret_key")
PROJECT_ID = config.get("project_id")
VERSION_ID = config.get("version_id")

STATUSES = {
    "PASS": 1,
    "FAIL": 2,
    "WIP": 3,
    "BLOCKED": 4,
    "UNEXECUTED": -1
}


class ZapiCalls(object):
    GET_CYCLES = "%s/cycles/search" % ZAPI_VERSION
    POST_EXECUTIONS = "%s/executions" % ZAPI_VERSION
    PUT_EXECUTION = "%s/execution" % ZAPI_VERSION
    GET_EXECUTIONS_LIST = "%s/executions/search/cycle" % ZAPI_VERSION
    GET_EXECUTIONS_BY_SPRINT = "%s/executions/search/sprint" % ZAPI_VERSION

JWT_EXPIRE = 3600
DEFAULT_HEADERS = {"zapiAccessKey": ACCESS_KEY}


def get_jwt(canonical):
    payload_token = {
        'sub': LOGIN,
        'qsh': hashlib.sha256(canonical.encode('utf-8')).hexdigest(),
        'iss': ACCESS_KEY,
        'exp': int(time.time()) + JWT_EXPIRE,
        'iat': int(time.time())
    }
    token = jwt.encode(payload_token, SECRET_KEY, algorithm='HS256').strip().decode('utf-8')
    return token


def get_request(canonical_uri, canonical_path):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("GET&%s&%s" % (canonical_uri, canonical_path))
    res = ZAPI_URL + canonical_uri + "?%s" % canonical_path
    r = requests.get(res, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def post_request(canonical_uri, payload=None):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("POST&%s&" % canonical_uri)
    DEFAULT_HEADERS["Content-Type"] = "application/json"
    res = ZAPI_URL + canonical_uri
    r = requests.post(res, data=payload, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def put_request(canonical_uri, payload=None):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("PUT&%s&" % canonical_uri)
    DEFAULT_HEADERS["Content-Type"] = "application/json"
    res = ZAPI_URL + canonical_uri
    r = requests.put(res, data=payload, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def handle_response_status(response):
    if response.status_code in (200, 201, 204):
        return response
    else:
        raise Exception(response.url, response.content, response.status_code)