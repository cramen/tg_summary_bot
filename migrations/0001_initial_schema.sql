CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY,
    title TEXT
);

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    message TEXT,
    chat_id INTEGER,
    author_id INTEGER,
    date DATETIME,
    FOREIGN KEY (chat_id) REFERENCES chats (id),
    FOREIGN KEY (author_id) REFERENCES authors (id)
);
