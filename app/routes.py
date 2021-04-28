# -*- coding: utf-8 -*-
from app import app, db, admin_permission
from flask import render_template, request, redirect, url_for, flash, current_app, Response
from app.forms import StartPageForm, LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from flask_principal import identity_changed, Identity, Principal, RoleNeed, identity_loaded
import db_handler
import os
import easygui
import json
import shutil
import datetime
import importlib
import requests
import plugins


principal = Principal(app)
SEPARATE_TESTS = dict()  # Избранные тесты из группы, которая не выбрана полностью
active_plugins = []  # Плагины подключенные в данный момент
plugins_dir = "plugins"  # Папка, в которую помещаются все подключаемые плагины

# TODO: Примерный словарь данных о прогоне, актуализировать при реализавции
collects_data_report = {'time': 'time', 'status': 'stop', 'current_test': 'Someone test', 'author': 'some_author'}
db_updated = True  # Обновление БД Тестреил выполнено по расписанию
last_time_success_db_update = None  # Дата последнего успешного обновления

@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
@login_required
def index():
    """
    Рендер стартовой страницы
    """
    form = StartPageForm()
    if request.method == 'POST':
        return render_template('index.html', form=form)
    return render_template('index.html', form=form)


@app.route('/get_status_db', methods=['GET'])
def get_status_db() -> json:
    """Возвращает в js состояние обновления БД Тестреил"""
    data = {'db_status': db_updated, 'date_update': last_time_success_db_update}
    return json.dumps(data)


def db_testrail_status(success: bool):
    """
    ф-я меняющая статус-состояние бд Testrail
    :param success: True если БД обновлена успешно
    """
    global db_updated, last_time_success_db_update
    if success:
        db_updated = True
        last_time_success_db_update = str(datetime.datetime.now())
    else:
        db_updated = False


@app.route('/change_path', methods=['GET'])
def change_path() -> str:
    """
    Ф-я для выбора нестандартного пути к main.py
    """
    app.logger.info(f'Измененеие в пути к файлу main.py')
    path = easygui.fileopenbox('Please choose your main file')
    if path:
        return path
    else:
        app.logger.info(f'Измененеие в пути к файлу main.py не приняты')
        return 'CANCELED'


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    ф-я выполнения аутентификации в систему
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильное имя или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        app.logger.info(f'Вход под пользователем {user.username}')
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.role))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/login_as_guest')
def login_as_guest():
    """
    Ф-я аутентификации под гостевым профилем
    """
    app.logger.info('Login as guest')
    user = User.query.filter_by(username='guest').first()
    login_user(user)
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.role))
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
@admin_permission.require(http_exception=403)
def register():
    """
    Ф-я для внесения нового пользователя в БД пользователей
    """
    form = RegistrationForm()
    if 'Изменить' in str(request.form):
        user_name_old = form.select_user.data
        user = User.query.filter_by(username=user_name_old).first()
        user.username = form.username.data.lower()
        user.email = form.email.data
        user.password = form.password.data
        user.role = form.role.data
        db.session.commit()
        app.logger.info(f'Изменения в учетку у пользователя {user.username}')
        return redirect(url_for('index'))
    else:
        if form.validate_on_submit():
            user = User(username=form.username.data.lower(),
                        email=form.email.data,
                        password=form.password.data,
                        role=form.role.data.lower()
                        )
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно добавлен')
            app.logger.info(f'В БД добавлен пользователь {user.username}')
            return redirect(url_for('index'))
        return render_template('registration.html', title='Register', form=form)


@app.route('/logout')
def logout():
    """
    Ф-я выхода из системы
    """
    app.logger.info('Logout')
    logout_user()
    identity_changed.send(current_app._get_current_object(), identity=Identity('user'))
    return redirect(url_for('index'))


@identity_loaded.connect
def on_identity_loaded(sender, identity):
    """
    Ф-я определения прав пользователя
    """
    needs = []
    if identity.id == 'admin':
        needs.append(RoleNeed('admin'))
    for n in needs:
        identity.provides.add(n)


@app.route('/get_user_information', methods=['GET'])
def get_user_information() -> dict:
    """
    Ф-я извлечения данных о пользователе (Исп-ся в редактировании пользователя)
    """
    user_name = request.args.get('chosenUser')
    user = User.query.filter_by(username=user_name).first()
    app.logger.info(f'Просмотр информации о пользователе {user.username}')
    return {'name': user.username, 'email': user.email, 'password': user.password, 'role': user.role}


@app.route('/get_users', methods=['GET'])
def get_users() -> dict:
    """
    Получения списка пользователей из БД (Исп-ся при редактировании пользователей)
    """
    users_dict = {}
    users = User.query.all()
    for i in users:
        users_dict[i.id] = i.username
    return users_dict


@app.route('/del_user', methods=['GET'])
def del_user() -> str:
    """
    Удаление пользователя из БД
    """
    user_name = request.args.get('chosenUser')
    user = User.query.filter_by(username=user_name).first()
    db.session.delete(user)
    db.session.commit()
    app.logger.info(f'Пользователь {user.username} удален')
    return 'Пользователь ' + user.username + ' удален'


@app.route('/get_from_db', methods=['GET'])
def get_sections() -> dict:
    """
    ф-я получения групп тестов (исп-ся для создания списка групп файлов при запуске веб интерфейса)
    """
    id = request.args.get('id')
    data = db_handler.get_data(id)
    return dict(data)


@app.route('/json_result', methods=['POST'])
def make_json():
    """
    Ф-я создания результирующей json строки для отправки агенту
    (В данный момент просто создает json в корне, в будущем доработать отправку агенту)
    """
    app.logger.info('Запуск тестирования (в данный момент создание json в корне)')
    data = request.form['jsonFile']
    try:
        # Проверка существования в корне уже созданного файла json
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'testpaln.json')
        os.remove(path)
    except:
        pass
    with open('testplan.json', 'w') as json_file:
        json_file.write(data)
    return 'Json файл создан'


@app.route('/plugins')
@admin_permission.require(http_exception=403)
def plugins_control():
    """
    Ф-я для сбора, управления и отображения плагинов
    """
    plugins = get_all_plugins_from_plugins_dir()
    return render_template('plugins.html', title='Управление плагинами', plugins=plugins, active_plugins=active_plugins)


def get_all_plugins_from_plugins_dir() -> dict:
    """
    Сбор списка плагинов.
    :return: Список плагинов из папки Plugins в данный момент
    """
    plugins = {}
    for dir_name in os.listdir(plugins_dir):
        if not dir_name.endswith(".py") and not dir_name.endswith("__"):
            with open(f'plugins/{dir_name}/config.json', 'r') as conf:
                data = json.loads(conf.read())
            plugins[dir_name] = data.get('description')
    return plugins


@app.route('/on_off_plugin', methods=['POST'])
def on_off_plugin():
    """
    Ф-я добавления/удаления плагинов, вызывается Ajax'ом при изменении статуса плагина
    """
    plugin_name = request.form['plugin']  # Имя плагина
    action = request.form['action']  # Действие выполняемое с плагиным (вкл/выкл)
    if action == 'add':
        active_plugins.append(plugin_name)
        app.logger.info(f'Включение плагина {plugin_name}')
    else:
        active_plugins.remove(plugin_name)
        app.logger.info(f'Отключение плагина {plugin_name}')
    return 'success'


@app.route('/some_rout_for_agents_reports')
def agents_report():
    """Гипотетический роут, на который с агента будет приходить информация о текущем состоянии"""
    # TODO: При готовности агента реализовать парсинг данных, который он предоставляет
    #  и запись их в collects_data_report
    current_plugins = get_all_plugins_from_plugins_dir()  # Cписок всех плагинов в папке Plugins
    for plugin in active_plugins:
        # Проверка, на случай если плагин, находящихся в списке активных был удален из папки Plugins
        if plugin in current_plugins:
            path_for_plugin = plugins_dir+'.'+plugin+'.'+'main'
            importlib.import_module(path_for_plugin)
            # Запускаем ф-ю main() из свежеимпортированного плагина
            eval(path_for_plugin+'.main()')
        else:
            active_plugins.remove(plugin)
    return redirect(url_for('index'))

@app.route('/some_route_for_test_fast_api')
def test_fastapi():
    requests.get("http://127.0.0.2:8000/test_fastApi")
    return redirect(url_for('index'))


@app.route('/get_json_plugin_config', methods=['GET'])
def get_json_plugin_config():
    """
    Ф-я загрузки настроек плагина, вызывается при просмотре и редактировании настроек
    :return: выгруженные из json настройки плагина
    """
    plugin_name = request.args.get('pluginId')  # Имя плагина
    app.logger.info(f'Открытие настроек плагина {plugin_name}')
    current_plugins_config_path = plugins_dir + r'/' + plugin_name + r'/config.json'
    with open(current_plugins_config_path, 'r') as conf:
        data = json.loads(conf.read())
    return data


@app.route('/plugin_config_update', methods=['POST'])
def plugin_config_update():
    """
    ф-я изменения настроек плагина.
    Получает из js json с новыми настройками и изменяем существующий json с конфигом
    :return:
    """
    new_config = request.form['jsonFile']  # Новые настройки
    plugin_name = request.form['plugin_name']  # Имя плагина
    app.logger.info(f'Выполняется изменение настроек плагина {plugin_name}')
    current_plugins_config_path = plugins_dir + r'/' + plugin_name + r'/config.json'
    new_config = json.loads(new_config)
    with open(current_plugins_config_path, 'r') as conf:
        data = json.loads(conf.read())
    data.update(new_config)
    with open(current_plugins_config_path, 'w') as conf:
        conf.write(json.dumps(data))
    return 'True'


@app.route('/pluginsDefaultLoad', methods=['POST'])
def plugins_default_load():
    """
    Загрузка настроек по умолчани. Копирует json из папки backup
    :return: в случае Успеха возвращает true
    """
    plugin_name = request.form['name_plugin']  # Имя плагина
    app.logger.info(f'Выполняется сброс настроек плагина {plugin_name}')
    current_plugins_config_path = plugins_dir + r'/' + plugin_name + r'/config.json'
    current_plugins_config_path_backup = plugins_dir + r'/' + plugin_name + r'/backup/config.json'
    try:
        shutil.copyfile(current_plugins_config_path_backup, current_plugins_config_path)
        app.logger.info(f'Загрузка настроек плагина {plugin_name} выполнена успешно')
        return 'True'
    except:
        app.logger.error(f'Загрузка настроек плагина {plugin_name} не выполнена из-за ошибки ')
        return 'False'

