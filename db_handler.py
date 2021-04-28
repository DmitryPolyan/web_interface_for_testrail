from sqlalchemy import *
from sqlalchemy.orm import create_session
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.ext.declarative import declarative_base

#Create and engine and get the metadata
Base = declarative_base()
engine = create_engine('sqlite:///testrail_db/TestrailDB.sqlite', echo=True)
metadata = MetaData(bind=engine)

class Testrail(Base):
    __table__ = Table('Testrail', metadata, autoload=True)

#Create a session to use the tables
session = create_session(bind=engine)


def get_data(id_parents):
    """
    Получение нужных данных из БД на основе их родителя.
    :param id_parents: ИД родителя
    :return:
    """
    if id_parents == -1:
        temp = [('-', '-')]
    else:
        temp = []
    data = session.query(Testrail).filter_by(id_parents=id_parents).all()
    for d in data:
        temp.append((d.id, d.name))
    return temp