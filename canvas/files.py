from __future__ import annotations
from typing import *
import os
import asyncio
from dataclasses import dataclass, field
from httpx import AsyncClient
from models import ModelBase


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


@dataclass(init=False)
class Folder(ModelBase):
    id: str
    name: str
    site: "Canvas"
    full_name: str = None
    parent: "Folder" = None

    files_url: str = None
    folders_url: str = None
    files: List[File] = field(default_factory=list)
    folders: List[Folder] = field(default_factory=list)

    created_at: str = None
    updated_at: str = None


    async def get_folders(self, client: AsyncClient, with_params: bool = True, params: dict = {}):
        if with_params:
            params = default_params.copy().update(params)
            res = await client.get(self.folders_url, params=params)
        else:
            res = await client.get(self.folders_url)
        data = res.json()
        if 'errors' in data:
            return False
        self.folders = [ 
            Folder(
                **i,
                site=self.site,
                parent=self
            ) for i in data
        ]
        return True


    async def get_files(self, client: AsyncClient, params: dict = {}):
        params = default_params.copy().update(params)
        res = await client.get(self.files_url, params=params)
        data = res.json()
        if 'errors' in data:
            return False
        self.files = [ 
            File(
                **i,
                site=self.site,
                parent=self
            ) for i in data
        ]
        return True


    async def get_items(
        self, 
        client: AsyncClient,
        with_params=True,
        params={},
        recursive=False,
    ):
        """Get all files and folders under the current folder."""
        file_task = asyncio.create_task(self.get_files(client, params=params))
        folder_task = asyncio.create_task(self.get_folders(client, with_params=with_params, params=params))
        await folder_task
        if recursive and folder_task:
            await asyncio.gather(
                *[f.get_items(client=client, recursive=True) for f in self.folders]
            )
        await file_task


    def print_tree(self, indent: bool = 1, sep: str = '-', recursive: bool = True):
        pre_str = sep * 4 * indent
        for f in self.files:
            print(pre_str + 'File:  ' + f.display_name)
        for f in self.folders:
            print(pre_str + 'Folder:' + f.name)
            if recursive:
                f.print_tree(indent=indent+1, recursive=recursive)


    def print_tree_list(self, recursive: bool = True):
        for f in self.files:
            print(f.get_relative_path())
        for f in self.folders:
            print(f.name)
            if recursive:
                f.print_tree_list(recursive=recursive)
        return len(self.files)


    def count(self, t: str = None, recursive: bool = False):
        """Count the number of files/folders/both under the current folder"""
        len_map = { 'file': len(self.files), 'folder': len(self.folders) }
        cur = len_map.get(t, len(self.files) + len(self.folders))
        if recursive:
            cur += sum([f.count(t=t, recursive=True) for f in self.folders])
        return cur

    def total_size(self):
        size = sum([f.size for f in self.files])
        size += sum([f.total_size() for f in self.folders])
        return size



@dataclass(init=False)
class File(ModelBase):
    id: str
    filename: str
    display_name: str
    folder_id: str
    size: int
    user: dict
    url: str

    parent: Folder
    site: Canvas

    created_at: str
    updated_at: str


    def get_relative_path(self):
        path = self.display_name
        cur_folder = self.parent
        while cur_folder:
            path = os.path.join(cur_folder.name, path)
            cur_folder = cur_folder.parent
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
        res = client.get(self.url, follow_redirects=True)
        with open(filename, 'bw') as f:
            f.write(res.content)
        print(f'{filename} saved ({len(res.content)})')


