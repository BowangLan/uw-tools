from __future__ import annotations
import os
from dataclasses import dataclass, field, fields, _MISSING_TYPE
import typing
from util import with_client, print_size
import requests
from bs4 import BeautifulSoup

@dataclass(init=False)
class ModelBase:

    def __init__(self, **kwargs):
        fields_ = [f for f in fields(self)]
        names = set([f.name for f in fields_])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)
        for f in fields_:
            if f.name not in list(kwargs.keys()):
                if not isinstance(f.default, _MISSING_TYPE):
                    v = f.default
                elif not isinstance(f.default_factory, _MISSING_TYPE):
                    v = f.default_factory()
                else:
                    v = None
                setattr(self, f.name, v)


@dataclass
class Canvas:
    base_url: str = 'https://canvas.uw.edu'
    courses: typing.List[Course] = field(default_factory=list)

    @with_client
    def get_marked_courses(self, client: requests.Session = None):
        url = self.base_url + "/api/v1/users/self/favorites/courses"
        params = {
            'include[]': ['term'],
            'exclude[]': ['enrollments'],
            'sort': 'nickname'
        }
        res = client.get(url, params=params)
        data = res.json()
        self.courses = [
            Course(**c, site=Canvas)
            for c in data
        ]
        return self.courses

    @with_client
    def get_dashboard_cards(self, client: requests.Session = None):
        url = self.base_url + '/api/v1/dashboard/dashboard_cards'
        res = client.get(url)
        data = res.json()
        return data




@dataclass(init=False)
class Course(ModelBase):
    """This class represents a course on Canvas"""
    account_id: str
    id: str
    site: Canvas
    course_code: str
    name: str
    friendly_name: str
    term: dict
    calendar = dict

    enrollment_term_id: str
    start_at: str

    root_folder: Folder = None
    
    def by_path_url(self, path: str = ''):
        return self.site.base_url + "/api/v1/courses/{}/folders/by_path/{}".format(
            self.id, path
        )
    
    @with_client
    def get_folder_by_path(self, client: requests.Session = None, path: str = ''):
        """Calling by_path API to get information about a course folder
        """
        res = client.get(self.by_path_url(path=path))
        data = res.json()
        return Folder(**data[0], site=self.site)

    @with_client
    def get_root_folder(self, client: requests.Session = None):
        self.root_folder = self.get_folder_by_path(client=client)

    @with_client
    def ping(self, client: requests.Session = None):
        url = self.site.base_url + "/api/v1/courses/{}/ping".format(self.id)
        res = client.post(url)
        return res

    @with_client
    def get_course_page(self, client: requests.Session = None):
        url = self.site.base_url + '/courses/{}'.format(self.id)
        res = client.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tabs = []
        for tab in soup.findAll(class_='section'):
            name = tab.a.string
            url = tab.a['href']
            tabs.append({'name': name, 'url': url})

        return tabs

    @with_client
    def get_todo(self, user_id: str, client: requests.Session = None, per_page: int = 10):
        params = {
            "start_date": "2021-12-25T08:00:00.000Z",
            "order": "asc",
            "context_codes[]": ["course_{}".format(self.id), "user_{}".format(user_id)],
        }
        url = self.site.base_url + "/api/v1/planner/items"
        res = client.get(url, params=params)
        current_todo_url = res.headers['link'].split('; ')[1].split(',')[1][1:-1]
        current_todo_url = current_todo_url.replace('per_page=10', 'per_page={}'.format(per_page))
        res = client.get(current_todo_url)
        data = res.json()
        return data




@dataclass(init=False)
class Folder(ModelBase):
    id: str
    name: str
    site: Canvas
    full_name: str = None
    parent: Folder = None

    files_url: str = None
    folders_url: str = None
    files: typing.List[File] = field(default_factory=list)
    folders: typing.List[Folder] = field(default_factory=list)

    created_at: str = None
    updated_at: str = None


    def make_get_items_params(self, **kwargs):
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
        if kwargs:
            params.update(kwargs)
        return params


    @with_client
    def get_items(
        self, 
        client: requests.Session = None, 
        with_params=True,
        params={},
        recursive=False,
    ):
        """Get all files and folders under the current folder.
        """
        params = self.make_get_items_params(**params)
        if with_params:
            folder_res = client.get(self.folders_url, params=params)
        else:
            folder_res = client.get(self.folders_url)
        file_res = client.get(self.files_url, params=params)
        folder_data = folder_res.json()
        file_data = file_res.json()
        if 'errors' in folder_data:
            # print(data)
            # print('Not authorized')
            return
        try:
            self.folders = [ 
                Folder(
                    **i,
                    site=self.site,
                    parent=self
                ) 
                for i in folder_data]
            self.files = [ 
                File(
                    **i,
                    site=self.site,
                    parent=self
                ) 
                for i in file_data]
            if recursive:
                [f.get_items(client=client, recursive=True) for f in self.folders]
            return True
        except:
            print('error')
            # print(data)

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
        if t == 'file':
            cur = len(self.files)
        elif t == 'folder':
            cur = len(self.folders)
        else:
            cur = len(self.files) + len(self.folders)
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

    @with_client
    def get_detail(self, client: requests.Session = None):
        url = self.site.base_url + "/api/v1/files/{}".format(self.id)
        res = client.get(url)
        data = res.json()
        for k,v in data.items():
            set(self, k, v)
        print('Got info for file ' + self.filename)

    @with_client
    def download(self, client: requests.Session = None, d: str = ''):
        filename = os.path.join(d, self.get_relative_path())
        res = client.get(self.url, follow_redirects=True)
        with open(filename, 'bw') as f:
            f.write(res.content)
        print(f'{filename} saved ({len(res.content)})')


