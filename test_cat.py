"""单版块签到验证脚本。

用法:
    python test_cat.py <手机号> <密码> [cat_id ...]

不指定 cat_id 时默认验证 130（影之刃零），并自动带上 cat_id=1（3楼公告版）
作为对照组：对照组能签到成功、目标版块也返回成功，才说明该 cat_id 有效。

只输出接口原始返回，不改动 cat_id.json。
"""
import json
import os
import sys
import time

# 确保能 import 同目录下的 signin 模块（无论从哪个目录运行）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试阶段不推送通知，避免打扰
os.environ.setdefault("NOTIFIER_TYPE", "none")

import signin as signin_mod  # noqa: E402
from signin import HuluxiaSignin  # noqa: E402

CONTROL_CAT_ID = "1"      # 3楼公告版，已知可签到，用来验证登录态是否正常
TARGET_CAT_ID = "130"     # 待验证版块


def probe(client: HuluxiaSignin, cat_id: str) -> dict:
    """对单个版块发起签到，返回解析后的响应（解析失败时返回原始文本）。"""
    client.cat_id = str(cat_id)
    raw = client.session.post(
        url=client._build_signin_url(),
        headers=signin_mod.DEFAULT_HEADERS,
        data={"sign": client.sign_get().upper()},
    ).text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def main() -> int:
    if len(sys.argv) < 3:
        print("用法: python test_cat.py <手机号> <密码> [cat_id ...]")
        return 2

    phone, password = sys.argv[1], sys.argv[2]
    targets = sys.argv[3:] or [TARGET_CAT_ID]

    client = HuluxiaSignin()
    try:
        client._login(phone, password)
    except Exception as e:
        print(f"登录失败：{e}")
        return 1

    info = client.user_info()
    print(f"登录成功：{info['nick']}  Lv.{info['level']}  "
          f"经验 {info['exp']}/{info['next_exp']}\n")

    # 先跑对照组，确认登录态本身是好的
    order = [CONTROL_CAT_ID] + [c for c in targets if c != CONTROL_CAT_ID]
    for cat_id in order:
        tag = "对照组" if cat_id == CONTROL_CAT_ID else "目标版块"
        res = probe(client, cat_id)
        ok = res.get("status") == 1
        exp = res.get("experienceVal", 0)
        print(f"[{tag}] cat_id={cat_id}  status={res.get('status')}  "
              f"签到{'成功' if ok else '失败'}  经验+{exp}")
        print(f"          原始返回: {json.dumps(res, ensure_ascii=False)}")
        time.sleep(3)

    return 0


if __name__ == "__main__":
    sys.exit(main())
