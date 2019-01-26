# coding: utf-8
"""
业务辅助方法集
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os
import requests
import oss2
from urllib.parse import unquote

from flask import current_app
from werkzeug.utils import secure_filename

from .tool import create_uuid_str


def send_push_by_jpush(app_name, platform, reg_id, content, out_id, **kwargs):
    """
    通过极光发送推送
    :param app_name:    应用名称
    :param platform:    系统平台
    :param reg_id:      极光ID
    :param content:     推送内容
    :param out_id:      应用流水ID
    :return: bool:      返回成功或失败
    """
    jpush_url = current_app.config.get("JPUSH_SERVER_URL")
    if not jpush_url:
        current_app.logger.error("未配置Jpush网关地址")
        return False

    apns_production = current_app.config.get("JPUSH_APNS_PRODUCTION", True)
    data = {"channel": "api", "app_name": app_name, "platform": platform, "reg_id": reg_id,
            "content": content, "out_id": out_id, "apns_production": apns_production, **kwargs}
    try:
        result = requests.post(jpush_url, json=data, timeout=2)
        res = result.json()
    except Exception as e:
        current_app.logger.error("发送失败: reg_id:%s, %s", reg_id, e)
        return False

    if res["code"] == 0:
        current_app.logger.info("发送成功: reg_id:%s", reg_id)
        return True
    else:
        current_app.logger.error("发送失败: reg_id:%s, return:%s", reg_id, res['msg'])
        return False


def send_sms_by_alisms(app_name, phone_number, template_code, template_params, out_id):
    """
    通过阿里云sms发送短信
    :param app_name:        应用名称
    :param phone_number:     接收短信的手机号
    :param template_code:    短信模板ID
    :param template_params:  短信模板参数
    :param out_id:           业务流水号
    :return: bool:          返回成功或失败
    """
    sms_server_url = current_app.config.get("ALISMS_SERVER_URL")
    if not sms_server_url:
        current_app.logger.error("未配置短信网关地址")
        return False

    sign_name = current_app.config.get("SMS_SIGN_NAME")
    if not sign_name:
        current_app.logger.error("未配置短信签名")
        return False

    data = {"channel": "api", "app_name": app_name, "sign_name": sign_name, "phone_number": phone_number,
            "template_code": template_code, "template_params": template_params, "out_id": out_id}
    try:
        result = requests.post(sms_server_url, json=data, timeout=2)
        res = result.json()
    except Exception as e:
        current_app.logger.error("发送失败: phone_number:%s, %s", phone_number, e)
        return False

    if res["code"] == 0:
        current_app.logger.info("发送成功: phone_number:%s", phone_number)
        return True
    else:
        current_app.logger.error("发送失败: phone_number:%s, return:%s", phone_number, res['msg'])
        return False


def upload_file_to_oss(bucket_name, file, file_name=None):
    """
    上传文件到阿里云OSS
    :param bucket_name:     bucket_name
    :param file:            文件数据
    :param file_name:       文件名
    :return: res_url:       返回文件在OSS的访问URL
    """
    endpoint = current_app.config.get("OSS_ACCESS_ENDPOINT")
    oss_access_key_id = current_app.config.get("OSS_ACCESS_KEY_ID")
    oss_access_key_secret = current_app.config.get("OSS_ACCESS_KEY_SECRET")
    if endpoint is None or oss_access_key_id is None or oss_access_key_secret is None:
        current_app.logger.error("OSS配置不正确")
        return False

    if file_name is None:
        if hasattr(file, "filename"):
            file_ext = os.path.splitext(secure_filename(file.filename))
            file_name = "%s%s" % (create_uuid_str(), file_ext[1] if file_ext[1] != "" else "." + file_ext[0])
        else:
            file_name = create_uuid_str()

    bucket = oss2.Bucket(oss2.Auth(oss_access_key_id, oss_access_key_secret), endpoint, bucket_name)
    try:
        result = bucket.put_object(file_name, file)
    except Exception as e:
        current_app.logger.error("OSS上传文件失败: %s", e)
        return False
    if result.status != 200:
        current_app.logger.error("OSS上传文件失败, result.status: %s", result.status)
        return False
    if result.resp.status != 200:
        current_app.logger.error("OSS上传文件失败, result.resp.status: %s", result.resp.status)
        return False
    if result.resp.response.status_code != 200:
        current_app.logger.error("OSS上传文件失败, result.resp.response.status_code: %s", result.resp.response.status_code)
        return False
    return unquote(result.resp.response.url)


def delete_file_from_oss(bucket_name, key):
    """
    从阿里云OSS删除文件
    :param bucket_name:     bucket_name
    :param key:             文件的key
    :return: bool:          返回成功或失败
    """
    endpoint = current_app.config.get("OSS_ACCESS_ENDPOINT")
    oss_access_key_id = current_app.config.get("OSS_ACCESS_KEY_ID")
    oss_access_key_secret = current_app.config.get("OSS_ACCESS_KEY_SECRET")
    if endpoint is None or oss_access_key_id is None or oss_access_key_secret is None:
        current_app.logger.error("OSS配置不正确")
        return False

    bucket = oss2.Bucket(oss2.Auth(oss_access_key_id, oss_access_key_secret), endpoint, bucket_name)
    try:
        result = bucket.delete_object(key)
    except Exception as e:
        current_app.logger.error("OSS删除文件失败: %s", e)
        return False
    if result.status != 204:
        current_app.logger.error("OSS删除文件失败, result.status: %s", result.status)
        return False
    return True
