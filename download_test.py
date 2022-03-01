from httpx import AsyncClient, Request
import asyncio
import timeit

from util import with_async_timeit
from rich import print
from rich.progress import Progress, TransferSpeedColumn, BarColumn, TimeElapsedColumn, DownloadColumn
import sys


print(sys.argv)
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


async def get_content_length(client, url):
    res = await client.get(url, headers={'range': 'bytes=0-1'})
    total_len = int(res.headers.get('Content-Range').split('/')[-1])
    return total_len

@with_async_timeit
async def download(client: AsyncClient):
    print('Start sync downloading')
    data = b''
    total_len = await get_content_length(client, test_url)
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.2f}%",
        TimeElapsedColumn(),
        TransferSpeedColumn(),
        DownloadColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Downloading...", total=total_len)
        async with client.stream('GET', test_url) as r:
            async for chunk in r.aiter_bytes():
                data += chunk
                progress.update(task, advance=len(chunk))
    print("Data length", len(data))
    


@with_async_timeit
async def download_by_parts(client: AsyncClient, req: Request):
    b_list = []
    async def download_part(rg, i, progress, task, task2 = None) -> None:
        req.headers.update({'range': 'bytes='+rg})
        r = await client.send(req, stream=True)
        async for data in r.aiter_bytes():
            b_list[i] += data
            progress.update(task, advance=len(data))
            if task2:
                progress.update(task2, advance=len(data))
        await r.aclose()
        if task2:
            progress.update(task2, visible=False)
    
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

    print('Start async downloading')
    res = await client.get(test_url, headers={'range': 'bytes=0-1'})
    total_len = int(res.headers.get('Content-Range').split('/')[-1])
    part_count = 80
    parts,parts_str = divide_to_parts(total_len, part_count)
    b_list = [b'' for _ in range(len(parts))]
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
        await asyncio.gather(*[
            download_part(
                parts_str[i],
                i,
                progress,
                main_task,
                # tasks[i]
            ) for i in range(len(parts))
        ])
        for b in b_list:
            data += b
    if total_len == len(data): print("[b green]Download complete")
    else: print("[b red]Download incomplete: {} / {}".format(len(data), total_len))
        

async def test_download_by_parts(client):
    test_results = {}
    t_count = 12
    for pcount in range(3, 20):
        test_results[pcount] = {'data': []}
        for t in range(t_count):
            print("Start testing: part count = {}; trial = {:d}".format(pcount, t+1),end=' ')
            start = timeit.default_timer()
            await download_by_parts(client, pcount)
            duration = timeit.default_timer() - start
            test_results[pcount]['data'].append(duration)
            print("{:.2f}s".format(duration))
        test_results[pcount]['average'] = sum(test_results[pcount]['data']) / t_count
    print('Test results:')
    print(test_results)




    
async def main():
    async with AsyncClient() as client:
        req = client.build_request('GET', test_url)
        await download_by_parts(client, req)
        # await download(client)
        # await test_download_by_parts(client)

asyncio.run(main())