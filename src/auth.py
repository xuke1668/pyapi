# coding: utf-8
"""
权限认证
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
验证token的装饰器
"""
import time
from functools import wraps
from hmac import compare_digest

from flask import current_app, g, request
from itsdangerous import URLSafeSerializer

from . import cache
from .tool import get_client_ident


# token名称
TOKEN_NAME = "token"
# token缓存前缀
TOKEN_PREFIX = "user_token_"
# token缓存时间
TOKEN_LIFETIME = 7 * 24 * 60 * 60


class TokenErr(Exception):
    def __init__(self, name, desc="", **kwargs):
        self.name = name
        self.desc = desc
        self.kwargs = kwargs


def create_token(user_id, password, client_info=""):
    """
    生成并缓存token
    :param user_id:  缓存token的用户标识
    :param password: 用户密码
    :param client_info: 客户端信息
    :return: token
    """
    create_time = int(time.time())
    user_ident = get_client_ident(client_info)
    token_lifetime = current_app.config.get("TOKEN_LIFETIME", TOKEN_LIFETIME)
    key = current_app.config.get("SECRET_KEY", '')
    token_serializer = URLSafeSerializer(key)
    token = token_serializer.dumps((user_id, password, user_ident, token_lifetime, create_time))
    cache.set("{0}{1}".format(TOKEN_PREFIX, user_id), token, timeout=token_lifetime)
    return token


def clear_token(user_id):
    """
    清除token
    :param user_id: 缓存token的用户标识
    """
    cache.delete("{0}{1}".format(TOKEN_PREFIX, user_id))


def need_token(func):
    """校验token合法性"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token_id = current_app.config.get("TOKEN_NAME", TOKEN_NAME)
        token = request.headers.get(token_id) or g.request_data.get(token_id)
        if token is None:
            raise TokenErr("TOKEN_NOT_FOUND", "缺少登录凭证")

        # 解析token
        key = current_app.config.get("SECRET_KEY", "")
        try:
            token_serializer = URLSafeSerializer(key)
            user_id, password, user_ident, token_lifetime, create_time = token_serializer.loads(token)
        except Exception:
            raise TokenErr("TOKEN_ERROR", "非法的登录凭证")

        # 判断token环境是否改变
        identifier = get_client_ident(g.get("client_info"))
        if not compare_digest(str(user_ident), str(identifier)):
            raise TokenErr("TOKEN_CHANGED", "登录环境改变", user_id=user_id)

        # 判断token缓存是否有效
        cached_token = cache.get("{0}{1}".format(TOKEN_PREFIX, user_id))
        if cached_token:
            if not compare_digest(cached_token, token):  # token不同时，把cached_token解析出来比对哪里有变化，以便给出精准提示
                try:
                    _user_id, _password, _user_ident, _token_lifetime, _create_time = token_serializer.loads(cached_token)
                except Exception:
                    raise TokenErr("TOKEN_INVALID", "登录凭证已失效", user_id=user_id)
                if user_id != _user_id or password != _password:
                    raise TokenErr("TOKEN_INVALID", "登录凭证已失效", user_id=user_id)
                if user_ident != _user_ident:
                    raise TokenErr("TOKEN_CHANGED", "登录环境改变", user_id=user_id)
                if int(create_time) < int(_create_time):
                    raise TokenErr("TOKEN_INVALID", "登录凭证已过期", user_id=user_id)
        else:
            raise TokenErr("TOKEN_INVALID", "登录凭证已过期", user_id=user_id)

        # 刷新token时间
        if token_lifetime:
            cache.set("{0}{1}".format(TOKEN_PREFIX, user_id), token, timeout=token_lifetime)

        g.user_id = user_id
        g.user_login_time = create_time

        return func(*args, **kwargs)
    return wrapper
