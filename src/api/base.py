# coding: utf-8
"""
基础接口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
账号相关基本接口
"""
import re
from datetime import datetime

from flask import g, current_app, request

from .. import db
from ..tool import is_mobile, is_password, is_sms_code, is_date, get_datetime, create_random_num, create_uuid_str, datediff
from ..service import send_sms_by_alisms, upload_file_to_oss, delete_file_from_oss
from ..response import api_return
from ..model.base import AdminUser as UserInfo, VerifySMS

from . import api, need_login, login_user, logout_user


###################################################################
# 注册接口
###################################################################
@api.route("/get_register_code/", methods=["POST"])
def get_register_code():
    """
    #group  基础
    #name   获取注册的验证码
    #desc   获取注册的验证码，验证码通过短信下发
    #param  account     <str>     账号
    #return code    <str>   验证码，只有测服会返回
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {"code": "123456"}
    }
    """
    account = str(g.request_data.get("account", "")).strip()

    if not is_mobile(account):
        current_app.logger.debug("手机号参数错误: account:%s", account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")

    user = UserInfo.query.filter_by(account=account).first()
    if user:
        current_app.logger.debug("账号已存在: account:%s", account)
        return api_return("DATA_EXIST", "账号已存在")

    app_name = current_app.config.get("APP_NAME", "")
    last_time = get_datetime(day=-1)
    sms_business = "register"
    code_limit = int(current_app.config.get("MAX_REGISTER_CODE_ONE_DAY", 5))
    count = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business)\
        .filter(VerifySMS.create_time > last_time).count()
    if count >= code_limit:
        current_app.logger.debug("请求次数超出限制: account:%s, count:%s, code_limit:%s", account, count, code_limit)
        return api_return("REQUEST_NUMBER_LIMIT", "请求次数超出限制")

    code_interval = int(current_app.config.get("SMS_CODE_INTERVAL_TIME", 60))
    last = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business)\
        .order_by(VerifySMS.id.desc()).first()
    if last and (datetime.now() - last.create_time).total_seconds() < code_interval:
        current_app.logger.debug("请求频率超出限制: account:%s", account)
        return api_return("REQUEST_INTERVAL_LIMIT", "请求频率超出限制")

    # 发送短信验证码
    code = create_random_num(6)
    reset_code = VerifySMS(app_name=app_name, phone=account, business=sms_business, code=code)
    if current_app.config.get("ENV") == "development":  # 测服直接把验证码从接口返回，不发短信
        res_data = {"code": code}
    else:
        business_id = create_uuid_str()
        sms_res = send_sms_by_alisms(app_name, account, "SMS_118315037", {"code": code}, business_id)
        if not sms_res:
            current_app.logger.error("短信发送失败: account:%s, code:%s", account, code)
            return api_return("SMS_SEND_FAILED", "短信发送失败，请稍后再试！")
        reset_code.business_id = business_id
        res_data = None

    try:
        db.session.add(reset_code)
        db.session.commit()
        current_app.logger.info("获取成功: account:%s", account)
        return api_return("OK", "获取成功", res_data)
    except Exception as e:
        current_app.logger.error("获取失败: account:%s, %s", account, e)
        return api_return("FAILED", "获取失败")


@api.route("/register/", methods=["POST"])
def register():
    """
    #group  基础
    #name   注册账号
    #desc   注册账号，注册后直接进入登录状态
    #param  account     <str>     账号
    #param  password    <str>    新密码
    #param  code    <str>        验证码
    #return user_id  <int>   用户ID
    #return account <str>   用户账号
    #return nickname    <str>   用户昵称
    #return avatar_url  <str>   用户头像URL
    #return age <int>   用户年龄
    #return sex <int>   用户性别
    #return birthday    <str>   用户生日
    #return token   <str>   登录token
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "user_id": 1,
            "account": "15800881234",
            "nickname": "泰先生",
            "avatar_url": "",
            "sex": 1,
            "birthday": "1990-09-09",
            "age": 27,
            "expiry_date": "2018-09-22",
            "token": "tXsfaN60"
        }
    }
    """
    account = str(g.request_data.get("account", "")).strip()
    password = str(g.request_data.get("password", "")).strip()
    code = str(g.request_data.get("code", "")).strip()

    if not is_mobile(account):
        current_app.logger.debug("手机号参数错误: account:%s", account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")
    if not is_password(password):
        current_app.logger.debug("密码参数错误: account:%s, password:%s", account, password)
        return api_return("PARAM_FORMAT_ERROR", "密码参数错误")
    if not is_sms_code(code):
        current_app.logger.debug("验证码参数错误: account:%s, code:%s", account, code)
        return api_return("PARAM_FORMAT_ERROR", "验证码参数错误")

    user = UserInfo.query.filter_by(account=account).first()
    if user:
        current_app.logger.debug("账号已存在: account:%s", account)
        return api_return("DATA_EXIST", "账号已存在")

    app_name = current_app.config.get("APP_NAME", "")
    sms_business = "register"
    code = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business, code=code, status=0).first()
    if code is None:
        current_app.logger.debug("验证码无效: account:%s, code:%s", account, code)
        return api_return("PARAM_CODE_ERROR", "验证码无效")
    valid_time = current_app.config.get("CODE_VALID_TIME", 10 * 60)
    if (datetime.now() - code.create_time).total_seconds() > valid_time:
        current_app.logger.debug("验证码已过期: account:%s, code:%s", account, code)
        return api_return("PARAM_CODE_INVALID", "验证码已过期")

    user = UserInfo(account=account, password=password)
    db.session.add(user)
    code.status = 1  # 修改验证码状态为已使用
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error("注册失败: account:%s, %s", account, e)
        return api_return("FAILED", "注册失败")

    # 缓存token
    token = login_user(user)

    # 格式化返回值
    login_info = {
        "user_id": user.id, "account": user.account, "nickname": user.nickname, "avatar_url": user.avatar_url,
        "sex": user.sex, "birthday": user.birthday if user.birthday else "",
        "age": user.age, "token": token
    }

    current_app.logger.info("注册成功: account:%s", account)
    return api_return("OK", "注册成功", login_info)


###################################################################
# 登录接口
###################################################################
@api.route("/login/", methods=["POST"])
def login():
    """
    #group  基础
    #name   登录
    #desc   登录系统
    #param  account     <str>     登录账号
    #param  password    <str>    登录密码
    #return user_id  <int>   用户ID
    #return account <str>   用户账号
    #return nickname    <str>   用户昵称
    #return avatar_url  <str>   用户头像URL
    #return sex <int>   用户性别
    #return birthday    <str>   用户生日
    #return age <int>   用户年龄
    #return token   <str>   登录token
    #example
    {
        "code": 0,
        "msg": "登录成功",
        "data": {
            "user_id": 1,
            "account": "15800881234",
            "nickname": "泰先生",
            "avatar_url": "",
            "sex": 1,
            "birthday": "1990-09-09",
            "age": 0,
            "token": "tXsfaN60"
        }
    }
    """
    account = str(g.request_data.get("account", "")).strip()
    password = str(g.request_data.get("password", "")).strip()

    if not is_mobile(account):
        current_app.logger.debug("手机号参数错误: account:%s", account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")
    if not is_password(password):
        current_app.logger.debug("密码参数错误: account:%s, password:%s", account, password)
        return api_return("PARAM_FORMAT_ERROR", "密码参数错误")

    user = UserInfo.query.filter_by(account=account).first()
    if user is None:
        current_app.logger.debug("账号不存在: account:%s", account)
        return api_return("USER_NOT_FOUND", "账号不存在")
    if user.status != 1:
        current_app.logger.debug("账号已禁用: account:%s, status:%s", account, user.status)
        return api_return("USER_INVALID", "账号已禁用")
    if not user.check_password(password):
        current_app.logger.debug("密码错误: account:%s", account)
        return api_return("USER_PWD_ERROR", "密码错误")

    # 更新用户信息
    user.app_channel = g.get("app_channel", "")
    user.app_version = g.get("app_version", "")
    user.os_type = g.get("os_type", "")
    user.os_version = g.get("os_version", "")

    # 缓存token
    token = login_user(user)

    # 格式化返回值
    login_info = {
        "user_id": user.id, "account": user.account, "nickname": user.nickname, "avatar_url": user.avatar_url,
        "sex": user.sex, "birthday": user.birthday if user.birthday else "",
        "age": user.age, "token": token
    }

    try:
        db.session.commit()
        current_app.logger.info("登录成功: account:%s, app_channel:%s, app_version:%s, os_type:%s, os_version:%s", account, user.app_channel, user.app_version, user.os_type, user.os_version)
    except Exception as e:
        current_app.logger.error("登录成功但更新版本信息失败, account:%s, %s", account, e)
    return api_return("OK", "登录成功", login_info)


@api.route("/logout/", methods=["POST"])
@need_login
def logout():
    """
    #group  基础
    #name   注销
    #desc   注销登录
    #priv   need_login
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": ""
    }
    """
    logout_user()
    current_app.logger.info("注销成功: account:%s", g.user.account)
    return api_return("OK", "注销成功")


###################################################################
# 用户信息管理接口
###################################################################
@api.route("/get_user_info/", methods=["POST"])
@need_login
def get_user_info():
    """
    #group  基础
    #name   查询用户
    #desc   查询用户基本信息
    #priv   need_login
    #return user_id  <int>   用户ID
    #return account <str>   用户账号
    #return nickname    <str>   用户昵称
    #return avatar_url  <str>   用户头像URL
    #return age <int>   用户年龄
    #return sex <int>   用户性别
    #return birthday    <str>   用户生日
    #return remark   <str>   备注
    #example
    {
        "code": 0,
        "msg": "查询成功",
        "data": {
            "user_id": 3,
            "account": "15800881234",
            "nickname": "小明",
            "avatar_url": "",
            "age": 27,
            "sex": 1,
            "birthday": "1989-08-08",
            "remark": ""
        }
    }
    """

    data = {"user_id": g.user.id, "account": g.user.account, "nickname": g.user.nickname, "avatar_url": g.user.avatar_url,
            "sex": g.user.sex, "birthday": g.user.birthday if g.user.birthday else "", "age": g.user.age,
            "remark": g.user.remark}

    app_version = g.get("app_version")
    if app_version != g.user.app_version:
        g.user.app_version = app_version

    os_version = g.get("os_version")
    if os_version != g.user.os_version:
        g.user.os_version = os_version

    try:
        db.session.commit()
        current_app.logger.info("查询成功: account:%s, app_channel:%s, app_version:%s, os_type:%s, os_version:%s",
                                g.user.account, g.user.app_channel, g.user.app_version, g.user.os_type, g.user.os_version)
    except Exception as e:
        current_app.logger.error("查询成功但更新版本信息失败: account:%s, %s", g.user.account, e)
    return api_return("OK", "查询成功", data)


@api.route("/update_user/", methods=["POST"])
@need_login
def update_user():
    """
    #group  基础
    #name   更新用户
    #desc   更新用户基本信息
    #priv   need_login
    #param  nickname    <str>   <可选>  昵称
    #param  sex     <int>    <可选>  学员性别，1男，2女
    #param  birthday    <str>   <可选>  生日，1999-09-09
    #param  remark    <str>   <可选>  备注
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": ""
    }
    """
    nickname = g.request_data.get("nickname")
    sex = g.request_data.get("sex")
    birthday = g.request_data.get("birthday")
    remark = g.request_data.get("remark")

    if nickname is not None:
        nickname = str(nickname).strip()
        if len(nickname) < 1 or len(nickname) > 30:
            current_app.logger.debug("昵称长度不符合: account:%s, nickname:%s", g.user.account, nickname)
            return api_return("PARAM_ERROR", "昵称长度不符，需要1-30个字符")
        g.user.nickname = nickname

    if sex is not None:
        if sex not in [1, 2]:
            current_app.logger.debug("性别参数错误: account:%s, sex:%s", g.user.account, sex)
            return api_return("PARAM_ERROR", "性别参数错误")
        g.user.sex = sex

    if birthday is not None:
        birthday = str(birthday).strip()
        if not is_date(birthday) or datediff(datetime.now().strftime("%F"), birthday) < 1:
            current_app.logger.debug("生日参数错误: account:%s, birthday:%s", g.user.account, birthday)
            return api_return("PARAM_ERROR", "生日参数错误")
        g.user.birthday = birthday

    if remark is not None:
        remark = str(remark).strip()
        if len(nickname) > 250:
            current_app.logger.debug("备注长度不符合: account:%s, remark:%s", g.user.account, remark)
            return api_return("PARAM_ERROR", "备注长度不符，需要少于250个字符")
        g.user.remark = remark

    try:
        db.session.commit()
        current_app.logger.info("修改成功: account:%s", g.user.account)
        return api_return("OK", "修改成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("修改失败, account:%s, %s", g.user.account, e)
        return api_return("FAILED", "修改失败")


@api.route("/update_password/", methods=["POST"])
@need_login
def update_password():
    """
    #group  基础
    #name   修改用户密码
    #desc   修改用户密码
    #priv   need_login
    #param  old_password    <str>    旧密码
    #param  new_password    <str>        新密码
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": ""
    }
    """
    old_password = str(g.request_data.get("old_password", "")).strip()
    new_password = str(g.request_data.get("new_password", "")).strip()

    if old_password == new_password:
        current_app.logger.debug("新密码不能与旧密码相同: account:%s", g.user.account)
        return api_return("PARAM_ERROR", "新密码不能与旧密码相同")

    if not is_password(old_password) or not is_password(new_password):
        current_app.logger.debug("密码参数错误: account:%s", g.user.account)
        return api_return("PARAM_ERROR", "密码参数错误")

    if not g.user.check_password(old_password):
        current_app.logger.debug("旧密码错误: account:%s", g.user.account)
        return api_return("USER_PWD_ERROR", "旧密码错误")

    g.user.password = new_password
    try:
        db.session.commit()
        logout_user()
        current_app.logger.info("修改成功: account:%s", g.user.account)
        return api_return("OK", "修改成功，请重新登录！")
    except Exception as e:
        current_app.logger.error("修改失败: account:%s, %s", g.user.account, e)
        return api_return("FAILED", "修改失败")


@api.route("/upload_avatar/", methods=["POST"])
@need_login
def upload_avatar():
    """
    #group  基础
    #name   上传头像
    #desc   上传头像
    #priv   need_login
    #param  avatar_file  <file>      头像文件
    #return avatar_url  <str>   用户头像URL
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "avatar_url": "http://avatar.xxx.cn/2_123.jpg"
        }
    }
    """
    avatar_file = request.files.get("avatar_file")

    if not avatar_file:
        current_app.logger.debug("用户头像错误: avatar file account:%s", g.user.account)
        return api_return("PARAM_ERROR", "用户头像错误")

    bucket_name = current_app.config.get("OSS_AVATAR_BUCKET_NAME", "dev_avatar")
    upload_url = upload_file_to_oss(bucket_name, avatar_file)
    if not upload_url:
        current_app.logger.error("文件上传失败: account:%s", g.user.account)
        return api_return("FAILED", "文件上传失败")

    # 删除旧的头像
    if g.user.avatar_url:
        old_avatar_key = g.user.avatar_url.split("/")[-1]
        result = delete_file_from_oss(bucket_name, old_avatar_key)
        if not result:
            current_app.logger.error("旧头像删除失败: account:%s, old_avatar:%s", g.user.account, old_avatar_key)

    # 将地址替换为自有域名，然后更新头像地址
    own_avatar_domain = current_app.config.get("OWN_AVATAR_DOMAIN")
    upload_url = re.sub("://.*/", "://{0}/".format(own_avatar_domain), upload_url) if own_avatar_domain else upload_url
    g.user.avatar_url = upload_url
    try:
        db.session.commit()
        current_app.logger.info("上传成功: account:%s, avatar_url:%s", g.user.account, g.user.avatar_url)
        return api_return("OK", "上传成功", {"avatar_url": g.user.avatar_url})
    except Exception as e:
        current_app.logger.error("上传失败, account:%s, %s", g.user.account, e)
        return api_return("FAILED", "上传失败")


###################################################################
# 重置密码接口
###################################################################
@api.route("/get_reset_password_code/", methods=["POST"])
def get_reset_password_code():
    """
    #group  基础
    #name   获取重置密码的验证码
    #desc   获取重置密码的验证码，验证码通过短信下发
    #priv   need_login
    #param  account     <str>     账号
    #return code    <str>   验证码，只有测服会返回
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {"code": "123456"}
    }
    """
    account = str(g.request_data.get("account", "")).strip()

    if not is_mobile(account):
        current_app.logger.debug("手机号参数错误: account:%s", account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")

    user = UserInfo.query.filter_by(account=account).first()
    if user is None:
        current_app.logger.debug("账号不存在: account:%s", account)
        return api_return("USER_NOT_FOUND", "账号不存在")
    if user.status != 1:
        current_app.logger.debug("账号已禁用: account:%s, status:%s", account, user.status)
        return api_return("USER_INVALID", "账号已禁用")

    app_name = current_app.config.get("APP_NAME", "")
    last_time = get_datetime(day=-1)
    sms_business = "reset_password"
    code_limit = int(current_app.config.get("MAX_RESET_CODE_ONE_DAY", 5))
    count = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business)\
        .filter(VerifySMS.create_time > last_time).count()
    if count >= code_limit:
        current_app.logger.debug("请求次数超出限制: account:%s, count:%s, code_limit:%s", account, count, code_limit)
        return api_return("REQUEST_NUMBER_LIMIT", "请求次数超出限制")

    code_interval = int(current_app.config.get("SMS_CODE_INTERVAL_TIME", 60))
    last = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business)\
        .order_by(VerifySMS.id.desc()).first()
    if last and (datetime.now() - last.create_time).total_seconds() < code_interval:
        current_app.logger.debug("请求频率超出限制: account:%s", account)
        return api_return("REQUEST_INTERVAL_LIMIT", "请求频率超出限制")

    # 发送短信验证码
    code = create_random_num(6)
    reset_code = VerifySMS(app_name=app_name, phone=account, business=sms_business, code=code)
    if current_app.config.get("ENV") == "development":  # 测服直接把验证码从接口返回
        res_data = {"code": code}
    else:
        business_id = create_uuid_str()
        sms_res = send_sms_by_alisms(app_name, account, "SMS_118315037", {"code": code}, business_id)
        if not sms_res:
            current_app.logger.error("短信发送失败: account:%s, code:%s", account, code)
            return api_return("SMS_SEND_FAILED", "短信发送失败，请稍后再试！")
        reset_code.business_id = business_id
        res_data = None

    try:
        db.session.add(reset_code)
        db.session.commit()
        current_app.logger.info("获取成功: account:%s", account)
        return api_return("OK", "获取成功", res_data)
    except Exception as e:
        current_app.logger.error("获取失败: account:%s, %s", account, e)
        return api_return("FAILED", "获取失败")


@api.route("/reset_password/", methods=["POST"])
def reset_password():
    """
    #group  基础
    #name   重置用户密码
    #desc   重置用户密码，重置后直接进入登录状态
    #priv   need_login
    #param  account     <str>     账号
    #param  password    <str>    新密码
    #param  code    <str>        验证码
    #return user_id  <int>   用户ID
    #return account <str>   用户账号
    #return nickname    <str>   用户昵称
    #return avatar_url  <str>   用户头像URL
    #return age <int>   用户年龄
    #return sex <int>   用户性别
    #return birthday    <str>   用户生日
    #return token   <str>   登录token
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "user_id": 1,
            "account": "15800881234",
            "nickname": "泰先生",
            "avatar_url": "",
            "age": 0,
            "sex": 1,
            "birthday": "1990-09-09",
            "token": "tXsfaN60"
        }
    }
    """
    account = str(g.request_data.get("account", "")).strip()
    password = str(g.request_data.get("password", "")).strip()
    code = str(g.request_data.get("code", "")).strip()

    if not is_mobile(account):
        current_app.logger.debug("手机号参数错误: account:%s", account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")
    if not is_password(password):
        current_app.logger.debug("密码参数错误: account:%s, password:%s", account, password)
        return api_return("PARAM_FORMAT_ERROR", "密码参数错误")
    if not is_sms_code(code):
        current_app.logger.debug("验证码参数错误: account:%s, code:%s", account, code)
        return api_return("PARAM_FORMAT_ERROR", "验证码参数错误")

    user = UserInfo.query.filter_by(account=account).first()
    if user is None:
        current_app.logger.debug("账号不存在: account:%s", account)
        return api_return("USER_NOT_FOUND", "账号不存在")
    if user.status != 1:
        current_app.logger.debug("账号已禁用: account:%s, status:%s", account, user.status)
        return api_return("USER_INVALID", "账号已禁用")

    app_name = current_app.config.get("APP_NAME", "")
    sms_business = "reset_password"
    code = VerifySMS.query.filter_by(app_name=app_name, phone=account, business=sms_business, code=code, status=0).first()
    if code is None:
        current_app.logger.debug("验证码无效: account:%s, code:%s", account, code)
        return api_return("PARAM_CODE_ERROR", "验证码无效")
    valid_time = current_app.config.get("CODE_VALID_TIME", 10 * 60)
    if (datetime.now() - code.create_time).total_seconds() > valid_time:
        current_app.logger.debug("验证码已过期: account:%s, code:%s", account, code)
        return api_return("PARAM_CODE_INVALID", "验证码已过期")

    code.status = 1  # 修改验证码状态为已使用
    user.password = password
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error("重置失败: account:%s, %s", account, e)
        return api_return("FAILED", "重置失败")

    # 缓存token
    token = login_user(user)

    # 格式化返回值
    login_info = {
        "user_id": user.id, "account": user.account, "nickname": user.nickname, "avatar_url": user.avatar_url,
        "sex": user.sex, "birthday": user.birthday if user.birthday else "",
        "age": user.age, "token": token
    }

    current_app.logger.info("重置成功: account:%s", account)
    return api_return("OK", "重置成功", login_info)


###################################################################
# 更换账号接口
###################################################################
@api.route("/get_change_account_code/", methods=["POST"])
@need_login
def get_change_account_code():
    """
    #group  基础
    #name   获取修改账号的验证码
    #desc   获取修改账号的验证码，验证码通过短信下发
    #priv   need_login
    #param  new_account     <str>     新账号
    #param  password    <str>   当前账号的密码
    #return code    <str>   验证码，只有测服会返回
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": {"code": "123456"}
    }
    """
    new_account = str(g.request_data.get("new_account", "")).strip()
    password = str(g.request_data.get("password", "")).strip()

    if not is_mobile(new_account):
        current_app.logger.debug("手机号参数错误: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")

    if not g.user.check_password(password):
        current_app.logger.debug("密码错误: account:%s", g.user.account)
        return api_return("USER_PWD_ERROR", "密码错误")

    # 验证新账号是否已注册
    new_user = UserInfo.query.filter_by(account=new_account).first()
    if new_user:
        current_app.logger.debug("账号已被使用: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("PARAM_ERROR", "账号已被使用")

    app_name = current_app.config.get("APP_NAME", "")
    last_time = get_datetime(day=-1)
    sms_business = "change_account"
    code_limit = int(current_app.config.get("MAX_CHANGE_ACCOUNT_CODE_ONE_DAY", 1))
    count = VerifySMS.query.filter_by(app_name=app_name, phone=new_account, business=sms_business)\
        .filter(VerifySMS.create_time > last_time).count()
    if count >= code_limit:
        current_app.logger.debug("请求次数超出限制: account:%s, new_account:%s, count:%s, code_limit:%s", g.user.account, new_account, count, code_limit)
        return api_return("REQUEST_NUMBER_LIMIT", "请求次数超出限制")

    code_interval = int(current_app.config.get("SMS_CODE_INTERVAL_TIME", 60))
    last = VerifySMS.query.filter_by(app_name=app_name, phone=new_account, business=sms_business)\
        .order_by(VerifySMS.id.desc()).first()
    if last and (datetime.now() - last.create_time).total_seconds() < code_interval:
        current_app.logger.debug("请求频率超出限制: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("REQUEST_INTERVAL_LIMIT", "请求频率超出限制")

    # 发送短信验证码
    code = create_random_num(6)
    reset_code = VerifySMS(app_name=app_name, phone=new_account, business=sms_business, code=code)
    if current_app.config.get("ENV") == "development":  # 测服直接把验证码从接口返回
        res_data = {"code": code}
    else:
        business_id = create_uuid_str()
        sms_res = send_sms_by_alisms(app_name, new_account, "SMS_118315037", {"code": code}, business_id)
        if not sms_res:
            current_app.logger.error("短信发送失败: account:%s, new_account:%s, code:%s", g.user.account, new_account, code)
            return api_return("SMS_SEND_FAILED", "短信发送失败，请稍后再试！")
        reset_code.business_id = business_id
        res_data = None

    try:
        db.session.add(reset_code)
        db.session.commit()
        current_app.logger.info("获取成功: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("OK", "获取成功", res_data)
    except Exception as e:
        current_app.logger.error("获取失败: account:%s, new_account:%s, %s", g.user.account, new_account, e)
        return api_return("FAILED", "获取失败")


@api.route("/change_account/", methods=["POST"])
@need_login
def change_account():
    """
    #group  基础
    #name   修改用户账号
    #desc   修改用户登录账号
    #priv   need_login
    #param  new_account     <str>     新账号
    #param  code    <str>        验证码
    #example
    {
        "code": 0,
        "msg": "成功",
        "data": ""
    }
    """
    new_account = str(g.request_data.get("new_account", "")).strip()
    code = str(g.request_data.get("code", "")).strip()

    if not is_mobile(new_account):
        current_app.logger.debug("手机号参数错误: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("PARAM_MOBILE_ERROR", "手机号参数错误")
    if not is_sms_code(code):
        current_app.logger.debug("验证码参数错误: account:%s, new_account:%s, code:%s", g.user.account, new_account, code)
        return api_return("PARAM_FORMAT_ERROR", "验证码参数错误")

    # 验证新账号是否已注册
    new_user = UserInfo.query.filter_by(account=new_account).first()
    if new_user:
        current_app.logger.debug("账号已被使用: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("PARAM_ERROR", "账号已被使用")

    app_name = current_app.config.get("APP_NAME", "")
    sms_business = "change_account"
    code = VerifySMS.query.filter_by(app_name=app_name, phone=new_account, business=sms_business, code=code, status=0).first()
    if code is None:
        current_app.logger.debug("验证码无效: account:%s, new_account:%s, code:%s", g.user.account, new_account, code)
        return api_return("PARAM_CODE_ERROR", "验证码无效")
    valid_time = current_app.config.get("CODE_VALID_TIME", 10 * 60)
    if (datetime.now() - code.create_time).total_seconds() > valid_time:
        current_app.logger.debug("验证码已过期: account:%s, new_account:%s, code:%s", g.user.account, new_account, code)
        return api_return("PARAM_CODE_INVALID", "验证码已过期")

    code.status = 1  # 修改验证码状态为已使用
    g.user.account = new_account    # 修改账号
    try:
        db.session.commit()
        current_app.logger.info("修改成功: account:%s, new_account:%s", g.user.account, new_account)
        return api_return("OK", "修改成功")
    except Exception as e:
        current_app.logger.error("修改失败: account:%s, new_account:%s, %s", g.user.account, new_account, e)
        return api_return("FAILED", "修改失败")
