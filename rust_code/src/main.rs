/*  Rust semaphore and mutex example.
    See readme for info and usage.  */


// main imports -----------------------------------------------------
#[macro_use]  // for logging
extern crate log;

// lib.rs imports ---------------------------------------------------
use concurrency_template_code::setup_logging;
use concurrency_template_code::make_random_nums;
use concurrency_template_code::make_results_dict;
use concurrency_template_code::add_urls_to_results;
use concurrency_template_code::get_max_concurrent_requests;

use std::collections::BTreeMap;
use std::collections::HashMap;


// main controller --------------------------------------------------
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    // set up logging -----------------------------------------------
    setup_logging();
    debug!( "main() log message" );

    // generate list of random numbers ------------------------------
    /* These will be used for dict-keys and url-delays. */
    let random_nums: Vec<i32> = make_random_nums().await;

    // initialize results dict --------------------------------------
    /*  This will hold all the results. 
        Using BTreeMap instead of HashMap simply for convenient viewing of print-statements and logging. */
    let mut results = make_results_dict( &random_nums ).await;

    // populate results dict with urls ------------------------------
    add_urls_to_results( &mut results ).await;

    // make requests ------------------------------------------------
    make_requests( &mut results ).await;

    // Return Ok() to indicate that the program completed successfully
    Ok( () )
}


async fn make_requests( _results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
    
    let max_concurrent_requests: i32 = get_max_concurrent_requests().await;


}