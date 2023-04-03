"""
Trio semaphore and mutex example.
Note: technically uses trio's `CapacityLimiter` as a semaphore, because it's easier to inspect.
"""

import datetime
import json
import logging
import math
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
SYNCHRONOUS_WRITE_DELAY = float( os.environ.get('ASYNC_PY_TEST__SYNCHRONOUS_WRITE_DELAY', '0.5') )
log.debug( f'SYNCHRONOUS_WRITE_DELAY, ``{SYNCHRONOUS_WRITE_DELAY}``' )

estimate_sequential_processing_time = math.ceil( (URLS_COUNT * 2) + (URLS_COUNT * SYNCHRONOUS_WRITE_DELAY) )
estimate_async_processing_time_a = math.ceil( (URLS_COUNT * 2 / LIMIT) )
# log.debug( f'estimate_async_processing_time_a, ``{estimate_async_processing_time_a}``' )
estimate_async_processing_time_b = math.ceil( (URLS_COUNT * SYNCHRONOUS_WRITE_DELAY) )
# log.debug( f'estimate_async_processing_time_b, ``{estimate_async_processing_time_b}``' )
estimate_async_processing_time = estimate_async_processing_time_a + estimate_async_processing_time_b
# log.debug( f'estimate_async_processing_time, ``{estimate_async_processing_time}``' )
log.debug( f'''
---
For {URLS_COUNT} urls, each requiring about 2-seconds to respond, 
    and a file-write delay of {SYNCHRONOUS_WRITE_DELAY} seconds, 
    sequential processing would take about {estimate_sequential_processing_time} seconds.

Our asynchrous processing, with a limit of {LIMIT} requests at-a-time,
    still with a file-write delay of {SYNCHRONOUS_WRITE_DELAY} seconds,
    should take a little over {estimate_async_processing_time} seconds.
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
    results_dct = {}                            # fetch() will update this dict, just to show how data from different tasks can be shared
    limiter = trio.CapacityLimiter( LIMIT )     # trio.Semaphore( LIMIT ) would also work, but CapacityLimiter is easier to inspect
    lock = trio.Lock()
    async with trio.open_nursery() as nursery:
        for entry in url_data:
            url = entry['url']
            job_name = entry['job_name']
            nursery.start_soon(fetch, url, job_name, results_dct, limiter, lock)

    ## final write to json file ------------------------------------
    with open('results.json', 'a') as f:
        jsn = json.dumps( results_dct, sort_keys=True, indent=2 )
        f.writelines( [jsn, '\n'] )
    log.debug( f'results_dct appended to json file' )

    ## log time ----------------------------------------------------
    post_end_time = time.monotonic()            # hit after all the nursery tasks are done
    full_elapsed_time = post_end_time - pre_start_time
    log.debug( f'full_elapsed_time, ``{full_elapsed_time}``' )    

    return


async def fetch(url, job_name, results_dct, limiter, lock):
    """ Queries urls asynchronously (respecting limiter), and updates (synchronously) json file.
        Called by main() """
    async with limiter:
        ## when limiter allows, query url -----------------------
        log.debug( f'limiter-queue, ``{limiter}``' )
        start_time = time.monotonic()
        log.debug( f'job, ``{job_name}`` get starting' )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            assert response.status_code == 200, response.status_code
            data = response.text
            jdct = json.loads( data )
            # log.debug( f'jdct, ``{pprint.pformat(jdct)}``' )
            trace_id = jdct['headers']['X-Amzn-Trace-Id']
            results_dct[ job_name ] = trace_id
            log.debug( f'trace_id, ``{trace_id}``' )
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
    time.sleep( SYNCHRONOUS_WRITE_DELAY )  ## set this to .5 and view the logs to better see the effect of the lock
    with open('results.json', 'a') as f:
        jsn = json.dumps( {'url': url, 'time-taken': elapsed_time} )
        f.writelines( [jsn, '\n'] )
    log.debug( f'job, ``{job_name}`` written to json file' )
    return


if __name__ == '__main__':
    trio.run( main )


"""
Usage...

% source ../env/bin/activate  # for access to trio and httpx
% python3 ./trio_sem_mutex.py
"""

"""
Sample output...

[10/Mar/2023 22:43:10] DEBUG [trio_sem_mutex-<module>()::29] URLS_COUNT, ``10``
[10/Mar/2023 22:43:10] DEBUG [trio_sem_mutex-<module>()::31] LIMIT, ``3``
[10/Mar/2023 22:43:10] DEBUG [trio_sem_mutex-<module>()::33] RESULTS_FILE_PATH, ``results.json``
[10/Mar/2023 22:43:10] DEBUG [trio_sem_mutex-<module>()::35] SYNCHRONOUS_WRITE_DELAY, ``0.5``
[10/Mar/2023 22:43:10] DEBUG [trio_sem_mutex-<module>()::44] 
---
For 10 urls, each requiring about 2-seconds to respond, 
    and a file-write delay of 0.5 seconds, 
    sequential processing would take about 25 seconds.

Our asynchrous processing, with a limit of 3 requests at-a-time, 
    should take a little over 12 seconds.
---
[SNIP]
(Lots of output shows the flow of processing, and the capacity-limiter and mutex working.)
[SNIP]
[10/Mar/2023 22:43:23] DEBUG [trio_sem_mutex-main()::98] full_elapsed_time, ``13.402209874941036``
"""