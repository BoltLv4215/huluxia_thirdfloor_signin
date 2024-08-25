import hashlib
import json
import os
import random
import time
import requests
from logger import logger

# 随机配置
phone_brand_type_list = list(["MI", "Huawei", "UN", "OPPO", "VO"])  # 随机设备厂商
device_code_random = random.randint(111, 987)  # 随机设备识别码

# 配置
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


# 企业微信群机器人 推送
def text_push(msg):
    text_url = os.getenv('WECHAT_ROBOT_URL')
    if not text_url:
        raise ValueError("环境变量 WECHAT_ROBOT_URL 未设置")
    text_data = {
        "msgtype": "markdown",
        "markdown": {
            "content": msg,
            "mentioned_list": ["@all"],
            "mentioned_mobile_list": ["@all"]
        }
    }
    requests.post(url=text_url, json=text_data)



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

    # 手机号密码登录
    def psd_login(self, account, password):
        """
        手机号密码登录

        :param account: 手机号
        :param password: 密码
        :return: 登录结果
        """
        login_url = 'http://floor.huluxia.com/account/login/ANDROID/4.0?' \
                    'platform=' + platform + \
                    '&gkey=' + gkey + \
                    '&app_version=' + app_version + \
                    '&versioncode=' + versioncode + \
                    '&market_id=' + market_id + \
                    '&_key=&device_code=' + device_code + \
                    '&phone_brand_type=' + phone_brand_type
        login_data = {
            'account': account,
            'password': self.md5(password),
            'login_type': 2
        }
        # print(login_data)
        login_res = session.post(url=login_url, data=login_data, headers=headers)
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
            text_push("手机号或密码错误!")
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
        msg_result: str = ''  # 消息聚合
        self.set_config(acc, psd)
        info = self.user_info()
        msg_1 = f'正在为<font color="warning">**{info[0]}**</font>签到\n'
        msg1 = f'> 当前等级：Lv.{info[1]}\n' \
               f'> 当前经验值：<font color="info">{info[2]}</font>\n' \
               f'> 下一等级目标经验值：{info[3]}'
        logger.info(msg_1)
        logger.info(msg1)
        msg_1 += msg1
        text_push(msg_1)
        time.sleep(1)
        # text_push(msg1)
        # msg_result += msg_1
        exp_get = 0  # 经验值
        for ct in cat_id_dict.keys():
            self.cat_id = ct
            sign = self.sign_get().upper()
            signin_url = 'http://floor.huluxia.com/user/signin/ANDROID/4.1.8?' \
                         'platform=' + platform + \
                         '&gkey=' + gkey + \
                         '&app_version=' + app_version + \
                         '&versioncode=' + versioncode + \
                         '&market_id=' + market_id + \
                         '&_key=' + self._key + \
                         '&device_code=' + device_code + \
                         '&phone_brand_type=' + phone_brand_type + \
                         '&cat_id=' + self.cat_id + \
                         '&time=' + str(self.timestamp())
            post_data = {
                'sign': sign
            }
            signin_res = session.post(url=signin_url, headers=headers, data=post_data)
            try:
                signin_res = signin_res.json()
            except Exception:
                msg_2 = '<font color="warning">**出现错误！终止签到**</font>'
                # msg_result += msg_2
                text_push(msg_2)
                logger.info(msg_2)
                break
            # print(signin_res)
            signin_status = signin_res['status']
            if signin_status == 0:
                logger.info(signin_res)
                message = f'【{cat_id_dict[self.cat_id]}】签到失败！请手动签到！'
                logger.info(message)
                text_push(message)
                time.sleep(3)
                continue
            signin_exp = signin_res['experienceVal']
            self.signin_continue_days = signin_res['continueDays']
            msg_4 = f'【{cat_id_dict[self.cat_id]}】签到成功，经验+{signin_exp}\n\ncat_id:{self.cat_id}\n\n'
            msg_result += msg_4
            logger.info(msg_4)
            # text_push(msg_4)
            exp_get += signin_exp
            time.sleep(3)
        msg_5 = f'本次签到共获得：{exp_get}经验值'
        # msg_result += msg_5
        logger.info(msg_5)
        # text_push(msg_result)
        text_push(msg_5)
        # 完成签到
        inf = self.user_info()
        msg_6 = f'已为<font color="warning">**{inf[0]}**</font>完成签到\n'
        # 经验值计算
        sign_day = (int(inf[3]) - int(inf[2])) / int(exp_get) + 1
        msg6 = f'> 当前等级：Lv.{inf[1]}\n' \
               f'> 当前经验值：<font color="info">{inf[2]}</font>\n' \
               f'> 已连续签到{self.signin_continue_days}天\n' \
               f'> 下一等级目标经验值：{inf[3]}\n' \
               f'> 还需签到<font color="warning">{int(sign_day)}</font>天'
        logger.info(msg_6)
        # text_push(msg_6)
        msg_6 += msg6
        logger.info(msg6)
        time.sleep(1)
        text_push(msg_6)