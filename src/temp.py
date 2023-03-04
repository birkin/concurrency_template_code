import json
import logging
import os
import random
import time

import httpx, trio


logging.basicConfig( level=logging.DEBUG )
log = logging.getLogger(__name__)


LIMIT = int( os.environ.get('ASYNC_PY_TEST__LIMIT', '3') )  # permissible number of concurrent requests


async def fetch(url, delay, lock):
    async with trio.open_nursery() as nursery:
        async with trio.Semaphore( LIMIT ) as sem:
            start_time = time.monotonic()
            await trio.sleep(delay)
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                assert response.status_code == 200
                data = response.text
                log.debug( f'data, ``{data}``' )
            end_time = time.monotonic()
            elapsed_time = end_time - start_time
            async with lock:
                with open('results.json', 'a') as f:
                    json.dump({'url': url, 'time-take': elapsed_time}, f)
                    f.write('\n')

async def main():
    urls = [f'http://httpbin.org/delay/{random.uniform(0.1, 0.5)}' for _ in range(10)]
    lock = trio.Lock()
    async with trio.open_nursery() as nursery:
        for url in urls:
            log.debug( f'url, ``{url}``' )
            nursery.start_soon(fetch, url, random.uniform(0.1, 0.5), lock)

if __name__ == '__main__':
    trio.run(main)
