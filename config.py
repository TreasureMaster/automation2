# СУБД
DBMS = 'postgres'
# Основная БД
DB_NAME = 'estate_register'
# Тестовая БД
# PG_DB_NAME = 'test_restful_messages'
SQL_INIT_FILE = 'temp/estate_register.sql'
# SQL_INIT_FILE = 'initdb/test.sql'
# USER_TEMPLATE = 'initdb/user_create_template.sql'
# GRANT_TEMPLATE = 'initdb/user_grant_template.sql'

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
CLIENT_USERNAME = 'test_user'
CLIENT_PASSWORD = 'pswd'

USER_CONNECT = {
    'user': CLIENT_USERNAME,
    'password': CLIENT_PASSWORD,
    **DB_URL,
    'dbname': DB_NAME,
}
# USER_CONNECT = ROOT_CONNECT

# Для вставки в SQL-скрипт
USER_GRANT = {
    'username': CLIENT_USERNAME,
    'password': CLIENT_PASSWORD,
    **DB_URL,
    'db': DB_NAME,
    # 'host': '%',
}
