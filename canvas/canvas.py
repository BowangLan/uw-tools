from __future__ import annotations
from typing import *
from dataclasses import dataclass, field
from httpx import AsyncClient
from bs4 import BeautifulSoup
from rich import print
from db import create_db_object, filter_fields
from models import ModelBase
from scraper import AsyncScraperBase, JSONScraperBase
from .files import Folder, create_or_update
from httpx import Response

base_url: str = 'https://canvas.uw.edu'


class CanvasScraperErrorBase(AsyncScraperBase):

    def validate_response(self, res: Response) -> bool:
        data = res.json()
        if 'errors' in data:
            self.errors += data['errors']


class CanvasMarkedCourseScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'markd_course'
    
    async def make_request(
        self, 
        include: list = ['term'], 
        exclude: list = ['enrollments'], 
        sort: str = 'nickname'
    ) -> Coroutine[Response, str, int]:
        params = {
            'include[]': include,
            'exclude[]': exclude,
            'sort': sort
        }
        url = base_url + "/api/v1/users/self/favorites/courses"
        return await self.client.get(url, params=params)


class CanvasDashboardScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'dashboard'

    async def make_request(self) -> Coroutine[Response, str, int]:
        url = base_url + '/api/v1/dashboard/dashboard_cards'
        return await self.client.get(url)
        

class CanvasCoursePingScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'course_ping'

    async def make_request(self, id: str) -> Coroutine[Response, str, int]:
        url = base_url + "/api/v1/courses/{}/ping".format(id)
        return await self.client.post(url)


class CanvasFolderByPathScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'course_folder_by_path'

    def parse(self, data: Union[list, dict]) -> dict:
        return data[0]
    
    async def make_request(self, id: str, path: str = '') -> Coroutine[Response, str, int]:
        url = base_url + "/api/v1/courses/{}/folders/by_path/{}".format(id, path)
        return await self.client.get(url)


class CanvasCourseFolderScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'course_folder_scraper'

    async def make_request(self, folders_url: str, folders_count: int) -> Coroutine[Response, str, int]:
        return await self.client.get(folders_url, params={'per_page': folders_count})


class CanvasCourseFileScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'course_file_scraper'

    async def make_request(self, id: int) -> Coroutine[Response, str, int]:
        url = base_url + "/api/v1/files/{}".format(self.id)
        return await self.client.get(url)
    

class CanvasCourseFileDetailScraper(JSONScraperBase, CanvasScraperErrorBase):

    name = 'course_file_detail_scraper'

    async def make_request(self, id: str) -> Coroutine[Response, str, int]:
        url = base_url + "/api/v1/files/{}".format(self.id)
        return await self.client.get(url)
    

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
        url = base_url + "/api/v1/users/self/favorites/courses"
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
        print(data)
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
    

    async def get_folder_by_path(self, client: AsyncClient, session, path: str = ''):
        """Calling by_path API to get information about a course folder
        """
        res = await client.get(self.by_path_url(path=path))
        data = res.json()
        # return Folder(**filter_fields(Folder, **data[0], site=self.site))
        data = data[0]
        kwargs = {
            **data, 
            'is_root': 1,
            'site': self.site,
            'parent': None,
            'course': self
        }
        ins,status = create_or_update(Folder, session, **kwargs.copy())
        return ins


    async def get_root_folder(self, client: AsyncClient, session):
        self.root_folder = await self.get_folder_by_path(client, session)
    

    def load_items_from_db(self, session):
        ins: Folder = session.query(Folder).filter_by(course_id=self.id, is_root=1).first()
        if ins:
            self.root_folder = ins
            self.root_folder.course = self
            self.root_folder.site = self.site
            self.root_folder.load_subitems_from_db(session)
        else:
            print("Course folder root doesn't exist")


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



