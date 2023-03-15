/* 
Rust semaphore and mutex example.
*/

// main imports -----------------------------------------------------
#[macro_use]  // for logging
extern crate log;
// use serde_json::{json};
use std::collections::BTreeMap;
use std::collections::HashMap;

// lib.rs imports ---------------------------------------------------
use concurrency_template_code::setup_logging;
use concurrency_template_code::make_random_nums;
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
    let mut results = make_results_dict( &random_nums ).await;
    debug!( "testing to see if i still have access to results, ``{:#?}``", &results );

    // populate results dict with urls ------------------------------
    add_urls_to_results( &mut results ).await;
    debug!( "testing to see if i still have access to results, ``{:#?}``", &results );



    // Return Ok() to indicate that the program completed successfully
    Ok( () )
}


// make urls --------------------------------------------------------
async fn add_urls_to_results( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) {
    
    // iterate through results-dict entries --------------------------
    for (key, value) in results {
        debug!( "key, ``{:#?}``", &key);
        debug!( "value, ``{:#?}``", &value);
    }

}





// // make urls --------------------------------------------------------
// async fn add_urls_to_results( results: &mut BTreeMap<i32, String>, random_nums: &Vec<i32> ) {
    
//     // iterate through results-dict entries --------------------------
//     for integer_element in random_nums {
//         // let zz: () = integer_element; // yields: found `&i32`
//         let mut url_dict: std::collections::BTreeMap<String, String> = std::collections::BTreeMap::new();
//         let seconds_float: f32 = *integer_element as f32 / 1000.0;
//         let url_value: String = format!("http://httpbin.org/delay/{:.3 }", seconds_float);  // limits the number of decimal places to 3
//         debug!( "url_value, ``{:#?}``", &url_value);

//         url_dict.insert("url".to_string(), url_value);
//         println!("url_dict, ``{:#?}``", &url_dict);
        
//         let json_string = json!(url_dict).to_string();
//         println!("json_string, ``{:#?}``", &json_string);
//         results.insert( *integer_element, json_string );
//     }

//     // return urls 
//     // urls
// }


// // make urls --------------------------------------------------------
// async fn make_urls() -> Vec<std::string::String> {
    
//     // create a list of random numbers ------------------------------

//     let mut urls: Vec<String> = Vec::new();
//     let mut range_generator = rand::thread_rng();
//     for _i in 0..10 {
//         let random_number: i32 = range_generator.gen_range(1800..=2200);
//         // let zz: () = random_number;  // yields `found integer`

//         let random_number_string: String = random_number.to_string();
//         let url: String = format!("http://httpbin.org/delay/{}", &random_number_string);
//         urls.push(url);
//     }

//     // return urls 
//     urls
// }
