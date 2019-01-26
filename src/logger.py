# coding: utf-8
"""
日志插件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
处理日志相关配置
"""
import os
from logging import handlers, Formatter

from flask.logging import default_handler


class Logger(object):
    def __init__(self, app=None, log_dir=None, log_level=None, log_keep_day=None):
        self.log_dir = "logs"
        self.log_level = 20     # CRITICAL:50,ERROR:40,WARNING:30,INFO:20,DEBUG:10,NOTSET:0
        self.log_keep_day = 30

        self.app = app
        if app is not None:
            self.init_app(app, log_dir, log_level, log_keep_day)

    def init_app(self, app, log_dir=None, log_level=None, log_keep_day=None):
        # 移除缺省的日志记录器
        app.logger.removeHandler(default_handler)

        self.log_dir = log_dir if log_dir else app.config.get("LOG_DIR", self.log_dir)
        self.log_level = log_level if log_level else app.config.get("LOG_LEVEL", self.log_level)
        self.log_keep_day = log_keep_day if log_keep_day else app.config.get("LOG_KEEP_DAY", self.log_keep_day)

        if self.log_dir.startswith("/"):
            log_path = os.path.normpath(self.log_dir)
        else:
            log_path = os.path.normpath(os.path.join(app.root_path, '../', self.log_dir))
        if not os.path.isdir(log_path):
            try:
                os.makedirs(log_path)
            except Exception as e:
                raise e

        formatter = Formatter('%(asctime)s|%(levelname)s|%(pathname)s(%(lineno)d)|%(funcName)s|%(message)s')
        log_file = os.path.join(log_path, app.name + '.log')
        log_file_handler = handlers.TimedRotatingFileHandler(log_file, when="D", backupCount=self.log_keep_day)
        log_file_handler.setFormatter(formatter)
        app.logger.addHandler(log_file_handler)
        app.logger.setLevel(int(self.log_level))
