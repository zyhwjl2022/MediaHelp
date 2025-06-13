"""天翼云盘工具函数"""

import hashlib
from typing import Dict, Any
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

def sort_params(params: Dict[str, Any]) -> str:
    """
    对参数进行排序并拼接
    :param params: 参数字典
    :return: 排序后的参数字符串
    """
    if not params:
        return ""
    
    # 将参数转换为 key=value 形式并排序
    sorted_items = sorted(
        [f"{k}={v}" for k, v in params.items()],
        key=lambda x: x
    )
    return "&".join(sorted_items)

def get_signature(params: Dict[str, Any]) -> str:
    """
    获取参数签名
    :param params: 参数字典
    :return: MD5签名
    """
    sorted_params = sort_params(params)
    return hashlib.md5(sorted_params.encode()).hexdigest()

def rsa_encrypt(public_key: str, data: str) -> str:
    """
    RSA加密
    :param public_key: PEM格式的公钥
    :param data: 待加密数据
    :return: 十六进制格式的加密结果
    """
    # 处理公钥格式
    if not public_key.startswith("-----BEGIN PUBLIC KEY-----"):
        public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
    
    # 加载公钥
    rsa_key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(rsa_key)
    
    # 加密数据
    encrypted = cipher.encrypt(data.encode())
    return encrypted.hex().upper() 