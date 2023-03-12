/* 
Rust semaphore and mutex example.
*/

// main imports -----------------------------------------------------
#[macro_use]  // for logging
extern crate log;
use rand::Rng;

// lib.rs imports ---------------------------------------------------
use concurrency_template_code::setup_logging;
use concurrency_template_code::make_results_dict;

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
    /* This will hold all the results. 
        Using BTreeMap instead of HashMap simply for convenient viewing of print-statements and logging. */
    let _results: std::collections::BTreeMap<i32, String> = make_results_dict( &random_nums ).await;
    

    // make urls ----------------------------------------------------
    let urls: Vec<std::string::String> = make_urls().await;
    println!("urls, ``{:#?}``", urls);
 
    // Return Ok() to indicate that the program completed successfully
    Ok(())
}


// make random numbers ----------------------------------------------
async fn make_random_nums() -> Vec<i32> {
    /* Creates a list of unique random numbers. */
    let mut random_nums: Vec<i32> = Vec::new();
    while random_nums.len() < 10 {
        let mut range_generator = rand::thread_rng();
        let random_number: i32 = range_generator.gen_range(1800..=2200);
        if !random_nums.contains(&random_number) {
            random_nums.push(random_number);
        }
    }
    // sort list
    random_nums.sort();
    println!("random_nums, ``{:#?}``", random_nums);
    random_nums
}

// make urls --------------------------------------------------------
async fn make_urls() -> Vec<std::string::String> {
    
    // create a list of random numbers ------------------------------

    let mut urls: Vec<String> = Vec::new();
    let mut range_generator = rand::thread_rng();
    for _i in 0..10 {
        let random_number: i32 = range_generator.gen_range(1800..=2200);
        // let zz: () = random_number;  // yields `found integer`

        let random_number_string: String = random_number.to_string();
        let url: String = format!("http://httpbin.org/delay/{}", &random_number_string);
        urls.push(url);
    }

    // return urls 
    urls
}

// async fn make_urls() -> Vec<std::string::String> {
//     let mut urls: Vec<String> = Vec::new();
//     urls.push("https://www.google.com".to_string());
//     urls.push("https://www.yahoo.com".to_string());

//     // make a random integer between 1800 and 2200, inclusive
//     let mut rng = rand::thread_rng();
//     let random_number = rng.gen_range(1800..=2200);
//     println!("Random number between 1800 and 2200: {}", random_number);

//     let arr: [String; 3] = ["a".to_string(), "b".to_string(), "c".to_string()];
//     println!("arr, ``{:#?}``", arr);

//     // return urls 
//     urls
// }