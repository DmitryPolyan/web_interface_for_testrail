# -*- coding: utf8 -*-
#
# Данный файл служит для отправки результатов тестирования по КСС
# в тестрейл. Он работает в паре с crp.py - и имеет зависимость в
# виде установленного гугл-хрома.
# Большая часть взаимодействия производиться через АПИ тестрейла,
# но некоторый функционал в ТестРейле не доступен через АПИ ,
# данные потребности закрываются гугл-хромом с заскриптованными действиями
#
# - почему все написано так грязно?
# этот файл переписанный оригинальный версии отправки отчетности, изначально,
# планировалось, что он просто будет починен и доведен до рабочего состояния,
# но в процессе выполнения задачи оказалось, что не работает слишком многое.
# Чище было бы создать новый проект, но кол-во изменений уже было высоко, а
# сроки не вечны. Оставим это для старой версии КСС.

import os
import re
import sys
import time
import zipfile
import configparser
import crp as crp

from libs.testrail_api import testrail_api as tr
from datetime import date
from argparse import ArgumentParser


class TestRail(object):

    def __init__(self, vFuncName=None, vCurrTestResult=None, configuration_name=None):
        # self.currentPath = os.path.abspath(os.path.dirname(sys.argv[0]))
        # self.configPath = self.currentPath + '\\' + path
        self.configPath = r"C:\dev\kss\Data\test_id_testrail.ini"
        if not os.path.exists(self.configPath):
            raise ValueError('No path for config file found!')
        else:
            parser = configparser.ConfigParser()
            found = parser.read(self.configPath, encoding='UTF-8')
            if not found:
                raise ValueError('No config file found!')
        lst = parser.sections()
        for name in lst:
            self.__dict__.update(parser.items(name))
        # Иницилизация

        self.api_tr = tr.APIClient('https://testrail.testing.kraftway.lan', user = 'autotest@kraftway.lan',
                                   password = 'EhyNvJkWnLvrTzudEbNW-GnRf.5oasP2JSHf645Mk')
        self.path_to_tools = None
        # self.testrail_group_name = f'{self.projectName}_testbench'

        # Имя конфигурации формируется:
        # Модель_СерийныйНомер_ВерсияПрошивки_ПоследнийОктетIPv4тестовогоСтенда
        # пример: SamsungSSD960EVO250GB_S3ESNX0JA00124J_2B7QCXE7_44
        # self.testrail_config_name = 'None_None_None'

        self.vCurrTestResult = vCurrTestResult
        self.vFuncName = vFuncName
        self.tc_path = "/home/tmp"
        # TODO Перевесить
        #  self.exec_time_float = exec_time_float
        #  self.custom = custom
        self.exec_time_float = 999
        self.custom = False
        # данные для редактирования планов в тест-рейл
        self.login = 'autotest@kraftway.lan'
        self.passw = '1qaz@WSX3edc'
        self.autogenerate_plan_name = True
        self.projectname = 'Универсал'  # имя проректа в тестрейл
        self.suite_name = 'Автотесты'  # это имя набора уже готовых тест-кейсов
        self.configuration_name = 'плата'  # Тимур назвал конфигурации "плата"
        self.assigned_id = 38  # 38 это id УЗ autotester@kraftway.lan

    def get_project_id(self, name):
        """
        поиск id проекта по имени.
        :param name: имя проекта
        :return: id проекта
        """
        result = -1
        for i in self.api_tr.get_projects():
            if i['name'] == str(name):
                result = i['id']
                break
        return result

    def get_suite_id(self, project_id, name=None):
        """
        Метод ищет актуальный тип прогона в TR, основываясь на спецсимволе
        @ перед началом текстового названия прогона. При этом сам прогон в TR
        должен содержать имя из прогонов данного фреймворка
        :param self: экземпляр тестрейла
        :param project_id: номер проекта
        :param name: имя - должно совпадать с именем прогона во фреймворке
        :return: если найден результат - id, иначе весь список прогонов []
        """
        # deprecated func (original from auto-ssd proj)
        # result = -1
        # for i in self.api_tr.get_suites(project_id):
        #     if re.search(f'@{name}.*', i['name']):
        #         result = i['id']
        #         break
        # return result

        result = -1
        print('*'*10)
        print(project_id, name)
        for i in self.api_tr.get_suites(project_id):
            print(i['name'])
            if name in i['name']:  # re.search(f'{name}.*', i['name']):
                result = i['id']
                break
        return result

    def get_group_id(self, group_name, project_id):
        result = -1
        for i in self.api_tr.get_configs(project_id):
            if i['name'] == group_name:
                result = i['id']
                break
        return result

    def get_config_id(self, config_name, project_id):
        result = -1
        for i in self.api_tr.get_configs(project_id):
            for u in i['configs']:
                if u['name'] == config_name:
                    result = u['id']
                    break
        return result

    def get_config_name(self, config_id, project_id):
        result = -1
        for i in self.api_tr.get_configs(project_id):
            for u in i['configs']:
                if u['id'] == config_id:
                    result = u['name']
                    break
        return result

    def get_plan_id(self, project_id, plan_name, assigned_id=None):
        result = -1

        plans = self.api_tr.get_plans(project_id)
        #if assigned_id == None:
        #    plans = self.api_tr.get_plans(project_id)
        #else:
        #    plans = self.api_tr.get_plans(project_id, created_by=assigned_id)
        for i in plans:
            if i['name'] == plan_name:
                result = i['id']
                break
        return result

    def check_suite_in_plan(self, plan_id, suite_id):
        result = -1
        plan = self.api_tr.get_plan(plan_id)
        for i in plan['entries']:

            if i['suite_id'] == suite_id:
                result = plan_id
                break
        return result

    def create_new_plan(self, tr_config_name=None, tr_suite_name=None, specific_name_for_testplan=None):
        print('create new plan')

        tr_project_name = self.projectname


        # получить project id
        project_id = self.get_project_id(tr_project_name)
        if project_id == -1:
            print('[ERR] ID проекта не был найден, убедитесь, что проект с таким именем существует.')
            raise

        # проверяем есть ли группа, если нет - создаем
        # group_id = self.get_group_id(testrail_group_name, project_id)
        # if group_id == -1:
        #     self.api_tr.add_config_group(project_id, name=self.configuration_name)
            # time.sleep(1)
            # group_id = self.get_group_id(self.configuration_name, project_id)

        # создать конфигурации, если их нет
        # config_id = self.get_config_id(tr_config_name, project_id)
        # if config_id == -1:
        #     self.api_tr.add_config(group_id, name=tr_config_name)
        #     time.sleep(1)
        #     config_id = self.get_config_id(tr_config_name, project_id)
        config_id = self.get_config_id(config_name=tr_config_name, project_id=project_id)

        # получаем id сюиты
        suite_id = self.get_suite_id(project_id, name=self.suite_name)

        # test-plan description
        plan_desc = "automatically generated test plan for the {0} project.".format(self.projectname)

        if specific_name_for_testplan == None:
            # имя текущего тест-плана, это дата его проведения
            plan_date = 'autotest_{0}'.format(date.today().strftime("%d.%m.%y"))  # {0}'.format(date.today().strftime("%d.%m.%y"))
        else:
            plan_date = specific_name_for_testplan

        self.autogenerate_plan_name = plan_date

        # проверим наличие существующего тест плана с таким именем
        plan_id = self.get_plan_id(project_id, plan_date, self.assigned_id)
        run_id = None

        # проверим , возможно прогон и план уже созданы и нам нужно создавать новые?
        if plan_id != -1:
            # получаем список run для созданного тест плана
            dict_list_runs = self.get_list_of_run(plan_id)

            for key_id in dict_list_runs:
                if int(dict_list_runs[key_id]['suite_id']) == int(suite_id):
                    if dict_list_runs[key_id]['config'] == tr_config_name:
                        run_id = dict_list_runs[key_id]['id']
                        return plan_id, run_id

        if plan_id == -1:
            # создаем тест-план
            print('suite_id', suite_id)
            print("config_ids", config_id)
            self.api_tr.add_plan(project_id, name=plan_date, description=plan_desc,
                                 entries=[{'suite_id': suite_id, "name": tr_suite_name, "assignedto_id": self.assigned_id,
                                           "config_ids": [config_id], 'runs': [{"include_all": True,
                                                                                "assignedto_id": self.assigned_id,
                                                                                "config_ids": [config_id]}]}])


            # получаем id созданного тест-плана, проверяем создан ли он
            plan_id = self.get_plan_id(project_id, plan_date, self.assigned_id)
            # получаем список run для созданного тест плана
            dict_list_runs = self.get_list_of_run(plan_id)
            # забираем run id. Т.К. план только что создан - там один единственный ран
            for key_id in dict_list_runs:
                run_id = dict_list_runs[key_id]['id']

            return plan_id, run_id

        elif plan_id != -1 and run_id is None:
            # # а если тест план уже есть - обновляем его
            # Данный функционал на момент написания скрипта не был реализован в апи тест-рейла, а
            # некоторая его часть реализована, но с багами в самом testrail, из-за чего
            # реализовано обходное решение

            url_edit = 'https://testrail.kraftway.lan/index.php?/plans/edit/{0}/1'.format(plan_id)
            chromium = crp.ChromeRemoteProtocol(url=url_edit,
                                                bin='"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"')
            chromium.connect()
            time.sleep(1)
            clear, full = chromium.evaluate('document.title')
            if 'Войти' in clear:
                print(chromium.evaluate('document.getElementById("name").value = "{0}";'.format(self.login)))
                print(chromium.evaluate('document.getElementById("password").value = "{0}";'.format(self.passw)))
                chromium.evaluate("document.getElementById('button_primary').click();")
                time.sleep(4)  # ждем загрузки страницы
            chromium.evaluate('document.location.href = "{0}";'.format(url_edit))
            time.sleep(4)

            # получаем список текущих entry run's
            entries_list = []
            entries_html, _ = chromium.evaluate('document.getElementById("entries").innerHTML')
            for e_row in entries_html.split("\n"):
                reg_e = re.search(r'\sid=\"entry-.{1,50}\">', e_row)
                if reg_e:
                    entries_list.append(re.sub(r'\sid=\"entry-|\">', '', reg_e.group()))

            # добавляем новый
            print(chromium.evaluate('App.Plans.loadEntry();'))
            print('document.getElementById("choose_suite_id")[0].value = {0};'.format(suite_id))
            print(chromium.evaluate('document.getElementById("choose_suite_id")[0].value = {0};'.format(suite_id)))
            print(chromium.evaluate('document.getElementById("chooseSuiteDialogSubmit").click();'))

            entries_html, _ = chromium.evaluate('document.getElementById("entries").innerHTML')

            # Найдем новый entry run , который мы только что создали
            entry_run = None
            for e_row in entries_html.split("\n"):
                reg_e = re.search(r'\sid=\"entry-.{1,50}\">', e_row)
                if reg_e:
                    tmp = re.sub(r'\sid=\"entry-|\">', '', reg_e.group())
                    if tmp not in entries_list:
                        entry_run = tmp

            for x in entries_html.split('button-configurations'):
                reg_x = re.search(r'[Aa]p{2}\.[Pp]lans\.select[Cc]onfigs\(\d{3},.{1,50}\);', x)
                print("reg_x")
                print(reg_x)
                if reg_x:
                    iii = int(re.sub(r'^.*\(|,.*', '', reg_x.group()))
                    if int(suite_id) == int(re.sub(r'^.*\(|,.*', '', reg_x.group())):  # (?<=\()\d{3}

                        chromium.evaluate(reg_x.group())
                        configuration_html, _ = chromium.evaluate('document.getElementById("configurations").innerHTML')
                        for z in configuration_html.split('configuration-item'):

                            if str(tr_config_name) in z:
                                config_chkbx_id = re.search(r'config[Cc]heckbox-\d{1,3}', z).group()

                                # меняем название набора в тест-плане
                                print(chromium.evaluate("this.blur(); App.Plans.selectName('{0}');".format(entry_run)))
                                chromium.evaluate('document.getElementById("editName").value = "{0}"'.format(tr_suite_name))
                                chromium.evaluate("document.getElementsByClassName('button button-left button-positive button-ok dialog-action-default')[15].click()")

                                # добавление конфигурации
                                chromium.evaluate(
                                    "App.Plans.selectConfigs({0}, '{1}'); document.getElementById('{2}').checked = true; document.getElementById('selectConfigsSubmit').click();".format(iii,entry_run,config_chkbx_id))
                                break
                        break

            print(chromium.evaluate('document.getElementById("accept").click();'))
            print(chromium.evaluate('document.getElementById("confirmDiffSubmit").click();'))

            print(chromium.evaluate('window.close()'))
            chromium.close_and_exit()

        # получаем id созданного тест-плана, проверяем создан ли он
        plan_id = self.get_plan_id(project_id, plan_date, self.assigned_id)
        # получаем список run для созданного тест плана
        dict_list_runs = self.get_list_of_run(plan_id)
        # сверяем, для поиска наиболее подходящего
        # нас интересует последний созданный ран, у которого - suite_id аналогичен нашему и, возможно, совпадает config_id
        # --- правка --- config id теперь совпадает всегда, т.к. без него прогоны более не создаются
        flague = -1
        run_id = None
        for key_id in dict_list_runs:
        # Логика - если совпадает сюита - то это ран схожий с нашим, если совпадает конфиг, то точно наш ран, если
        # конфига нет, то мы берем последний созданный ран схожий с нашим и надеемся, что это он...
        # --- правка --- из-за изменившейся логики, мы теперь берем последний ран с нашим конфигом, а не первый из списка

            if int(dict_list_runs[key_id]['suite_id']) == int(suite_id):

                config_name = self.get_config_name(config_id, project_id)
                if dict_list_runs[key_id]['config'] == config_name:
                    run_id = dict_list_runs[key_id]['id']
                    flague = 0
                    # break
                if flague == -1:
                    run_id = dict_list_runs[key_id]['id']
        return plan_id, run_id

    @staticmethod
    def write_js(content, path_to):
        with open(path_to, 'w+') as f:
            f.write(content)

    # Поиск ИД теста по имени
    def ID_by_name(self, run, tc_name):
        # case = global_var.api_tr.send_get('get_tests/' + str(global_var.api_tr_buildName))
        case = self.api_tr.send_get('get_tests/' + str(run))
        for entry in case:
            print(entry['title'])
            print(tc_name)

            if entry['title'] == tc_name and self.custom == False:
                case = entry['id']
                return case

            elif entry['title'] == tc_name:
                if self.custom in entry['custom_preconds']:
                    case = entry['id']
                    return case
        # print("{0} - test not found".format(tc_name.encode("cp1251").decode("utf-8")))
        print(tc_name)
        sys.exit()

    def CurrRun(self, buildname=None):
        #Декодирование данных из конфига
        self.projectname = self.projectname.encode("cp1251").decode("utf-8")
        self.planname = self.planname.encode("cp1251").decode("utf-8")

        if buildname == None:
            self.buildname = self.buildname.encode("cp1251").decode("utf-8")
            if self.buildname == "" or self.buildname == None:
                self.buildname = self.autogenerate_plan_name
        else:
            self.buildname = buildname

        num = 0
        project = ' '
        plan = ' '
        run = ' '
        #Запрашиваем список проектов, ищем используемый нами по имени. Сохраняем ИД проекта
        find_project = self.api_tr.send_get('get_projects')
        for entry in find_project:
            if entry['name'] == self.projectname:
                project = entry['id']
        if project == ' ':
            raise BaseException("Проект с именем " + "\"" + self.projectname + "\"" +": не найден!")
        #Запрашщиваем список прогонов\наборов в проекте. Ищем требуемый прогон\набор
        if self.planname != " ": #Если поле для имени набора не пустое, выполняется поиск прогона в наборе
            find_plan = self.api_tr.send_get('get_plans/' + str(project))
            for entry in find_plan:
                if entry['name'] == self.planname:
                    plan = entry['id']
            if plan == ' ':
                raise BaseException("Набор прогонов с именем " +"\"" + self.planname + "\"" + "не найден! ")
            curr_plan = self.api_tr.send_get('get_plan/' + str(plan))
            for entry in curr_plan['entries']:
                if entry['name'] == self.buildname:
                    run = entry['runs'][0]['id']
                    return run
                    # while num < len(entry['runs']):
                    #     #if entry['runs'][num]['config'] == self.platformname:
                    #     if "," in entry['runs'][num]['config']:
                    #         if self.platformname in entry['runs'][num]['config']:
                    #             if self.os in entry['runs'][num]['config']:
                    #                 run = entry['runs'][num]['id']
                    #                 return run
                    #             else:
                    #                 num += 1
                    #         else:
                    #             num += 1
                    #     else:
                    #         if entry['runs'][num]['config']==self.platformname:
                    #             run = entry['runs'][num]['id']
                    #             return run
                    #         else:
                    #             num += 1
                #raise BaseException("Прогон тестов" + "\"" + self.buildname+ "\"" + " не найден")


            raise BaseException(self.buildname + ": not found ")
        else:
            #Ветка для прогонов в проекте, вне наборов
            run = self.api_tr.send_get('get_runs/' + str(project))
            for entry in run:
                if entry['name'] == self.buildname:
                    run = entry['id']
                    return run
            raise BaseException(self.buildname + ": not found ")

    def SendResult(self, test_id, test_time, test_path):  # Отправка результатов в тестрейл
        hardcode_path = 'C:/dev/kss/'
        test_path = hardcode_path + test_path
        test_path = test_path.replace(r'\\', '/')
        test_path = test_path.replace('\\', '/')

        if "pass" in str(self.vCurrTestResult).lower():  #  == 'passed'
            status = 1
        elif "fail" in str(self.vCurrTestResult).lower():  #  == "failed"
            status = 5
        else:
            raise BaseException(self.vCurrTestResult + " не найден")

        # if os.path.exists(test_path) == False:
        #     for ch in range(1, len(logpath)):
        #         if '/' in logpath[len(logpath) - ch]:
        #             logtest = logpath[0:len(logpath) - ch]
        #             break
        #     logtest = logtest + '/result.zip'


        if "pass" in str(self.vCurrTestResult).lower():
            comment = "Пройдено!" + str(test_time) + " \nОтчет можно увидеть здесь: "  #  @{report_path}"
        else:
            comment = "Ошибка!" + str(test_time) + "\nОтчет можно увидеть здесь:  "   #{report_path}"

        exec_time = test_time + ' s' #  f'{round(test_time.total_seconds())} s'
        print("Время: "+str(exec_time))
        # Отправка результатов, где:
        # test_id ид теста, status - статус, comment - комментарий, exec_time - затраченное время в секундах
        result = self.api_tr.send_post('add_result/' + str(test_id),
                                       {'status_id': status, 'comment': comment, 'elapsed': exec_time})
        result_id = result['id']

        # logpath это путь до папки с логами, но на каталог назад, в нем будет сформирован архив

        zip_name = re.split(r'(?<=\d{4})(\\\\|\\|\/|\/\/)(?<!\d{2}_\d{2}_\d{2})',
                            re.sub(r'(\\\\|\\|\/|\/\/)\w+(\\\\|\\|\/|\/\/)?$', '', test_path.strip()))

        logpath = zip_name[0]
        logtest = logpath + '/' + zip_name[2] + '.zip'
        print('#####################################')
        print(logpath)
        print(logtest)
        print('#####################################')

        if self._zipped(test_path, logtest) != -1:
            self.api_tr.send_post('add_attachment_to_result/' + str(result_id), logtest)
        else:
            print('Error on report archiving process!')
            os.exit()  # raise в jython работает не так , как питоне 3+, поэтому так

        # path=path[:-4]
        # if self.vCurrTestResult != 'passed':
        #     for root, dirs, files in os.walk(test_path):
        #         for file in files:
        #             print("Прикрепляется файл: " + file)
        #             # Прикреплоение аттачментов к тесту
        #             # self.api_tr.send_post('add_attachment_to_result/' + str(result_id), test_path + file)
        #             self.api_tr.send_post('add_attachment_to_result/' + str(result_id), test_path + file)


    def _zipped(self, test_path, logtest):
        # zip folder
        print(test_path)
        print(logtest)

        zip_ = zipfile.ZipFile(logtest, 'a')

        for root, dirs, files in os.walk(test_path):
            for file in files:
                print(file)
                try:
                    zip_.write(os.path.join(root, file), os.path.join(root, file)[len(test_path):],zipfile.ZIP_DEFLATED)
                except:
                    return -1
        return 0




    def GetFname(self):
        #Считывание базы тестов и поиск оригинального названия тестов в соответсвии с функциональным именем теста
        parser = configparser.ConfigParser()
        parser.read(self.configPath, encoding='utf-8')
        print(self.vFuncName)
        tc_name = parser.get("base", self.vFuncName)
        if ";" in tc_name:
            tc_name = tc_name.split(";")
        return tc_name

    def get_list_of_run(self, plan_id=None):
        dict_entry = {}

        curr_plan = self.api_tr.send_get('get_plan/' + str(plan_id))

        for entry in curr_plan['entries']:
            dict_entry[str(entry['runs'][0]['id'])] = {}
            dict_entry[str(entry['runs'][0]['id'])]['id'] = str(entry['runs'][0]['id'])
            dict_entry[str(entry['runs'][0]['id'])]['suite_id'] = str(entry['runs'][0]['suite_id'])
            dict_entry[str(entry['runs'][0]['id'])]['name'] = str(entry['runs'][0]['name'])
            dict_entry[str(entry['runs'][0]['id'])]['config'] = str(entry['runs'][0]['config'])

        return dict_entry


def sendresult(vFuncName, vCurrTestResult, test_time, test_path, configuration_name, plan_id, run_id, suite_name='Автотесты'):
    # Инициализация, подготовка переменных
    api = TestRail(vFuncName, vCurrTestResult, configuration_name)

    print('vFuncName', vFuncName)
    print('vCurrTestResult', vCurrTestResult)
    print('test_time', test_time)
    print('test_path', test_path)
    print('conf', configuration_name)
    print('plan_id', plan_id)
    print('run_id', run_id)
    print('suite_name', suite_name)


    if plan_id == None:
        plan_id, run_id = api.create_new_plan(
            tr_config_name=configuration_name,
            tr_suite_name=suite_name)  # 769

    print(plan_id, run_id)
    tc_name = api.GetFname()

    if type(tc_name) is list:
        i = 0
        while i < len(tc_name):
            test_id = api.ID_by_name(run_id, tc_name[i])
            api.SendResult(test_id,
                           str(int(test_time)),
                           test_path)  # Отправка результата
            i = i + 1
    else:

        test_id = api.ID_by_name(run_id, tc_name)
        api.SendResult(test_id,
                       str(int(test_time)),
                       test_path)  # Отправка результата

    # api = testrail(vFuncName, vCurrTestResult, configuration_name)
    #
    # if run_id == None:
    #     plan_id, run_id = api.create_new_plan(tr_config_name=configuration_name, tr_suite_name=suite_name)  # 769
    # print(plan_id, run_id)
    # tc_name = api.GetFname()
    #
    # if type(tc_name) is list:
    #     i = 0
    #     while i < len(tc_name):
    #         test_id = api.ID_by_name(run_id, tc_name[i])
    #         api.SendResult(test_id, test_time, test_path)  # Отправка результата
    #         i = i + 1
    # else:
    #
    #     test_id = api.ID_by_name(run_id, tc_name)
    #     api.SendResult(test_id, test_time, test_path)  # Отправка результата

# # # # # # # # Если вы хотите запускать файл отдельно


parser = ArgumentParser(prog=sys.argv[0], usage="%(prog)s [OPTION]... [PARAMS]...\n...")
opt = parser.add_argument
opt("-tn", "--test_name", metavar="", help="name of the test function")
opt("-tr", "--test_result", metavar="", help="passed of fail")
opt("-tt", "--test_time", metavar="", help="time of the test execution")
opt("-tp", "--test_path", metavar="", help="path to the test artefacts")
opt("-pid", "--plan_id", metavar="", help="plan_id on the testrail")
opt("-rid", "--run_id", metavar="", help="run_id on the testrail")
opt("-sn", "--suite_name", metavar="", help="suite_name")
opt("-cn", "--configuration_name", metavar="", help="configuration name or platform name (like KWAS, KWC612S2)")

cli_args = parser.parse_args(sys.argv[1:])

sendresult(vFuncName=cli_args.test_name,
           vCurrTestResult=cli_args.test_result,
           test_time=cli_args.test_time,
           test_path=cli_args.test_path,
           configuration_name=cli_args.configuration_name,
           plan_id=cli_args.plan_id,  # 6452 , cli_args.plan_id
           run_id=cli_args.run_id,  # 6460 , cli_args.run_id
           suite_name=cli_args.suite_name)
