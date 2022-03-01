from abc import ABC, abstractclassmethod, abstractmethod
from typing import *
from bs4 import BeautifulSoup
from httpx import Response, AsyncClient
from numpy import kaiser
from rich import print


class AsyncScraperBase(ABC):

    name: str
    client: AsyncClient
    errors: list[dict[str: str]]

    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.errors = []

    @abstractmethod
    async def make_request(self, **kwargs: dict[str, Any]) -> Coroutine[Response, str, int]:
        pass

    async def _make_request(self, **kwargs: dict[str, Any]) -> Coroutine[Response, str, int]:
        return await self.make_request(**kwargs)

    def validate_response(self, res: Response) -> bool:
        pass

    def validate_parsed_data(self, data: Any) -> bool:
        pass

    @abstractmethod
    def parse(self, res: Response) -> Any:
        pass

    @abstractmethod
    async def scrape(self, client: AsyncClient, **kwargs: dict[str, Any]):
        try:
            res = await self._make_request(**kwargs)
            self.validate_response(res)
            if len(self.errors) == 0:
                data = self.parse(res)
                self.validate_parsed_data(data)
        except Exception as e:
            self.errors.append({
                'message': e.__class__.__name__ + ': ' + str(e.args)
            })
        if len(self.errors) != 0:
            for e in self.errors:
                print(e['message'])
            return False
        return data


class JSONScraperBase(AsyncScraperBase):

    async def _make_request(self, **kwargs: dict[str, Any]) -> Coroutine[Union[list, dict], str, int]:
        res = await self.make_request(**kwargs)
        return res.json()

    @abstractmethod
    def validate_response(self, data: Union[list, dict]) -> bool:
        pass
    
    def parse(self, data: Union[dict, list]) -> Any:
        return data


class SoupScraperBase(AsyncScraperBase):

    @abstractmethod
    def parse_soup(self, soup: BeautifulSoup) -> Any:
        pass

    def parse(self, res: Response):
        soup = BeautifulSoup(res.text, 'html.parser')
        return self.parse_soup(soup)
