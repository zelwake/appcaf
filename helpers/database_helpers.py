from db import db
from enum import Enum, member


class AllowedWordTables(Enum):
    CZECH = 'czech_word'
    ENGLISH = 'english_word'
    FRENCH = 'french_word'


def get_word_id(word, table) -> int:
    values = [key.value for key in AllowedWordTables]
    if table not in values:
        raise ValueError(f"Invalid table. Allowed values: {', '.join(table.value for table in AllowedWordTables)}")

    word_id = db.execute(f'SELECT id FROM {table} WHERE word = ?',
                         word)
    if word_id:
        return word_id[0]['id']
    try:
        db.execute(f'INSERT INTO {table} (word) VALUES (?)',
                   word)
        word_id = db.execute(f'SELECT id FROM {table} WHERE word = ?',
                             word)
        return word_id[0]['id']
    except RuntimeError as e:
        print(f'insertion error {table}:\n{e}')
        return 0


class DatabaseWordPairTable(Enum):
    CZECH_ENGLISH_PAIR = 'czech_english_pair'
    CZECH_FRENCH_PAIR = 'czech_french_pair'
    ENGLISH_FRENCH_PAIR = 'english_french_pair'


def insert_word_pair(table, id1, id2):
    values = [key.value for key in DatabaseWordPairTable]
    if table not in values:
        return False

    try:
        pairs = table.split('_')
        query = f'INSERT OR IGNORE INTO {table} ({pairs[0]}_word_id, {pairs[1]}_word_id) VALUES (?, ?)'
        db.execute(query, id1, id2)
    except RuntimeError as e:
        print(f'Error while creating pairs:\n{e}')
        return False
    return True
