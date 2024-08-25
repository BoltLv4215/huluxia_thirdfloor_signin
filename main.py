import time
from signin import HuluxiaSignin, text_push
import os

# 检查环境变量
text_url = os.getenv('WECHAT_ROBOT_URL')
print(f"WECHAT_ROBOT_URL: {text_url}")  # 调试输出
if not text_url:
    raise ValueError("环境变量 WECHAT_ROBOT_URL 未设置")
accounts_str = os.getenv('ACCOUNTS')
print(f"ACCOUNTS: {accounts_str}")  # 调试输出
if not accounts_str:
    raise ValueError("环境变量 ACCOUNTS 未设置")

# 解析账号信息
accounts = [acc.split(',') for acc in accounts_str.split('\n') if acc]

# 实例化 HuluxiaSignin 类
huluxia_signin_obj = HuluxiaSignin()

# 遍历账号进行签到
for account in accounts:
    huluxia_signin_obj.huluxia_signin(account[0], account[1])
    time.sleep(60)

text_push('**所有账号签到完成**')


