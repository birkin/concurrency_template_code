"""
Trio semaphore and mutex example.
Note: technically uses trio's `CapacityLimiter` as a semaphore, because it's easier to inspect.
"""

import datetime
import json
import logging
import os
import pprint
import random
import time

import httpx    # sync and async http client
import trio     # async library


logging.basicConfig( 
    level=logging.DEBUG ,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', 
    datefmt='%d/%b/%Y %H:%M:%S'
    )


log = logging.getLogger(__name__)


URLS_COUNT = int( os.environ.get('ASYNC_PY_TEST__URLS_COUNT', '10') )   # number of urls to fetch
log.debug( f'URLS_COUNT, ``{URLS_COUNT}``' )
LIMIT = int( os.environ.get('ASYNC_PY_TEST__LIMIT', '3') )              # permissible number of concurrent requests
log.debug( f'LIMIT, ``{LIMIT}``' )
log.debug( '''
---
For 10 urls, and a limit of 3 requests at-a-time, 
  we should expect 4 sets of calls, with each call and thus each set taking about 2 seconds. 
With a little extra time for overhead, and sequential json-file writes,
  the total time should be a little over 8 seconds.
---
''' )


async def fetch(url, job_name, limiter, lock):
    """ Queries urls asynchronously (respecting limiter), and updates (synchronously) json file.
        Called by main() """

    async with limiter:
        ## when limiter allows, query url -----------------------
        log.debug( f'limiter-queue, ``{limiter}``' )
        start_time = time.monotonic()
        log.debug( f'job, ``{job_name}`` get starting' )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            assert response.status_code == 200
            data = response.text
            log.debug( f'job, ``{job_name}`` response received' )
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        log.debug( f'job, ``{job_name}``; elapsed_time, ``{elapsed_time}``' )
        ## _synchronosly_ update json file ----------------------
        async with lock:
            with open('results.json', 'a') as f:
                json.dump({'url': url, 'time-taken': elapsed_time}, f)
                f.write('\n')
        log.debug( f'job, ``{job_name}`` written to json file' )


async def main():
    """ Sets up urls & loads up queue of urls.
        Called by if __name__ == '__main__' """
    
    ## set up urls --------------------------------------------------
    url_data = []
    total_delay = 0
    for i in range( URLS_COUNT ):
        rndm_num = random.randint(1800, 2200)                          # I want a little variability in the 2-second url-delay call
        actual_num = rndm_num / 1000
        total_delay += actual_num                                      # so total delay if sequential would be c. 20 seconds
        url = f'http://httpbin.org/delay/{actual_num}'
        url_data.append( {'url': url, 'job_name': str(rndm_num) } )    # yes, we _could_ have identical job-names, but that's ok
    log.debug( f'total_delay, ``{total_delay}`` seconds' )
    log.debug( f'url_data, ``{pprint.pformat(url_data)}``' )

    ## clear json file ----------------------------------------------
    with open('results.json', 'w') as f:
        jsn = json.dumps( {'run_timestamp': str(datetime.datetime.now())} )
        f.writelines( [jsn, '\n'],  )

    ## query urls ---------------------------------------------------
    pre_start_time = time.monotonic()
    limiter = trio.CapacityLimiter( LIMIT )                             # trio.Semaphore( LIMIT ) would also work, but CapacityLimiter is easier to inspect
    lock = trio.Lock()
    async with trio.open_nursery() as nursery:
        for entry in url_data:
            url = entry['url']
            job_name = entry['job_name']
            nursery.start_soon(fetch, url, job_name, limiter, lock)
    post_end_time = time.monotonic()
    full_elapsed_time = post_end_time - pre_start_time
    log.debug( f'full_elapsed_time, ``{full_elapsed_time}``' )    


if __name__ == '__main__':
    trio.run( main )


"""
Usage...

% source ../venv/bin/activate  # for access to trio and httpx
% python3 ./trio_sem_mutex.py
"""

"""
Sample output...

[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-<module>()::29] URLS_COUNT, ``10``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-<module>()::31] LIMIT, ``3``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-<module>()::32] 
---
For 10 urls, and a limit of 3 requests at-a-time, 
  we should expect 4 sets of calls, with each call and thus each set taking about 2 seconds. 
With a little extra time for overhead, and sequential json-file writes,
  the total time should be a little over 8 seconds.
---

[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-main()::80] total_delay, ``19.433999999999997`` seconds
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-main()::81] url_data, ``[{'job_name': '2175', 'url': 'http://httpbin.org/delay/2.175'},
 {'job_name': '1934', 'url': 'http://httpbin.org/delay/1.934'},
 {'job_name': '1819', 'url': 'http://httpbin.org/delay/1.819'},
 {'job_name': '1817', 'url': 'http://httpbin.org/delay/1.817'},
 {'job_name': '2074', 'url': 'http://httpbin.org/delay/2.074'},
 {'job_name': '1864', 'url': 'http://httpbin.org/delay/1.864'},
 {'job_name': '1986', 'url': 'http://httpbin.org/delay/1.986'},
 {'job_name': '1944', 'url': 'http://httpbin.org/delay/1.944'},
 {'job_name': '1895', 'url': 'http://httpbin.org/delay/1.895'},
 {'job_name': '1926', 'url': 'http://httpbin.org/delay/1.926'}]``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 7 waiting>``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::50] job, ``1819`` get starting
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 7 waiting>``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::50] job, ``1934`` get starting
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 7 waiting>``
[04/Mar/2023 17:05:08] DEBUG [trio_sem_mutex-fetch()::50] job, ``2175`` get starting
[04/Mar/2023 17:05:10] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.819 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:10] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.934 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::55] job, ``1819`` response received
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::55] job, ``1934`` response received
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::58] job, ``1819``; elapsed_time, ``2.030095124966465``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::58] job, ``1934``; elapsed_time, ``2.022778750048019``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::64] job, ``1819`` written to json file
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::64] job, ``1934`` written to json file
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 5 waiting>``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::50] job, ``1817`` get starting
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 5 waiting>``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::50] job, ``2074`` get starting
[04/Mar/2023 17:05:10] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.175 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::55] job, ``2175`` response received
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::58] job, ``2175``; elapsed_time, ``2.2459352910518646``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::64] job, ``2175`` written to json file
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 4 waiting>``
[04/Mar/2023 17:05:10] DEBUG [trio_sem_mutex-fetch()::50] job, ``1864`` get starting
[04/Mar/2023 17:05:12] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.817 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::55] job, ``1817`` response received
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::58] job, ``1817``; elapsed_time, ``1.941491000005044``
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::64] job, ``1817`` written to json file
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 3 waiting>``
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::50] job, ``1986`` get starting
[04/Mar/2023 17:05:12] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.074 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::55] job, ``2074`` response received
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::58] job, ``2074``; elapsed_time, ``2.147264374885708``
[04/Mar/2023 17:05:12] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.864 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::64] job, ``2074`` written to json file
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::55] job, ``1864`` response received
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 2 waiting>``
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::50] job, ``1944`` get starting
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::58] job, ``1864``; elapsed_time, ``1.9434524590615183``
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::64] job, ``1864`` written to json file
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 1 waiting>``
[04/Mar/2023 17:05:12] DEBUG [trio_sem_mutex-fetch()::50] job, ``1895`` get starting
[04/Mar/2023 17:05:14] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.986 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::55] job, ``1986`` response received
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::58] job, ``1986``; elapsed_time, ``2.147870291955769``
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::64] job, ``1986`` written to json file
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x1056178e0, 3/3 with 0 waiting>``
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::50] job, ``1926`` get starting
[04/Mar/2023 17:05:14] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.895 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::55] job, ``1895`` response received
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::58] job, ``1895``; elapsed_time, ``1.979730417020619``
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::64] job, ``1895`` written to json file
[04/Mar/2023 17:05:14] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.944 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::55] job, ``1944`` response received
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::58] job, ``1944``; elapsed_time, ``2.342596333939582``
[04/Mar/2023 17:05:14] DEBUG [trio_sem_mutex-fetch()::64] job, ``1944`` written to json file
[04/Mar/2023 17:05:16] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.926 "HTTP/1.1 200 OK"
[04/Mar/2023 17:05:16] DEBUG [trio_sem_mutex-fetch()::55] job, ``1926`` response received
[04/Mar/2023 17:05:16] DEBUG [trio_sem_mutex-fetch()::58] job, ``1926``; elapsed_time, ``2.0467622079886496``
[04/Mar/2023 17:05:16] DEBUG [trio_sem_mutex-fetch()::64] job, ``1926`` written to json file
[04/Mar/2023 17:05:16] DEBUG [trio_sem_mutex-main()::99] full_elapsed_time, ``8.173782166908495``
"""