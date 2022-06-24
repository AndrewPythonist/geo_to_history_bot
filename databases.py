import sqlite3


def ensure_connection(func):
    """ Декоратор для подключения к СУБД: открывает соединение,
        выполняет переданную функцию и закрывает за собой соединение.
        Потокобезопасно!
    """
    def inner(*args, **kwargs):
        with sqlite3.connect('geo_to_history.db') as conn:
            kwargs['conn'] = conn
            res = func(*args, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    """ Проверить что нужные таблицы существуют, иначе создать их

        Важно: миграции на такие таблицы вы должны производить самостоятельно!

        :param conn: подключение к СУБД
        :param force: явно пересоздать все таблицы
    """
    c = conn.cursor()

    # Информация о пользователе
    # TODO: создать при необходимости...

    # Сообщения от пользователей
    if force:
        c.execute('DROP TABLE IF EXISTS geolocation')

    c.execute('''
        CREATE TABLE IF NOT EXISTS geolocation (
            id          INTEGER PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            username	TEXT NOT NULL,
            latitude	REAL NOT NULL,
            longitude	REAL NOT NULL,
            date		INTEGER NOT NULL
        )
    ''')

    # Сохранить изменения
    conn.commit()


@ensure_connection
def add_geo(conn, user_id: int, username: str, latitude: float, longitude: float, date: int):
    c = conn.cursor()
    c.execute('INSERT INTO geolocation (user_id, username, latitude, longitude, date) VALUES (?, ?, ?, ?, ?)', (user_id, username, latitude, longitude, date))
    conn.commit()


@ensure_connection
def count_messages(conn, user_id: int):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM geolocation WHERE user_id = ? LIMIT 1', (user_id, ))
    (res, ) = c.fetchone()
    return res

