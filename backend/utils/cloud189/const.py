"""天翼云盘常量定义"""

# API URLs
WEB_URL = "https://cloud.189.cn"
AUTH_URL = "https://open.e.189.cn"
API_URL = "https://api.cloud.189.cn"

# 认证相关
ACCOUNT_TYPE = "02"
APP_ID = "8025431004"
CLIENT_TYPE = "10020"
RETURN_URL = "https://m.cloud.189.cn/zhuanti/2020/loginErrorPc/index.html"

# 客户端标识
VERSION = "6.2"
PC_CLIENT = "TELEPC"
CHANNEL_ID = "web_cloud.189.cn"

# 默认请求头
DEFAULT_HEADERS = {
    "Accept": "application/json;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": f"{WEB_URL}/web/main/",
    # "Origin": WEB_URL,
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}

# 文件类型
FILE_TYPE_FOLDER = 1
FILE_TYPE_FILE = 2

# 默认根目录ID
ROOT_FOLDER_ID = "-11"

# 批量任务类型
TASK_TYPE_SHARE_SAVE = "SHARE_SAVE"
TASK_TYPE_DOWNLOAD = "DOWNLOAD"

def get_client_suffix():
    """获取客户端后缀参数"""
    from time import time
    return {
        "clientType": PC_CLIENT,
        "version": VERSION,
        "channelId": CHANNEL_ID,
        "rand": int(time() * 1000)
    } 