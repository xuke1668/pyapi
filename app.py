# coding: utf-8

from os import getenv
from click import argument

from src import create_app, db


env = getenv("APP_ENV", "dev").lower()
name = getenv("APP_NAME", __name__).lower()
flask_app = create_app(env, name)


@flask_app.cli.command("init_db")
def init_db():
    """初始化数据库基本表结构"""
    print(f"【{env}】环境下库表结构初始化...", end="")
    db.create_all()
    print("完成")


@flask_app.cli.command("drop_db")
def drop_db():
    """删除所有库表结构"""
    rv = input(f"确定要删除【{env}】环境下所有数据吗？[Y/N]\n")
    if rv and rv.lower() in ('y', 'yes'):
        print('删除所有数据...', end="")
        db.drop_all()
        print('完成')


@flask_app.cli.command("rebuild_table")
@argument('table_name')
def rebuild_table(table_name):
    print("drop table {0}".format(table_name))
    db.session.execute("drop table IF EXISTS {0}".format(table_name))
    print("create all")
    db.create_all()
    print("完成")
