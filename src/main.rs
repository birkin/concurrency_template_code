/* 
Rust semaphore and mutex example.
*/

// set up imports ---------------------------------------------------
#[macro_use]
extern crate log;


// use env_logger::{Builder};
// use log::{LevelFilter};
use rand::Rng;

// use std::io::Write;

// import logging
use concurrency_template_code::setup_logging;

// main controller --------------------------------------------------
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    // set up logging -----------------------------------------------
    setup_logging();
    debug!( "main() log message" );

    // make urls ----------------------------------------------------
    let urls: Vec<std::string::String> = make_urls().await;
    println!("urls, ``{:#?}``", urls);
 
    // Return Ok() to indicate that the program completed successfully
    Ok(())
}


// make urls --------------------------------------------------------
async fn make_urls() -> Vec<std::string::String> {
    let mut urls: Vec<String> = Vec::new();
    let mut range_generator = rand::thread_rng();
    for _i in 0..10 {
        let random_number = range_generator.gen_range(1800..=2200);
        let random_number_string = random_number.to_string();
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