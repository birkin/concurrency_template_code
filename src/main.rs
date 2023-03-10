/* 
Rust semaphore and mutex example.
*/

// set up imports ---------------------------------------------------
#[macro_use]
extern crate log;

use env_logger::{Builder};
use log::{LevelFilter};
use rand::Rng;
use std::io::Write;

// main controller --------------------------------------------------
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    // set up logging -----------------------------------------------
    let mut builder = Builder::new();
    let log_level_envar: String = "CNCRNCY_TMPLT__LOG_LEVEL".to_string();
    let log_level: String = std::env::var(&log_level_envar).unwrap_or_else(|error| {
        panic!("Problem getting envar, ``{:?}``; error, ``{:?}``", &log_level_envar, error);
    });
    // let log_level: String = std::env::var("CNCRNCY_TMPLT__LOG_LEVEL").unwrap_or_else(|error| {
    //     panic!("Problem getting envar -- ``{:?}``", error);
    // });
    if log_level == "debug" {
        builder.filter(None, LevelFilter::Debug);
    } else  {
        builder.filter(None, LevelFilter::Info);
    }
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
    debug!("logging initialized");

    // make urls ----------------------------------------------------
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