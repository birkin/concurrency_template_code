use std::collections::BTreeMap;
use std::fs::File;
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::time::Instant;

use ordered_float::OrderedFloat;
use reqwest::Url;
use serde::{Serialize, Serializer};
use tokio::task;

#[derive(Clone, Eq, Hash, PartialEq, PartialOrd, Ord)]
struct SerializableOrderedFloat(OrderedFloat<f64>);

impl Serialize for SerializableOrderedFloat {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{:.3}", self.0 .0))
    }
}

impl From<OrderedFloat<f64>> for SerializableOrderedFloat {
    fn from(value: OrderedFloat<f64>) -> Self {
        SerializableOrderedFloat(value)
    }
}

async fn fetch_url(delay: f64) -> Result<(OrderedFloat<f64>, String), reqwest::Error> {
    let url = Url::parse(&format!("https://httpbin.org/delay/{:.3}", delay)).unwrap();
    let response = reqwest::get(url).await?;
    let json: serde_json::Value = response.json().await?;
    let response_id = json["headers"]["X-Amzn-Trace-Id"].as_str().unwrap().to_string();
    Ok((OrderedFloat(delay), response_id))
}

async fn store_result(shared_results: Arc<Mutex<BTreeMap<SerializableOrderedFloat, String>>>, response_result: (OrderedFloat<f64>, String)) {
    let mut guard = shared_results.lock().unwrap();
    guard.insert(response_result.0.into(), response_result.1);
    drop(guard);

    let mut file = File::create("results.json").unwrap();
    let guard = shared_results.lock().unwrap();
    file.write_all(serde_json::to_string_pretty(&*guard).unwrap().as_bytes()).unwrap();
}

async fn worker(delay: f64, shared_results: Arc<Mutex<BTreeMap<SerializableOrderedFloat, String>>>) {
    let response_result = fetch_url(delay).await.unwrap();
    store_result(shared_results, response_result).await;
}

#[tokio::main]
async fn main() {
    let delays = vec![
        2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11,
    ];

    let max_concurrent_calls = 3;
    let shared_results = Arc::new(Mutex::new(BTreeMap::<SerializableOrderedFloat, String>::new()));

    let start_time = Instant::now();

    let mut handles = Vec::new();
    let mut current_concurrent_calls = 0;

    for delay in delays {
        let shared_results_clone = Arc::clone(&shared_results);
        let handle = task::spawn(async move { worker(delay, shared_results_clone).await });
        handles.push(handle);
        current_concurrent_calls += 1;

        if current_concurrent_calls == max_concurrent_calls {
            for handle in handles.drain(..) {
                handle.await.unwrap();
            }
            current_concurrent_calls = 0;
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
