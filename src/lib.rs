#[macro_use]
extern crate log;

use env_logger::{Builder};
use log::{LevelFilter};
use rand::Rng;
use std::collections::BTreeMap;
use std::collections::HashMap;
use std::io::Write;


// set up logging ---------------------------------------------------
pub fn setup_logging() {
    let mut builder = Builder::new();
    let log_level_envar: String = "CNCRNCY_TMPLT__LOG_LEVEL".to_string();
    let log_level: String = std::env::var(&log_level_envar).unwrap_or_else(|error| {
        panic!("Problem getting envar, ``{:?}``; error, ``{:?}``. Did you source the envar.sh file?", &log_level_envar, error);
    });
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
    debug!("logging initialized");}


// make random numbers ----------------------------------------------
pub async fn make_random_nums() -> Vec<i32> {
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


// make results dict ------------------------------------------------
pub async fn make_results_dict( random_nums: &Vec<i32> ) -> BTreeMap<i32, HashMap<String, String>> {
    /* Creates a dict with random-numbers as keys and 'init' as values. */
    let mut results: BTreeMap<i32, HashMap<String, String>> = BTreeMap::new();
    for random_num in random_nums {
        let mut inner_map: HashMap<String, String> = HashMap::new();
        inner_map.insert("url".to_string(), "foo".to_string());
        inner_map.insert("time_taken".to_string(), "bar".to_string());
        inner_map.insert("amz_id".to_string(), "baz".to_string());
        debug!("inner_map, ``{:#?}``", inner_map);
        results.insert(*random_num, inner_map);
    }
    debug!("results, ``{:#?}``", results);
    results
}

// // make results dict ------------------------------------------------
// pub async fn make_results_dict( random_nums: &Vec<i32> ) -> std::collections::BTreeMap<i32, String> {
//     /* Creates a dict with random-numbers as keys and 'init' as values. */
//     let mut results: std::collections::BTreeMap<i32, String> = std::collections::BTreeMap::new();
//     for random_num in random_nums {
//         results.insert(*random_num, "init".to_string());
//     }
//     println!("results, ``{:#?}``", results);
//     results
// }
