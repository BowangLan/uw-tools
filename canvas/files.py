from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from typing import *
import os
import asyncio
from dataclasses import dataclass, field
from httpx import AsyncClient
from models import ModelBase
from db import Base, create_db_object, filter_fields, try_add
import dateutil.parser
from sqlalchemy import Column, String, Integer, DateTime, Boolean

from util import parse_iso_datetime, print_size


default_params = {
    "include[]": [
        "user", 
        "usage_rights", 
        "enhanced_preview_url",
        "context_asset_string",
    ],
    "per_page": "20",
    "sort": "",
    "order": "",
}


def create_from_json(model, **kwargs):
    if isinstance(kwargs['updated_at'], str):
        kwargs['updated_at'] = dateutil.parser.isoparse(kwargs['updated_at']).replace(tzinfo=None)
    if isinstance(kwargs['created_at'], str):
        kwargs['created_at'] = dateutil.parser.isoparse(kwargs['created_at']).replace(tzinfo=None)
    if kwargs.get('parent'):
        kwargs['parent_id'] = kwargs['parent'].id
    if kwargs.get('course'):
        kwargs['course_id'] = kwargs['course'].id
    return create_db_object(model, **kwargs)


def update_from_json(model, session, **kwargs):
    """Update a row given a row as a dictionary if the row already exists and updated_at is greater
    Return value: (instance, status)
     - status: 0 (updated), 1 (not updated), 2 (do not exist, ins = None)
    """
    kwargs['updated_at'] = dateutil.parser.isoparse(kwargs['updated_at']).replace(tzinfo=None)
    kwargs['created_at'] = dateutil.parser.isoparse(kwargs['created_at']).replace(tzinfo=None)
    ins = session.query(model).filter_by(id=kwargs['id']).first()
    if ins:
        fields, non_fields = filter_fields(model, **kwargs)
        for k,v in non_fields.items():
            setattr(ins, k, v)
        if ins.updated_at < kwargs['updated_at']:
            for k,v in fields.items():
                setattr(ins, k, v)
            session.commit()
            return ins, 1 # udpated
        return ins, 0 # not updated
    return None, 2 # does not exist


def create_or_update(model, session, **kwargs):
    ins, u = update_from_json(
        model, session, **kwargs.copy()
    )
    if u == 1 or u == 0: # if the instance already exists
        return ins, u
    else: # if the instance doesn't exist
        ins = create_from_json(model, **kwargs)
        session.add(ins)
        session.commit()
        return ins, u




class Folder(Base):
    __tablename__ = 'folders'

    id = Column(String, primary_key=True)
    name = Column(String)
    files_count = Column(Integer)
    folders_count = Column(Integer)
    full_name = Column(String)

    files_url = Column(String)
    folders_url = Column(String)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    parent_id = Column(String)
    course_id = Column(String)

    is_root = Column(Integer, default=0)

    files: List[File] = []
    folders: List[Folder] = []
    site: "Canvas"
    parent: "Folder"
    course: "Course"


    async def get_folders(self, client: AsyncClient, session):
        res = await client.get(self.folders_url, params={'per_page': self.folders_count})
        data = res.json()
        if 'errors' in data:
            return False
        update_count = 0
        create_count = 0
        self.folders = []
        for i in data:
            kwargs = dict(
                **i, 
                site=self.site, 
                parent=self, 
                course=self.course
            )
            ins, u = create_or_update(Folder, session, **kwargs.copy())
            if u == 1:
                update_count += 1
            elif u == 2:
                create_count += 1
            self.folders.append(ins)
        print('{} files updated'.format(update_count))
        print('{} files created'.format(create_count))
        return True


    async def get_files(self, client: AsyncClient, session, params: dict = {}):
        params = default_params.copy().update(params)
        res = await client.get(self.files_url, params=params)
        data = res.json()
        if 'errors' in data:
            return False
        self.files = []
        update_count = 0
        create_count = 0
        for i in data:
            kwargs = dict(
                **i, 
                site=self.site, 
                parent=self, 
                course=self.course
            )
            ins, u = create_or_update(File, session, **kwargs.copy())
            if u == 1:
                update_count += 1
            elif u == 2:
                create_count += 1
            self.files.append(ins)
        return True


    async def get_items(
        self, 
        client: AsyncClient,
        session,
        params={},
        recursive=False,
    ):
        """Get all files and folders under the current folder"""
        file_task = asyncio.create_task(self.get_files(client, session, params=params))
        folder_task = asyncio.create_task(self.get_folders(client, session))
        await folder_task
        if recursive and folder_task:
            await asyncio.gather(
                *[f.get_items(client, session, recursive=True) for f in self.folders]
            )
        await file_task


    def tree(self, indent: bool = 1, sep: str = '-', recursive: bool = True):
        pre_str = sep * 4 * indent
        for f in self.files:
            print(pre_str + 'File:  ' + f.display_name)
        for f in self.folders:
            print(pre_str + 'Folder:' + f.name)
            if recursive:
                f.tree(indent=indent+1, recursive=recursive)


    def tree_list(self, recursive: bool = True):
        for f in self.files:
            print(f.get_relative_path())
        for f in self.folders:
            print(f.name)
            if recursive:
                f.tree_list(recursive=recursive)
        return len(self.files)

    
    def summary(self):
        print(f'Total item count: {self.count(recursive=True)}')
        print(f'Total file count: {self.count(t="file", recursive=True)}')
        print(f'Total folder count: {self.count(t="folder", recursive=True)}')
        print(f'Total size: {print_size(self.total_size())}')


    def count(self, t: str = None, recursive: bool = True):
        """Count the number of files/folders/both under the current folder"""
        len_map = { 'file': len(self.files), 'folder': len(self.folders)}
        cur = len_map.get(t, len(self.folders) + len(self.files))
        if recursive:
            cur += sum([f.count(t=t, recursive=True) for f in self.folders])
        return cur


    def total_size(self):
        """Calculate the total size of the current folder in bytes"""
        size = sum([f.size for f in self.files])
        size += sum([f.total_size() for f in self.folders])
        return size

    
    """DB related methods"""
    def save_to_db(self, session):
        """Save all files and folders under the current folder to the database"""
        try_add(session, self)
        for f in self.files:
            try_add(session, f)
        for f in self.folders:
            f.save_to_db(session)
        
    
    def load_subitems_from_db(self, session):
        """Load folder with matching id from the database"""
        self.folders: list[Folder] = session.query(Folder).filter_by(parent_id=self.id).all()
        self.files = session.query(File).filter_by(parent_id=self.id).all()
        for f in self.files + self.folders:
            f.parent = self
            f.course = self.course
            f.site = self.site
        for f in self.folders:
            f.load_subitems_from_db(session)




class File(Base):
    __tablename__ = 'files'

    id = Column(String, primary_key=True)
    filename = Column(String)
    display_name = Column(String)
    folder_id = Column(String)
    size = Column(Integer)
    url = Column(String)
    user = Column(String)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    parent_id = Column(String)
    course_id = Column(String)

    site: "Canvas"
    parent: "Folder"
    course: "Course"


    def get_relative_path(self):
        path = self.display_name
        cur_folder = self.parent
        while cur_folder:
            path = os.path.join(cur_folder.name, path)
            cur_folder = getattr(cur_folder, 'parent', None)
        return path


    async def get_detail(self, client: AsyncClient):
        url = self.site.base_url + "/api/v1/files/{}".format(self.id)
        res = client.get(url)
        data = res.json()
        for k,v in data.items():
            set(self, k, v)
        print('Got info for file ' + self.filename)


    async def download(self, client: AsyncClient = None, d: str = ''):
        filename = os.path.join(d, self.get_relative_path())
        dir = os.path.dirname(filename)
        res = await client.get(self.url, follow_redirects=True)
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(filename, 'bw') as f:
            f.write(res.content)
        print(f'{filename} saved ({len(res.content)})')



class FileManager:
    """A file manager for managing course files on canvas"""

    def __init__(self) -> None:
        pass
