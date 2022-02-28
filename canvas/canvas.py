from __future__ import annotations
from typing import *
from dataclasses import dataclass, field
from httpx import AsyncClient
from bs4 import BeautifulSoup
from rich import print
from models import ModelBase
from .files import Folder


@dataclass
class Canvas:

    base_url: str = 'https://canvas.uw.edu'
    courses: List[Course] = field(default_factory=list)


    async def get_marked_courses(
        self, 
        client: AsyncClient, 
        include: list = ['term'], 
        exclude: list = ['enrollments'], 
        sort: str = 'nickname'
    ):
        url = self.base_url + "/api/v1/users/self/favorites/courses"
        # params = {
        #     'include[]': ['term'],
        #     'exclude[]': ['enrollments'],
        #     'sort': 'nickname'
        # }
        params = {
            'include[]': include,
            'exclude[]': exclude,
            'sort': sort
        }
        res = await client.get(url, params=params)
        data = res.json()
        self.courses = [
            Course(**c, site=Canvas)
            for c in data
        ]
        return self.courses


    async def get_dashboard_cards(self, client: AsyncClient):
        url = self.base_url + '/api/v1/dashboard/dashboard_cards'
        res = await client.get(url)
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
    

    async def get_folder_by_path(self, client: AsyncClient = None, path: str = ''):
        """Calling by_path API to get information about a course folder
        """
        res = await client.get(self.by_path_url(path=path))
        data = res.json()
        return Folder(**data[0], site=self.site)


    async def get_root_folder(self, client: AsyncClient = None):
        self.root_folder = await self.get_folder_by_path(client=client)


    async def ping(self, client: AsyncClient = None):
        url = self.site.base_url + "/api/v1/courses/{}/ping".format(self.id)
        res = await client.post(url)
        return res


    async def get_course_page(self, client: AsyncClient = None):
        url = self.site.base_url + '/courses/{}'.format(self.id)
        res = await client.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tabs = []
        for tab in soup.findAll(class_='section'):
            name = tab.a.string
            url = tab.a['href']
            tabs.append({'name': name, 'url': url})

        return tabs


    async def get_todo(self, user_id: str, client: AsyncClient = None, per_page: int = 10):
        params = {
            "start_date": "2021-12-25T08:00:00.000Z",
            "order": "asc",
            "context_codes[]": ["course_{}".format(self.id), "user_{}".format(user_id)],
        }
        url = self.site.base_url + "/api/v1/planner/items"
        res = await client.get(url, params=params)
        current_todo_url = res.headers['link'].split('; ')[1].split(',')[1][1:-1]
        current_todo_url = current_todo_url.replace('per_page=10', 'per_page={}'.format(per_page))
        res = await client.get(current_todo_url)
        data = res.json()
        return data



