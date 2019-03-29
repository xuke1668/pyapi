# coding: utf-8
"""
系统工具方法集
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import sys
import re
import decimal
import string
import hmac
import base64
import hashlib
import uuid
import time
import traceback
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from hashlib import sha512
from random import choice


from flask import request


def is_blank(var):
    return not (var and var.strip())


def is_email(var):
    if var is None:
        return False
    regexp = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
    return re.search(regexp, str(var))


def is_url(var):
    if var is None:
        return False
    regexp = r"^((ht|f)tps?):\/\/[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&:\/~\+#]*[\w\-\@?^=%&\/~\+#])?$"
    return re.search(regexp, str(var))


def is_phone(var):
    if var is None:
        return False
    regexp = r"^(0[0-9]{2,3}\-?)?([2-9][0-9]{6,7})+(\-[0-9]{1,4})?$"
    return re.search(regexp, str(var))


def is_mobile(var):
    if var is None:
        return False
    return is_mobile_cn(var) or is_mobile_hk(var) or is_mobile_mo(var) or is_mobile_tw(var)


def is_mobile_cn(var):
    if var is None:
        return False
    regexp = r"^1\d{10}$"
    return re.search(regexp, str(var))


def is_mobile_hk(var):
    if var is None:
        return False
    regexp = r"^(6|9)\d{7}$"
    return re.search(regexp, str(var))


def is_mobile_mo(var):
    if var is None:
        return False
    regexp = r"^6\d{6}$"
    return re.search(regexp, str(var))


def is_mobile_tw(var):
    if var is None:
        return False
    regexp = r"^9\d{8}$"
    return re.search(regexp, str(var))


def is_date(var):
    if var is None:
        return False
    regexp = r"^(1\d{3}|2\d{3})[-/.]{1}(0?\d|1[0-2]{1})[-/.]{1}(0?\d|[12]{1}\d|3[01]{1})$"
    if re.search(regexp, str(var)):
        try:
            return datetime.strptime(re.sub(r'[/.]', '-', str(var)), '%Y-%m-%d')
        except ValueError:    # 防止出现2018.06.31这种错误
            return False
    else:
        return False


def is_time(var):
    if var is None:
        return False
    regexp = r"^(0?\d|1\d|2[0-3]{1})[:-]{1}(0?\d|[1-5]{1}\d)[:-]{1}(0?\d|[1-5]{1}\d)$"
    return re.search(regexp, str(var))


def is_datetime(var):
    if var is None:
        return False
    try:
        d, t = var.split(" ")
    except ValueError:
        return False
    return is_date(d) and is_time(t)


def is_password(var):
    if var is None:
        return False
    regexp = r"^[\w.-~@#$%^&*]{6,16}$"
    return re.search(regexp, str(var))


def is_sms_code(var):
    if var is None:
        return False
    regexp = r"^[a-zA-Z0-9]{6}$"
    return re.search(regexp, str(var))


def get_error_info():
    """输出最近一个错误栈的file, line, func, code"""
    error_info = traceback.format_exception(*sys.exc_info(), -1)[1]
    error_reg = re.compile(r'File\s*"([^"].*)",\s*line\s*([^,].*),\s*in\s*([^\n].*)\s*\n\s*([^\n].*)\s*\n', re.S | re.M)
    error_field = error_reg.findall(error_info)
    return error_field[0] if error_field else ("", "", "", "")


def get_datetime(now=None, year=0, month=0, week=0, day=0, hour=0, minute=0, second=0):
    if now is None:
        now = datetime.now()
    res = now + relativedelta(years=int(year), months=int(month), weeks=int(week), days=int(day), hours=int(hour), minutes=int(minute), seconds=int(second))
    return res


def get_timestamp(now=None, year=0, month=0, week=0, day=0, hour=0, minute=0, second=0):
    dt = get_datetime(now, year, month, week, day, hour, minute, second)
    return int(time.mktime(dt.timetuple()))


def get_param_sign(**kwargs):
    """根据传入的参数，排序后生成md5值"""
    s = '&'.join(['{0}={1}'.format(k, v) for k, v in sorted(kwargs.items(), key=lambda x: x[0])])
    return md5(s)


def get_remote_addr():
    """获取客户端IP地址"""
    address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if address is not None:
        address = address.encode('utf-8').split(b',')[0].strip()
    return address.decode()


def get_client_ident(var=None):
    """获取客户端标识"""
    user_agent = request.headers.get('User-Agent')
    if user_agent is not None:
        user_agent = user_agent.encode('utf-8')
    if var is None or var == "":
        base = str(user_agent)
    else:
        base = '{0}|{1}'.format(var, user_agent)
    h = sha512()
    h.update(base.encode('utf8'))
    return h.hexdigest()


def get_age(born, today=None):
    """计算年龄"""
    if isinstance(born, datetime):
        born = born.date()
    elif isinstance(born, date):
        pass
    else:
        return 0

    if isinstance(today, datetime):
        today = today.date()
    elif isinstance(today, date):
        pass
    else:
        today = date.today()

    try:
        birthday = born.replace(year=today.year)
    except ValueError:      # 防止非闰年的2月29
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def get_max_hr(sex, age):
    """计算最大心率"""
    if not sex or re.search(r"^\d$", str(sex)) is None:
        sex = 1
    if not age or re.search(r"^\d+$", str(age)) is None:
        age = 25
    if int(sex) == 1:
        max_hr = 220
    else:
        max_hr = 224
    return max_hr - int(age)


def create_uuid_str():
    """生成UUID字符串"""
    return str(uuid.uuid1()).replace('-', '')


def create_random_str(length=6, chars=string.ascii_letters + string.digits):
    """生成随机字符"""
    return ''.join([choice(chars) for _ in range(length)])


def create_random_num(length=6):
    """生成随机数字"""
    return create_random_str(length, chars=string.digits)


def hmacb64(obj_str, secret, alg='sha1'):
    """对字符串进行hmac"""
    if alg == 'sha1':
        alg = hashlib.sha1
    h = hmac.new(secret.encode(), obj_str.encode(), alg)
    return base64.b64encode(h.digest()).decode()


def md5(obj_str):
    """对字符串进行md5"""
    m = hashlib.md5()
    m.update(obj_str.encode())
    return m.hexdigest()


def datediff(var1, var2):
    """比较两个日期差, 日期格式必须是%Y-%m-%d格式的date字符串"""
    # noinspection PyBroadException
    try:
        date1 = datetime.strptime(var1, "%Y-%m-%d")
        date2 = datetime.strptime(var2, "%Y-%m-%d")
    except Exception:
        return 0
    return (date1-date2).days


def datetimediff(var1, var2):
    """比较两个时间差, 日期格式必须是%Y-%m-%d %H:%M:%S格式的datetime字符串"""
    # noinspection PyBroadException
    try:
        datetime1 = datetime.strptime(var1, "%Y-%m-%d %H:%M:%S")
        datetime2 = datetime.strptime(var2, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return 0
    return int((datetime1-datetime2).total_seconds())


def db_to_dict(inst, cls):
    """数据库对象转换为字典"""
    d = dict()
    for c in cls.__table__.columns:
        name = c.name
        v = getattr(inst, name)
        if v is None:
            d[name] = str()
        else:
            if isinstance(v, datetime):
                d[name] = v.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(v, date):
                d[name] = v.strftime('%Y-%m-%d')
            elif isinstance(v, decimal.Decimal):
                d[name] = float(v)
            else:
                d[name] = v
    return d
