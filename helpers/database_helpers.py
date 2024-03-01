from db import db
from enum import Enum


class AllowedTables(Enum):
    CZECH = 'czech_word'
    ENGLISH = 'english_word'
    FRENCH = 'french_word'


def get_word_id(word, table) -> int:
    if table not in AllowedTables:
        raise ValueError(f"Invalid table. Allowed values: {', '.join(table.value for table in AllowedTables)}")

    word_id = db.execute(f'SELECT id FROM {table} WHERE word = ?', word)
    if word_id:
        return word_id[0]['id']
    try:
        db.execute(f'INSERT INTO {table} (word) VALUES (?)', word)
        word_id = db.execute(f'SELECT id FROM {table} WHERE word = ?', word)
        return word_id[0]['id']
    except RuntimeError as e:
        print(f'insertion error {table}:\n{e}')
        return 0
