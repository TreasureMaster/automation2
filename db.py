import os
import re

import click
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


from config import (
    DBMS,
    DB_NAME,
    SQL_INIT_FILE,
    ROOT_CONNECT,
    USER_GRANT,
    CLIENT_USERNAME,
    # USER_TEMPLATE,
    # GRANT_TEMPLATE,
    # USER_CONNECT,
)
from postgres_dialect import (
    DB_EXISTS,
    CREATE_DATABASE,
    DELETE_DATABASE,
    USER_EXISTS,
    DELETE_USER,
    CREATE_USER,
    SET_USER_GRANT,
)
# from models.config import USER_CONNECT


def get_db(dbname=None, connect_info=None):
    if connect_info is None:
        connect_info = ROOT_CONNECT
    if dbname is not None:
        connect_info['dbname'] = dbname
    db = psycopg2.connect(**connect_info)
    return db

def connect_db(dbname=DB_NAME, connect_info=None):
    """Присоединиться к конкретной БД (из config.py)"""
    return get_db(dbname, connect_info)

def db_exists(db_name):
    """Проверка существования БД"""
    with get_db().cursor() as cursor:
        cursor.execute(DB_EXISTS.format(db_name))
        exists = cursor.fetchone()
    return exists is not None

def user_exists(username):
    """Проверка существования пользователя"""
    with get_db().cursor() as cursor:
        cursor.execute(USER_EXISTS.format(username))
        exists = cursor.fetchone()
    return exists is not None

def user_create(username):
    """Создание пользователя"""
    conn = get_db()
    if not user_exists(username):
    #     user_revoke(username)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(CREATE_USER.format(**USER_GRANT))

def user_delete(username):
    """Удаление пользователя"""
    conn = get_db()
    if user_exists(username):
    #     user_revoke(username)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(DELETE_USER.format(username))

def set_user_grant(username):
    """Добавление прав пользователю пользователя"""
    conn = get_db()
    if user_exists(username):
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(SET_USER_GRANT.format(**USER_GRANT))

# def user_revoke(username):
#     """отзыв привилегий пользователя"""
#     conn = get_db()
#     # if user_exists(username):
#     with conn.cursor() as cursor:
#         # cursor.execute("""REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{username}'@'localhost'; {}""".format(username))
#         cursor.execute("""REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{}'""".format(username))

def db_create(db_name):
    """Создание БД"""
    conn = get_db()
    if not db_exists(db_name):
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(CREATE_DATABASE.format(db_name))

def db_delete(db_name):
    """Удаление БД"""
    conn = get_db()
    if db_exists(db_name):
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(DELETE_DATABASE.format(db_name))

def sqlfile_execute(sql_file, db_name, **kwargs):
    """Заполнить БД из скрипта SQL"""
    conn = get_db(db_name)
    if os.path.exists(sql_file):
        # with conn.cursor() as cursor:
        if DBMS == 'postgres':
            exec_postgres_file(conn, sql_file)

def exec_postgres_file(conn, sql_file):
    # conn = get_db(db_name)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cursor:
        cursor.execute(open(sql_file, 'r', encoding='utf-8').read())

    # MariaDB
    # print ("\n[INFO] Executing SQL script file: '%s'" % (sql_file))
    # statement = ""

    # for line in open(sql_file, encoding='utf-8'):
    #     line = line.format(**kwargs)
    #     if re.match(r'--', line):
    #         continue
    #     if not re.search(r'[^-;]+;', line):
    #         statement = statement + line
    #     else:
    #         statement = statement + line
    #         #print "\n\n[DEBUG] Executing SQL statement:\n%s" % (statement)
    #         try:
    #             cursor.execute(statement)
    #         except (mariadb.OperationalError, mariadb.ProgrammingError) as e:
    #             print ("\n[WARN] MySQLError во время выполнения \n\tАргументы: '%s'" % (str(e.args)))

    #         statement = ""

def user_init(db_name):
    """Создание нового пользователя"""
    username = CLIENT_USERNAME
    if username is not None:
        res = click.prompt(
            f"Эта процедура будет работать с пользователем '{username}'. "
            "Вы согласны? [(д)а/(н)ет] >> "
        ).lower()
        if res in ('да', 'д', 'yes', 'y'):
            if user_exists(username):
                res = click.prompt(
                    f"Пользователь '{username}' уже существует. "
                    "Удалить пользователя? [(д)а/(н)ет] >> "
                ).lower()
                if res in ('да', 'д', 'yes', 'y'):
                    user_delete(username)
                else:
                    click.echo(
                        'Отмена создания нового пользователя (уже существует).'
                    )
                    res = click.prompt(
                        f"Добавить пользователю '{username}' права на БД "
                        "'{db_name}'? [(д)а/(н)ет] >> "
                    ).lower()
                    if res in ('да', 'д', 'yes', 'y'):
                        # sqlfile_execute(GRANT_TEMPLATE, db_name, **USER_GRANT)
                        set_user_grant(username)
                    else:
                        click.echo('Отмена добавления прав новому пользователю')
                    return
            # sqlfile_execute(USER_TEMPLATE, db_name, **USER_GRANT)
            user_create(username)
        else:
            click.echo('Отмена создания нового пользователя.')

@click.command('init-db')
@click.option('--sql-file', '-f', default=SQL_INIT_FILE, help='название SQL-файла')
@click.option('--db-name', '-db', default=DB_NAME, help='имя базы данных')
def db_init(sql_file, db_name):
    """Инициализация новой БД"""
    if db_exists(db_name):
        res = click.prompt(f"Эта процедура полностью удалит базу данных '{db_name}' и создаст новую. Вы согласны? [(д)а/(н)ет] >> ").lower()
        if res in ('да', 'д', 'yes', 'y'):
            click.echo('Удаляем старую БД, создаем и заполняем новую')
            db_delete(db_name)
            db_create(db_name)
            sqlfile_execute(sql_file, db_name)
            user_init(db_name)
        else:
            click.echo('Отмена инициализации БД')
            return
    else:
        click.echo('Создаем новую БД и заполняем ее данными')
        db_create(db_name)
        sqlfile_execute(sql_file, db_name)
        user_init(db_name)
    click.echo(f"Новая БД '{db_name}' создана")


if __name__ == '__main__':

    print('--- DB connect' + '-'*50)
    # conn = get_db()
    # print(conn)
    # print(user_exists('postgres'))
    # db_init()
    user_init(DB_NAME)