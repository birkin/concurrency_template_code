import json, os, pprint, sys, time
from multiprocessing import Pool, Manager

import requests


# Fictional weather API
def fetch_url(delay):
    # response = requests.get(f'http://weather-api.com/temperature/{delay}')
    url = f'http://httpbin.org/delay/{delay}'
    response = requests.get( url )
    response_id = response.json()['headers']['X-Amzn-Trace-Id']
    return delay, response_id

# Writing results synchronously to JSON file
def store_result(shared_results, response_result):
    print( 'saving to file' )
    with shared_results.lock:
        time.sleep( .5 )
        shared_results.results[response_result[0]] = response_result[1]
        with open('results.json', 'w') as f:
            json.dump( dict(shared_results.results), f, indent=2 )  # dict() is needed to make the dict-proxy object JSON serializable

def worker( delay_results_tuple ):  # delay_results_tuple is of type `list[ tuple[float, _Namespace] ]`
    delay, shared_results = delay_results_tuple
    response_result = fetch_url(delay)
    store_result( shared_results, response_result )

def main():
    print( 'starting main()' )
    delays = [2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11]  # from manually running ``random.randint(1800, 2200) / 1000``

    # Load environmental variable
    max_concurrent_calls = int(os.getenv('MAX_CONCURRENT_CALLS', 3))

    manager = Manager()
    shared_results = manager.Namespace()
    shared_results.lock = manager.Lock()
    shared_results.results: 'DictProxy[Any, Any]' = manager.dict()  # type: ignore
    delays_results_tuples = [(delay, shared_results) for delay in delays]

    with Pool(processes=max_concurrent_calls) as pool:
        for _ in pool.imap_unordered(worker, delays_results_tuples):
            pass

    print( 'leaving main()' )

    # end main()...


if __name__ == '__main__':
    print( 'starting if...' )
    start_time = time.monotonic()
    main()
    end_time = time.monotonic()            # hit after all the nursery tasks are done
    full_elapsed_time = end_time - start_time
    print( f'full_elapsed_time, ``{full_elapsed_time}``' )
    sys.exit( 0 )
