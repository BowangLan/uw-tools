import asyncio
from venv import create
from httpx import AsyncClient
from settings import *
# from models import Canvas
from canvas.canvas import Canvas, Course
from canvas.files import Folder, File
import dateutil.parser
from util import print_size, load_cookie, save_cookie, with_async_timeit
from rich import print
from db import init_engine, create_session

# TODO load ans save cookie
# TODO file counts under folder
# TODO download folder (initial)
# TODO download to a specified directory
# TODO update folder and check diff (e.g. 0 files updated, 2 new files downloaded)
# TODO log
# TODO schedule folder update


@with_async_timeit
async def print_course(client, c: Course):
    c.ping(client=client)
    print(c.name)
    await c.get_root_folder(client=client)
    await c.root_folder.get_items(client=client)
    # print(f'Folder count: {len(c.root_folder.folders)}')
    # print(f'File count: {len(c.root_folder.files)}')
    # c.root_folder.print_tree(recursive=True)
    # c.root_folder.print_tree_list()
    
    print(f'Total item count: {c.root_folder.count(recursive=True)}')
    print(f'Total file count: {c.root_folder.count(t="file", recursive=True)}')
    print(f'Total size: {print_size(c.root_folder.total_size())}')
    print()


@with_async_timeit
async def print_courses(site: Canvas, client):
    await asyncio.gather(*[print_course(client, c) for c in site.courses])


def download_all(site, client):
    for c in site.courses:
        c.get_root_folder(client=client)


cookie = r'''ps_rvm_ZkiN={"pssid":"cUfHplPvgnivwQ3R-1641287405864","last-visit":"1641287408017"}; log_session_id=5e1a4f5641b3b064e8ce886c4a5fba7f; _legacy_normandy_session=hdpPmm_00h29fyt09UYvjA+efztve0sPZqBQf2rGW7KkaKfXr9swCyyGzG4WQnRwxx-daT9p6SUC7-kPMTZaAeHw4R_ncoyiTp2nD7-wKPhAGwtIxQ3apzIDqZu89aQv9bApvZ77GL-8ruTWiAkLvXIq5_NNR_RptQd_p1YJXj6BIu6cmxh5wya935QFLJxhxnnmlw9uDJmGph0iQUGhZ6P9lTOUekGuK8u2hHOmLg4_5CJrkA2bFtVYcYpvvykH2M1RtsqX13a6hATdIUtp0-HJRb0bYMIWP31K7vQInQ6JyNdAcnaNkrjZEHY0i0Z5MnXaAFUBi3OjCdQdmyvP0X_lsOMNWZtrM8a__47BHfrSFToZwVudVCzUzDARem8LJIx0S3_s2sVYW47TF7sR4mBeqEPCPt9QrdGjp2UzR4p4NS_3sEAVVYzeZg7t5aAXfW6NdlYyS9ETszti7HWXbbl98MESrr4LFwRrI-gaBSdJUHB3MTZ7nE18gIOeXVl4fU-AjH_1iUVeJI0dM8JwpHt7ThzPdI8KjladVkT9ADmUMt8Xb-y936j8WZIUca21fy76elFO2K18lo8IZKzGoqKSd0omSrUD1DrluUutNRFJVRUa9P7PFSjWriiMiM8kxwbmFhXHKWzgrKVsoABhDbygW28b2OW5EuHs0ePvAFs3A.EsrHwIbsK_qpCd7ryxIxYXAmGgg.YhxKTQ; canvas_session=hdpPmm_00h29fyt09UYvjA+efztve0sPZqBQf2rGW7KkaKfXr9swCyyGzG4WQnRwxx-daT9p6SUC7-kPMTZaAeHw4R_ncoyiTp2nD7-wKPhAGwtIxQ3apzIDqZu89aQv9bApvZ77GL-8ruTWiAkLvXIq5_NNR_RptQd_p1YJXj6BIu6cmxh5wya935QFLJxhxnnmlw9uDJmGph0iQUGhZ6P9lTOUekGuK8u2hHOmLg4_5CJrkA2bFtVYcYpvvykH2M1RtsqX13a6hATdIUtp0-HJRb0bYMIWP31K7vQInQ6JyNdAcnaNkrjZEHY0i0Z5MnXaAFUBi3OjCdQdmyvP0X_lsOMNWZtrM8a__47BHfrSFToZwVudVCzUzDARem8LJIx0S3_s2sVYW47TF7sR4mBeqEPCPt9QrdGjp2UzR4p4NS_3sEAVVYzeZg7t5aAXfW6NdlYyS9ETszti7HWXbbl98MESrr4LFwRrI-gaBSdJUHB3MTZ7nE18gIOeXVl4fU-AjH_1iUVeJI0dM8JwpHt7ThzPdI8KjladVkT9ADmUMt8Xb-y936j8WZIUca21fy76elFO2K18lo8IZKzGoqKSd0omSrUD1DrluUutNRFJVRUa9P7PFSjWriiMiM8kxwbmFhXHKWzgrKVsoABhDbygW28b2OW5EuHs0ePvAFs3A.EsrHwIbsK_qpCd7ryxIxYXAmGgg.YhxKTQ; _csrf_token=NsIjQhe1TnzdeSgzVOPbUDzMxZe361/vmEGTqLzvQyxkp3BwVuUqNo4pW1UEmbo7a7Tx9tCFHIT0NOrkhY5sZQ=='''


async def main():
    init_engine(database_string)
    session = create_session()

    client = AsyncClient()
    # load_cookie(client, cookie_filename)
    # client.headers.update({'cookie': cookie, 'user-agent': user_agent})
    client.headers.update({'user-agent': user_agent})

    site = Canvas()
    await site.get_marked_courses(client=client)
    c = site.courses[3]

    # c.load_items_from_db(session)

    # get folders from scraping
    await c.ping(client)
    await c.get_root_folder(client, session)
    # await c.root_folder.get_items(client, session, recursive=True)
    # print('Total folder count: {}'.format(c.root_folder.count('folder')))

    # c.root_folder.tree()
    c.root_folder.summary()

    f = c.root_folder.folders[2]
    # await f.files[0].download(client, '.')

    # await print_courses(site, client)
    # print([f.full_name for f in site.courses[-1].root_folder.folders])
    # print(site.courses[-1].root_folder.count('folder'))

    # save course folders to db
    # print("Adding all folders from course {} folder {}".format(c.name, c.root_folder.full_name))
    # c.root_folder.save_to_db(session)
    # try:
    #     session.commit()
    # except Exception as e:
    #     print(e)
    #     session.rollback()
    # print('Done')

    # load courses from db
    # for r in session.query(Folder).all():
    #     print(r.id, r.updated_at, r.full_name)
    #     print(type(r))


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

    await client.aclose()
    # save_cookie(client.cookies.jar, cookie_filename)
    

if __name__ == '__main__':
    asyncio.run(main())
