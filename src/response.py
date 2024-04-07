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


GLOBAL_REQUEST_PARAM_LIST = {
    "app_channel": {"type": "str", "desc": "APP渠道", "reg": r"\w+", "required": True},
    "app_version": {"type": "str", "desc": "APP版本", "reg": r"\w+", "required": False},
    "os_type": {"type": "str", "desc": "系统类型", "reg": r"\w+", "required": False},
    "os_version": {"type": "str", "desc": "系统版本", "reg": r"\w+", "required": False},
}
GLOBAL_RESPONSE_CODE_LIST = {
    "200": (0, "成功"),
    "400": (400, "请求异常"),
    "401": (401, "需要验证身份"),
    "403": (403, "禁止访问"),
    "404": (404, "接口不存在"),
    "405": (405, "方法不支持"),
    "413": (413, "提交数据过大"),
    "414": (414, "请求地址过长"),
    "500": (500, "服务器异常"),
    "502": (502, "网关异常"),
    "503": (503, "服务不可用"),
    "504": (504, "网关超时"),

    "ERR": (-1, "未知错误"),

    "OK": (0, "成功"),
    "SUCCESS": (0, "成功"),
    "ERROR": (1, "错误"),
    "FAILED": (1, "失败"),

    "DB_CONN_FAILED": (10, "数据库连接失败"),
    "SQL_ERROR": (11, "SQL错误"),

    "SMS_SEND_FAILED": (20, "短信发送失败"),

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
            return super().default(obj)


def json_return(data):
    return Response(json.dumps(data, cls=JsonEncoder, separators=(",", ":")), mimetype="application/json")
