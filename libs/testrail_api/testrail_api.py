#
# TestRail API binding for Python 3.x (API v2, available since
# TestRail 3.0)
# Compatible with TestRail 3.0 and later.
#
# Learn more:
#
# http://docs.gurock.com/testrail-api2/start
# http://docs.gurock.com/testrail-api2/accessing
#
# Copyright Gurock Software GmbH. See license.md for details.
#

import requests
import json
import base64


class APIClient:
    def __init__(self, base_url, user, password):
        self.user = user
        self.password = password
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'
        # Todo: Тимур, прекрати хардкодить такие вещи, вынеси сертификат в конфиг :)
        self.ca = r"C:\Dev\Jyth\kss\trunk\Libs\rootCA.crt"


    #
    # Send Get
    #
    # Issues a GET request (read) against the API and returns the result
    # (as Python dict) or filepath if successful file download
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. get_case/1)
    #
    # filepath            The path and file name for attachment download
    #                     Used only for 'get_attachment/:attachment_id'
    #
    def send_get(self, uri, filepath=None):
        return self.__send_request('GET', uri, filepath)

    #
    # Send POST
    #
    # Issues a POST request (write) against the API and returns the result
    # (as Python dict).
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. add_case/1)
    # data                The data to submit as part of the request (as
    #                     Python dict, strings must be UTF-8 encoded)
    #                     If adding an attachment, must be the path
    #                     to the file
    #
    def send_post(self, uri, data):
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri
        # auth=str(base64.b64encode(bytes(self.user + ':' + self.password), 'utf-8')).strip()
        auth = str(
            base64.b64encode(
                bytes('%s:%s' % (self.user, self.password), 'utf-8')
            ),
            'ascii'
        ).strip()
        headers = {'Authorization': 'Basic ' + auth}

        if method == 'POST':
            if uri[:14] == 'add_attachment':    # add_attachment API method
                files = {'attachment': (open(data, 'rb'))}
                response = requests.post(url, headers=headers, files=files, verify=self.ca)
                files['attachment'].close()
            else:
                headers['Content-Type'] = 'application/json'
                payload = bytes(json.dumps(data), 'utf-8')
                response = requests.post(url, headers=headers, data=payload, verify=self.ca)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers, verify=self.ca)

        if response.status_code > 201:
            try:
                error = response.json()
            except:     # response.content not formatted as JSON
                error = str(response.content)
            raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
        else:
            if uri[:15] == 'get_attachment/':   # Expecting file, not JSON
                try:
                    open(data, 'wb').write(response.content)
                    return (data)
                except:
                    return ("Error saving attachment.")
            else:
                return response.json()


    # added at 03.02.2020 by Vituris ===================================
    # Расширение функционала - добавление методов для работы с TestRail

    # project(s) - проект
    def get_project(self, project_id):
        return self.send_get('get_project/%s' % project_id)


    def get_projects(self, is_completed=None):
        pattern = 'get_projects'

        if is_completed is not None:
            pattern += '&is_completed=%s' % int(is_completed)

        return self.send_get(pattern)

    # =======================================================
    # test-Plan(s) - тест-планы из TestRail = = = = = = = = =
    def get_plan(self, plan_id):
        return self.send_get('get_plan/%s' % plan_id)

    def get_plans(self, project_id, created_after=None, created_before=None,
                  created_by=None, is_completed=None, limit=None,
                  offset=None, milestone_id=None):
        pattern = 'get_plans/%s' % project_id

        if created_after is not None:
            pattern += '&created_after=%s' % created_after

        if created_before is not None:
            pattern += '&created_before=%s' % created_before

        if created_by is not None:
            pattern += '&created_by=%s' % ','.join(created_by)

        if is_completed is not None:
            pattern += '&is_completed=%s' % int(is_completed)

        if limit is not None:
            pattern += '&limit=%s' % limit

        if offset is not None:
            pattern += '&offset=%s' % offset

        if milestone_id is not None:
            pattern += '&milestone_id=%s' % ','.join(milestone_id)

        return self.send_get(pattern)

    def add_plan(self, project_id, **kwargs):
        """
        The following POST fields are supported:
        name	    string	    The name of the test plan (required)
        description	string	    The description of the test plan
        milestone_id	int	    The ID of the milestone to link to the test plan
        entries	    array	    An array of objects describing the test runs of
                                the plan, see _add_plan_entry
        """
        return self.send_post('add_plan/%s' % project_id, data=kwargs)

    def update_plan(self, plan_id, entry_id='', **kwargs):
        """
        The following POST fields are supported:
        name	    string	    The name of the test plan (required)
        description	string	    The description of the test plan
        milestone_id	int	    The ID of the milestone to link to the test plan
        entries	    array	    An array of objects describing the test runs of
                                the plan, see _add_plan_entry
        """
        # print(f'update_plan_entry/{plan_id}/{entry_id}:{kwargs}')
        # return self.send_post('update_plan/%s/%s' % (plan_id, entry_id), data=kwargs)
        return self.send_post('update_plan_entry/%s/%s' % (plan_id, entry_id), data=kwargs)

    # =================================================================
    # suites - part (наборы)
    def get_suite(self, suite_id):
        return self.send_get('get_suite/%s' % suite_id)

    def get_suites(self, project_id):
        return self.send_get('get_suites/%s' % project_id)

    def add_suite(self, project_id, **kwargs):
        """
        The following POST fields are supported:
        name	    string	The name of the test suite (required)
        description	string	The description of the test suite
        """
        return self.send_post('add_suite/%s' % project_id, data=kwargs)

    # =================================================================
    # получаем список Run(s) - тест прогоны из TestRail = = = = = = = = =
    def get_run(self, run_id):
        return self.send_get('get_run/%s' % run_id)

    def get_runs(self, project_id, created_after=None, created_before=None,
                 created_by=None, is_completed=None, limit=None,
                 offset=None, milestone_id=None, suite_id=None):
        pattern = 'get_runs/%s' % project_id

        if created_after is not None:
            pattern += '&created_after=%s' % created_after

        if created_before is not None:
            pattern += '&created_before=%s' % created_before

        if created_by is not None:
            pattern += '&created_by=%s' % ','.join(created_by)

        if is_completed is not None:
            pattern += '&is_completed=%s' % int(is_completed)

        if limit is not None:
            pattern += '&limit=%s' % limit

        if offset is not None:
            pattern += '&offset=%s' % offset

        if milestone_id is not None:
            pattern += '&milestone_id=%s' % ','.join(milestone_id)

        if suite_id is not None:
            pattern += '&suite_id=%s' % ','.join(suite_id)

        return self.send_post(pattern)


    def add_run(self, project_id, **kwargs):
        """
        The following POST fields are supported:
        suite_id	    int	    The ID of the test suite for the test run
                                (optional if the project is operating in single
                                suite mode, required otherwise)
        name	        string	The name of the test run
        description	    string	The description of the test run
        milestone_id	int	    The ID of the milestone to link to the test run
        assignedto_id	int	    The ID of the user the test run should be
                                assigned to
        include_all	    bool	True for including all test cases of the test
                                suite and false for a custom case selection
                                (default: true)
        case_ids	    array	An array of case IDs for the custom case
                                selection
        """
        return self.send_post('add_run/%s' % project_id, data=kwargs)

    # ==============================================================
    # config(s) or Entity(s) or Entries - конфигурации тест-планов или прогонов

    def get_configs(self, project_id):
        return self.send_get('get_configs/%s' % project_id)

    def add_config_group(self, project_id, **kwargs):
        """
        kwargs: name	string	The name of the configuration group (required)
        """
        return self.send_post('add_config_group/%s' % project_id, data=kwargs)

    def add_config(self, config_group_id, **kwargs):
        """
        kwargs: name	string	The name of the configuration (required)
        """
        return self.send_post('add_config/%s' % config_group_id, data=kwargs)


    # =====================================================================================


class APIError(Exception):
    pass
