# Проверка существования БД
DB_EXISTS = """SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}'"""
# Создание БД
CREATE_DATABASE = """CREATE DATABASE {}"""
# Удаление БД
DELETE_DATABASE = """DROP DATABASE {}"""
# Проверка сущестования пользователя
USER_EXISTS = """SELECT 1 FROM pg_roles WHERE rolname='{}'"""
# Удаление пользователя
DELETE_USER = """DROP USER IF EXISTS {}"""
# Удаление пользователя с зависимостями
DROP_RELATIONS = """DROP OWNED BY {}"""
# Создание пользователя
CREATE_USER = """CREATE USER {user} WITH CREATEDB PASSWORD '{password}'"""
# Добавление пользователю прав на БД
SET_USER_GRANT = """GRANT ALL PRIVILEGES ON DATABASE "{dbname}" to {user}"""
