

import asyncio
import sqlite3
import subprocess
import os
import sys
import configparser
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, User
from datetime import datetime, timedelta

SESSION_NAME = 'tg_client'
DB_NAME = 'telegram_messages.db'
CONFIG_DIR = os.path.expanduser('~/.tg_bot')
API_CONFIG_FILE = os.path.join(CONFIG_DIR, 'api.conf')
LLM_CONFIG_FILE = os.path.join(CONFIG_DIR, 'llm.conf')
BATCH_SIZE = 25


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_api_credentials():
    """
    Reads API credentials from the config file, or prompts the user if it doesn't exist.
    """
    config = configparser.ConfigParser()
    logging.info("Reading Telegram API credentials.")
    if os.path.exists(API_CONFIG_FILE):
        config.read(API_CONFIG_FILE)
        api_id = config.get('telegram', 'api_id')
        api_hash = config.get('telegram', 'api_hash')
        logging.info("Telegram API credentials loaded from file.")
    else:
        logging.warning("Telegram API config file not found. Prompting user.")
        api_id = input("Enter your API ID: ")
        api_hash = input("Enter your API Hash: ")

        config['telegram'] = {'api_id': api_id, 'api_hash': api_hash}

        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        logging.info("Telegram API credentials saved to file.")

    return api_id, api_hash


def get_llm_credentials():
    """
    Reads LLM credentials from the config file, or prompts the user if it doesn't exist.
    """
    config = configparser.ConfigParser()
    logging.info("Reading LLM credentials.")
    if os.path.exists(LLM_CONFIG_FILE):
        config.read(LLM_CONFIG_FILE)
        api_key = config.get('yandex', 'api_key')
        folder_id = config.get('yandex', 'folder_id')
        logging.info("LLM credentials loaded from file.")
    else:
        logging.warning("LLM config file not found. Prompting user.")
        api_key = input("Enter your YANDEX_API_KEY: ")
        folder_id = input("Enter your YANDEX_FOLDER_ID: ")

        config['yandex'] = {'api_key': api_key, 'folder_id': folder_id}

        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(LLM_CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        logging.info("LLM credentials saved to file.")

    return api_key, folder_id


def create_database():
    """
    Applies database migrations.
    """
    logging.info("Applying database migrations.")
    migrations_path = resource_path('migrations')
    yoyo_ini_path = resource_path('yoyo.ini')
    try:
        subprocess.run(["yoyo", "apply", "--config", yoyo_ini_path, "--database", f"sqlite:///{DB_NAME}", "--batch", migrations_path], check=True)
        logging.info("Database migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error applying database migrations: {e}")
        raise


async def summarize_messages(messages, api_key, folder_id):
    """
    Summarizes a batch of messages using the Yandex GPT API.
    """
    logging.info(f"Summarizing {len(messages)} messages.")
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://llm.api.cloud.yandex.net/v1"
    )

    formatted_messages = ""
    for msg in messages:
        formatted_messages += f"Chat: {msg['chat_title']}\n"
        formatted_messages += f"Author: {msg['author_name']}\n"
        if msg['reply_to_text']:
            formatted_messages += f"In reply to: {msg['reply_to_text']}\n"
        formatted_messages += f"Message: {msg['text']}\n---\n"

    system_prompt = "Ты — полезный ассистент. Твоя задача — суммаризировать список новых сообщений из Telegram-чатов. Сообщения предоставляются пачками. Для каждой пачки предоставь краткую сводку. Если сообщение является ответом на другое, этот контекст предоставляется и должен использоваться для понимания хода разговора. Ответ должен быть на русском языке."

    try:
        result = client.chat.completions.create(
            model=f"gpt://{folder_id}/gpt-oss-20b/latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_messages}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        if hasattr(result, 'choices') and result.choices:
            choice = result.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                summary = choice.message.content or ""
                logging.info("Summarization successful.")
                return summary
        logging.warning("Failed to get summary from LLM.")
        return "Failed to get summary from LLM."
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return f"Error during summarization: {e}"


async def main():
    """
    Main function to connect to Telegram and listen for new messages.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("tg_client.log"),
            logging.StreamHandler()
        ]
    )
    logging.info("Application starting.")

    try:
        api_id, api_hash = get_api_credentials()
        create_database()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Load filtered chats
        cursor.execute("SELECT chat_id FROM filtered_chats")
        filtered_chats = {row[0] for row in cursor.fetchall()}
        logging.info(f"Loaded {len(filtered_chats)} filtered chats.")

        client = TelegramClient(SESSION_NAME, api_id, api_hash)
    except Exception as e:
        logging.error(f"Error during initialization: {e}")
        return

    @client.on(events.NewMessage())
    async def handler(event):
        """
        Event handler for new messages.
        """
        try:
            chat = await event.get_chat()
            sender = await event.get_sender()

            if not chat or not sender:
                return

            # Command processing
            if isinstance(chat, User) and chat.is_self:
                if event.message.text.startswith("/sbot add "):
                    try:
                        chat_id_to_add = int(event.message.text.split(" ")[2])
                        cursor.execute("INSERT OR IGNORE INTO filtered_chats (chat_id) VALUES (?)", (chat_id_to_add,))
                        conn.commit()
                        filtered_chats.add(chat_id_to_add)
                        logging.info(f"Added chat {chat_id_to_add} to filter.")
                        await event.respond(f"Chat {chat_id_to_add} added to filter.")
                    except (ValueError, IndexError):
                        logging.warning("Invalid /sbot add command format.")
                        await event.respond("Invalid command format. Use /sbot add <chat_id>")
                    return

                if event.message.text.startswith("/sbot del "):
                    try:
                        chat_id_to_del = int(event.message.text.split(" ")[2])
                        cursor.execute("DELETE FROM filtered_chats WHERE chat_id = ?", (chat_id_to_del,))
                        conn.commit()
                        if chat_id_to_del in filtered_chats:
                            filtered_chats.remove(chat_id_to_del)
                        logging.info(f"Removed chat {chat_id_to_del} from filter.")
                        await event.respond(f"Chat {chat_id_to_del} removed from filter.")
                    except (ValueError, IndexError):
                        logging.warning("Invalid /sbot del command format.")
                        await event.respond("Invalid command format. Use /sbot del <chat_id>")
                    return

                if event.message.text == "/sbot list":
                    logging.info("Processing /sbot list command.")
                    response = "Filtered chats:\n"
                    for chat_id in filtered_chats:
                        cursor.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
                        result = cursor.fetchone()
                        title = result[0] if result else "Unknown"
                        response += f"- {chat_id}: {title}\n"
                    await event.respond(response)
                    return

                if event.message.text.startswith("/sbot sum"):
                    logging.info("Processing /sbot sum command.")
                    parts = event.message.text.split(" ")
                    chat_id_filter = None
                    if len(parts) > 2:
                        try:
                            chat_id_filter = int(parts[2])
                        except ValueError:
                            logging.warning("Invalid chat ID in /sbot sum command.")
                            await event.respond("Invalid chat ID.")
                            return

                    llm_api_key, llm_folder_id = get_llm_credentials()

                    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
                    
                    chats_to_query = list(filtered_chats)
                    if chat_id_filter:
                        if chat_id_filter in filtered_chats:
                            chats_to_query = [chat_id_filter]
                        else:
                            await event.respond("Specified chat is not in the filter list.")
                            return

                    query = f"""
                        SELECT m.id, c.title, a.first_name, a.last_name, a.username, m.message, r.message
                        FROM messages m
                        JOIN chats c ON m.chat_id = c.id
                        JOIN authors a ON m.author_id = a.id
                        LEFT JOIN messages r ON m.reply_to_message_id = r.id
                        WHERE m.is_new = 1 AND m.date > ? AND m.chat_id IN ({','.join('?'*len(chats_to_query))})
                    """
                    params = [twenty_four_hours_ago] + chats_to_query

                    cursor.execute(query, params)
                    messages_to_process = cursor.fetchall()

                    if not messages_to_process:
                        await event.respond("No new messages to summarize.")
                        return

                    message_ids_to_update = [m[0] for m in messages_to_process]

                    messages_for_llm = []
                    for row in messages_to_process:
                        author_name = f"{row[2]} {row[3] if row[3] else ''}" if row[4] is None else row[4]
                        messages_for_llm.append({
                            'chat_title': row[1],
                            'author_name': author_name,
                            'text': row[5],
                            'reply_to_text': row[6]
                        })

                    summaries = []
                    for i in range(0, len(messages_for_llm), BATCH_SIZE):
                        batch = messages_for_llm[i:i + BATCH_SIZE]
                        summary = await summarize_messages(batch, llm_api_key, llm_folder_id)
                        summaries.append(summary)

                    full_summary = "\n".join(summaries)
                    await event.respond(full_summary)

                    # Mark messages as not new
                    if message_ids_to_update:
                        cursor.execute(f"UPDATE messages SET is_new = 0 WHERE id IN ({','.join('?'*len(message_ids_to_update))})", message_ids_to_update)
                        conn.commit()
                        logging.info(f"Marked {len(message_ids_to_update)} messages as not new.")

                    return

            if isinstance(chat, User) and chat.is_self:
                chat_title = "Saved Messages"
            elif hasattr(chat, 'title'):
                chat_title = chat.title
            else:
                chat_title = f"{chat.first_name} {chat.last_name if chat.last_name else ''}"

            if isinstance(sender, User):
                author_name = f"{sender.first_name} {sender.last_name if sender.last_name else ''}"
            elif isinstance(sender, Channel):
                author_name = sender.title
            else:
                author_name = "Unknown"

            # Insert chat information
            cursor.execute('INSERT OR IGNORE INTO chats (id, title) VALUES (?, ?)', (chat.id, chat_title))

            # Insert author information
            if isinstance(sender, User):
                cursor.execute('INSERT OR IGNORE INTO authors (id, first_name, last_name, username) VALUES (?, ?, ?, ?)',
                               (sender.id, sender.first_name, sender.last_name, sender.username))
            elif isinstance(sender, Channel):
                cursor.execute('INSERT OR IGNORE INTO authors (id, first_name, last_name, username) VALUES (?, ?, ?, ?)',
                               (sender.id, sender.title, None, sender.username))

            # Insert message
            cursor.execute('INSERT INTO messages (id, message, chat_id, author_id, date, reply_to_message_id, is_new) VALUES (?, ?, ?, ?, ?, ?, 1)',
                           (event.message.id, event.message.text, chat.id, sender.id, event.message.date, event.message.reply_to_msg_id))
            conn.commit()
            logging.info(f"Added new message from {chat_title} to database.")

        except Exception as e:
            logging.error(f"An error occurred in the message handler: {e}")

    async with client:
        logging.info("Client is running...")
        await client.run_until_disconnected()

    conn.close()
    logging.info("Application stopped.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Application failed to run: {e}")
