# Gemini Context

## Project Overview

This project is a Telegram client that collects new messages from all channels and saves them to an SQLite database.
You can get an AI-powered summary of new messages from the last 24 hours by sending commands to your "Saved Messages":

*   `/sbot sum`: Get a summary of all new messages from filtered chats.
*   `/sbot sum <chat_id>`: Get a summary of new messages from a specific filtered chat.

You can manage the filtered channels by sending commands to your "Saved Messages":
*   `/sbot add <chat_id>`: Add a chat to the filter.
*   `/sbot del <chat_id>`: Remove a chat from the filter.
*   `/sbot list`: List all the chats in the filter.

The digest will also show if a message is a reply to another message.

The application logs its activities and errors to `tg_client.log`.

It uses the following technologies:
*   Python
*   Telethon
*   SQLite
*   yoyo-migrations
*   PyInstaller
*   Yandex GPT

## Building and Running

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the client from source:**
    ```bash
    python3 tg_client.py
    ```
    The first time you run the application, it will prompt you for your Telegram and Yandex Cloud credentials.

## Packaging the Application

To package the application into a single, self-contained executable file, run the following command:

```bash
pyinstaller --onefile --name tg_client --add-data "yoyo.ini:." --add-data "migrations:migrations" --hidden-import="openai" tg_client.py
```

This will create a single executable file named `tg_client` in the `dist` directory. This executable can be run on its own without needing any other files.

## Key Files

*   `tg_client.py`: The main application file.
*   `requirements.txt`: The Python dependencies.
*   `telegram_messages.db`: The SQLite database where messages are stored.
*   `yoyo.ini`: The configuration file for yoyo-migrations.
*   `migrations/`: A directory containing database migration scripts in plain SQL.
*   `~/.tg_bot/api.conf`: The configuration file for the Telegram API credentials.
*   `~/.tg_bot/llm.conf`: The configuration file for the Yandex GPT credentials.
*   `tg_client.log`: The log file for the application.
*   `GEMINI.md`: This file.

## Development Conventions

*   The project uses `asyncio` for asynchronous operations.
*   Database migrations are handled by `yoyo-migrations` and are applied automatically on startup in non-interactive mode.
*   To create a new migration, add a new `.sql` file to the `migrations` directory.