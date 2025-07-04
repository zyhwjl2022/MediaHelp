import ssl
import json
import sys
import certifi
import asyncio
import websockets
import base64
import secrets
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
import random
import string
from typing import Dict, Any, Optional
from loguru import logger
from typing import List, Dict, Any

from utils.config_manager import config_manager

"""
配合 飞牛系统的Alist 项目，转存后自动下载
"""

async def create_websocket(url):
    """创建WebSocket连接，支持WSS加密连接"""
    if 'wss' in url:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_verify_locations(certifi.where())
        return await websockets.connect(url, ssl=ssl_context, ping_interval=None)
    else:
        return await websockets.connect(url, ping_interval=None)

async def wss_connect(websocket):
    """接收WebSocket消息"""
    return await websocket.recv()

async def close_websocket(websocket):
    """关闭WebSocket连接"""
    await websocket.close()

async def send_ping(websocket):
    """定时发送Ping消息保持连接活跃"""
    while True:
        await asyncio.sleep(30)  # 30秒发送一次
        await websocket.send('{"req":"ping"}')

def rsa_encrypt(message, public_key):
    """使用RSA公钥加密数据"""
    public_key = RSA.import_key(public_key)
    cipher = Cipher_pkcs1_v1_5.new(public_key)
    cipher_text = base64.b64encode(cipher.encrypt(message.encode('utf-8')))
    return cipher_text.decode('utf-8')

def encrypt(text, key, iv):
    """使用AES-CBC模式加密数据"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    encrypted = base64.b64encode(cipher.encrypt(pad(text).encode()))
    return encrypted.decode()

def unpad(data):
    """去除AES加密的填充"""
    pad = data[-1]
    if isinstance(pad, int):
        pad = chr(pad)
    return data[:-ord(pad)]

def decrypt(text, key, iv):
    """使用AES-CBC模式解密数据"""
    encodebytes = base64.decodebytes(text.encode())
    cipher = AES.new(key, AES.MODE_CBC, iv)
    text_decrypted = cipher.decrypt(encodebytes)
    text_decrypted = unpad(text_decrypted)
    return base64.b64encode(text_decrypted).decode()

oneMark = True
def print_progress_bar(iteration, total, prefix='', suffix='', length=35):
    """显示下载进度条"""
    global oneMark
    percent = (iteration / total) * 100
    filled_length = int(length * iteration // total)
    bar = '#' * filled_length + ' ' * (length - filled_length)
    percent_str = str(int(percent)).zfill(2)
    if percent < 100:
        percent_str = " " + percent_str
    if oneMark:
        print(f'{prefix} {bar} {percent_str}% {suffix}', end='')
        oneMark = False
    else:
        print(f'\r{prefix} {bar} {percent_str}% {suffix}', end='')
    sys.stdout.flush()

def seconds_to_hms(seconds):
    """将秒数转换为时分秒格式"""
    hours = seconds // 3600
    remainder = seconds % 3600
    minutes = remainder // 60
    seconds = remainder % 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

def format_byte_repr(byte_num):
    """格式化字节数为易读单位"""
    try:
        if isinstance(byte_num, str):
            byte_num = int(byte_num)
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_idx = 0
        while byte_num >= 1024 and unit_idx < 4:
            byte_num /= 1024
            unit_idx += 1
        return f'{byte_num:.2f}{units[unit_idx]}'
    except Exception as e:
        logger.error(f"字节格式化错误: {str(e)}")
        return f"{byte_num}B"

class Fnos:
    """飞牛系统交互类"""
    keyword = ""
    dramaList = []  # 待下载文件列表
    
    @staticmethod
    def processMediaType(savePath):
        """根据保存路径判断媒体类型"""
        if "电影" in savePath:
            return "电影"
        elif "电视剧" in savePath:
            return "电视剧"
        elif "动漫" in savePath:
            return "动漫"
        elif "综艺" in savePath:
            return "综艺"
        else:
            return "其他"

    def __init__(self):
        """初始化飞牛系统配置"""
        self.config = config_manager.get_config()
        self.fn_url = self.config.get("fn_url", "")
        self.fn_username = self.config.get("fn_username", "")
        self.fn_password = self.config.get("fn_password", "")
        self.quark_path = self.config.get("quark_path", "")
        self.cloud189_path = self.config.get("cloud189_path", "")
        self.cloud_file_path = self.config.get("cloud_file_path", "")
        self.save_path = self.config.get("save_path", "")
        self.cloud_type = self.config.get("cloud_type", "quark")
        self.download_wait = self.config.get("download_wait", False)
        self.aes_key = self.config.get("aes_key", "lUfJn1XJ9akUvmmwQplpVIy1XNC2jJ3q").encode()  # 转为字节
        self.dramaList = []
        # 验证配置完整性
        required_keys = ["fn_url", "fn_username", "fn_password", "quark_path", "save_path"] if "quark" == self.cloud_type else ["fn_url", "fn_username", "fn_password", "cloud189_path", "save_path"]
        self.missing = [k for k in required_keys if not self.config.get(k)]
        if self.missing:
            logger.error(f"配置缺失必要参数: {', '.join(self.missing)}，请检查配置")
        
        # 构建WebSocket连接地址
        self.websocket_url = f"ws://{self.fn_url}/websocket?type=main"
        # self.preReqid = secrets.token_hex(8)  # 生成随机请求ID
        self.preReqid = '676cf70d'
        self.download_path = ""

    async def connect_to_websocket(self):
        """创建并返回WebSocket连接"""
        return await create_websocket(self.websocket_url)

    async def authenticate(self, websocket, pub_key, si):
        """执行用户认证"""
        aes_iv = secrets.token_bytes(16)
        aes_iv_base64 = base64.b64encode(aes_iv).decode('utf-8')
        
        # 构造用户认证数据
        user_data = {
            "reqid": f"{self.preReqid}00000000000000000002",
            "user": self.fn_username,
            "password": self.fn_password,
            "deviceType": "Browser",
            "deviceName": "Mac OS-Google Chrome",
            "stay": True,
            "req": "user.login",
            "si": si
        }
        
        # 加密数据
        rsa_encrypted = rsa_encrypt(self.aes_key.decode(), pub_key)
        aes_encrypted = encrypt(json.dumps(user_data), self.aes_key, aes_iv)
        
        # 发送加密认证消息
        send_msg = {
            "rsa": rsa_encrypted,
            "iv": aes_iv_base64,
            "aes": aes_encrypted,
            "req": "encrypted"
        }
        await websocket.send(json.dumps(send_msg))
        return self.aes_key, aes_iv

    async def create_folder(self, websocket, secret, folder_path):
        """创建下载文件夹"""
        # 构造创建文件夹请求
        create_req = {
            "reqid": f"{self.preReqid}00000000000000000003",
            "path": folder_path,
            "req": "file.mkdir"
        }
        req_str = json.dumps(create_req)
        
        # 生成HMAC签名
        hmac_digest = HMAC.new(secret, req_str.encode(), digestmod=SHA256).digest()
        mark = base64.b64encode(hmac_digest).decode()
        
        # 发送创建请求
        await websocket.send(mark + req_str)
        response = await wss_connect(websocket)
        
        # 处理响应
        if '"result":"succ"' in response or '"errno":4102' in response:
            logger.info(f"文件夹创建成功: {folder_path}")
            return True,"文件夹创建成功"
        elif '"result":"fail"' in response:
            logger.error(f"文件夹创建失败: {folder_path}，请检查路径权限")
            return False,f"文件夹创建失败: {folder_path}，请检查路径权限"
        else:
            logger.warning(f"文件夹创建响应异常: {response}")
            return False,f"文件夹创建响应异常: {response}"
        
    def group_file_paths(self,file_paths: List[str], keyword: str) -> Dict[str, List[str]]:
        """
        根据指定关键词对文件路径进行分组
        
        参数:
        - file_paths: 包含文件路径的字符串列表
        - keyword: 用于切分路径的关键词
        
        返回:
        - 分组结果字典，键为切分后的路径部分，值为原始路径列表
        """
        groups = {}
        
        for path in file_paths:
            # 第一次切分：使用关键词切分，保留后半部分
            if keyword in path:
                _, after_keyword = path.split(keyword, 1)
                
                # 第二次切分：使用最后一个斜杠切分，保留前半部分
                last_slash_index = after_keyword.rfind('/')
                if last_slash_index != -1:
                    group_key = after_keyword[:last_slash_index]
                else:
                    group_key = ''
                    
                # 将路径添加到对应的分组
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(path)
        
        return groups

    async def download_files_task(self, websocket, secret, folder_path, file_list, ):
        """执行文件下载任务"""
        if not file_list:
            logger.error("未获取到待下载文件列表")
            return False,"未获取到待下载文件列表"
        
        # 输出分组结果
        reqid = secrets.token_hex(14)   
        # 构造文件复制请求
        files_str = ','.join(f'"{f}"' for f in file_list)
        download_req = {
            "reqid": f"{reqid}",
            "files": json.loads(f"[{files_str}]"),
            "pathTo": folder_path,
            "overwrite": 1,
            "description": f"夸克自动下载【{self.keyword}】",
            "req": "file.cp"
        }
        logger.debug(f"飞牛: 准备下载文件: {download_req}")
        req_str = json.dumps(download_req)
        
        # 生成HMAC签名
        hmac_digest = HMAC.new(secret, req_str.encode(), digestmod=SHA256).digest()
        mark = base64.b64encode(hmac_digest).decode()
        
        # 发送下载请求
        await websocket.send(mark + req_str)
        num = 0
        
        while True:
            response = await wss_connect(websocket)
            if reqid in response:
                logger.debug(f"下载响应: {response}")
                if '"sysNotify":"taskInfo"' in response:
                    logger.debug(f"下载响应: {response}")
                if '"sysNotify":"taskId"' in response:
                    logger.info("收到资源下载任务")
                    return True,"收到资源下载任务"
                elif '"result":"fail"' in response:
                    print()
                    logger.error(f"下载任务异常: {response}，请检查配置")
                    return False,f"下载任务异常: {response}，请检查配置"
                elif '"result":"cancel"' in response:
                    print()
                    logger.warning("下载任务被取消")
                    return False,"下载任务被取消"
        # while True:
        #     response = await wss_connect(websocket)
        #     logger.debug(f"ID:{self.preReqid}")
        #     logger.debug(f"ID:{self.preReqid}0000000000000000000000000")
        #     if self.preReqid+"0000000000000000000000000" in response:
        #         if '"sysNotify":"taskId"' in response:
        #             logger.info("收到资源下载任务")
        #         elif 'percent' in response:
        #             try:
        #                 data = json.loads(response)
        #                 percent = data.get('percent', 0)
        #                 if self.download_wait:
        #                     if num < percent:
        #                         time = seconds_to_hms(data.get('time', 0))
        #                         du = f"{format_byte_repr(data.get('size', 0))}/{format_byte_repr(data.get('sizeTotal', 0))}"
        #                         speed = f"{format_byte_repr(data.get('speed', 0))}/S"
        #                         suffix = f"{time} {du} {speed}"
        #                         print_progress_bar(percent, 100, prefix=f'⌛飞牛: {self.keyword} ', suffix=suffix)
        #                         num = percent
        #                 else:
        #                     logger.info("下载任务后台执行")
        #                     break
        #             except json.JSONDecodeError:
        #                 logger.error(f"下载进度解析失败: {response}")
        #         elif '"result":"succ"' in response:
        #             print()  # 换行显示完整进度条
        #             logger.success(f"下载任务完成: {folder_path}")
        #             break
        #         elif '"result":"fail"' in response:
        #             print()
        #             logger.error(f"下载任务异常: {response}，请检查配置")
        #             break
        #         elif '"result":"cancel"' in response:
        #             print()
        #             logger.warning("下载任务被取消")
        #             break
        #     else:
        #         logger.debug(f"收到未知响应: {response}")
        return True

    async def run_async(self):
        """异步运行主逻辑，协调各异步任务"""
        error_info = ""

        # 检查配置是否完整
        if self.missing:
            error_info = f"配置缺失必要参数: {', '.join(self.missing)}，请检查配置"
            logger.error(error_info)
            return False, error_info
        
        if not self.dramaList:
            # 手动保存 夸克网盘
            self.dramaList = [self.quark_path+self.cloud_file_path+"/"+self.keyword] if "quark" == self.cloud_type else [self.cloud189_path+self.cloud_file_path+"/"+self.keyword]
        elif isinstance(self.dramaList, list):
            # 确保dramaList中的路径是完整的
            logger.info(f"self.dramaList{self.dramaList}")
            self.dramaList = [self.quark_path + file if "quark" == self.cloud_type else self.cloud189_path + file for file in self.dramaList]
            
            logger.info(f"self.dramaList{self.dramaList}")

        logger.info(f"飞牛: 待下载文件列表：{self.dramaList}")

        # 构建下载路径
        self.download_path = f"{self.save_path}/{self.processMediaType(self.dramaList[0])}" if "quark" == self.cloud_type else f"{self.save_path}/{self.processMediaType(self.dramaList[0])}"
        logger.info(f"飞牛: 保存路径：{self.download_path}")

        try:
            # 创建WebSocket连接
            async with await self.connect_to_websocket() as websocket:
                try:
                    # 启动Ping任务保持连接
                    ping_task = asyncio.create_task(send_ping(websocket))
                    
                    # 发送获取RSA公钥请求
                    await websocket.send(f'{{"reqid":"{self.preReqid}00000000000000000001","req":"util.crypto.getRSAPub"}}')
                    
                    aes_key = None
                    aes_iv = None
                    secret = None
                    
                    while True:
                        response = await wss_connect(websocket)
                        
                        # 处理RSA公钥响应
                        if "-----BEGIN PUBLIC KEY-----" in response:
                            try:
                                data = json.loads(response)
                                pub_key = data.get("pub")
                                si = data.get("si")
                                if pub_key and si:
                                    aes_key, aes_iv = await self.authenticate(websocket, pub_key, si)
                                else:
                                    error_info = "未收到完整的公钥信息"
                                    logger.error(error_info)
                                    break
                            except json.JSONDecodeError as e:
                                error_info = f"公钥响应解析失败: {str(e)}"
                                logger.error(error_info)
                                break
                        
                        # 处理认证响应
                        elif self.preReqid+"00000000000000000002" in response:
                            try:
                                data = json.loads(response)
                                secret_str = data.get('secret')
                                if secret_str:
                                    decrypted_secret = decrypt(secret_str, aes_key, aes_iv)
                                    secret = base64.b64decode(decrypted_secret)
                                    logger.success("用户认证成功")
                                    
                                    if self.cloud_file_path:
                                        logger.debug("未启用分组处理")
                                        # 创建下载文件夹
                                        create_folder_result,create_folder_msg = await self.create_folder(websocket, secret, self.download_path+"/"+self.keyword)
                                        if create_folder_result:
                                            # 执行文件下载
                                            download_files_task_result,download_files_task_msg = await self.download_files_task(websocket, secret, self.download_path, self.dramaList)
                                            if download_files_task_result:
                                                logger.success("文件下载任务已提交")
                                                return True,"文件下载任务已提交"
                                            else:
                                                error_info = download_files_task_msg
                                                logger.error(error_info)
                                                break
                                        else:
                                            error_info = create_folder_msg
                                            break
                                    else:
                                        # 分组处理
                                        logger.debug(f"file_list:{self.dramaList}")
                                        grouped_paths = self.group_file_paths(self.dramaList, self.keyword)
                                        isBreak = False
                                        for sub_path, paths in grouped_paths.items():
                                            download_path = self.download_path+"/"+self.keyword+sub_path
                                            # 创建下载文件夹
                                            create_folder_result,create_folder_msg = await self.create_folder(websocket, secret, download_path)
                                            if create_folder_result:
                                                # 执行文件下载
                                                download_files_task_result,download_files_task_msg = await self.download_files_task(websocket, secret, download_path, paths)
                                                if download_files_task_result:
                                                    logger.success("文件下载任务已提交")
                                                else:
                                                    error_info = download_files_task_msg
                                                    logger.error(error_info)
                                                    isBreak = True
                                            else:
                                                error_info = create_folder_msg
                                                isBreak = True
                                            
                                        if isBreak:
                                            break
                                        else:
                                            return True,"文件下载任务已提交"
                                else:
                                    error_info = "认证响应中缺少secret字段"
                                    logger.error(error_info)
                                    break
                            except Exception as e:
                                error_info = f"认证处理异常: {str(e)}"
                                logger.error(error_info)
                                break
                        
                        # 处理Ping响应
                        elif "pong" in response:
                            continue
                        
                        # 处理未知响应
                        else:
                            if response:  # 避免空响应日志
                                logger.debug(f"收到其他响应: {response}")
                    
                except asyncio.CancelledError:
                    logger.warning("任务被取消")
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("WebSocket连接正常关闭")
                except websockets.exceptions.ConnectionClosedError as e:
                    error_info = f"WebSocket连接异常关闭: {str(e)}"
                    logger.error(error_info)
                except Exception as e:
                    error_info = f"下载任务异常: {str(e)}"
                    logger.error(error_info)
                finally:
                    # 取消Ping任务
                    if 'ping_task' in locals():
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
                    # 确保连接关闭
                    await close_websocket(websocket)
        except OSError as e:
            error_info = f"连接失败: {str(e)}，请检查飞牛系统URL和网络连接"
            logger.error(error_info)
        except Exception as e:
            error_info = f"未知错误: {str(e)}"
            logger.error(error_info)

        return False, error_info

# # 示例调用（需在异步环境中使用）
# async def example_usage():
#     # 初始化飞牛实例
#     fn_os = Fnos()
#     # 设置任务参数
#     fn_os.keyword = "测试任务"
#     fn_os.dramaList = [
#         "/path/to/file1.mp4",
#         "/path/to/file2.mkv"
#     ]
#     # 执行异步下载
#     await fn_os.run_async()

# # 如果作为脚本直接运行
# if __name__ == "__main__":
#     # 安装loguru日志处理器
#     logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
#     # 运行示例
#     asyncio.run(example_usage())

fn_os = Fnos()