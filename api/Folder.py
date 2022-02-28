import typing
from __future__ import annotations
from dataclasses import dataclass
from .util import with_client
import httpx
from .Site import Site
from .File import File

@dataclass
class Folder:
    id: str
    name: str
    full_name: str = None
    parent: Folder = None

    full_files_url: str = None
    full_folders_url: str = None
    files: typing.List[File] = None
    folders: typing.List[Folder] = None

    created_at: str = None
    updated_at: str = None

    site: Site

    def make_get_items_params(self):
        params = {
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
        return params

    @with_client
    def get_files(self, client: httpx.Client = None):
        params = self.make_get_items_params()
        res = client.get(self.full_files_url, params=params)
        data = res.json()
        self.files = [
            File(
                **data,
                site=self.site,
                parent=self
            ) 
        for i in data]
        return self.files

    @with_client
    def get_folders(self, client: httpx.Client = None, with_params=True):
        if with_params:
            params = self.make_get_items_params()
            res = client.get(self.full_folders_url, params=params)
        else:
            res = client.get(self.full_folders_url)
        data = res.json()
        self.folders = [
            Folder(
                id=str(i['id']), 
                name=i['name'], 
                site=self.site,
                parent=self
            ) 
        for i in data]
    
    @with_client
    def get_items(self, client: httpx.Client = None):
        self.get_folders(client=client)
        self.get_files(client=client)
