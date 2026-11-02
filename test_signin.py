"""signin.py 独立调用测试脚本。

用法:
    python test_signin.py <手机号> <密码>

作用:
    不依赖 main.py / GitHub Actions，直接本地调用 HuluxiaSignin
    对单个账号执行全版块签到，用于验证 signin.py 逻辑是否正常。
"""
import os
import sys

# 确保能 import 同目录下的 signin 模块（无论从哪个目录运行）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试阶段默认不推送通知，避免打扰；如需推送可设 NOTIFIER_TYPE=wechat/email
os.environ.setdefault("NOTIFIER_TYPE", "none")

from signin import HuluxiaSignin  # noqa: E402


def test_signin(account: str, password: str) -> int:
    """单独封装：对指定账号执行签到，返回本次获得的总经验值。

    :param account: 手机号
    :param password: 密码
    :return: 签到总经验值
    """
    client = HuluxiaSignin()
    return client.huluxia_signin(account, password)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python test_signin.py <手机号> <密码>")
        sys.exit(2)

    phone, pwd = sys.argv[1], sys.argv[2]
    print(f"开始测试签到，账号: {phone}")
    try:
        exp = test_signin(phone, pwd)
        print(f"\n=== 签到完成，共获得 {exp} 经验值 ===")
    except Exception as e:
        print(f"\n=== 签到失败：{e} ===")
        sys.exit(1)
