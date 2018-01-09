import json
import logging
import os
import time

import errno

import utils


if not os.path.exists(os.path.dirname("../log/")):
    try:
        os.makedirs(os.path.dirname("../log/"))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise

logging.basicConfig(filename="../log/pass_machine_%s.log" % time.time(), level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger("requests").setLevel(logging.WARNING)


class Cycle(object):
    def __init__(self):
        self._project_name = utils.JIRA_PROJECT
        self._cycle_name = utils.TEST_CYCLE
        self._ids = self.get_project_and_cycle(self._cycle_name, self._project_name)
        self._project_id = self._ids["project_id"]
        self._version_id = self._ids["version_id"]
        self._cycle_id = self._ids["cycle_id"]
        self._executions = self.get_all_executions_in_cycle()

    def get_project_and_cycle(self, cycle_name, project_name):
        logging.info("Get project id, version id and cycle id for project '%s' and cycle '%s'" % (project_name,
                                                                                                  cycle_name))
        all_fields = self.get_zql_fields().json()
        project_data = filter(lambda x: x["name"] == project_name, all_fields["fields"]["project"])
        if not project_data:
            raise Exception("Project %s is not found!" % project_name)
        cycle_data = filter(lambda x: x["name"] == cycle_name, all_fields["fields"]["cycleName"])
        if not cycle_data:
            raise Exception("Cycle %s is not found!" % cycle_name)
        ids = {
            "project_id": project_data[0]["id"],
            "version_id": cycle_data[0]["versionId"],
            "cycle_id": cycle_data[0]["id"],
            "cycle_name": cycle_name
        }
        return ids

    @staticmethod
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

    @staticmethod
    def update_execution_status(execution, status):
        if execution is not None:
            req = {
                "status": {"id": utils.STATUSES[status]},
                "issueId": execution["execution"]["issueId"],
                "projectId": execution["execution"]["projectId"],
                "cycleId": execution["execution"]["cycleId"],
                "versionId": execution["execution"]["versionId"],
            }
            canonical_path = utils.ZapiCalls.PUT_EXECUTION
            resp = utils.put_request(canonical_path + "/" + execution["execution"]["id"], json.dumps(req))
            logging.info("Test-case %s is now in status %s. Labels are: %s" % (
                execution["issueKey"], status, execution["issueLabel"].split(",")))
            return resp

    @staticmethod
    def get_zql_fields():
        return utils.get_request_no_params(utils.ZapiCalls.GET_ZQL_FIELDS)

    def get_list_of_executions(self, offset):
        canonical_path = "expand=action&offset=%s&projectId=%s&versionId=%s" % (offset,
                                                                                self._project_id,
                                                                                self._version_id)
        return utils.get_request(utils.ZapiCalls.GET_EXECUTIONS_LIST + "/" + self._cycle_id, canonical_path).json()

    def get_all_executions_in_cycle(self):
        """Get all executions, ignoring status and labels.
        """
        logging.info("Get all executions in Test Cycle %s and cache it" % self._cycle_name)
        processed = 0
        content = self.get_list_of_executions(processed)
        execs = []
        total_executions = content["totalCount"]
        while processed <= total_executions:
            for execution in content["searchObjectList"]:
                execs.append(execution)
            # 50 is max fetch size in zapi
            processed += 50
            content = self.get_list_of_executions(processed)
        logging.info("Done! Cached executions: %s" % total_executions)
        return execs

    def get_executions_by_status_and_labels(self, status, labels=None):
        """Get executions by status and labels.

        :param status: status of test execution, for example UNEXECUTED
        :param labels: list of issue labels, like ["automated", "regression"].
                       Omit param if search by labels is not needed
        """
        if labels is None:
            labels = []
        logging.info("Find executions with status %s in Test Cycle %s" % (status, self._cycle_name))
        by_status = []
        logging.info("Executions search criteria: %s" % labels)
        logging.info("Total executions in cycle: %s" % len(self._executions))
        for execution in self._executions:
            if execution["execution"]["status"]["name"] == status and set(labels) < set(
                    execution["issueLabel"].split(",")):
                by_status.append(execution)
        logging.info("Total executions matching criteria: %s" % len(by_status))
        return by_status

    def get_execution_by_issue_key(self, issue_key):
        """Get executions by issue key.

        :param issue_key: the issue key of test execution, <project>-<issue_id>
        """
        logging.info("Find executions for issue %s in Test Cycle %s" % (issue_key, self._cycle_name))
        for execution in self._executions:
            if execution["issueKey"] == issue_key:
                logging.info("Found!")
                return execution
        logging.warn("Didn't find execution for issue %s" % issue_key)
        return None
