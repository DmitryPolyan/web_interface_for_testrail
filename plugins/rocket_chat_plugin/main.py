from plugins.base import BasePluginsClass
from app.routes import collects_data_report
from flask_login import current_user
from rocketchat_API.rocketchat import RocketChat
import json


class RocketChatPlugin(BasePluginsClass):
    dir_path = 'plugins/rocket_chat_plugin/config.json'

    def __init__(self, **collects_data_report):
        super().__init__(**collects_data_report)
        with open(self.dir_path, 'r') as conf:
            data_conf = json.loads(conf.read())
        self.user = data_conf.get('user')
        self.password = data_conf.get('password')
        self.server_url = data_conf.get('server_url')

    def send_information_to_rc(self):
        """
        Ф-я отправляет сообщение о текущем статусе тестирования в рокетчат
        """
        rocket = RocketChat(self.user, self.password, server_url=self.server_url, ssl_verify=False)
        # Формируем имя для отправки информации, отправляем все текущему пользователю
        rocket_chat_channel = '@' + current_user.email.split('@')[0]
        # Формирование сообщения для пользователя
        message = ' '.join([self.time, self.current_test, ' - Status:', self.status])
        rocket.chat_post_message(message, channel=rocket_chat_channel, alias='Autotest_notice').json()


def main():
    rcp = RocketChatPlugin(**collects_data_report)
    rcp.send_information_to_rc()
