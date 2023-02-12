import os

import click
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


from config import (
    DB_URL,
    DBMS,
    DB_NAME,
    SQL_INIT_FILE,
    ROOT_CONNECT,
    USER_GRANT,
    # CLIENT_USERNAME,
    # USER_CONNECT,
    # USER_ROOT_CONNECT,
    ROOT_USER,
    CLIENT_USER,
)
from postgres_dialect import (
    DB_EXISTS,
    CREATE_DATABASE,
    CREATE_DATABASE_POSTGIS,
    DELETE_DATABASE,
    USER_EXISTS,
    DELETE_USER,
    CREATE_USER,
    SET_USER_GRANT,
    DROP_RELATIONS,
)


class Connection:
    """Создает соединение для данного пользователя и БД"""
    _CONNECTION = None

    def __init__(self, connect_info, dbname=None):
        """Инициализирует соединение
        
        :param connect_info: Словарь данных для соединения
            (user, password, host, port, dbname).
        :param dbname: Изменение или добавление имени БД для подключения
        """
        print(connect_info)
        if dbname is not None:
            connect_info['dbname'] = dbname
        self._CONNECTION = psycopg2.connect(**connect_info)

    def get_connection(self):
        return self._CONNECTION


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


class UserDB:
    __slots__ = ('user', 'password')

    def __init__(self, user_info={}):
        self.user = user_info.get('user')
        self.password = user_info.get('password')

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return {'user': self.user, 'password': self.password}

    def __set__(self, instance, value):
        raise AttributeError(
            'Изменение парамтров после инициализации не предусмотрено'
        )


class HostDB:
    __slots__ = ('host', 'port')

    def __init__(self, host_info={}):
        self.host = host_info.get('host')
        self.port = host_info.get('port')

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return {'host': self.host, 'port': self.port}

    def __set__(self, instance, value):
        raise AttributeError(
            'Изменение парамтров после инициализации не предусмотрено'
        )


class BaseDB:
    """Процедуры для работы с БД через заданное соединение"""
    root = UserDB()
    client = UserDB()
    host = HostDB()

    def __init__(self, is_root=True):
        # по умолчанию - подключение root
        self.root_connect() if is_root else self.user_connect()

    def exists(self, dbname):
        """Проверка существования БД"""
        with self.connection.cursor() as cursor:
            cursor.execute(DB_EXISTS.format(dbname))
            exists = cursor.fetchone()
        return exists is not None

    def create(self, dbname, is_postgis=False):
        """Создание БД"""
        if not self.exists(dbname):
            with self.connection.cursor() as cursor:
                cursor.execute((
                    CREATE_DATABASE_POSTGIS if is_postgis else CREATE_DATABASE
                ).format(dbname))

    # def recreate(self, dbname):
    #     """Пересоздание БД: удаление + создание"""
    #     self.delete(dbname)
    #     self.create(dbname)

    def delete(self, dbname):
        """Удаление БД"""
        if self.exists(dbname):
            with self.connection.cursor() as cursor:
                cursor.execute(DELETE_DATABASE.format(dbname))

    def _connect(self, connect_info):
        """Переподключение к БД с другими данными"""
        self.connection = Connection(connect_info).get_connection()
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    def root_connect(self, dbname=None):
        """Подключение к БД с данными root"""
        self._connect({**self.root, **self.host, 'dbname': dbname})

    def user_connect(self, dbname=DBMS):
        """Подключение к БД с данными user"""
        self._connect({**self.client, **self.host, 'dbname': dbname})

    def user_exists(self, username):
        """Проверка существования пользователя"""
        with self.connection.cursor() as cursor:
            cursor.execute(USER_EXISTS.format(username))
            exists = cursor.fetchone()
        return exists is not None

    def user_create(self, username):
        """Создание пользователя"""
        if not self.user_exists(username):
            with self.connection.cursor() as cursor:
                cursor.execute(CREATE_USER.format(**USER_GRANT))

    def user_delete(self, username):
        """Удаление пользователя"""
        self.user_relations_drop(username)
        if self.user_exists(username):
            with self.connection.cursor() as cursor:
                cursor.execute(DELETE_USER.format(username))

    def user_relations_drop(self, username):
        """Удаление зависимостей пользователя"""
        if self.user_exists(username):
            with self.connection.cursor() as cursor:
                cursor.execute(DROP_RELATIONS.format(username))

    def set_user_grant(self, username):
        """Добавление прав пользователю пользователя"""
        if self.user_exists(username):
            with self.connection.cursor() as cursor:
                cursor.execute(SET_USER_GRANT.format(**USER_GRANT))

    def get_clientname(self):
        """Получить имя пользователя"""
        return self.client['user']


class PostgresDB(BaseDB):
    root = UserDB(ROOT_USER)
    client = UserDB(CLIENT_USER)
    host = HostDB(DB_URL)


def sqlfile_execute(sql_file, db_name, **kwargs):
    """Заполнить БД из скрипта SQL"""
    if sql_file is not None:
        conn = get_db(db_name)
        if os.path.exists(sql_file):
            if DBMS == 'postgres':
                # conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    cursor.execute(
                        open(sql_file, 'r', encoding='utf-8').read()
                    )


def user_init(db):
    """Создание нового пользователя"""
    # Создание пользователя от имени рута
    if (username := db.get_clientname()) is not None:
        res = click.prompt(
            f"Эта процедура будет работать с пользователем '{username}'. "
            "Вы согласны? [(д)а/(н)ет] >> "
        ).lower()
        if res in ('да', 'д', 'yes', 'y'):
            if db.user_exists(username):
                res = click.prompt(
                    f"Пользователь '{username}' уже существует. "
                    "Удалить пользователя? [(д)а/(н)ет] >> "
                ).lower()
                if res in ('да', 'д', 'yes', 'y'):
                    db.user_delete(username)
                else:
                    click.echo(
                        'Отмена создания нового пользователя (уже существует).'
                    )
                    # res = click.prompt(
                    #     f"Добавить пользователю '{username}' права на БД "
                    #     "'{db_name}'? [(д)а/(н)ет] >> "
                    # ).lower()
                    # if res in ('да', 'д', 'yes', 'y'):
                    #     set_user_grant(username)
                    # else:
                    #     click.echo('Отмена добавления прав новому пользователю')
                    db.user_connect()
                    return
            db.user_create(username)
            db.user_connect()
        else:
            click.echo('Отмена создания нового пользователя.')
    else:
        print(username)


def is_postgis():
    """Использовать ли PostGIS ?"""
    res = click.prompt(f"Добавить шаблон PostGIS в БД. Вы согласны? [(д)а/(н)ет] >> ").lower()
    if res in ('да', 'д', 'yes', 'y'):
        return True
    return False


@click.command('init-db')
@click.option('--sql-file', '-f', default=SQL_INIT_FILE, help='название SQL-файла')
@click.option('--dbname', '-db', default=DB_NAME, help='имя базы данных')
def db_init(sql_file, dbname):
    """Инициализация новой БД"""
    dbms = PostgresDB()
    if dbms.exists(dbname):
        res = click.prompt(f"Эта процедура полностью удалит базу данных '{dbname}' и создаст новую. Вы согласны? [(д)а/(н)ет] >> ").lower()
        if res in ('да', 'д', 'yes', 'y'):
            click.echo('Удаляем старую БД, создаем и заполняем новую')
            dbms.delete(dbname)
            user_init(dbms)
            dbms.create(dbname, is_postgis=is_postgis())
            sqlfile_execute(sql_file, dbname)
        else:
            click.echo('Отмена инициализации БД')
            return
    else:
        click.echo('Создаем новую БД и заполняем ее данными')
        user_init(dbms)
        dbms.create(dbname, is_postgis=is_postgis())
        sqlfile_execute(sql_file, dbname)
    click.echo(f"Новая БД '{dbname}' создана")


if __name__ == '__main__':

    print('--- DB connect' + '-'*50)
    # dbms = PostgresDB()
    # user_init(dbms)
    # print(dbms.user_exists('django_user'))
    # if dbms.user_exists('django_user'):
    #     dbms.user_drop('django_user')
    #     print('user deleted...')
    # else:
    #     dbms.user_create('django_user')
    #     print('user created...')
    #     dbms.user_connect()
        # psycopg2.connect(**{
        #     'user': 'django_user',
        #     'password': 'pswd',
        #     'host': 'localhost',
        #     'port': 5432,
        #     'dbname': 'postgres'
        # })

    db_init()
    # user_init(DB_NAME)
    # user_delete(CLIENT_USERNAME)
    # db_delete(DB_NAME)
    # db_create('dj_estate_register')
    # user_create('django_user')
    # set_user_grant('django_user')
    # user_init(DB_NAME)
