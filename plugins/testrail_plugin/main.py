from plugins.base import BasePluginsClass
from libs.testrail_api import testrail_api
from libs.testrail_api import testrail_handler_2
from datetime import date
from app.routes import collects_data_report
from flask_login import current_user
import json


class TestrailPlugin(BasePluginsClass):
    dir_path = 'plugins/testrail_plugin/config.json'

    def __init__(self, **collects_data_report):
        super().__init__(**collects_data_report)
        with open(self.dir_path, 'r') as conf:
            data_conf = json.loads(conf.read())
        self.user = data_conf.get('user')
        self.password = data_conf.get('password')
        self.server_url = data_conf.get('server')
        self.client = testrail_api.APIClient(self.server_url, self.user, self.password)
        with open('testplan.json', 'r') as testplan:
            self.data_testplan = json.loads(testplan.read())
        self.project_id = int(self.data_testplan[-2][1])
        self.suite_id = int(self.data_testplan[-1][1])
        self.assigned_id = self.client.send_get(f'get_user_by_email&email={self.user}')['id']

    def get_plan_id(self, plan_name, assigned_id=None):
        result = False
        plans = self.client.get_plans(self.project_id)
        for i in plans:
            if i['name'] == plan_name:
                result = i['id']
                break
        return result


def main():
    Testrail = TestrailPlugin()
    plan_name = 'autotest_{0}'.format(date.today().strftime("%d.%m.%y"))
    plan_id = Testrail.get_plan_id(plan_name)
    if plan_id:
        #TODO: Доделать, когда будет готов агент и будет приходить отбивка о выполнении текущего теста
        print('ok')
    else:
        Testrail.client.add_plan(Testrail.project_id, name=plan_name, entries=[{'suite_id': Testrail.suite_id, "assignedto_id": Testrail.assigned_id, 'runs': [{"include_all": True, "assignedto_id": Testrail.assigned_id}]}])
