use std::collections::BTreeMap;
use std::env;
use std::fs::File;
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::time::Instant;

use serde::Deserialize;
use tokio::task;
use tokio::task::JoinHandle;
use tokio::time::Duration;

#[derive(Deserialize)]
struct HttpbinResponse {
    headers: HttpbinHeaders,
}

#[derive(Deserialize)]
struct HttpbinHeaders {
    #[serde(rename = "X-Amzn-Trace-Id")]
    x_amzn_trace_id: String,
}

async fn fetch_url(delay: f64) -> (f64, String) {
    let url = format!("https://httpbin.org/delay/{}", delay);
    let response = reqwest::get(&url).await.unwrap();
    let response_json: HttpbinResponse = response.json().await.unwrap();
    let response_id = response_json.headers.x_amzn_trace_id;
    (delay, response_id)
}

async fn worker(delay: f64, shared_results: Arc<Mutex<BTreeMap<f64, String>>>) {
    let response_result = fetch_url(delay).await;
    store_result(shared_results, response_result).await;
}

async fn store_result(
    shared_results: Arc<Mutex<BTreeMap<f64, String>>>,
    response_result: (f64, String),
) {
    println!("Saving to file");
    let mut guard = shared_results.lock().unwrap();
    guard.insert(response_result.0, response_result.1);
    let mut file = File::create("results.json").unwrap();
    file.write_all(serde_json::to_string_pretty(&*guard).unwrap().as_bytes())
        .unwrap();
}

#[tokio::main]
async fn main() {
    println!("Starting main()");
    let delays = vec![
        2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11,
    ];
    let max_concurrent_calls = env::var("MAX_CONCURRENT_CALLS")
        .unwrap_or("3".to_string())
        .parse::<usize>()
        .unwrap();
    let shared_results = Arc::new(Mutex::new(BTreeMap::new()));

    let start_time = Instant::now();

    let mut handles: Vec<JoinHandle<()>> = vec![];

    for delay in delays {
        let shared_results_clone = Arc::clone(&shared_results);
        let handle = task::spawn(async move { worker(delay, shared_results_clone).await });
        handles.push(handle);
        if handles.len() == max_concurrent_calls {
            for handle in handles.drain(..) {
                handle.await.unwrap();
            }
        }
    }

    for handle in handles {
        handle.await.unwrap();
    }

    let end_time = Instant::now();
    let full_elapsed_time = end_time.duration_since(start_time);
    println!(
        "Full elapsed time: {}.{:03} seconds",
        full_elapsed_time.as_secs(),
        full_elapsed_time.subsec_millis()
    );
}
