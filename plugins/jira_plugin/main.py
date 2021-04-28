from jira import JIRA
from plugins.base import BasePluginsClass
import json


class JiraPlugin(BasePluginsClass):
    dir_path = 'plugins/jira_plugin/config.json'

    def __init__(self, **collects_data_report):
        super().__init__(**collects_data_report)
        with open(self.dir_path, 'r') as conf:
            data_conf = json.loads(conf.read())
        self.user = data_conf.get('user')
        self.password = data_conf.get('password')
        self.server_url = data_conf.get('server')
        self.jira_options = {'server': self.server_url}
        self.client = JIRA(options=self.jira_options, basic_auth=(self.user, self.password))
        with open('testplan.json', 'r') as testplan:
            self.data_testplan = json.loads(testplan.read())
        self.project_id = int(self.data_testplan[-2][1])

    def project_match(self):
        id_project = int(self.project_id)
        if id_project in [6, 29, 32, 35, 39]:
            return 'KSSAUTO'
        elif id_project == 21:
            return 'SSDAUTO'
        else:
            return 'ROSAUTO'


def main():
    Jira_object = JiraPlugin()
    Jira_object.client.create_issue(fields={'project': Jira_object.project_match(), 'issuetype': {'name': 'Task'}, 'summary': 'Test!'}),
