# coding: utf-8
"""
应用入口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import sys
import re
import time

from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import import_string

from .config import config
from .logger import Logger
from .cache import RedisCache as Cache

db = SQLAlchemy()
logger = Logger()
cache = Cache()


def before_request():
    """全局请求前处理函数"""
    g.request_stime = time.time()
    g.cur_path = re.sub('/+', '/', request.path + '/')

    # 搜集参数信息
    if request.method == "POST":
        if request.is_json:
            request_data = request.get_json(silent=True)
        else:
            request_data = request.form
    elif request.method == "GET":
        request_data = request.args
    else:
        request_data = request.values
    g.request_data = request_data if request_data else dict()


def prestart_check(app):
    """检测是否满足启动条件"""
    if not app.config.get("SECRET_KEY"):
        app.logger.error("Not found secret_key")
        return False
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.logger.error("Not found database_uri")
        return False
    with app.app_context():
        try:
            db.session.execute("show databases;")
        except Exception as e:
            app.logger.error("Database connection failed, %s", e)
            return False
        try:
            cache.get("")
        except Exception as e:
            app.logger.error("Cache connection failed, %s", e)
            return False
    return True


def create_app(env='development'):
    """程序工厂函数"""
    app = Flask(__name__)
    app.uptime = time.time()

    # 加载配置文件
    app.config.from_object(config[env])

    # 初始化插件
    logger.init_app(app)
    db.init_app(app)
    cache.init_app(app)

    # 加载蓝图模块
    blueprints = ['src.api:api']
    for bp_name in blueprints:
        app.register_blueprint(import_string(bp_name))

    # 加载钩子函数
    app.before_request(before_request)

    # 启动前检测
    if not prestart_check(app):
        sys.exit(1)

    app.logger.info("application started on %s, found %s api", env, len(list(app.url_map.iter_rules())) - 1)
    return app
