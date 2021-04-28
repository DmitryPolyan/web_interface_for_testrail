import subprocess
import logging
import os
import importlib
import testrail_db.db_creator
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
Principal(app)
admin_permission = Permission(RoleNeed('admin'))  # Для разграничения доступа юзера и админа

# Настройка логирования
file_handler = RotatingFileHandler('logs/webface.log', 'a', 1 * 1024 * 1024, 3)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.info('Startup of web interface')


sched = BackgroundScheduler()  # Планировщик обновления БД Тестреил
@sched.scheduled_job('cron', day_of_week='0-6', hour=11, minute=52)
def sensor():
    time_of_last_modification = os.stat(r'testrail_db\some_txt.txt').st_mtime
    app.logger.info('Старт обновления Базы данных из Testrail')
    testrail_db.db_creator.main()
    new_time_of_modification = os.stat(r'testrail_db\some_txt.txt').st_mtime
    if time_of_last_modification == new_time_of_modification:
        routes.db_testrail_status(False)
        app.logger.error('Ошибка обновления БД')
    else:
        routes.db_testrail_status(True)
        app.logger.info('База данных обновлена')


sched.start()


from app import routes, models, error