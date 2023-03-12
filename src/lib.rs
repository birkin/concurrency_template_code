#[macro_use]
extern crate log;

use env_logger::{Builder};
use log::{LevelFilter};
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
