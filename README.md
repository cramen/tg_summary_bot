# Telegram Summary Bot

This project is a Telegram client that collects new messages from filtered channels, saves them to an SQLite database, and provides AI-powered summaries.

## Features

*   Collects messages from specified Telegram channels.
*   Saves messages, chats, and authors to a local SQLite database.
*   Provides AI-powered summaries of new messages using Yandex GPT.
*   Summaries can be requested for all filtered chats or a specific chat.
*   Manage filtered chats via commands in your "Saved Messages".
*   Handles message replies to provide context in summaries.
*   Logs application activity and errors to `tg_client.log`.

## Commands

You can control the bot by sending commands to your "Saved Messages" in Telegram:

*   `/sbot sum`: Get a summary of all new messages from filtered chats from the last 24 hours.
*   `/sbot sum <chat_id>`: Get a summary of new messages from a specific filtered chat from the last 24 hours.
*   `/sbot add <chat_id>`: Add a chat to the filter.
*   `/sbot del <chat_id>`: Remove a chat from the filter.
*   `/sbot list`: List all the chats in the filter.

## Technologies Used

*   Python
*   Telethon
*   SQLite
*   yoyo-migrations
*   PyInstaller
*   Yandex GPT

## Getting Started

### Prerequisites

*   Python 3
*   Telegram API credentials (`API_ID` and `API_HASH`)
*   Yandex Cloud credentials (`YANDEX_API_KEY` and `YANDEX_FOLDER_ID`)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/cramen/tg_summary_bot.git
    cd tg_summary_bot
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Run the client from source:**
    ```bash
    python3 tg_client.py
    ```
2.  The first time you run the application, it will prompt you for your Telegram and Yandex Cloud credentials. These will be saved for future use.

## Packaging the Application

To package the application into a single, self-contained executable file, run the following command:

```bash
venv/bin/pyinstaller --onefile --name tg_client --add-data "yoyo.ini:." --add-data "migrations:migrations" --hidden-import="openai" tg_client.py
```

This will create a single executable file named `tg_client` in the `dist` directory.
