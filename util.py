import timeit
from httpx import AsyncClient
import dateutil.parser
import requests
import pickle
from rich import print

def with_client(func):
    def wrapper(*args, client: requests.Session = None, **kwargs):
        if not client:
            print('Client not specified')
            return
        res = func(*args, client=client, **kwargs)
        return res
    return wrapper

def print_size(size, unit_size: int = 1024, unit: str = 'B', current: str = ''):
    if size < unit_size ** 1:
        pass
    elif size < unit_size ** 2:
        unit = 'K' + unit
        size = float(size) / unit_size
    elif size < unit_size ** 3:
        unit = 'M' + unit
        size = float(size) / unit_size ** 2
    elif size < unit_size ** 4:
        unit = 'G' + unit
        size = float(size) / unit_size ** 3
    elif size < unit_size ** 5:
        unit = 'T' + unit
        size = float(size) / unit_size ** 4
    else:
        return size
    return '%.2f %s' % (size, unit)

def load_cookie(client: AsyncClient , cookie_filename):
    with open(cookie_filename, 'rb') as f:
        client.cookies.update(pickle.load(f))

def save_cookie(cookie_jar, cookie_filename):
    with open(cookie_filename, 'wb') as f:
        pickle.dump(cookie_jar, f)

def with_timeit(func):
    def wrapper(*args, **kwargs):
        start = timeit.default_timer()
        func(*args, **kwargs)
        duration = timeit.default_timer() - start
        print("Finish in {:.2f} seconds".format(duration))
    return wrapper

def with_async_timeit(func):
    async def wrapper(*args, **kwargs):
        start = timeit.default_timer()
        await func(*args, **kwargs)
        duration = timeit.default_timer() - start
        print("Finish in {:.2f} seconds".format(duration))
    return wrapper


def parse_iso_datetime(dt_string):
    return dateutil.parser.isoparse(dt_string).replace(tzinfo=None)