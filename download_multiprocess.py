import httpx
import sys
import timeit
from multiprocessing import Manager, Process

from util import with_timeit
from rich import print
from rich.progress import Progress, TransferSpeedColumn, BarColumn, TimeElapsedColumn, DownloadColumn


if len(sys.argv) == 1:
    size = '50MB'
    pcount = 50
elif len(sys.argv) == 2:
    size = sys.argv[1]
    pcount = 50
elif len(sys.argv) == 3:
    size = sys.argv[1]
    pcount = int(sys.argv[2])


test_url = r'http://ipv4.download.thinkbroadband.com/{}.zip'.format(size)
# test_url = r'https://sabnzbd.org/tests/internetspeed/{}.bin'.format(size)
# test_url = r'http://212.183.159.230/{}.zip'.format(size)


def get_content_length(url):
    res = httpx.get(url, headers={'range': 'bytes=0-1'})
    total_len = int(res.headers.get('Content-Range').split('/')[-1])
    return total_len


def download_part(b_list, rg, i, progress_dict = None) -> None:
    with httpx.stream('GET', test_url, headers={'range': 'bytes='+rg}) as r:
        for data in r.iter_bytes():
            b_list[i] += data
            if progress_dict:
                progress_dict['process'].update(progress_dict['task'], advance=len(data))
            # if task2:
            #     progress.update(task2, advance=len(data))
        # if task2:
        #     progress.update(task2, visible=False)


def divide_to_parts(total: int, part_count: int) -> list:
    part_len = total // part_count
    parts = [part_len for _ in range(part_count)]
    parts[-1] += total % part_count
    cur = 0
    output = []
    for i in range(len(parts)):
        s = '{}-{}'.format(cur, cur+parts[i]-1)
        output.append(s)
        cur += parts[i]
    return parts, output


@with_timeit
def download_by_parts(part_count: int):

    print("Getting file size...", end=" ")
    total_len = get_content_length(test_url)
    parts,parts_str = divide_to_parts(total_len, part_count)
    print(total_len)

    print('Start downloading using multiprocessing...')
    data = b''

    with Manager() as manager:
        b_list = manager.list([b'' for _ in range(len(parts))])

        processes = [
            Process(target=download_part, args=(
                b_list,
                parts_str[i],
                i,
            )) for i in range(len(parts))
        ]

        # Start processes
        for _,p in enumerate(processes):
            p.start()

        # Waiting the processes to complete
        for _,p in enumerate(processes):
            p.join()
        
        # add up parts of the file
        for b in b_list:
            data += b

    if total_len == len(data): print("[b green]Download complete")
    else: print("[b red]Download incomplete: {} / {}".format(len(data), total_len))
        




@with_timeit
def download_by_parts_with_progress_bar(part_count: int):

    print("Getting file size...", end=" ")
    total_len = get_content_length(test_url)
    parts,parts_str = divide_to_parts(total_len, part_count)
    print(total_len)

    print('Start downloading using multiprocessing...')
    data = b''

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.2f}%",
        TimeElapsedColumn(),
        TransferSpeedColumn(),
        DownloadColumn(),
    ) as progress:
        main_task = progress.add_task('[cyan]Downloading...', total=total_len)
        # tasks = [
        #     progress.add_task(
        #         'Downloading({})'.format(parts_str[i]), 
        #         total=parts[i]
        #     ) for i in range(len(parts))
        # ]

        with Manager() as manager:
            b_list = manager.list([b'' for _ in range(len(parts))])
            bar_dict = manager.dict({
                'proress': progress,
                'task': main_task
            })

            processes = [
                Process(target=download_part, args=(
                    b_list,
                    parts_str[i],
                    i,
                    # bar_dict,
                )) for i in range(len(parts))
            ]

            # Start processes
            for _,p in enumerate(processes):
                p.start()

            # Waiting the processes to complete
            for _,p in enumerate(processes):
                p.join()
            
            # add up parts of the file
            for b in b_list:
                data += b

    if total_len == len(data): print("[b green]Download complete")
    else: print("[b red]Download incomplete: {} / {}".format(len(data), total_len))
        

def test_download_by_parts():
    test_results = {}
    t_count = 12
    for pcount in range(3, 20):
        test_results[pcount] = {'data': []}
        for t in range(t_count):
            print("Start testing: part count = {}; trial = {:d}".format(pcount, t+1),end=' ')
            start = timeit.default_timer()
            download_by_parts(pcount)
            duration = timeit.default_timer() - start
            test_results[pcount]['data'].append(duration)
            print("{:.2f}s".format(duration))
        test_results[pcount]['average'] = sum(test_results[pcount]['data']) / t_count
    print('Test results:')
    print(test_results)


def main():
    download_by_parts(pcount)


if __name__ == '__main__':
    main()