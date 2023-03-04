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

[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-<module>()::29] URLS_COUNT, ``10``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-<module>()::31] LIMIT, ``3``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-<module>()::32] 
---
For 10 urls, and a limit of 3 requests at-a-time, 
  we should expect 4 sets of calls, with each call and thus each set taking about 2 seconds. 
With a little extra time for overhead, and sequential json-file writes,
  the total time should be a little over 8 seconds.
---

[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-main()::80] total_delay, ``19.6`` seconds
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-main()::81] url_data, ``[{'job_name': '2006', 'url': 'http://httpbin.org/delay/2.006'},
 {'job_name': '1920', 'url': 'http://httpbin.org/delay/1.92'},
 {'job_name': '1806', 'url': 'http://httpbin.org/delay/1.806'},
 {'job_name': '2158', 'url': 'http://httpbin.org/delay/2.158'},
 {'job_name': '1964', 'url': 'http://httpbin.org/delay/1.964'},
 {'job_name': '1848', 'url': 'http://httpbin.org/delay/1.848'},
 {'job_name': '2087', 'url': 'http://httpbin.org/delay/2.087'},
 {'job_name': '2032', 'url': 'http://httpbin.org/delay/2.032'},
 {'job_name': '1808', 'url': 'http://httpbin.org/delay/1.808'},
 {'job_name': '1971', 'url': 'http://httpbin.org/delay/1.971'}]``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 7 waiting>``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::50] job, ``2032`` get starting
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 7 waiting>``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::50] job, ``1808`` get starting
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 7 waiting>``
[04/Mar/2023 17:02:01] DEBUG [trio_sem_mutex-fetch()::50] job, ``1971`` get starting
[04/Mar/2023 17:02:03] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.971 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::55] job, ``1971`` response received
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::58] job, ``1971``; elapsed_time, ``2.0823427500436082``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::64] job, ``1971`` written to json file
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 6 waiting>``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::50] job, ``2087`` get starting
[04/Mar/2023 17:02:03] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.808 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::55] job, ``1808`` response received
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::58] job, ``1808``; elapsed_time, ``2.2007986250100657``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::64] job, ``1808`` written to json file
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 5 waiting>``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::50] job, ``1848`` get starting
[04/Mar/2023 17:02:03] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.032 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::55] job, ``2032`` response received
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::58] job, ``2032``; elapsed_time, ``2.2878178749233484``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::64] job, ``2032`` written to json file
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 4 waiting>``
[04/Mar/2023 17:02:03] DEBUG [trio_sem_mutex-fetch()::50] job, ``1964`` get starting
[04/Mar/2023 17:02:05] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.848 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::55] job, ``1848`` response received
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::58] job, ``1848``; elapsed_time, ``2.0166136249899864``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::64] job, ``1848`` written to json file
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 3 waiting>``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::50] job, ``2158`` get starting
[04/Mar/2023 17:02:05] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.087 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::55] job, ``2087`` response received
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::58] job, ``2087``; elapsed_time, ``2.1519664999796078``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::64] job, ``2087`` written to json file
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 2 waiting>``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::50] job, ``1806`` get starting
[04/Mar/2023 17:02:05] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.964 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::55] job, ``1964`` response received
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::58] job, ``1964``; elapsed_time, ``2.0312898340635``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::64] job, ``1964`` written to json file
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 1 waiting>``
[04/Mar/2023 17:02:05] DEBUG [trio_sem_mutex-fetch()::50] job, ``1920`` get starting
[04/Mar/2023 17:02:07] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.806 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::55] job, ``1806`` response received
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::58] job, ``1806``; elapsed_time, ``1.9417592090321705``
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::64] job, ``1806`` written to json file
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::48] limiter-queue, ``<trio.CapacityLimiter at 0x105ec77f0, 3/3 with 0 waiting>``
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::50] job, ``2006`` get starting
[04/Mar/2023 17:02:07] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.92 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::55] job, ``1920`` response received
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::58] job, ``1920``; elapsed_time, ``1.994709249935113``
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::64] job, ``1920`` written to json file
[04/Mar/2023 17:02:07] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.158 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::55] job, ``2158`` response received
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::58] job, ``2158``; elapsed_time, ``2.2306508329929784``
[04/Mar/2023 17:02:07] DEBUG [trio_sem_mutex-fetch()::64] job, ``2158`` written to json file
[04/Mar/2023 17:02:09] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.006 "HTTP/1.1 200 OK"
[04/Mar/2023 17:02:09] DEBUG [trio_sem_mutex-fetch()::55] job, ``2006`` response received
[04/Mar/2023 17:02:09] DEBUG [trio_sem_mutex-fetch()::58] job, ``2006``; elapsed_time, ``2.144777457928285``
[04/Mar/2023 17:02:09] DEBUG [trio_sem_mutex-fetch()::64] job, ``2006`` written to json file
[04/Mar/2023 17:02:09] DEBUG [trio_sem_mutex-main()::99] full_elapsed_time, ``8.337517666979693``
"""