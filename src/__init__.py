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
from sqlalchemy import text
from werkzeug.utils import import_string

from .config import config
from .logger import Logger
from .cache import Cache
from .doc import ApiDoc

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


def check_app(app):
    """检测是否满足启动条件"""
    if not app.config.get("SECRET_KEY"):
        print(f"Not found secret_key")
        sys.exit(1)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        print(f"Not found database_uri")
        sys.exit(1)
    with app.app_context():
        try:
            db.session.execute(text("show databases;"))
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)
        try:
            cache.get("")
        except Exception as e:
            print(f"Cache connection failed: {e}")
            sys.exit(1)


def create_app(env="dev", name="app"):
    """程序工厂函数"""
    if not env or not name:
        print(f"create_app 参数错误：env:{env}, name:{name}")
        sys.exit(1)

    app = Flask(__name__ if not name else name)
    app.uptime = time.time()

    # 加载配置文件
    app.config.from_object(config.get(env))
    app.config["APP_ENV"] = env
    app.config["APP_NAME"] = app.name

    # 初始化插件
    logger.init_app(app)
    db.init_app(app)
    cache.init_app(app, cache_type=app.config.get("CACHE_TYPE"))

    # 加载蓝图模块
    blueprints = ["src.api:api"]
    for bp_name in blueprints:
        app.register_blueprint(import_string(bp_name))

    # 加载钩子函数
    app.before_request(before_request)

    # 生成api文档
    if app.config.get("APP_API_DOC"):
        ApiDoc(app, api_blueprints=["api"])     # 指定要生成接口文档的蓝图name

    # 启动前检测
    check_app(app)

    app.logger.info("application started on %s, found %s api.", env, len(list(app.url_map.iter_rules())) - 1)
    return app
