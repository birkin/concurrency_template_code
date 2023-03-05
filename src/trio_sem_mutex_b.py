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


## load envars ------------------------------------------------------
URLS_COUNT = int( os.environ.get('ASYNC_PY_TEST__URLS_COUNT', '10') )   # number of urls to fetch
log.debug( f'URLS_COUNT, ``{URLS_COUNT}``' )
LIMIT = int( os.environ.get('ASYNC_PY_TEST__LIMIT', '3') )              # permissible number of concurrent requests
log.debug( f'LIMIT, ``{LIMIT}``' )
RESULTS_FILE_PATH = os.environ.get('ASYNC_PY_TEST__RESULTS_FILE_PATH', 'results.json')
log.debug( f'RESULTS_FILE_PATH, ``{RESULTS_FILE_PATH}``' )


log.debug( '''
---
For 10 urls, and a limit of 3 requests at-a-time, 
  we should expect 4 sets of calls, with each call and thus each set taking about 2 seconds. 
With a little extra time for overhead, and sequential json-file writes,
  the total time should be a little over 8 seconds.
---
''' )


async def main():
    """ Controller:
        Sets up urls & loads up queue of urls with call to fetch().
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
    limiter = trio.CapacityLimiter( LIMIT )     # trio.Semaphore( LIMIT ) would also work, but CapacityLimiter is easier to inspect
    lock = trio.Lock()
    async with trio.open_nursery() as nursery:  # if I wanted to store results, I could define a result-dict just before or after this line, and pass it to the nursery
        for entry in url_data:
            url = entry['url']
            job_name = entry['job_name']
            nursery.start_soon(fetch, url, job_name, limiter, lock)
    post_end_time = time.monotonic()            # hit after all the nursery tasks are done
    full_elapsed_time = post_end_time - pre_start_time
    log.debug( f'full_elapsed_time, ``{full_elapsed_time}``' )    

    return


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
        log.debug( f'ready to write job, ``{job_name}`` to json file at ``{time.perf_counter()}``')
        async with lock:
            log.debug( f'got lock for job, ``{job_name}`` about to write to json file at ``{time.perf_counter()}``')
            update_json_file( url, elapsed_time, job_name )
    return


def update_json_file( url, elapsed_time, job_name ):
    """ Updates file of json lines.
        Called by fetch(), synchronously. """
    # time.sleep( 0.5 )  ## enable this and view the logs to better see the effect of the lock
    with open('results.json', 'a') as f:
        jsn = json.dumps( {'url': url, 'time-taken': elapsed_time} )
        f.writelines( [jsn, '\n'] )
    log.debug( f'job, ``{job_name}`` written to json file' )
    return


if __name__ == '__main__':
    trio.run( main )


"""
Usage...

% source ../venv/bin/activate  # for access to trio and httpx
% python3 ./trio_sem_mutex.py
"""

"""
Sample output...

[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-<module>()::28] URLS_COUNT, ``10``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-<module>()::30] LIMIT, ``3``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-<module>()::32] RESULTS_FILE_PATH, ``results.json``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-<module>()::35] 
---
For 10 urls, and a limit of 3 requests at-a-time, 
  we should expect 4 sets of calls, with each call and thus each set taking about 2 seconds. 
With a little extra time for overhead, and sequential json-file writes,
  the total time should be a little over 8 seconds.
---

[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-main()::58] total_delay, ``19.856`` seconds
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-main()::59] url_data, ``[{'job_name': '2184', 'url': 'http://httpbin.org/delay/2.184'},
 {'job_name': '2169', 'url': 'http://httpbin.org/delay/2.169'},
 {'job_name': '2033', 'url': 'http://httpbin.org/delay/2.033'},
 {'job_name': '2057', 'url': 'http://httpbin.org/delay/2.057'},
 {'job_name': '1909', 'url': 'http://httpbin.org/delay/1.909'},
 {'job_name': '2037', 'url': 'http://httpbin.org/delay/2.037'},
 {'job_name': '1842', 'url': 'http://httpbin.org/delay/1.842'},
 {'job_name': '1819', 'url': 'http://httpbin.org/delay/1.819'},
 {'job_name': '1943', 'url': 'http://httpbin.org/delay/1.943'},
 {'job_name': '1863', 'url': 'http://httpbin.org/delay/1.863'}]``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 7 waiting>``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``2033`` get starting
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 7 waiting>``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``2169`` get starting
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 7 waiting>``
[05/Mar/2023 10:13:13] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``2184`` get starting
[05/Mar/2023 10:13:15] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.033 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``2033`` response received
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``2033``; elapsed_time, ``2.1644889579620212``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``2033`` to json file at ``808225.059076875``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``2033`` about to write to json file at ``808225.059165625``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``2033`` written to json file
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 6 waiting>``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``2057`` get starting
[05/Mar/2023 10:13:15] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.169 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``2169`` response received
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``2169``; elapsed_time, ``2.240068915998563``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``2169`` to json file at ``808225.142316541``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``2169`` about to write to json file at ``808225.142569833``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``2169`` written to json file
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 5 waiting>``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``1909`` get starting
[05/Mar/2023 10:13:15] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.184 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``2184`` response received
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``2184``; elapsed_time, ``2.2563744590152055``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``2184`` to json file at ``808225.162304583``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``2184`` about to write to json file at ``808225.162376916``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``2184`` written to json file
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 4 waiting>``
[05/Mar/2023 10:13:15] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``2037`` get starting
[05/Mar/2023 10:13:17] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.057 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``2057`` response received
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``2057``; elapsed_time, ``2.1472854999592528``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``2057`` to json file at ``808227.207467375``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``2057`` about to write to json file at ``808227.207582416``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``2057`` written to json file
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 3 waiting>``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``1842`` get starting
[05/Mar/2023 10:13:17] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/2.037 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``2037`` response received
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``2037``; elapsed_time, ``2.1024795840494335``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``2037`` to json file at ``808227.265386458``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``2037`` about to write to json file at ``808227.265457458``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``2037`` written to json file
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 2 waiting>``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``1819`` get starting
[05/Mar/2023 10:13:17] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.909 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``1909`` response received
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``1909``; elapsed_time, ``2.175334749976173``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``1909`` to json file at ``808227.319158875``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``1909`` about to write to json file at ``808227.319217708``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``1909`` written to json file
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 1 waiting>``
[05/Mar/2023 10:13:17] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``1943`` get starting
[05/Mar/2023 10:13:19] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.842 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:19] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.819 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``1842`` response received
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``1819`` response received
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``1842``; elapsed_time, ``1.9448090840596706``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``1842`` to json file at ``808229.153258875``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``1819``; elapsed_time, ``1.8873844160698354``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``1819`` to json file at ``808229.153523458``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``1842`` about to write to json file at ``808229.153599208``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``1842`` written to json file
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::86] limiter-queue, ``<trio.CapacityLimiter at 0x104086da0, 3/3 with 0 waiting>``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::88] job, ``1863`` get starting
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``1819`` about to write to json file at ``808229.164902458``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``1819`` written to json file
[05/Mar/2023 10:13:19] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.943 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``1943`` response received
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``1943``; elapsed_time, ``2.0138801670400426``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``1943`` to json file at ``808229.333527791``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``1943`` about to write to json file at ``808229.333823625``
[05/Mar/2023 10:13:19] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``1943`` written to json file
[05/Mar/2023 10:13:21] DEBUG [_client-_send_single_request()::1734] HTTP Request: GET http://httpbin.org/delay/1.863 "HTTP/1.1 200 OK"
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-fetch()::93] job, ``1863`` response received
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-fetch()::96] job, ``1863``; elapsed_time, ``2.045841416926123``
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-fetch()::98] ready to write job, ``1863`` to json file at ``808231.200360125``
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-fetch()::100] got lock for job, ``1863`` about to write to json file at ``808231.200675041``
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-update_json_file()::112] job, ``1863`` written to json file
[05/Mar/2023 10:13:21] DEBUG [trio_sem_mutex_b-main()::76] full_elapsed_time, ``8.307708999956958``
"""