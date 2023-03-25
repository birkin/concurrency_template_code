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


// use tokio::sync::Semaphore;
// use std::fs::File;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, Semaphore};
use tokio::task;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;


async fn make_requests( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
    // get the maximum number of concurrent requests ----------------
    let max_concurrent_requests: usize = get_max_concurrent_requests().await;
    debug!( "max_concurrent_requests, ``{:?}``", &max_concurrent_requests );

    // get the total number of jobs ---------------------------------
    let total_jobs: usize = results.len();

    // set up semaphore ---------------------------------------------
    let semaphore = Arc::new(Semaphore::new(max_concurrent_requests));

    // set up the backup file ---------------------------------------
    let file_mutex = Arc::new(Mutex::new(File::create("results.txt").await.unwrap()));

    let tasks = (0..total_jobs)
        .map(|i| {
            let permit = Arc::clone(&semaphore);
            let backup_file_clone = Arc::clone(&file_mutex);
            task::spawn(async move {
                let _permit = permit.acquire().await;
                execute_job(i).await;
                backup_results_to_file( i, backup_file_clone ).await.unwrap();
            })
        })
        .collect::<Vec<_>>();

    futures::future::join_all(tasks).await;

}


async fn backup_results_to_file( 
    job_number: usize, 
    backup_file_clone: Arc<Mutex<File>>
    ) -> Result<(), Box<dyn std::error::Error>>  {
    println!("Starting backup after job {}", job_number);
    let mut file_writer = backup_file_clone.lock().await;
    file_writer.write_all(format!("{}\n", job_number).as_bytes()).await?;
    println!("Finished backup after job {}", job_number);
    Ok(())
}

async fn execute_job(i: usize) {
    println!("Starting job {}", i);
    tokio::time::sleep(Duration::from_secs(1)).await;
    println!("Finished job {}", i);
}
