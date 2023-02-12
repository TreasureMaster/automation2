# СУБД
DBMS = 'postgres'
# Основная БД
DB_NAME = 'dj_auction'
# Создатель БД
DB_OWNER = 'django_user'
# SQL-скрипт заполнения БД
# SQL_INIT_FILE = 'temp/estate_register.sql'
SQL_INIT_FILE = None

DB_URL = {
    'host': 'localhost',
    'port': 5432,
}

ROOT_CONNECT = {
    'user': 'postgres',
    'password': 'root',
    **DB_URL,
}

ROOT_USER = {
    'user': 'postgres',
    'password': 'root',
}

CLIENT_USER = {
    'user': DB_OWNER,
    'password': 'pswd',
}


# Для вставки в SQL-скрипт
USER_GRANT = {
    **CLIENT_USER,
    **DB_URL,
    'dbname': DB_NAME,
}
