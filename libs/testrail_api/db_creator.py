
import time
import datetime
from libs.testrail_api import testrail_handler_2
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData


SQLITE = 'sqlite'
TABLE = "Testrail"


class TestrailDB:
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}',
    }
    # Main DB Connection Ref Obj
    db_engine = None

    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()

        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)

            self.db_engine = create_engine(engine_url)
            print(self.db_engine)

        else:
            print("DBType is not found in DB_ENGINE")

    def create_db_tables(self):
        metadata = MetaData()
        testrail = Table(TABLE, metadata,
                      Column('id', Integer, primary_key=True),
                      Column('id_parents', Integer),
                      Column('name', String)
                      )

        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    def execute_query(self, query=''):
        if query == '' : return

        print (query)
        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)

    def delete_row(self, del_id):
        query = f"DELETE FROM {TABLE} WHERE id={del_id}"
        self.execute_query(query)
        print('Empty suites was delete')

    def delete_table(self):
        query = f"drop table if exists {TABLE}"
        self.execute_query(query)
        print('TABLE DELETE')

    def data_insert(self, id, id_parents, name):
        # Insert Data
        query = f"INSERT INTO {TABLE}(id, id_parents, name) VALUES ({id}, {id_parents},'{name}');"
        self.execute_query(query)

    def refresh_db(self):
        start_time = time.time()
        self.delete_table()
        self.create_db_tables()
        projects_id = []
        for i in testrail_handler_2.return_projects_list():
            self.data_insert(i[0], i[1], i[2])  # insert data
            projects_id.append(i[0])
        suites_id = {}
        print(projects_id)
        for i in projects_id:
            suites = []
            for j in testrail_handler_2.return_suites_list(i):
                print(j)
                self.data_insert(j[0], j[1], j[2])
                suites.append(j[0])
            suites_id[i] = suites
        sections_all_id = set()
        for i in suites_id.keys():
            for j in suites_id[i]:
                for k in testrail_handler_2.return_sections_list(i, j):
                    self.data_insert(k[0], k[1], k[2])
                    sections_all_id.add(k[0])
        for i in suites_id.keys():
            for j in suites_id[i]:
                section_id_in_suite = set()
                for k in testrail_handler_2.return_cases_list(i, j):
                    self.data_insert(k[0], k[1], k[2])
                    section_id_in_suite.add(k[1])
                sections_all_id.symmetric_difference_update(section_id_in_suite)
        # Удаляем пустые группы
        for i in sections_all_id:
            self.delete_row(i)
        time_end = time.time() - start_time
        print('Обновление базы выполнено за', time_end)


def test_schedule(folder):
    """
    Ф-я записывает текущее время в файл
    :param folder: папка, с файлом для записи
    :return:
    """
    with open(f'{folder}some_txt.txt', 'w') as f:
        f.write(str(datetime.datetime.now()))


if __name__ == '__main__':
    # trdb = TestrailDB(SQLITE, dbname=r'testrail_db\TestrailDB.sqlite')
    # trdb.refresh_db()
    test_schedule('testrail_db\\')