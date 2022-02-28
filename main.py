import datetime
import dateutil.parser
import requests
import pickle
from settings import *
from models import Canvas
from pprint import pprint
from dataclasses import fields, asdict
from util import print_size, load_cookie, save_cookie

# TODO load ans save cookie
# TODO file counts under folder
# TODO download folder (initial)
# TODO download to a specified directory
# TODO update folder and check diff (e.g. 0 files updated, 2 new files downloaded)
# TODO log
# TODO schedule folder update


def print_courses(site: Canvas, client):
    for c in site.courses:
        c.ping(client=client)
        print(c.name)
        c.get_root_folder(client=client)
        c.root_folder.get_items(client=client, with_params=False, recursive=True)
        # print(f'Folder count: {len(c.root_folder.folders)}')
        # print(f'File count: {len(c.root_folder.files)}')
        c.root_folder.print_tree(recursive=True)
        # c.root_folder.print_tree_list()
        
        print(f'Total item count: {c.root_folder.count(recursive=True)}')
        print(f'Total file count: {c.root_folder.count(t="file", recursive=True)}')
        print(f'Total size: {print_size(c.root_folder.total_size())}')
        print()

def download_all(site, client):
    for c in site.courses:
        c.get_root_folder(client=client)

def main():
    client = requests.Session()
    load_cookie(client, cookie_filename)
    # client.headers.update({'cookie': cookie, 'user-agent': user_agent})
    client.headers.update({'user-agent': user_agent})

    site = Canvas()
    site.get_marked_courses(client=client)
    print_courses(site, client)

    # c1 = site.courses[3]
    # res = c1.get_course_page(client=client)
    # pprint(res)

    # user_id = '4020142'
    # res = c1.get_todo(user_id, client=client, per_page=40)
    # for p in res:
        # todo = p['plannable']
        # if todo.get('start_at'):
            # start = dateutil.parser.isoparse(todo['start_at'])
        # else:
            # start = ''
        # print('TODO: ' + todo['title'] + '\n' + ' '*6 + str(start))

    save_cookie(client, cookie_filename)
    client.close()
    

if __name__ == '__main__':
    main()
