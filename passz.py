import hashlib
import json
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

JWT_EXPIRE = 3600
DEFAULT_HEADERS = {"zapiAccessKey": ACCESS_KEY}

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


def get_cycles():
    canonical_path = "expand=&projectId=%s&versionId=%s" % (PROJECT_ID, VERSION_ID)
    return _get_request(ZapiCalls.GET_CYCLES, canonical_path)


def get_cycle(cycle_name):
    resp = get_cycles().content
    content = json.loads(resp)
    cycle = filter(lambda x: x["name"] == cycle_name, content)
    if not cycle:
        raise Exception("Cycle %s is not found!" % cycle_name)
    return cycle[0]


def update_bulk_executions_status(executions, status):
    # Request doesn't work
    req = {
        "status": STATUSES[status],
        "executions": executions
    }
    canonical_path = ZapiCalls.POST_EXECUTIONS
    return _post_request(canonical_path, json.dumps(req))


def update_execution_status(execution, status):
    req = {
        "status": {"id": STATUSES[status]},
        "issueId": execution["execution"]["issueId"],
        "projectId": execution["execution"]["projectId"],
        "cycleId": execution["execution"]["cycleId"],
        "versionId": execution["execution"]["versionId"],
    }
    canonical_path = ZapiCalls.PUT_EXECUTION
    resp = _put_request(canonical_path + "/" + execution["execution"]["id"], json.dumps(req))
    print "Test-case %s is now in status %s" % (execution["issueKey"], status)
    return resp


def get_list_of_executions(cycle):
    cycle_id = get_cycle(cycle)
    canonical_path = "expand=action&projectId=%s&versionId=%s" % (PROJECT_ID, VERSION_ID)
    return _get_request(ZapiCalls.GET_EXECUTIONS_LIST + "/" + cycle_id["id"], canonical_path).content


def get_executions_by_status_and_label(cycle, status, labels):
    executions = get_list_of_executions(cycle)
    by_status = []
    content = json.loads(executions)
    for execution in content["searchObjectList"]:
        if execution["execution"]["status"]["name"] == status and set(labels) < set(execution["issueLabel"].split(",")):
            by_status.append(execution)
    return by_status


def _get_jwt(canonical):
    payload_token = {
        'sub': LOGIN,
        'qsh': hashlib.sha256(canonical.encode('utf-8')).hexdigest(),
        'iss': ACCESS_KEY,
        'exp': int(time.time()) + JWT_EXPIRE,
        'iat': int(time.time())
    }
    token = jwt.encode(payload_token, SECRET_KEY, algorithm='HS256').strip().decode('utf-8')
    return token


def _get_request(canonical_uri, canonical_path):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % _get_jwt("GET&%s&%s" % (canonical_uri, canonical_path))
    res = ZAPI_URL + canonical_uri + "?%s" % canonical_path
    r = requests.get(res, headers=DEFAULT_HEADERS)
    return _handle_response_status(r)


def _post_request(canonical_uri, payload=None):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % _get_jwt("POST&%s&" % canonical_uri)
    DEFAULT_HEADERS["Content-Type"] = "application/json"
    res = ZAPI_URL + canonical_uri
    r = requests.post(res, data=payload, headers=DEFAULT_HEADERS)
    return _handle_response_status(r)


def _put_request(canonical_uri, payload=None):
    DEFAULT_HEADERS["Authorization"] = "JWT %s" % _get_jwt("PUT&%s&" % canonical_uri)
    DEFAULT_HEADERS["Content-Type"] = "application/json"
    res = ZAPI_URL + canonical_uri
    r = requests.put(res, data=payload, headers=DEFAULT_HEADERS)
    return _handle_response_status(r)


def _handle_response_status(response):
    if response.status_code in (200, 201, 204):
        return response
    else:
        raise Exception(response.url, response.content)

if __name__ == '__main__':
    unexecuted = get_executions_by_status_and_label("1.1.151 Performance test", "UNEXECUTED", ["automated"])
    for execution in unexecuted:
        update_execution_status(execution, "PASS")
