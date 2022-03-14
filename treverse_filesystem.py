import os
import sys
import asyncio
import multiprocessing
from util import print_size, with_timeit, with_async_timeit


@with_async_timeit
async def async_get_file_info(d):
    return list(os.walk(d))


@with_timeit
def get_file_info(d):
    return list(os.walk(d))


def get_folder_size(walk):
    size = 0
    for path, _, files in walk:
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


async def main():
    d = get_file_info(os.path.expanduser('~'))
    size = get_folder_size(d)
    print("Folder size: {}".format(print_size(size)))


if __name__ == '__main__':
    asyncio.run(main())