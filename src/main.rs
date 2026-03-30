use std::sync::Arc;

use tbot::menu::authorize;
use tracing::{Level, event, span};
use tracing_subscriber;

mod tbot {
    pub mod menu;
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_max_level(Level::INFO).init();
    let token = env!("TELEGRAM_BOT_TOKEN");
    event!(Level::INFO, "Starting TBot");

    //   let span = span!(Level::INFO, "main", a = "10");
    //    let _guard = span.enter();
    authorize(token).await.unwrap();
}
