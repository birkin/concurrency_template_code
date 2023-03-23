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

// use tokio::sync::Mutex;
// use tokio::task;
// use tokio::time::{sleep, Duration};

// use std::sync::Arc;



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


use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Semaphore;
use tokio::task;

async fn make_requests( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
    // get the maximum number of concurrent requests ----------------
    let max_concurrent_requests: usize = get_max_concurrent_requests().await;
    debug!( "max_concurrent_requests, ``{:?}``", &max_concurrent_requests );

    // get the total number of jobs ---------------------------------
    let total_jobs: usize = results.len();

    // set up semaphore ---------------------------------------------
    let semaphore = Arc::new(Semaphore::new(max_concurrent_requests));

    let tasks = (0..total_jobs)
        .map(|i| {
            let permit = Arc::clone(&semaphore);
            task::spawn(async move {
                let _permit = permit.acquire().await;
                execute_job(i).await;
            })
        })
        .collect::<Vec<_>>();

    futures::future::join_all(tasks).await;

}


async fn execute_job(i: usize) {
    println!("Starting job {}", i);
    tokio::time::sleep(Duration::from_secs(1)).await;
    println!("Finished job {}", i);
}



// use std::sync::Arc;
// use std::time::Duration;
// use tokio::sync::Semaphore;
// use tokio::task;

// async fn make_requests( _results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
//     // Set the maximum number of concurrent requests
//     let max_concurrent_requests: usize = get_max_concurrent_requests().await;
//     debug!( "max_concurrent_requests, ``{:?}``", &max_concurrent_requests );

//     // const MAX_CONCURRENT_JOBS: usize = 3;
//     const TOTAL_JOBS: usize = 10;

//     let semaphore = Arc::new(Semaphore::new(max_concurrent_requests));

//     let tasks = (0..TOTAL_JOBS)
//         .map(|i| {
//             let permit = Arc::clone(&semaphore);
//             task::spawn(async move {
//                 let _permit = permit.acquire().await;
//                 execute_job(i).await;
//             })
//         })
//         .collect::<Vec<_>>();

//     futures::future::join_all(tasks).await;

// }
