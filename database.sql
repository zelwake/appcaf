CREATE TABLE IF NOT EXISTS czech_word (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS english_word (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS french_word (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS czech_english_pair (
    czech_word_id INTEGER NOT NULL REFERENCES czech_word(id),
    english_word_id INTEGER NOT NULL REFERENCES english_word(id),
    PRIMARY KEY (czech_word_id, english_word_id)
);

CREATE TABLE IF NOT EXISTS czech_french_pair (
    czech_word_id INTEGER NOT NULL REFERENCES czech_word(id),
    french_word_id INTEGER NOT NULL REFERENCES french_word(id),
    PRIMARY KEY (czech_word_id, french_word_id)
);

CREATE TABLE IF NOT EXISTS english_french_pair (
    english_word_id INTEGER NOT NULL REFERENCES english_word(id),
    french_word_id INTEGER NOT NULL REFERENCES french_word(id),
    PRIMARY KEY (english_word_id, french_word_id)
);

CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    language_from TEXT NOT NULL,
    language_to TEXT NOT NULL,
    total INT NOT NULL,
    round INT DEFAULT 1,
    finished BOOLEAN NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finish_time TIMESTAMP,
    CHECK ( finished IN (0, 1))
);

CREATE TABLE IF NOT EXISTS test_word_relation (
    test_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    round INTEGER NOT NULL,
    try INT DEFAULT 0,
    answer_one TEXT,
    answer_two TEXT,
    FOREIGN KEY (test_id) REFERENCES test(id),
    PRIMARY KEY (test_id, word_id)
);

CREATE TABLE IF NOT EXISTS account (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_account_relation (
    account_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    FOREIGN KEY (account_id) REFERENCES account(id),
    FOREIGN KEY (test_id) REFERENCES test(id),
    PRIMARY KEY (account_id, test_id)
)


