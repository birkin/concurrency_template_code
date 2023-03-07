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

#[macro_use]
extern crate log;

// use env_logger::{Builder, Target};
// use env_logger;
use env_logger::{Builder};
// use log::{error, warn, info, debug, trace};
// use log::{LevelFilter, Metadata, Record};
use log::{LevelFilter};
use rand::Rng;
use std::io::Write;


// set up envars ----------------------------------------------------


// main controller --------------------------------------------------
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    println!( "starting main()" );
    // set up logging ---------------------------------------------------
    // let log_level = std::env::var("API_KEY")?;
    let log_level = std::env::var("CNCRNCY_TMPLT__LOG_LEVEL").unwrap_or_else(|error| {
        panic!("Problem getting envar -- ``{:?}``", error);
    });
    println!("log_level, ``{}``", log_level);

    let mut builder = Builder::new();
    builder.filter(None, LevelFilter::Info);

    builder.format(|buf, record| {
        let mut level_style = buf.style();
        level_style.set_bold(true);
        // level_style.set_color(Some(level_color(record.level())));

        let mut target_style = buf.style();
        target_style.set_bold(true);

        writeln!(
            buf,
            "{} {} [{}] {}:{}: {}",
            chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
            level_style.value(record.level()),
            target_style.value(record.target()),
            record.file().unwrap_or("unknown"),
            record.line().unwrap_or(0),
            record.args()
        )
    });

    builder.init();

    debug!("debug message");
    info!("info message");

    // let mut log_builder = Builder::from_default_env();
    // log_builder.target(Target::Stdout);
    // log_builder.init();
    // let msg: String = format!(
    //     "\n\n-------\n`starting logchecker_project code at, ``{:?}``",
    //     local_time.to_rfc3339()
    // );
    // info!("{}", msg);

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