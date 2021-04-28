class BasePluginsClass():
    def __init__(self, **collects_data_report):
        self.__time = collects_data_report.get('time')
        self.__status = collects_data_report.get('status')
        self.__current_test = collects_data_report.get('current_test')
        self.__author = collects_data_report.get('author')


    @staticmethod
    def plugin_description():
        """
        Ф-я для возвращения описания действий плагина
        """
        pass

    @property
    def time(self):
        return self.__time

    @property
    def status(self):
        return self.__status

    @property
    def current_test(self):
        return self.__current_test

    @property
    def author(self):
        return self.__author
