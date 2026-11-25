import os
import time

from logger import logger
from signin import HuluxiaSignin

# 检查环境变量
accounts_str = os.getenv('ACCOUNTS')
if not accounts_str:
    logger.error("环境变量 ACCOUNTS 未设置")
    raise ValueError("环境变量 ACCOUNTS 未设置")

# 解析账号信息：逐行解析并跳过空行；
# 用 partition 而不是 split(',')，这样密码里含英文逗号也能正确切分。
accounts = []
for line in accounts_str.splitlines():
    line = line.strip()
    if not line:
        continue
    phone, sep, password = line.partition(',')
    if not sep or not phone.strip() or not password.strip():
        logger.warning(f"账号信息格式不正确，已跳过：{line}")
        continue
    accounts.append((phone.strip(), password.strip()))

if not accounts:
    raise ValueError("ACCOUNTS 中没有有效账号，格式应为：手机号,密码")

logger.info(f"共解析到 {len(accounts)} 个账号")

# 实例化 HuluxiaSignin 类
huluxia_signin_obj = HuluxiaSignin()

# 遍历账号进行签到
for index, (phone, password) in enumerate(accounts):
    try:
        huluxia_signin_obj.huluxia_signin(phone, password)
        logger.info(f"账号 {phone} 签到成功")
    except Exception as e:
        logger.error(f"账号 {phone} 签到失败: {e}")
    # 多账号之间留出间隔，最后一个账号不必再等
    if index < len(accounts) - 1:
        time.sleep(60)
