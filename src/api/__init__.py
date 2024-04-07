# coding: utf-8
"""
接口蓝图
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re
from copy import deepcopy
from functools import wraps

from flask import Blueprint, current_app, g, request
from werkzeug.exceptions import HTTPException

from ..response import json_return, GLOBAL_REQUEST_PARAM_LIST, GLOBAL_RESPONSE_CODE_LIST
from ..tool import get_error_info
from ..auth import TokenErr, need_token, create_token, clear_token
from ..model.base import AdminUser as UserInfo


api = Blueprint("api", __name__, url_prefix="/api")

# 公共参数列表
COMMON_REQUEST_PARAM_LIST = deepcopy(GLOBAL_REQUEST_PARAM_LIST)
COMMON_REQUEST_PARAM_LIST.update({
    "os_type": {"type": "str", "desc": "系统类型", "reg": r"\w+", "required": True},
    "device_uuid": {"type": "str", "desc": "设备唯一标识", "reg": r"\w+", "required": True},
})
api.COMMON_REQUEST_PARAM_LIST = COMMON_REQUEST_PARAM_LIST

# 公共返回值列表
COMMON_RESPONSE_CODE_LIST = deepcopy(GLOBAL_RESPONSE_CODE_LIST)
COMMON_RESPONSE_CODE_LIST.update({
    "ERR": (-1, "未知错误"),
    "TOKEN_NOT_FOUND": (2100, "缺少登录凭证"),
    "TOKEN_ERROR": (2101, "非法的登录凭证"),
    "TOKEN_INVALID": (2102, "登录凭证已失效"),
    "TOKEN_CHANGED": (2103, "登录环境改变"),
    "TOKEN_EXPIRED": (2104, "登录凭证已过期"),
    "TOKEN_TYPE_ERROR": (2105, "登录凭证类型错误"),
    "TOKEN_USER_ERROR": (2106, "无效的用户"),
    "TOKEN_USER_INVALID": (2107, "账号已禁用"),
    "TOKEN_PWD_ERROR": (2108, "密码已被改变"),

    "USER_NOT_LOGIN": (2200, "用户未登录"),
    "USER_NOT_FOUND": (2201, "用户不存在"),
    "USER_INVALID": (2202, "无效的用户"),
    "USER_TYPE_ERROR": (2203, "用户类型错误"),
    "USER_PWD_ERROR": (2204, "用户密码错误"),
    "USER_PRIV_ERROR": (2205, "用户权限不足"),
    "USER_EXIST": (2206, "用户已存在"),
})
api.COMMON_RESPONSE_CODE_LIST = COMMON_RESPONSE_CODE_LIST


def api_return(code, msg=None, data=None, **kwargs):
    code = str(code).upper()
    response_codes = getattr(current_app.blueprints.get(request.blueprint, current_app), "COMMON_RESPONSE_CODE_LIST", COMMON_RESPONSE_CODE_LIST)
    if code not in response_codes.keys():
        code = "ERR"
    if msg is None:
        msg = response_codes[code][1]
    if data is None:
        data = ""

    result = {"code": response_codes[code][0], "msg": msg, "data": data}
    result.update(kwargs)
    return json_return(result)


@api.before_request
def before_request():
    """蓝图请求前处理函数"""
    for field_name, p in getattr(current_app.blueprints.get(request.blueprint, current_app), "COMMON_REQUEST_PARAM_LIST", dict()).items():     # 验证公共参数
        field_reg = p.get("reg")
        field_required = p.get("required")
        field_data = str(g.request_data.get(field_name, "")).strip()
        if field_required and re.search(field_reg, str(field_data)) is None:
            current_app.logger.error(f"公共参数错误：{field_name}:{field_data}")
            return api_return("PARAM_ERROR", f"公共参数错误：{field_name}")
        setattr(g, field_name, field_data)
    g.client_info = f"{g.get('app_channel', '')}-{g.get('os_type', '')}-{g.get('device_uuid', '')}"


@api.errorhandler(TokenErr)
def token_error_handler(error):
    current_app.logger.error("Token错误：{0}, {1}".format(error.desc, str(error.kwargs)))
    return api_return(error.name, error.desc)


@api.errorhandler(Exception)
def other_error_handler(error):
    if isinstance(error, HTTPException):
        current_app.logger.error("Http错误：{0}, {1}".format(error.code, error.description))
        return api_return(error.code)
    file, line, func, _ = get_error_info()
    current_app.logger.error('代码错误：{0}, {1}({2})[{3}]'.format(str(error), file, line, func))
    return api_return("ERR", "服务器内部异常")


def need_login(func):
    """在need_token的基础上验证用户数据，或者可以验证其他访问权限"""
    @wraps(func)
    @need_token
    def wrapper(*args, **kwargs):
        user_id = g.get("user_id")
        if not user_id:
            raise TokenErr("TOKEN_USER_ERROR", "无效的用户ID")

        user = UserInfo.query.filter_by(id=user_id).first()
        if user is None:
            raise TokenErr("TOKEN_USER_ERROR", "无效的用户", user_id=user_id)
        if user.status != 1:
            raise TokenErr("TOKEN_USER_INVALID", "账号已禁用", user_id=user_id, account=user.account)

        g.user = user

        return func(*args, **kwargs)
    return wrapper


def login_user(user):
    """登录用户，创建并返回token"""
    return create_token(user.id, user.password, g.get("client_info"))


def logout_user():
    """登出用户，清除缓存token"""
    clear_token(g.get("user_id", 0))


# 导入蓝图要加载的接口
from . import base
