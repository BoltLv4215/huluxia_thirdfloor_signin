import hashlib
import json
import logging
import os
import random
import time
from typing import Dict, List, Optional

import requests

from logger import logger
from notifier import Notifier, get_notifier

# ---------------------------------------------------------------------------
# 常量配置
# ---------------------------------------------------------------------------
PLATFORM = '2'
GKEY = '000000'
APP_VERSION = '4.3.1.5.2'
VERSION_CODE = '398'
MARKET_ID = 'floor_web'
SIGN_SECRET = 'fa1c28a5b62e79c3e63d9030b6142e4b'
PHONE_BRAND_TYPES = ["MI", "Huawei", "UN", "OPPO", "VO"]

DEFAULT_HEADERS = {
    "Connection": "close",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "User-Agent": "okhttp/3.8.1",
    "Host": "floor.huluxia.com",
}

# 版块 ID 配置文件：相对本文件定位，避免从其他目录运行时找不到
CAT_ID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cat_id.json')


def _load_cat_ids() -> Dict[str, str]:
    """读取版块 ID 映射表。"""
    with open(CAT_ID_FILE, 'r', encoding='UTF-8') as f:
        return json.loads(f.read())


class HuluxiaSignin:
    """葫芦侠三楼签到客户端。"""

    def __init__(self, cat_ids: Optional[Dict[str, str]] = None,
                 sign_interval: int = 3) -> None:
        self.cat_ids = cat_ids if cat_ids is not None else _load_cat_ids()
        self.sign_interval = sign_interval

        # 会话状态
        self.session = requests.Session()
        self._key = ''
        self.userid = ''
        self.cat_id = ''
        self.signin_continue_days = 0

        # 设备指纹（同一实例内的多个账号视为同一台设备）
        self.device_code = f'%5Bd%5D5125c3c6-f{random.randint(111, 987)}-4c6b-81cf-9bc467522d61'
        self.phone_brand_type = random.choice(PHONE_BRAND_TYPES)

        # 通知器
        self.notifier_type = os.getenv("NOTIFIER_TYPE", "none")
        self.notifier = self._build_notifier()

    # ------------------------------------------------------------------
    # 通知相关
    # ------------------------------------------------------------------
    def _build_notifier(self) -> Notifier:
        config = {
            "webhook_url": os.getenv("WECHAT_ROBOT_URL"),
            "smtp_server": "smtp.qq.com",
            "port": 465,
        }
        if self.notifier_type == "email":
            raw = os.getenv("EMAIL_CONFIG")
            if not raw:
                raise ValueError("缺少邮箱配置：请设置 EMAIL_CONFIG 环境变量")
            try:
                email_config = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError("邮箱配置格式错误，请检查 EMAIL_CONFIG 的值。") from e
            config.update({
                "username": email_config.get("username"),
                "auth_code_or_password": email_config.get("auth_code_or_password"),
                "sender_email": email_config.get("sender_email"),
                "recipient_email": email_config.get("recipient_email"),
            })
        return get_notifier(self.notifier_type, config)

    def _emit(self, message: str, buffer: List[str], level: int = logging.INFO) -> None:
        """统一处理通知与日志：微信即时发送、邮箱缓存、none 忽略。"""
        if self.notifier_type == "wechat":
            self.notifier.send(message)
        elif self.notifier_type == "email":
            buffer.append(message)
        logger.log(level, message)

    # ------------------------------------------------------------------
    # 登录与用户信息
    # ------------------------------------------------------------------
    def psd_login(self, account: str, password: str) -> Dict:
        """手机号 + 密码登录，返回登录响应 JSON。"""
        device_model = f"iPhone{random.randint(14, 17)}%2C{random.randint(1, 6)}"
        login_url = (
            'https://floor.huluxia.com/account/login/IOS/1.0?'
            'access_token=&app_version=1.2.2&code='
            '&device_code=' + self.device_code +
            '&device_model=' + device_model +
            '&email=' + account +          # 接口字段名为 email，实为手机号
            '&market_id=floor_huluxia&openid=&'
            'password=' + self.md5(password) +
            '&phone='
            '&platform=1'
        )
        login_res = self.session.get(url=login_url, headers=DEFAULT_HEADERS)
        return login_res.json()

    def _login(self, account: str, password: str) -> None:
        """登录并保存会话凭证；失败时抛出异常。"""
        data = self.psd_login(account, password)
        if data.get('status') == 0:
            raise RuntimeError("手机号或密码错误，登录失败")
        self._key = data['_key']
        self.userid = data['user']['userID']

    def _build_user_info_url(self) -> str:
        return (
            'http://floor.huluxia.com/user/info/ANDROID/4.1.8?'
            'platform=' + PLATFORM +
            '&gkey=' + GKEY +
            '&app_version=' + APP_VERSION +
            '&versioncode=' + VERSION_CODE +
            '&market_id=' + MARKET_ID +
            '&_key=' + self._key +
            '&device_code=' + self.device_code +
            '&phone_brand_type=' + self.phone_brand_type +
            '&user_id=' + str(self.userid)
        )

    def user_info(self) -> Dict[str, str]:
        """返回用户昵称、等级、当前经验与下一级所需经验。"""
        data = requests.get(url=self._build_user_info_url(), headers=DEFAULT_HEADERS).json()
        return {
            'nick': data['nick'],
            'level': data['level'],
            'exp': data['exp'],
            'next_exp': data['nextExp'],
        }

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    def mask_nickname(nickname: str) -> str:
        if len(nickname) > 2:
            return nickname[0] + '*' * (len(nickname) - 2) + nickname[-1]
        if len(nickname) == 2:
            return '*' + nickname[-1]
        return nickname

    @staticmethod
    def timestamp() -> int:
        return int(time.time())

    def sign_get(self) -> str:
        """生成签到签名：md5("cat_id" + 版块id + "time" + 时间戳 + 固定密钥)。"""
        raw = "cat_id" + self.cat_id + "time" + str(self.timestamp()) + SIGN_SECRET
        return self.md5(raw)

    def _build_signin_url(self) -> str:
        return (
            "http://floor.huluxia.com/user/signin/ANDROID/4.1.8?"
            f"platform={PLATFORM}&gkey={GKEY}&app_version={APP_VERSION}&versioncode={VERSION_CODE}"
            f"&market_id={MARKET_ID}&_key={self._key}&device_code={self.device_code}"
            f"&phone_brand_type={self.phone_brand_type}&cat_id={self.cat_id}&time={self.timestamp()}"
        )

    @staticmethod
    def _remaining_days(cur_exp: str, next_exp: str, total_exp: int) -> str:
        if not total_exp:
            return "未知"
        return str((int(next_exp) - int(cur_exp)) // total_exp + 1)

    # ------------------------------------------------------------------
    # 签到主流程
    # ------------------------------------------------------------------
    def huluxia_signin(self, account: str, password: str) -> int:
        """对单个账号执行全版块签到，返回获得的总经验值。"""
        self._login(account, password)
        info = self.user_info()
        nick = self.mask_nickname(info['nick'])
        buffer: List[str] = []

        self._emit(
            f'正在为{nick}签到\n等级：Lv.{info["level"]}\n经验值：{info["exp"]}/{info["next_exp"]}',
            buffer,
        )

        total_exp = 0
        for ct, name in self.cat_ids.items():
            self.cat_id = ct
            try:
                res = self.session.post(
                    url=self._build_signin_url(),
                    headers=DEFAULT_HEADERS,
                    data={"sign": self.sign_get().upper()},
                ).json()
            except Exception as e:
                self._emit(f"签到过程中出现错误：{e}", buffer, logging.ERROR)
                break

            if res.get('status') == 0:
                self._emit(f'【{name}】签到失败，请手动签到。', buffer, logging.WARNING)
            else:
                exp = res.get('experienceVal', 0)
                self.signin_continue_days = res.get('continueDays', 0)
                self._emit(f'【{name}】签到成功，经验值 +{exp}', buffer)
                total_exp += exp
            time.sleep(self.sign_interval)

        self._emit(f'本次为{nick}签到共获得：{total_exp} 经验值', buffer)

        final = self.user_info()
        final_nick = self.mask_nickname(final['nick'])
        remain = self._remaining_days(final['exp'], final['next_exp'], total_exp)
        final_msg = (
            f'已为{final_nick}完成签到\n等级：Lv.{final["level"]}\n'
            f'经验值：{final["exp"]}/{final["next_exp"]}\n'
            f'已连续签到 {self.signin_continue_days} 天\n还需签到 {remain} 天'
        )
        self._emit(final_msg, buffer)

        if self.notifier_type == "email" and buffer:
            self.notifier.send("\n\n".join(buffer))

        return total_exp
