import json, os, pprint, sys, time
from multiprocessing import Pool, Manager

import requests


## controller -------------------------------------------------------

def main():
    print( 'starting main()' )
    ## define delay-seconds -----------------------------------------
    delays = [2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11]  # from manually running ``random.randint(1800, 2200) / 1000``
    ## load envar ---------------------------------------------------
    max_concurrent_calls = int(os.getenv('MAX_CONCURRENT_CALLS', 3))
    ## instantiate manager ------------------------------------------
    """ 
    - multiprocessing.Manager() is a factory function that provides a manager-object 
        ...which can hold Python objects and allow other processes to manipulate them using proxies.
    - It's used here to: 
        - create a shared namespace for the results...
        - to create/carry a lock to allow the results to be saved to disk synchronously (avoiding race-conditions). 
    """
    manager = Manager()
    shared_results = manager.Namespace()
    shared_results.lock = manager.Lock()        # the manager-object is now carrying a lock
    shared_results.results = manager.dict()     # the manager-object is now carrying a ``DictProxy[Any, Any]`` (not json serializable) where the results will be stored
    delays_results_tuples = [(delay, shared_results) for delay in delays]   # creates a list of tuples, where each tuple contains a delay and the shared_results object
    ## instantiate the multiprocessing pool -------------------------
    """
    - The pool is instantiated with a max_concurrent_calls value...
    - Then the worker function is called repeatedly, passing each a 'display_results_tuple' entry.
        - Reminder: each tuple contains:
            - a delay-seconds float 
            - the Manager() object containing a lock and a results-storage-holder.
    """
    with Pool(processes=max_concurrent_calls) as pool:
        for _ in pool.imap_unordered(worker, delays_results_tuples):  # `_` indicates worker doesn't return anything
            pass  
    print( 'leaving main()' )

    # end def main()


## helper functions -------------------------------------------------

def worker( delay_results_tuple ):  # delay_results_tuple is type `list[ tuple[float, Manager.Namespace()] ]`
    """ Worker function. 
        Called by main() """
    delay, shared_results = delay_results_tuple
    response_result = fetch_url(delay)
    store_result( shared_results, response_result )

def fetch_url( delay: float ):
    """ Queries url and returns response.
        Called by worker() """
    url = f'http://httpbin.org/delay/{delay}'
    response = requests.get( url )
    response_id = response.json()['headers']['X-Amzn-Trace-Id']
    return delay, response_id

def store_result( shared_results, response_result ):  # shared_results is type Manager.Namespace(); response_result is type `tuple[float, str]`
    """ Writes response to JSON file, synchronously. 
        Called by worker()  """
    print( 'saving to file' )
    with shared_results.lock:
        time.sleep( .5 )
        shared_results.results[response_result[0]] = response_result[1]
        with open('results.json', 'w') as f:
            json.dump( dict(shared_results.results), f, indent=2 )  # dict() is needed to make the dict-proxy object JSON serializable


## entry point ------------------------------------------------------

if __name__ == '__main__':
    print( 'starting if...' )
    start_time = time.monotonic()
    main()
    end_time = time.monotonic()
    full_elapsed_time = end_time - start_time
    print( f'full_elapsed_time, ``{full_elapsed_time}``' )
    sys.exit( 0 )
