from dataclasses import dataclass
import os
from __future__ import annotations
from util import with_client
import httpx
from Site import Site
from Folder import Folder

@dataclass
class File:
    id: str
    filename: str
    display_name: str
    folder_id: str
    size: int
    user: dict
    url: str

    parent: Folder
    site: Site

    created_at: str
    updated_at: str

    def get_relative_path(self):
        path = self.filename
        cur_folder = self.parent
        while cur_folder:
            path = os.path.join(cur_folder.name, path)
            cur_folder = cur_folder.parent
        return path

    @with_client
    def get_detail(self, client: httpx.Client = None):
        url = self.site.base_url + "/api/v1/files/{}".format(self.id)
        res = client.get(url)
        data = res.json()
        for k,v in data.items():
            set(self, k, v)
        print('Got info for file ' + self.filename)

    @with_client
    def download(self, client: httpx.Client = None, d: str = ''):
        filename = os.path.join(d, self.get_relative_path())
        res = client.get(self.url, follow_redirects=True)
        with open(filename, 'bw') as f:
            f.write(res.content)
        print(f'{filename} saved ({len(res.content)})')

