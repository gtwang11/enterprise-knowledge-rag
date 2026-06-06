"""安全工具：bcrypt 哈希、随机密码、复杂度校验"""

import re
import secrets
import string

import bcrypt

from config import PASSWORD_BCRYPT_COST, PASSWORD_MIN_LENGTH


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(PASSWORD_BCRYPT_COST)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def validate_password_complexity(password: str) -> tuple[bool, str]:
    """校验密码复杂度，返回 (是否通过, 错误信息)"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"密码长度至少 {PASSWORD_MIN_LENGTH} 位"

    categories = 0
    if re.search(r'[A-Z]', password):
        categories += 1
    if re.search(r'[a-z]', password):
        categories += 1
    if re.search(r'[0-9]', password):
        categories += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
        categories += 1

    if categories < 3:
        return False, "密码必须包含大写字母、小写字母、数字、特殊字符中的至少 3 类"

    return True, ""


def generate_random_password(length: int = 12) -> str:
    """生成随机密码：大小写字母 + 数字 + 特殊字符"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        ok, _ = validate_password_complexity(password)
        if ok:
            return password
