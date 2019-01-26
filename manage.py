# coding: utf-8
"""
项目管理文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
项目起停、数据库初始化等
"""

import sys
import unittest

from flask_script import Manager, Server, prompt_bool

from src import create_app, db
from src.model import base

app = create_app('development')
manager = Manager(app)


def make_shell_context():
    return dict(app=app, db=db, model=base)


@manager.command
def init_db():
    """初始化数据库基本表结构"""
    print("库表结构初始化...", end="")
    db.create_all()
    print("完成")


@manager.command
def drop_db():
    """删除所有库表结构"""
    if prompt_bool("确定要删除所有数据吗？"):
        print('\n删除所有数据...', end="")
        db.drop_all()
        print('完成')


@manager.option('-n', '--name', dest='name')
def rebuild_table(name):
    print("drop table {0}".format(name))
    db.session.execute("drop table IF EXISTS {0}".format(name))
    print("create all")
    db.create_all()
    print("完成")


@manager.command
def run_test():
    """运行测试用例"""
    tests = unittest.TestLoader().discover('./tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.add_command("run", Server("0.0.0.0", port=8850))
    if len(sys.argv) == 1:
        sys.argv.extend(["run", "--threaded"])
    manager.run()
