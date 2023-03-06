use std::env;
use std::fs::File;
use std::io::prelude::*;
use std::sync::Arc;

use tokio::sync::mpsc;
use tokio::sync::Semaphore;
use tokio::task;
use serde::{Deserialize, Serialize};

// Define a struct to hold weather data for each city
#[derive(Debug, Deserialize, Serialize)]
struct WeatherData {
    name: String,
    temperature: f32,
}

// The main function
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Set the list of cities to retrieve weather data for
    let cities = vec![
        ("London", "51.5072,-0.1276"),
        ("New York", "40.7128,-74.0060"),
        ("Tokyo", "35.6762,139.6503"),
        ("Paris", "48.8566,2.3522"),
        ("Berlin", "52.5200,13.4050"),
        ("Rome", "41.9028,12.4964"),
        ("Moscow", "55.7558,37.6173"),
        ("Madrid", "40.4168,-3.7038"),
        ("Toronto", "43.6532,-79.3832"),
        ("Sydney", "-33.8651,151.2094"),
    ];

    // Create a semaphore to limit concurrency to 3 requests at a time
    let concurrency_limit = Arc::new(Semaphore::new(3));

    // Create a channel for sending weather data from the tasks to the main thread
    let (tx, mut rx) = mpsc::channel::<WeatherData>(cities.len());

    // Create a Mutex to ensure that the weather data file is only updated by one task at a time
    let file_mutex = Arc::new(tokio::sync::Mutex::new(()));

    // Spawn a task for each city to retrieve weather data asynchronously
    for (city_name, coordinates) in cities {
        // Clone the semaphore, channel sender, and file Mutex for use in the task
        let concurrency_limit = concurrency_limit.clone();
        let tx = tx.clone();
        let file_mutex = file_mutex.clone();

        task::spawn(async move {
            // Acquire a permit from the semaphore to limit concurrency
            let permit = concurrency_limit.acquire().await.unwrap();

            // Build the URL for the weather API request
            let url = format!(
                "https://api.weather.gov/points/{}/forecast",
                coordinates
            );
            println!( "url, ``{}``", url );

            // Send the request to the weather API and parse the JSON response
            let response = reqwest::get(&url).await.unwrap();
            let json = response.json::<serde_json::Value>().await.unwrap();

            // Extract the temperature from the JSON response
            let temperature = json["properties"]["periods"][0]["temperature"].as_f64().unwrap() as f32;

            // Send the weather data for this city through the channel
            tx.send(WeatherData {
                name: city_name.to_string(),
                temperature,
            })
            .await
            .unwrap();

            // Release the semaphore permit to allow other tasks to run
            drop(permit);
        });
    }

    // Drop the sender end of the channel to signal that we're done sending data
    drop(tx);

    // Receive weather data from the tasks as it becomes available
    while let Some(data) = rx.recv().await {
        // Clone the file Mutex for use in this loop iteration
        let file_mutex = file_mutex.clone();

        // Lock the file Mutex to ensure that the file is only updated by one task at a time
        let _guard = file_mutex.lock().await;

        // Open the weather data file
        let mut file = File::open("weather.json").unwrap();

        // Read the current contents of the file into memory
        let mut contents = String::new();
        file.read_to_string(&mut contents).unwrap();

        // Deserialize the current weather data from the file, or create an empty Vec if the file is empty
        let mut weather_data: Vec<WeatherData> = serde_json::from_str(&contents).unwrap_or_default();

        // Find the index of the weather data for this city in the Vec, if it exists
        let index = weather_data.iter().position(|d| d.name == data.name);

        // If weather data for this city already exists, update it; otherwise, add it to the Vec
        match index {
            Some(i) => {
                // Update the existing weather data for this city
                weather_data[i] = data;
            }
            None => {
                // Add the new weather data for this city to the Vec
                weather_data.push(data);
            }
        }

        // Open the weather data file for writing
        let mut file = File::create("weather.json").unwrap();

        // Serialize the updated weather data and write it back out to the file
        file.write_all(serde_json::to_string(&weather_data).unwrap().as_bytes())
            .unwrap();
    }

    // Return Ok() to indicate that the program completed successfully
    Ok(())
}
