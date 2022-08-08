# СУБД
DBMS = 'postgres'
# Основная БД
DB_NAME = 'dj_estate_register'
# SQL-скрипт заполнения БД
SQL_INIT_FILE = 'temp/estate_register.sql'

DB_URL = {
    'host': 'localhost',
    'port': 5432,
}

ROOT_CONNECT = {
    'user': 'postgres',
    'password': 'root',
    **DB_URL,
}
# 2 параметра пользователя
CLIENT_USERNAME = 'django_user'
CLIENT_PASSWORD = 'pswd'

USER_CONNECT = {
    'user': CLIENT_USERNAME,
    'password': CLIENT_PASSWORD,
    **DB_URL,
    'dbname': DB_NAME,
}

# Для вставки в SQL-скрипт
USER_GRANT = {
    'username': CLIENT_USERNAME,
    'password': CLIENT_PASSWORD,
    **DB_URL,
    'db': DB_NAME,
}
