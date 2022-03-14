import os
from httpx import AsyncClient
from canvas.files import FileModel, FolderModel


class CanvasFileManager:
    """A file manager"""

    client: AsyncClient
    root: FolderModel

    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    def latest_update(self, t = '', count: int = 10):
        """Get the latest updated files and/or folders"""
        pass

    async def download_file(self, file: FileModel):
        s = self.scrapers['file'](self.client) 
        data = await s.scrape(file.id)
        if data:
            filepath = file.get_relative_path()
            dir = os.path.dirname(filepath)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(filepath, 'wb') as f:
                f.write(data)
                print(f'{filepath} saved ({len(data)})')

    def download_folder(self, folder: FolderModel):
        pass

    def download_all(self):
        """Download all files"""
        pass

    def get_latest_file_info(self):
        """Get the latest file and folder information from the web"""
        pass

    def update_local(self):
        """Update local files and folders to match stored file information in memory"""

    async def download_latest(self):
        """Download the latest updated files"""
        await self.get_latest_file_info()
        self.update_local()
