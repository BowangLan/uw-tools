import typing
from dataclasses import dataclass
import httpx
from .util import with_client
from api import Course

@dataclass
class Site:
    base_url = 'https://canvas.uw.edu'
    courses: typing.List[Course.CanvasCourse] = []

    @with_client
    def get_marked_courses(self, client: httpx.Client = None):
        url = self.base_url + "/api/v1/users/self/favorites/courses"
        params = {
            'include[]': ['term'],
            'exclude[]': ['enrollments'],
            'sort': 'nickname'
        }
        res = client.get(url, params=params)
        data = res.json()
        self.courses = [
            Course.CanvasCourse(**c, site=Site)
            for c in data
        ]
        return self.courses

    @with_client
    def get_dashboard_cards(self, client: httpx.Client = None):
        url = self.base_url + '/api/v1/dashboard/dashboard_cards'
        res = client.get(url)
        data = res.json()
        return data
