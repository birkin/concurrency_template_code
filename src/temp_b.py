import json
import logging
import os
import pprint
import random
import time
from urllib.parse import urlsplit

import httpx, trio


logging.basicConfig( level=logging.DEBUG )
log = logging.getLogger(__name__)


LIMIT = int( os.environ.get('ASYNC_PY_TEST__LIMIT', '2') )  # permissible number of concurrent requests


async def fetch(url, job_name, sem, lock):
    log.debug( f'sem_a, ``{sem.value}``' )
    async with trio.open_nursery() as nursery:
        # async with trio.Semaphore( LIMIT ) as sem:
        
        async with sem:
            log.debug( f'sem_b, ``{sem.value}``' )
            start_time = time.monotonic()
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                assert response.status_code == 200
                data = response.text
                # log.debug( f'data, ``{data}``' )
            end_time = time.monotonic()
            elapsed_time = end_time - start_time
            log.debug( f'job, ``{job_name}``; elapsed_time, ``{elapsed_time}``' )
            # async with lock:
            #     time.sleep( 0.25 )
            #     with open('results.json', 'a') as f:
            #         json.dump({'url': url, 'time-take': elapsed_time}, f)
            #         f.write('\n')

async def main():
    pre_start_time = time.monotonic()
    url_data = []
    total_delay = 0
    for i in range( 20 ):
        num_a = random.randint(4800, 5200)                          # I want a little variability in the url-delay call
        num = num_a / 10000
        total_delay += num                                          # so total delay will be around 5 seconds
        url = f'http://httpbin.org/delay/{num}'
        url_data.append( {'url': url, 'job_name': str(num_a) } )    # yes, we _could_ have identical job-names, but that's ok
    log.debug( f'total_delay, ``{total_delay}``' )
    log.debug( f'url_data, ``{pprint.pformat(url_data)}``' )

    lock = trio.Lock()
    sem = trio.Semaphore( LIMIT )
    async with trio.open_nursery() as nursery:
        for entry in url_data:
            url = entry['url']
            job_name = entry['job_name']
            nursery.start_soon(fetch, url, job_name, sem, lock)

    post_end_time = time.monotonic()
    full_elapsed_time = post_end_time - pre_start_time
    log.debug( f'full_elapsed_time, ``{full_elapsed_time}``' )



if __name__ == '__main__':
    trio.run( main )
