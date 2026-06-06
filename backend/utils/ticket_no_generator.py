"""工单编号生成器 TK-YYYYMMDDHHMMSS-XXXXX (thread-safe)"""

import random
import string
from datetime import datetime


def generate_ticket_no() -> str:
    """生成唯一工单编号（时间戳+随机后缀，无DB依赖，线程安全）"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"TK-{ts}-{suffix}"
