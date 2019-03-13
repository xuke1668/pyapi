# coding: utf-8
"""
返回值处理
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
实现返回值格式化方法，统一返回码
"""

import json
import decimal
from datetime import date, time, datetime

from flask import Response


RESPONSE_CODE_LIST = {
    "ERR": (-1, "未知错误"),

    "OK": (0, "成功"),
    "SUCCESS": (0, "成功"),
    "ERROR": (1, "错误"),
    "FAILED": (1, "失败"),

    "DB_CONN_FAILED": (10, "数据库连接失败"),
    "SQL_ERROR": (11, "SQL错误"),

    "SMS_SEND_FAILED": (20, "短信发送失败"),

    "CODE400": (400, "请求异常"),
    "CODE403": (403, "无访问权限"),
    "CODE404": (404, "接口不存在"),
    "CODE405": (405, "方法不支持"),
    "CODE500": (500, "服务端异常"),

    "REQUEST_NUMBER_LIMIT": (1000, "请求次数超出限制"),
    "REQUEST_INTERVAL_LIMIT": (1001, "请求频率超出限制"),
    "REAUEST_NOT_JSON": (1002, "请求不是JSON格式"),

    "PARAM_NOT_FOUND": (1100, "参数不足"),
    "PARAM_TYPE_ERROR": (1101, "参数类型错误"),
    "PARAM_ERROR": (1102, "参数错误"),
    "PARAM_RANGE_ERROR": (1103, "参数范围错误"),
    "PARAM_FORMAT_ERROR": (1104, "参数格式错误"),
    "PARAM_MOBILE_ERROR": (1105, "手机号错误"),
    "PARAM_EMAIL_ERROR": (1106, "邮箱错误"),
    "PARAM_PHONE_ERROR": (1107, "电话错误"),
    "PARAM_TIMESTR_ERROR": (1108, "时间错误"),
    "PARAM_CODE_ERROR": (1109, "验证码错误"),
    "PARAM_CODE_INVALID": (1110, "验证码无效"),

    "DATA_EXIST": (2000, "数据已存在"),
    "DATA_NOT_FOUND": (2001, "数据不存在"),
    "DATA_NOT_CHANGE": (2002, "数据未改变"),
    "DATA_ERROR": (2003, "数据错误"),

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

}


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return super().default(self, obj)


def json_return(data):
    return Response(json.dumps(data, cls=JsonEncoder, separators=(",", ":")), mimetype="application/json")


def api_return(code, msg=None, data=None, **kwargs):
    code = str(code).upper()
    if code not in RESPONSE_CODE_LIST.keys():
        code = "ERR"
    if msg is None:
        msg = RESPONSE_CODE_LIST[code][1]
    if data is None:
        data = ""

    result = {"code": RESPONSE_CODE_LIST[code][0], "msg": msg, "data": data}
    result.update(kwargs)
    return json_return(result)
