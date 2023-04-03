import json, os, pprint, sys, time
from multiprocessing import Pool, Manager

import requests


# Fictional weather API
def fetch_temperature(city):
    # response = requests.get(f'http://weather-api.com/temperature/{city}')
    url = f'http://httpbin.org/delay/{city}'
    response = requests.get( url )
    response_id = response.json()['headers']['X-Amzn-Trace-Id']
    # return city, response.json()['temperature']
    return city, response_id

# Writing results synchronously to JSON file
def store_result(shared_results, city_temp):
    print( 'saving to file' )
    with shared_results.lock:
        time.sleep( .5 )
        shared_results.results[city_temp[0]] = city_temp[1]
        with open('results.json', 'w') as f:
            json.dump( dict(shared_results.results), f, indent=2 )  # dict() is needed to make the dict-proxy object JSON serializable

def worker(city_results_tuple):
    city, shared_results = city_results_tuple
    temperature = fetch_temperature(city)
    store_result(shared_results, temperature)

def main():
    print( 'starting main()' )
    cities = [2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11]

    # Initialize results dictionary
    # with open('results.json', 'w') as f:
    #     json.dump({}, f)

    # Load environmental variable
    max_concurrent_calls = int(os.getenv('MAX_CONCURRENT_WEATHER_API_CALLS', 3))

    manager = Manager()
    shared_results = manager.Namespace()
    shared_results.lock = manager.Lock()
    shared_results.results: 'DictProxy[Any, Any]' = manager.dict()  # type: ignore
    cities_results_tuples = [(city, shared_results) for city in cities]

    with Pool(processes=max_concurrent_calls) as pool:
        for _ in pool.imap_unordered(worker, cities_results_tuples):
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
