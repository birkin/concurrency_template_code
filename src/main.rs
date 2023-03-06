/* 
Rust semaphore and mutex example.
*/

// use std::env;
// use std::fs::File;
// use std::io::prelude::*;
// use std::sync::Arc;

// use tokio::sync::mpsc;
// use tokio::sync::Semaphore;
// use tokio::task;
// use serde::{Deserialize, Serialize};

// set up imports ---------------------------------------------------
use rand::Rng;

// set up logging ---------------------------------------------------


// set up envars ----------------------------------------------------


// main controller --------------------------------------------------
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    let urls: Vec<std::string::String> = make_urls().await;
    println!("urls, ``{:#?}``", urls);
 
    // Return Ok() to indicate that the program completed successfully
    Ok(())
}


// make urls --------------------------------------------------------
async fn make_urls() -> Vec<std::string::String> {
    let mut urls: Vec<String> = Vec::new();
    urls.push("https://www.google.com".to_string());
    urls.push("https://www.yahoo.com".to_string());

    // make a random integer between 1800 and 2200, inclusive
    let mut rng = rand::thread_rng();
    let random_number = rng.gen_range(1800..=2200);
    println!("Random number between 1800 and 2200: {}", random_number);

    let arr: [String; 3] = ["a".to_string(), "b".to_string(), "c".to_string()];
    println!("arr, ``{:#?}``", arr);

    // return urls 
    urls
}