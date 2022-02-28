import requests
import pickle

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

def load_cookie(client: requests.Session, cookie_filename):
    with open(cookie_filename, 'rb') as f:
        client.cookies.update(pickle.load(f))

def save_cookie(client: requests.Session, cookie_filename):
    with open(cookie_filename, 'wb') as f:
        pickle.dump(client.cookies, f)

