# coding: utf-8
"""
项目配置文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
各项参数配置
"""


class Config:
    APP_VERSION = "0123456789"
    APP_UPDATE_TIME = "2024-04-03 13:50:12"
    SECRET_KEY = "hard to guess string"

    # SQLALCHEMY数据库链接配置
    SQLALCHEMY_POOL_SIZE = 100              # 连接池个数
    SQLALCHEMY_POOL_TIMEOUT = 30            # 超时时间，秒
    SQLALCHEMY_POOL_RECYCLE = 3600          # 空连接回收时间，秒
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    CACHE_TYPE = "redis"                    # 设置缓存类型，redis 或 memory（默认）

    SMS_CODE_INTERVAL_TIME = 60             # 验证码获取间隔
    SMS_CODE_VALID_TIME = 10 * 60           # 验证码有效时间，秒
    MAX_REGISTER_CODE_ONE_DAY = 5           # 一天内最多获得几次注册验证码
    MAX_RESET_CODE_ONE_DAY = 5              # 一天内最多获得几次重置密码验证码
    MAX_CHANGE_ACCOUNT_CODE_ONE_DAY = 1     # 一天内最多获得几次重置账号验证码

    TOKEN_NAME = "token"                    # 请求头中的token字段名称
    TOKEN_LIFETIME = 7 * 24 * 60 * 60       # token缓存时间

    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID = ""
    OSS_ACCESS_KEY_SECRET = ""
    OSS_ACCESS_ENDPOINT = ""
    OSS_AVATAR_BUCKET_NAME = ""


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 10
    SQLALCHEMY_DATABASE_URI = "mysql://pyapi_dev_user:pyapi_dev_pwd_123@127.0.0.1:3306/pyapi_dev?charset=utf8mb4"
    REDIS_URI = "redis://localhost:6379/0"
    APP_API_DOC = True


class TestingConfig(Config):
    TESTING = True
    LOG_LEVEL = 10
    SQLALCHEMY_DATABASE_URI = "mysql://pyapi_test_user:pyapi_test_pwd_123@127.0.0.1:3306/pyapi_test?charset=utf8mb4"
    REDIS_URI = "redis://localhost:6379/0"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "mysql://pyapi_user:pyapi_pwd_123@127.0.0.1:3306/pyapi?charset=utf8mb4"
    REDIS_URI = "redis://localhost:6379/0"


config = {
    "dev": DevelopmentConfig,
    "test": TestingConfig,
    "prod": ProductionConfig
}
