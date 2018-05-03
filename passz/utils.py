import hashlib
import jwt
import time
import yaml

import requests

try:
    config = yaml.safe_load(open("../config.yml"))
except IOError:
    raise Exception("Please, create config.yml from config.yml.example")

BASE_JIRA_URL = config.get("jira")
ZAPI_URL = config.get("zapi")
ZAPI_VERSION = config.get("zapi_version")
JIRA_LOGIN = config.get("login")
ZAPI_ACCESS_KEY = config.get("access_key")
ZAPI_SECRET_KEY = config.get("secret_key")
JIRA_PROJECT = config.get("project")
TEST_CYCLE = config.get("test_cycle")
LABELS = config.get("search_by")
STATUS_FROM = config.get("status_from")
STATUS_TO = config.get("status_to")

JWT_EXPIRE = 3600
DEFAULT_HEADERS = {"zapiAccessKey": ZAPI_ACCESS_KEY}

STATUSES = {
    "PASS": 1,
    "FAIL": 2,
    "WIP": 3,
    "BLOCKED": 4,
    "UNEXECUTED": -1
}


class ZapiCalls(object):
    GET_CYCLES = "%s/cycles/search" % ZAPI_VERSION
    GET_ZQL_FIELDS = "%s/zql/fields/values" % ZAPI_VERSION
    POST_EXECUTIONS = "%s/executions" % ZAPI_VERSION
    PUT_EXECUTION = "%s/execution" % ZAPI_VERSION
    GET_EXECUTIONS_LIST = "%s/executions/search/cycle" % ZAPI_VERSION


def get_jwt(canonical):
    payload_token = {
        'sub': JIRA_LOGIN,
        'qsh': hashlib.sha256(canonical.encode('utf-8')).hexdigest(),
        'iss': ZAPI_ACCESS_KEY,
        'exp': int(time.time()) + JWT_EXPIRE,
        'iat': int(time.time())
    }
    token = jwt.encode(payload_token, ZAPI_SECRET_KEY, algorithm='HS256').strip().decode('utf-8')
    return token


def get_request(canonical_uri, canonical_path):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("GET&%s&%s" % (canonical_uri, canonical_path))
    res = ZAPI_URL + canonical_uri + "?%s" % canonical_path
    r = requests.get(res, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def get_request_no_params(canonical_uri):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("GET&%s&" % canonical_uri)
    res = ZAPI_URL + canonical_uri
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


def delete_request(canonical_uri, canonical_path):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % get_jwt("DELETE&%s&%s" % (canonical_uri, canonical_path))
    res = ZAPI_URL + canonical_uri + "?%s" % canonical_path
    r = requests.delete(res, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def handle_response_status(response):
    if response.status_code in (200, 201, 204):
        return response
    else:
        raise Exception(response.url, response.content, response.status_code)
