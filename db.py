from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import *


Base = declarative_base()


def init_engine(db_string):
    global engine, Session
    engine = create_engine(db_string)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)


def create_session():
    global Session
    return Session()
    

def filter_fields(cls: DeclarativeMeta, **kwargs) -> dict[str, Any]:
    def is_field(k):
        return k in cls.__table__.columns
    def is_non_field(k):
        return k in cls.__dict__['__annotations__'].keys() or k in cls.__dict__.keys()

    ignore_fields = []
    non_fields = {} # keys that are attributes of the class but are not table fields

    for k,v in kwargs.items():
        if is_field(k):
            continue
        if is_non_field(k):
            non_fields[k] = v
            continue
        ignore_fields.append(k)
    for k in ignore_fields:
        del kwargs[k]
    for k in non_fields.keys():
        del kwargs[k]
    return kwargs, non_fields


def create_db_object(model: DeclarativeMeta, **kwargs) -> Any:
    kwargs, non_fields = filter_fields(model, **kwargs)
    obj = model(**kwargs)
    for k,v in non_fields.items():
        setattr(obj, k, v)
    return obj


def get_or_create(session, model, **kwargs):
    obj = session.query(model).filter_by(*kwargs).first()
    if obj:
        return obj
    
def add_or_update(session, model, instance, primary_key: str = 'id'):
    ins_ = session.query(model).filter(**{primary_key: getattr(instance, primary_key)}).first()
    if ins_:
        pass

def try_add(session, instance):
    try:
        session.add(instance)
        session.commit()
    except Exception as e:
        # print(e)
        session.rollback()