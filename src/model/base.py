# coding: utf-8
"""
基础数据表
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import constant_time_compare

from .. import db
from ..tool import get_age


class AdminUser(db.Model):
    """管理员用户表"""
    __tablename__ = 't_admin_user'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, comment="ID")
    account = db.Column(db.String(32), unique=True, nullable=False, server_default='', comment="登录账号")
    password = db.Column(db.String(256), nullable=False, server_default='', comment="登录密码")
    nickname = db.Column(db.String(32), nullable=False, server_default='', comment="昵称")
    avatar_url = db.Column(db.String(256), nullable=False, server_default='', comment="头像URL")
    sex = db.Column(db.SmallInteger, nullable=False, server_default='0', comment="性别，0未知，1男性，2女性")
    birthday = db.Column(db.Date, comment="生日")
    app_channel = db.Column(db.String(32), nullable=False, server_default='', comment="APP渠道")
    app_version = db.Column(db.String(32), nullable=False, server_default='', comment="APP版本")
    os_type = db.Column(db.String(32), nullable=False, server_default='', comment="系统类型")
    os_version = db.Column(db.String(32), nullable=False, server_default='', comment="系统版本")
    remark = db.Column(db.String(256), nullable=False, server_default='', comment="备注")
    status = db.Column(db.SmallInteger, nullable=False, server_default='1', comment="状态，0无效，1有效")
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP"), comment="创建时间")
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment="更新时间")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password = generate_password_hash(self.password)

    @property
    def age(self):
        return get_age(self.birthday)

    def check_password(self, password, is_hash=False):
        if is_hash:
            return constant_time_compare(self.password, password)
        return check_password_hash(self.password, password)


class VerifySMS(db.Model):
    """短信验证码表"""
    __tablename__ = 't_verify_sms'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, comment="ID")
    app_name = db.Column(db.String(32), nullable=False, server_default='', comment="应用名称")
    business = db.Column(db.String(32), nullable=False, server_default='', comment="业务名称")
    business_id = db.Column(db.String(32), nullable=False, server_default='', comment="业务流水ID")
    phone = db.Column(db.String(16), nullable=False, server_default='', comment="手机号")
    code = db.Column(db.String(16), nullable=False, server_default='', comment="短信验证码")
    status = db.Column(db.SmallInteger, nullable=False, server_default='0', comment="状态，0未使用，1已使用")
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP"), comment="创建时间")
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment="更新时间")
