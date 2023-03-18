/* Functions called from main.rs main() */

#[macro_use]
extern crate log;

use env_logger::{Builder};
use log::{LevelFilter};
use rand::Rng;
use std::collections::BTreeMap;
use std::collections::HashMap;
use std::io::Write;


// make urls --------------------------------------------------------
pub async fn add_urls_to_results( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
    /* Iterates through the result items
        - gets the key (the random number)
        - divides the key by 1000 to get the (float) number of seconds that'll be used in the delay url
        - gets access to the inner hashmap to update the url value. */
    for ( key, inner_hashmap ) in results.iter_mut() {
        let seconds_float: f32 = *key as f32 / 1000.0;  // converts the integer key to a smaller float for the 
        let url_value: String = format!("http://httpbin.org/delay/{:.3 }", seconds_float);  // limits the number of decimal places to 3
        if let Some(url) = inner_hashmap.get_mut("url") {
            *url = url_value;  // the asterisk dereferences the value so it can be changed
        }
    }
    debug!( "results after url-update, ``{:#?}``", &results );
}


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
    while random_nums.len() < 10 {  // TODO: make this a parameter passed in from settings
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
    /* Creates a dict with the random-numbers as keys and another dict as values.
        The outer map is a BTreeMap instead of a HashMap just to be able to see the keys sorted in logging for development. */
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
