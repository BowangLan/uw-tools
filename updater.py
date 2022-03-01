from abc import ABC, abstractclassmethod
from typing import *


class UpdaterBase():

    primary_key: str = 'id'

    def __init__(self, session, model) -> None:
        self.session = session
        self.model = model
        self.objects: list = []
        self.updated_index_list: list[int] = []
        self.created_index_list: list[int] = []

    def row_exists(self, row: Any) -> bool:
        return self.session.query(self.model).filter_by(row[self.primary_key]).first()

    def create_row(self, row: dict) -> Any:
        ins = self.model(**row)
        self.session.add(ins)
        self.session.commit()
        return ins

    def update_row(self, ins: Any, new_data: dict) -> Any:
        new_data = self.before_update(new_data)
        for k,v in new_data.items():
            setattr(ins, k, v)
        self.session.commit()
        return ins

    def should_update(self, row: dict) -> bool:
        return True

    def before_update(self, row: dict) -> Any:
        return row

    def before_insert(self, row: dict) -> Any:
        return row

    def create_or_update(self, data: list):
        self.updated_index_list = []
        self.created_index_list = []
        self.objects = []
        for i,row in enumerate(data):
            ins = self.row_exists(row)
            if ins:
                self.objects.append(ins)
                should = self.should_update(row)
                if should:
                    self.update_row(ins, row)
                    self.updated_index_list.append(i)
            else:
                ins = self.create_row(self.before_insert(row))
                self.created_index_list.append(i)
            self.objects.append(ins)
    
    def count(self) -> bool:
        return len(self.is_updated_list)

                
            

def load_latest(session):
    pass
    
        