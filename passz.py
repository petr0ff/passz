import json
import logging
import time

import utils

logging.basicConfig(filename="pass_machine_%s.log" % time.time(), level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger("requests").setLevel(logging.WARNING)


def update_bulk_executions_status(executions, status):
    # Request doesn't work
    execution_ids = [eid["execution"]["id"] for eid in executions]
    logging.info("Set status %s for %s executions" % (status, len(execution_ids)))
    req = {
        "status": utils.STATUSES[status],
        "executions": execution_ids
    }
    canonical_path = utils.ZapiCalls.POST_EXECUTIONS
    return utils.post_request(canonical_path, json.dumps(req))


def update_execution_status(execution, status):
    req = {
        "status": {"id": utils.STATUSES[status]},
        "issueId": execution["execution"]["issueId"],
        "projectId": execution["execution"]["projectId"],
        "cycleId": execution["execution"]["cycleId"],
        "versionId": execution["execution"]["versionId"],
    }
    canonical_path = utils.ZapiCalls.PUT_EXECUTION
    resp = utils.put_request(canonical_path + "/" + execution["execution"]["id"], json.dumps(req))
    logging.info("Test-case %s is now in status %s. Labels are: %s" % (execution["issueKey"], status, execution["issueLabel"].split(",")))
    return resp


def get_cycles():
    canonical_path = "expand=executions&projectId=%s&versionId=%s" % (utils.PROJECT_ID, utils.VERSION_ID)
    return utils.get_request(utils.ZapiCalls.GET_CYCLES, canonical_path)


def get_cycle(cycle_name):
    resp = get_cycles().content
    content = json.loads(resp)
    cycle = filter(lambda x: x["name"] == cycle_name, content)
    if not cycle:
        raise Exception("Cycle %s is not found!" % cycle_name)
    return cycle[0]


def get_list_of_executions(cycle, offset):
    canonical_path = "expand=action&offset=%s&projectId=%s&versionId=%s" % (offset, utils.PROJECT_ID, utils.VERSION_ID)
    return utils.get_request(utils.ZapiCalls.GET_EXECUTIONS_LIST + "/" + cycle, canonical_path).content


def get_executions_by_status_and_label(cycle, status, labels):
    logging.info("Find executions with status %s in Test Cycle %s" % (status, cycle["name"]))
    offset = 0
    executions = get_list_of_executions(cycle["id"], offset)
    by_status = []
    content = json.loads(executions)
    total_executions = content["totalCount"]
    logging.info("Executions search criteria: %s" % labels)
    logging.info("Total executions in cycle: %s" % total_executions)
    while offset <= total_executions:
        for execution in content["searchObjectList"]:
            if execution["execution"]["status"]["name"] == status and set(labels) < set(
                    execution["issueLabel"].split(",")):
                by_status.append(execution)
        # 50 is max fetch size in zapi
        offset += 50
        executions = get_list_of_executions(cycle["id"], offset)
        content = json.loads(executions)
        logging.info("Processed executions: %s and found matching criteria: %s" % (offset, len(by_status)))
    logging.info("Total executions matching criteria: %s" % len(by_status))
    return by_status


if __name__ == '__main__':
    cycle = get_cycle("1.1.151 Regression test")
    executions_to_process = get_executions_by_status_and_label(cycle, "UNEXECUTED", ["automated"])
    for execution in executions_to_process:
        update_execution_status(execution, "PASS")
