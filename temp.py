from cookie import *
import httpx
from pprint import pprint


def get_course_folders(client: httpx.Client, course_id):
    folder_id = get_course_folder_id(client, course_id)
    data = get_folders(client, folder_id)
    data = [{
        'content': get_items(client, f_data['id']),
        **f_data
    } for f_data in data]
    # pprint(data)
    return data


def get_folders(client: httpx.Client, folder_id):
    url = "https://canvas.uw.edu/api/v1/folders/{}/folders".format(folder_id)
    res = client.get(url)
    data = res.json()
    data = list(map(lambda item: {
        'name': item['name'],
        'id': item['id']
    }, data))
    # pprint(data)
    return data


def get_file_detail(client: httpx.Client, file_id: str):
    url = "https://canvas.uw.edu/api/v1/files/" + file_id
    res = client.get(url) 
    data = res.json()
    return data
    # pprint(data)


def get_items(client: httpx.Client, folder_id: str):
    file_url = "https://canvas.uw.edu/api/v1/folders/{}/files".format(folder_id)
    folder_url = "https://canvas.uw.edu/api/v1/folders/{}/folders".format(folder_id)
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
    res = client.get(folder_url, params=params)
    res = client.get(file_url, params=params)
    data = res.json()
    data = list(map(lambda item: {
        'filename': item['display_name'],
        'id': str(item['id']),
        'folder_id': str(item['folder_id']),
        'size': item['size'],
        'by_user': item['user']['display_name'],
        'url': get_file_detail(client, str(item['id']))['url']
    }, data))
    return data
    

def get_course_folder_id(client: httpx.Client, course_id: str, path: str = ''):
    url = "https://canvas.uw.edu/api/v1/courses/{}/folders/by_path/".format(course_id)
    res = client.get(url)
    data = res.json()
    return data[0]['id']
    # if res.status_code == 200:
        # data = res.json()
        # files_url = data[0]['files_url']
        # folders_url = data[0]['folders_url']


def download_file(client: httpx.Client, url: str, filename: str):
    res = client.get(url, follow_redirects=True)
    print(res.status_code)
    with open(filename, 'bw') as f:
        f.write(res.content)
    print(f'{filename} saved ({len(res.content)})')


def ping_course(client: httpx.Client, course_id: str):
    url = "https://canvas.uw.edu/api/v1/courses/{}/ping".format(course_id)
    res = client.post(url)
    data = res.json()
    print('Ping {}: {}'.format(course_id, str(data)))


def get_all_courses(client: httpx.Client):
    url = "https://canvas.uw.edu/api/v1/users/self/favorites/courses"
    params = {
        'include[]': ['term'],
        'exclude[]': ['enrollments'],
        'sort': 'nickname'
    }
    res = client.get(url, params=params)
    data = res.json()
    return data

client = httpx.Client()
client.headers.update({'cookie': cookie, 'user-agent': user_agent})
c_id = '1518801'
ping_course(client, c_id)

# f_id = '86282420'
# f = get_file_detail(client, f_id)
# download_file(client, f['url'], f['filename'])

# folder_id = "10249330"
# get_files(client, folder_id=folder_id)

# get_folders(client, '9484264')

file_count = 0
folder_count = 0
data = get_course_folders(client, '1517469')
for f in data:
    print(f['name'])
    for f2 in f['content']:
        print(' '*4 + f2['filename'])
        # print(' '*4 + f2['url'])
