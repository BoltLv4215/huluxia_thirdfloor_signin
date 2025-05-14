import hashlib
import json
import os
import random
import time
import requests
from logger import logger
from notifier import get_notifier

# 随机配置
phone_brand_type_list = list(["MI", "Huawei", "UN", "OPPO", "VO"])  # 随机设备厂商
device_code_random = random.randint(111, 987)  # 随机设备识别码

# 静态配置
platform = '2'
gkey = '000000'
app_version = '4.3.1.5.2'
versioncode = '398'
market_id = 'floor_web'
device_code = '%5Bd%5D5125c3c6-f' + str(device_code_random) + '-4c6b-81cf-9bc467522d61'
phone_brand_type = random.choice(phone_brand_type_list)
_key = ''
cat_id = ''  # 版块id
userid = ''  # 用户id
signin_continue_days = ''  # 连续签到天数
headers = {
    "Connection": "close",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "User-Agent": "okhttp/3.8.1",
    "Host": 'floor.huluxia.com'
}
session = requests.Session()
# 版块id
with open('cat_id.json', 'r', encoding='UTF-8') as f:
    content = f.read()
    cat_id_dict = json.loads(content)

class HuluxiaSignin:
    """
    葫芦侠三楼签到类
    """
    def __init__(self):
        """
        初始化类
        """
        self._key = ''
        self.cat_id = ''
        self.userid = ''
        self.signin_continue_days = ''


        # 初始化通知器类型
        notifier_type = os.getenv("NOTIFIER_TYPE", "none")  # 可选：wechat(企业微信机器人）、email(邮箱推送)、none(不发送通知)
        config = {
            "webhook_url": os.getenv("WECHAT_ROBOT_URL"),  # 企业微信机器人 Webhook 地址
            "smtp_server": "smtp.qq.com",  # SMTP 服务器地址 默认QQ邮箱
            "port": 465  # SMTP 端口号
        }
        if notifier_type == "email":
            # 从环境变量获取邮箱配置
            email_config_str = os.getenv("EMAIL_CONFIG")
            if email_config_str:
                try:
                    email_config = json.loads(email_config_str)
                    config.update({
                        "username": email_config.get("username"),
                        "auth_code_or_password": email_config.get("auth_code_or_password"),
                        "sender_email": email_config.get("sender_email"),
                        "recipient_email": email_config.get("recipient_email")
                    })
                except json.JSONDecodeError:
                    print("邮箱配置格式错误，请检查 EMAIL_CONFIG 的值。")
                    raise
            else:
                print("没有配置 EMAIL_CONFIG 环境变量，请设置邮箱相关配置。")
                raise ValueError("缺少邮箱配置")
        self.notifier = get_notifier(notifier_type, config)

    # 手机号密码登录
    def psd_login(self, account, password):
        device_model = f"iPhone{random.randint(14, 17)}%2C{random.randint(1, 6)}"
        login_url = 'https://floor.huluxia.com/account/login/IOS/1.0?' \
                    'access_token=&app_version=1.2.2&code=' \
                    '&device_code=' + device_code + \
                    '&device_model=' + device_model + \
                    '&email=' + account + \
                    '&market_id=floor_huluxia&openid=&' \
                    'password=' + self.md5(password) + \
                    '&phone=' \
                    '&platform=1'
        login_res = session.get(url=login_url, headers=headers)
        # print("账号登录信息：", login_res.content)
        return login_res.json()

    # 登录后设置相关信息
    def set_config(self, acc, psd):
        """

        :param acc: 手机号
        :param psd: 密码
        :return: 返回登录后生成的key值
        """
        data = self.psd_login(acc, psd)
        status = data['status']
        if status == 0:
            self.notifier.send("手机号或密码错误!")
        else:
            self._key = data['_key']
            self.userid = data['user']['userID']
            return self._key

    # 获取用户信息
    def user_info(self):
        """

        :return: 返回用户的昵称、等级、当前经验值以及下一等级的经验值
        """
        get_info_url = 'http://floor.huluxia.com/user/info/ANDROID/4.1.8?' \
                       'platform=' + platform + \
                       '&gkey=' + gkey + \
                       '&app_version=' + app_version + \
                       '&versioncode=' + versioncode + \
                       '&market_id=' + market_id + \
                       '&_key=' + self._key + \
                       '&device_code=' + device_code + \
                       '&phone_brand_type=' + phone_brand_type + \
                       '&user_id=' + str(self.userid)
        get_info_res = requests.get(url=get_info_url, headers=headers).json()
        nick = get_info_res['nick']
        level = get_info_res['level']
        exp = get_info_res['exp']
        next_exp = get_info_res['nextExp']
        return nick, level, exp, next_exp

    # md5加密
    def md5(self, text: str) -> str:
        """

        :param text: 需要进行md5加密的文本内容
        :return: 加密后的内容
        """
        _md5 = hashlib.md5()
        _md5.update(text.encode())
        return _md5.hexdigest()

    # 时间戳
    def timestamp(self) -> int:
        # 原 int(round(time.time() * 1000)) 易出现参数错误
        return int(time.time())

    # sign 葫芦侠三楼签到用到的特殊签名
    def sign_get(self) -> str:
        """
        生成签到签名

        :return: 签到签名
        """
        n = self.cat_id
        i = str(self.timestamp())
        r = 'fa1c28a5b62e79c3e63d9030b6142e4b'
        result = "cat_id" + n + "time" + i + r
        c = self.md5(result)  # sign的构成：板块id + 时间戳 + 固定字符
        return c

    # 签到
    def huluxia_signin(self, acc, psd):
        """
        葫芦侠三楼签到

        :param acc: 手机号
        :param psd: 密码
        :return: 签到结果
        """
        # 初始化通知信息
        self.set_config(acc, psd)
        info = self.user_info()
        initial_msg = f'正在为{info[0]}签到\n等级：Lv.{info[1]}\n经验值：{info[2]}/{info[3]}'
        logger.info(initial_msg)

        # 获取通知类型
        notifier_type = os.getenv("NOTIFIER_TYPE")
        print("通知类型：", notifier_type)

        # 判断通知类型，微信即时发送，邮箱聚合消息
        if notifier_type == "wechat":  # 如果是微信通知，立即发送
            self.notifier.send(initial_msg)
            all_messages = []  # 微信即时发送，清空聚合消息
        elif notifier_type == "email":  # 如果是邮箱通知，聚合消息
            all_messages = [initial_msg]
        else:  # 不发送通知
            all_messages = []

        total_exp = 0  # 记录总共获取的经验值

        # 循环签到每个版块
        for ct in cat_id_dict.keys():
            self.cat_id = ct
            sign = self.sign_get().upper()
            signin_url = (
                f"http://floor.huluxia.com/user/signin/ANDROID/4.1.8?"
                f"platform={platform}&gkey={gkey}&app_version={app_version}&versioncode={versioncode}"
                f"&market_id={market_id}&_key={self._key}&device_code={device_code}"
                f"&phone_brand_type={phone_brand_type}&cat_id={self.cat_id}&time={self.timestamp()}"
            )
            post_data = {"sign": sign}
            try:
                signin_res = session.post(url=signin_url, headers=headers, data=post_data).json()
            except Exception as e:
                error_msg = f"签到过程中出现错误：{e}"
                if notifier_type == "wechat":
                    self.notifier.send(error_msg)  # 微信即时发送
                elif notifier_type == "email":
                    all_messages.append(error_msg)  # 聚合消息（邮箱通知）
                logger.error(error_msg)
                break

            # 处理签到结果
            if signin_res.get('status') == 0:
                fail_msg = f'【{cat_id_dict[self.cat_id]}】签到失败，请手动签到。'
                if notifier_type == "wechat":
                    self.notifier.send(fail_msg)  # 微信即时发送
                elif notifier_type == "email":
                    all_messages.append(fail_msg)  # 聚合消息（邮箱通知）
                logger.warning(fail_msg)
                time.sleep(3)
                continue

            # 签到成功，记录经验值
            signin_exp = signin_res.get('experienceVal', 0)
            self.signin_continue_days = signin_res.get('continueDays', 0)
            success_msg = f'【{cat_id_dict[self.cat_id]}】签到成功，经验值 +{signin_exp}'
            if notifier_type == "wechat":
                self.notifier.send(success_msg)  # 微信即时发送
            elif notifier_type == "email":
                all_messages.append(success_msg)  # 聚合消息（邮箱通知）
            logger.info(success_msg)
            total_exp += signin_exp
            time.sleep(3)

        # 汇总签到结果
        summary_msg = f'本次为{info[0]}签到共获得：{total_exp} 经验值'
        if notifier_type == "wechat":
            self.notifier.send(summary_msg)  # 微信即时发送
        elif notifier_type == "email":
            all_messages.append(summary_msg)  # 聚合消息（邮箱通知）
        logger.info(summary_msg)

        # 完成签到后的用户信息
        final_info = self.user_info()
        final_msg = f'已为{final_info[0]}完成签到\n等级：Lv.{final_info[1]}\n经验值：{final_info[2]}/{final_info[3]}\n已连续签到 {self.signin_continue_days} 天\n'
        remaining_days = (int(final_info[3]) - int(final_info[2])) // total_exp + 1 if total_exp else "未知"
        final_msg += f'还需签到 {remaining_days} 天'
        if notifier_type == "wechat":
            self.notifier.send(final_msg)  # 微信即时发送
        elif notifier_type == "email":
            all_messages.append(final_msg)  # 聚合消息（邮箱通知）
        logger.info(final_msg)

        # 如果是邮箱通知，发送聚合后的所有消息
        if notifier_type == "email" and all_messages:
            self.notifier.send("\n\n".join(all_messages))

