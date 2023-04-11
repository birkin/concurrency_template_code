use std::collections::BTreeMap;
use std::env;
use std::fs::File;
use std::io::prelude::*;
use std::sync::{Arc, Mutex};

use ordered_float::OrderedFloat;
use serde::{Serialize, Serializer};
use serde_json;
use tokio::task;

#[derive(Clone, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct SerializableOrderedFloat(OrderedFloat<f64>);

// impl From<f64> for SerializableOrderedFloat {
//     fn from(value: f64) -> Self {
//         SerializableOrderedFloat(OrderedFloat(value))
//     }
// }

impl From<OrderedFloat<f64>> for SerializableOrderedFloat {
    fn from(value: OrderedFloat<f64>) -> Self {
        SerializableOrderedFloat(value)
    }
}

// impl Serialize for SerializableOrderedFloat {
//     fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
//     where
//         S: Serializer,
//     {
//         self.0 .0.serialize(serializer)
//     }
// }

impl Serialize for SerializableOrderedFloat {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{:.3}", self.0 .0))
    }
}


#[derive(Serialize)]
struct SerializableOrderedFloatMap {
    results: BTreeMap<SerializableOrderedFloat, String>,
}

#[tokio::main]
async fn main() {
    let delays = [
        2.104, 1.981, 1.802, 2.073, 1.956, 2.127, 2.015, 1.933, 2.003, 2.11,
    ];
    let max_concurrent_calls: usize = env::var("MAX_CONCURRENT_CALLS")
        .unwrap_or_else(|_| "3".to_string())
        .parse()
        .unwrap();

    let shared_results = Arc::new(Mutex::new(BTreeMap::<SerializableOrderedFloat, String>::new()));

    let mut handles = vec![];

    for &delay in delays.iter() {
        let shared_results_clone = Arc::clone(&shared_results);
        let handle = task::spawn(async move {
            let response_result = fetch_url(delay).await;
            store_result(shared_results_clone, response_result).await;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.await.unwrap();
    }

    let guard = shared_results.lock().unwrap();
    let results_map = SerializableOrderedFloatMap {
        results: guard.clone(),
    };
    let json = serde_json::to_string_pretty(&results_map).unwrap();
    println!("{}", json);
}

async fn fetch_url(delay: f64) -> (OrderedFloat<f64>, String) {
    let url = format!("https://httpbin.org/delay/{:.3}", delay);
    let response = reqwest::get(&url).await.unwrap();
    let json: serde_json::Value = response.json().await.unwrap();
    let response_id = json["headers"]["X-Amzn-Trace-Id"].as_str().unwrap().to_string();
    (OrderedFloat(delay), response_id)
}

async fn store_result(
    shared_results: Arc<Mutex<BTreeMap<SerializableOrderedFloat, String>>>,
    response_result: (OrderedFloat<f64>, String),
) {
    let mut guard = shared_results.lock().unwrap();
    guard.insert(response_result.0.into(), response_result.1);
    let results_map = SerializableOrderedFloatMap {
        results: guard.clone(),
    };
    let json = serde_json::to_string_pretty(&results_map).unwrap();
    drop(guard);

    let mut file = File::create("results.json").unwrap();
    file.write_all(json.as_bytes()).unwrap();
}
