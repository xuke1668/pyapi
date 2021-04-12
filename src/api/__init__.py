# coding: utf-8
"""
接口蓝图
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re
from functools import partial, wraps

from flask import Blueprint, current_app, g, request

from ..response import api_return, RESPONSE_CODE_LIST
from ..tool import get_error_info
from ..auth import TokenErr, need_token, create_token, clear_token
from ..model.base import AdminUser as UserInfo


api = Blueprint("api", __name__, url_prefix="/api")

# 公共参数列表
COMMON_PARAM_LIST = [
        {"name": "app_channel", "type": "str", "desc": "APP渠道", "reg": r"\w+", "required": True},
        {"name": "app_version", "type": "str", "desc": "APP版本", "reg": r"\w+", "required": False},
        {"name": "os_type", "type": "str", "desc": "系统类型", "reg": r"\w+", "required": False},
        {"name": "os_version", "type": "str", "desc": "系统版本", "reg": r"\w+", "required": False},
        {"name": "device_uuid", "type": "str", "desc": "设备唯一标识", "reg": r"\w+", "required": False},
    ]


@api.before_request
def before_request():
    """蓝图请求前处理函数"""
    for p in COMMON_PARAM_LIST:     # 验证公共参数
        field_name = p.get("name")
        field_reg = p.get("reg")
        field_required = p.get("required")
        field_data = str(g.request_data.get(field_name, "")).strip()
        if field_required and re.search(field_reg, str(field_data)) is None:
            current_app.logger.debug("公共参数错误：{0}:{1}".format(field_name, field_data))
            return api_return("PARAM_ERROR", "公共参数错误：{0}".format(field_name))
        setattr(g, field_name, field_data)
    g.client_info = "-".join([str(g.get("app_channel", "")), str(g.get("os_type", "")), str(g.get("device_uuid", ""))])


@api.before_app_first_request
def register_api_doc():
    """全局第一个请求之前，把接口文档路由添加到应用中"""
    if current_app.config.get("ENV") == "development":
        from ..doc import generate_doc
        view_functions = [(k, v) for k, v in current_app.view_functions.items() if k.startswith(api.name+".")]
        api_doc_func = partial(generate_doc, view_functions=view_functions, common_param_list=COMMON_PARAM_LIST, response_code_list=RESPONSE_CODE_LIST)
        api_doc_endpoint = api.name + "_api_doc"
        api_doc_url = api.url_prefix + "/doc/" if api.url_prefix else "/doc/"
        current_app.add_url_rule(api_doc_url, view_func=api_doc_func, endpoint=api_doc_endpoint, methods=["GET"])
        # 由于请求分发（full_dispatch_request）之前request的内容就已经通过request_context装载完毕，那时候url_map中还没有文档接口。
        # 如果恰好第一个request就要请求文档接口，会导致request_context装载时match_request失败，产生404错误，然后调用请求分发时会弹出这个错误。
        # 这里在匹配到请求文档接口的意图后，手动修改request请求体，把错误去除后再把url_rule装载到请求体里，就可以了。
        if request.path == api_doc_url and request.method.upper() == "GET":
            request.routing_exception = None
            request.url_rule = current_app.url_map._rules_by_endpoint[api_doc_endpoint][0]
            request.view_args = {}


@api.errorhandler(TokenErr)
def error_token(error):
    current_app.logger.debug("Token错误：{0}, {1}".format(error.desc, str(error.kwargs)))
    return api_return(error.name, error.desc)


@api.errorhandler(Exception)
def catch_error(error):
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
            raise TokenErr("TOKEN_USER_ERROR", "无效的用户")

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


# 导入蓝图要加载的接口文件
from . import base
