// /* Contains helper functions mostly called from main.rs main() */

// #[macro_use]
// extern crate log;

// use env_logger::{Builder};
// use log::{LevelFilter};
// use rand::Rng;
// use std::collections::BTreeMap;
// use std::collections::HashMap;
// use std::io::Write;
// use std::sync::Arc;
// use std::time::Duration;
// use tokio::fs::File;
// use tokio::io::AsyncWriteExt;
// use tokio::sync::{Mutex, Semaphore};
// use tokio::task;


// pub fn setup_logging() {
//     /* Called by main() */
//     let mut builder = Builder::new();
//     let log_level_envar: String = "CNCRNCY_TMPLT__LOG_LEVEL".to_string();
//     let log_level: String = std::env::var(&log_level_envar).unwrap_or_else(|error| {
//         panic!("Problem getting envar, ``{:?}``; error, ``{:?}``. Did you source the envar.sh file?", &log_level_envar, error);
//     });
//     if log_level == "debug" {
//         builder.filter(None, LevelFilter::Debug);
//     } else  {
//         builder.filter(None, LevelFilter::Info);
//     }
//     builder.format(|buf, record| {
//         let mut level_style = buf.style();
//         level_style.set_bold(true);
//         // level_style.set_color(Some(level_color(record.level())));
//         let mut target_style = buf.style();
//         target_style.set_bold(true);
//         writeln!(
//             buf,
//             "{} {} [{}] {}:{}: {}",
//             chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
//             level_style.value(record.level()),
//             target_style.value(record.target()),
//             record.file().unwrap_or("unknown"),
//             record.line().unwrap_or(0),
//             record.args()
//         )
//     });
//     builder.init();
//     debug!("logging initialized");}


// pub async fn make_random_nums() -> Vec<i32> {
//     /* Creates a list of unique random numbers.
//         These will be used for dict-keys and url-delays.
//         Called by main() */
//     let mut random_nums: Vec<i32> = Vec::new();
//     while random_nums.len() < 10 {  // TODO: make this a parameter passed in from settings
//         let mut range_generator = rand::thread_rng();
//         let random_number: i32 = range_generator.gen_range(1800..=2200);
//         if !random_nums.contains(&random_number) {
//             random_nums.push(random_number);
//         }
//     }
//     // sort list
//     random_nums.sort();
//     println!("random_nums, ``{:#?}``", random_nums);
//     random_nums
// }


// pub async fn make_results_dict( random_nums: &Vec<i32> ) -> BTreeMap<i32, HashMap<String, String>> {
//     /* Creates a dict with the random-numbers as keys and another dict as values.
//         The outer map is a BTreeMap instead of a HashMap just to be able to see the keys sorted in logging for development.
//         This will be used to hold the results.
//         Called by main() */
//     let mut results: BTreeMap<i32, HashMap<String, String>> = BTreeMap::new();
//     for random_num in random_nums {
//         let mut inner_map: HashMap<String, String> = HashMap::new();
//         inner_map.insert("url".to_string(), "foo".to_string());
//         inner_map.insert("time_taken".to_string(), "bar".to_string());
//         inner_map.insert("amz_id".to_string(), "baz".to_string());
//         debug!("inner_map, ``{:#?}``", inner_map);
//         results.insert(*random_num, inner_map);
//     }
//     debug!("results, ``{:#?}``", results);
//     results
// }


// pub async fn add_urls_to_results( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
//     /* Makes urls and adds them to the results-dict.
//         Iterates through the result items
//         - gets the key (the random number)
//         - divides the key by 1000 to get the (float) number of seconds that'll be used in the delay url
//         - gets access to the inner hashmap to update the url value. 
//         Called by main() */
//     for ( key, inner_hashmap ) in results.iter_mut() {
//         let seconds_float: f32 = *key as f32 / 1000.0;  // converts the integer key to a smaller float for the 
//         let url_value: String = format!("http://httpbin.org/delay/{:.3 }", seconds_float);  // limits the number of decimal places to 3
//         if let Some(url) = inner_hashmap.get_mut("url") {
//             *url = url_value;  // the asterisk dereferences the value so it can be changed
//         }
//     }
//     debug!( "results after url-update, ``{:#?}``", &results );
// }


// pub async fn make_requests( results: &mut BTreeMap<i32, HashMap<std::string::String, std::string::String>> ) -> () {
//     /* Manages the setup and execution of the async request-tasks.
//         Creates a sepaphore to limit the number of concurrent requests.
//         Creates a mutex-protected backup file to store the results in case of a crash.
//         Iterates through the results-dict to create tasks for each entry.
//         - calls function to execute the task.
//         - calls function to save the results-dict to a backup file synchronously.
//     */
//     // get the maximum number of concurrent requests ----------------
//     let max_concurrent_requests: usize = get_max_concurrent_requests().await;
//     debug!( "max_concurrent_requests, ``{:?}``", &max_concurrent_requests );

//     // get the total number of jobs ---------------------------------
//     // let total_jobs: usize = results.len();

//     // set up semaphore ---------------------------------------------
//     let semaphore = Arc::new(Semaphore::new(max_concurrent_requests));

//     // set up the backup file ---------------------------------------
//     let file_mutex = Arc::new(Mutex::new(File::create("results.txt").await.unwrap()));

//     // Initialize an empty vector to store tasks --------------------
//     let mut tasks = Vec::new();

//     // Iterate through the results vector ---------------------------
//     for (i, (key, inner_hashmap)) in results.iter().enumerate() {
//         debug!( "key, ``{:?}``", &key );
//         debug!( "inner_hashmap, ``{:?}``", &inner_hashmap );
//         let permit = Arc::clone(&semaphore);
//         let backup_file_clone = Arc::clone(&file_mutex);
//         let task = task::spawn(async move {
//             let _permit = permit.acquire().await;
//             let amz_id = execute_job(i).await;
//             backup_results_to_file(i, backup_file_clone).await.unwrap();
//         });

//         // Push the spawned task into the tasks vector ----------------
//         tasks.push(task);
//     }

//     futures::future::join_all(tasks).await;

// }


// pub async fn get_max_concurrent_requests() -> usize {
//     /* Grabs max_concurrent_requests from envar.
//         Called by make_requests() */
//     let max_concurrent_requests_envar = "CNCRNCY_TMPLT__MAX_CONCURRENT_REQUESTS".to_string();  // enables error message to show what's missing
//     let max_concurrent_requests_string: String = std::env::var(&max_concurrent_requests_envar).unwrap_or_else(|error| {
//         panic!("Problem getting envar, ``{:?}``; error, ``{:?}``. Did you source the envar.sh file?", &max_concurrent_requests_envar, error);
//     });
//     // convert to int
//     let max_concurrent_requests: usize = max_concurrent_requests_string.parse().unwrap_or_else(|error| {
//         panic!("Problem converting envar, ``{:?}`` to int; error, ``{:?}``", &max_concurrent_requests_envar, error);
//     });
//     debug!( "max_concurrent_requests, ``{:?}``", &max_concurrent_requests);
//     max_concurrent_requests
// }

// async fn execute_job(i: usize) -> String {
//     /* Will call httpbin.org/delay/{seconds} and store part of the response to the results-dict.
//         Called by make_requests() */
//     debug!("Starting job {}", i);
//     tokio::time::sleep(Duration::from_secs(1)).await;
//     debug!("Finished job {}", i);
//     "foo".to_string()
// }

// async fn backup_results_to_file( 
//     /* Writes to file synchronously via Mutex.
//         Called by make_requests() */
//     job_number: usize, 
//     backup_file_clone: Arc<Mutex<File>>
//     ) -> Result<(), Box<dyn std::error::Error>>  {
//     let mut file_writer = backup_file_clone.lock().await;
//     debug!("Starting backup after job {}", job_number);
//     file_writer.write_all(format!("{}\n", job_number).as_bytes()).await?;
//     debug!("Finished backup after job {}", job_number);
//     Ok(())
// }

