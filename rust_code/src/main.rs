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
use concurrency_template_code::make_requests;


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
    debug!( "results after everything, ``{:#?}``", &results );

    // Return Ok() to indicate that the program completed successfully
    Ok( () )
}