from libs.testrail_api.testrail_api import *


server = ''
user = ''
password = ''
client = APIClient(server, user, password)


def return_projects_list():
    result = []
    projects = client.get_projects()
    for project in projects:
        result.append([project['id'], -1, project['name']])
    return result


def return_suites_list(project_id):
    result = []
    suites = client.get_suites(project_id)
    for suite in suites:
        result.append([suite['id'], project_id, suite['name']])
    return result


def return_sections_list(project_id, suite_id):
    result = []
    sections = client.send_get('get_sections/{}&suite_id={}'.format(project_id, suite_id))
    for section in sections:
        result.append([section['id'], suite_id, section['name']])
    return result


def return_cases_list(project_id, suite_id):
    result = []
    all_cases = client.send_get(f'get_cases/{project_id}&suite_id={suite_id}')
    for case in all_cases:
        result.append([case['id'], case['section_id'], case['title']])
    return result
