import os
import re
import yaml
import json
import time
import hmac
import base64
import urllib
import hashlib
import requests
import smtplib
import threading
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

class NotifyManager:
    _instance = None
    _config: Optional[Dict[str, Any]] = None
    _notify_functions: List[Callable] = []
    _default_config = {
        # 通知配置
        "HITOKOTO": False,  # 启用一言（随机句子）

        # Bark 通知
        "BARK_PUSH": "",  # bark IP 或设备码，例：https://api.day.app/DxHcxxxxxRxxxxxxcm/
        "BARK_ARCHIVE": "",  # bark 推送是否存档
        "BARK_GROUP": "",  # bark 推送分组
        "BARK_SOUND": "",  # bark 推送声音
        "BARK_ICON": "",  # bark 推送图标
        "BARK_LEVEL": "",  # bark 推送时效性
        "BARK_URL": "",  # bark 推送跳转URL

        # 控制台输出
        "CONSOLE": True,

        # 钉钉机器人
        "DD_BOT_SECRET": "",  # 钉钉机器人的 DD_BOT_SECRET
        "DD_BOT_TOKEN": "",  # 钉钉机器人的 DD_BOT_TOKEN

        # 飞书机器人
        "FSKEY": "",  # 飞书机器人的 FSKEY

        # Telegram 机器人
        "TG_BOT_TOKEN": "",  # Telegram 机器人的 token
        "TG_USER_ID": "",  # 接收消息的 Telegram 用户 ID
        "TG_API_HOST": "",  # Telegram API 接口地址
        "TG_PROXY_HOST": "",  # 代理服务器地址
        "TG_PROXY_PORT": "",  # 代理服务器端口
        "TG_PROXY_AUTH": "",  # 代理服务器认证

        # 邮件通知
        "SMTP_SERVER": "",  # SMTP 服务器地址
        "SMTP_SSL": "true",  # 是否使用 SSL
        "SMTP_EMAIL": "",  # 发件人邮箱
        "SMTP_PASSWORD": "",  # 发件人密码
        "SMTP_NAME": "",  # 发件人名称
        "SMTP_EMAIL_TO": "",  # 收件人邮箱，多个用逗号分隔
        "SMTP_NAME_TO": "",  # 收件人名称，多个用逗号分隔

        # Server酱
        "PUSH_KEY": "",  # server酱的 PUSH_KEY

        # 企业微信应用
        "QYWX_AM": "",  # 企业微信应用的 QYWX_AM，依次填入 corpid,corpsecret,touser(注:多个成员ID使用|隔开),agentid,media_id(选填，不填默认文本消息类型)

        # 企业微信机器人
        "QYWX_KEY": "",  # 企业微信机器人的 webhook key

        # PushDeer
        "DEER_KEY": "",  # PushDeer 的 PUSHDEER_KEY
        "DEER_URL": "",  # PushDeer 的自建服务器地址，可选

        # PushPlus
        "PUSH_PLUS_TOKEN": "",  # PushPlus 的 token
        "PUSH_PLUS_USER": "",  # PushPlus 的群组编码，不填仅发送给自己

        # QQ/TG/微信群机器人
        "GOBOT_URL": "",  # go-cqhttp的API地址，如 http://127.0.0.1/send_private_msg 或 /send_group_msg
        "GOBOT_QQ": "",  # go-cqhttp的QQ号或群号，GOBOT_URL设置 /send_private_msg 时填入 user_id=个人QQ，/send_group_msg 时填入 group_id=QQ群
        "GOBOT_TOKEN": "",  # go-cqhttp的access_token

        # Gotify
        "GOTIFY_URL": "",  # gotify地址，如 https://push.example.de:8080
        "GOTIFY_TOKEN": "",  # gotify的消息应用token
        "GOTIFY_PRIORITY": 0,  # 推送消息优先级，默认为0

        # iGot
        "IGOT_PUSH_KEY": "",  # iGot 的 IGOT_PUSH_KEY

        # wxpusher
        "WXPUSHER_APP_TOKEN": "",  # wxpusher的appToken
        "WXPUSHER_TOPIC_IDS": "",  # wxpusher的主题ID，多个用逗号分隔
        "WXPUSHER_UIDS": "",  # wxpusher的用户ID，多个用逗号分隔
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotifyManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化通知管理器"""
        self.config_path = Path(__file__).parent.parent / "config" / "notify.yaml"
        self._ensure_config_dir()
        self._load_config()
        self._init_notify_functions()

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        config_dir = self.config_path.parent
        if not config_dir.exists():
            config_dir.mkdir(parents=True)

    def _load_config(self) -> None:
        """从文件加载配置"""
        if not self.config_path.exists():
            self._config = self._default_config.copy()
            self._save_config()
            print(f"已创建默认配置文件：{self.config_path}")
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                # 检查是否有新增的配置项
                updated = False
                for key, value in self._default_config.items():
                    if key not in self._config:
                        self._config[key] = value
                        updated = True
                if updated:
                    self._save_config()
                    print(f"配置文件已更新：{self.config_path}")

    def _save_config(self) -> None:
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True)

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self._config.update(new_config)
        self._save_config()
        # 重新初始化通知函数
        self._init_notify_functions()

    def _init_notify_functions(self) -> None:
        """初始化通知函数列表"""
        self._notify_functions = []
        
        # 控制台输出
        if str(self._config.get("CONSOLE", "false")).lower() != "false":
            self._notify_functions.append(self._console)
            
        # Bark 通知
        if self._config.get("BARK_PUSH"):
            self._notify_functions.append(self._bark)
            
        # 钉钉机器人
        if self._config.get("DD_BOT_TOKEN") and self._config.get("DD_BOT_SECRET"):
            self._notify_functions.append(self._dingding)
            
        # 飞书机器人
        if self._config.get("FSKEY"):
            self._notify_functions.append(self._feishu)
            
        # Telegram 机器人
        if self._config.get("TG_BOT_TOKEN") and self._config.get("TG_USER_ID"):
            self._notify_functions.append(self._telegram)
            
        # SMTP 邮件
        if (self._config.get("SMTP_SERVER") and 
            self._config.get("SMTP_SSL") and 
            self._config.get("SMTP_EMAIL") and 
            self._config.get("SMTP_PASSWORD") and 
            self._config.get("SMTP_NAME")):
            self._notify_functions.append(self._smtp)

        # Server酱
        if self._config.get("PUSH_KEY"):
            self._notify_functions.append(self._server_chan)

        # 企业微信应用
        if self._config.get("QYWX_AM"):
            self._notify_functions.append(self._wecom_app)

        # 企业微信机器人
        if self._config.get("QYWX_KEY"):
            self._notify_functions.append(self._wecom_bot)

        # PushDeer
        if self._config.get("DEER_KEY"):
            self._notify_functions.append(self._pushdeer)

        # PushPlus
        if self._config.get("PUSH_PLUS_TOKEN"):
            self._notify_functions.append(self._pushplus)

        # QQ/TG/微信群机器人
        if self._config.get("GOBOT_URL") and self._config.get("GOBOT_QQ"):
            self._notify_functions.append(self._go_cqhttp)

        # Gotify
        if self._config.get("GOTIFY_URL") and self._config.get("GOTIFY_TOKEN"):
            self._notify_functions.append(self._gotify)

        # iGot
        if self._config.get("IGOT_PUSH_KEY"):
            self._notify_functions.append(self._igot)

        # wxpusher
        if self._config.get("WXPUSHER_APP_TOKEN") and (
            self._config.get("WXPUSHER_TOPIC_IDS") or self._config.get("WXPUSHER_UIDS")
        ):
            self._notify_functions.append(self._wxpusher)

    def _console(self, title: str, content: str) -> None:
        """控制台输出"""
        print(f"\n{title}\n\n{content}")

    def _bark(self, title: str, content: str) -> None:
        """Bark 通知"""
        try:
            if self._config.get("BARK_PUSH").startswith('http'):
                url = f'{self._config.get("BARK_PUSH")}'
            else:
                url = f'https://api.day.app/{self._config.get("BARK_PUSH")}'

            data = {
                "title": title,
                "body": content,
            }
            
            # 添加可选参数
            bark_params = {
                "BARK_ARCHIVE": "isArchive",
                "BARK_GROUP": "group",
                "BARK_SOUND": "sound",
                "BARK_ICON": "icon",
                "BARK_LEVEL": "level",
                "BARK_URL": "url",
            }
            
            for key, param in bark_params.items():
                if value := self._config.get(key):
                    data[param] = value

            response = requests.post(
                url=url,
                headers={"Content-Type": "application/json;charset=utf-8"},
                data=json.dumps(data),
                timeout=15
            ).json()

            if response["code"] == 200:
                print("Bark 推送成功！")
            else:
                print(f"Bark 推送失败：{response.get('message', '未知错误')}")
        except Exception as e:
            print(f"Bark 推送异常：{str(e)}")

    def _dingding(self, title: str, content: str) -> None:
        """钉钉机器人通知"""
        try:
            timestamp = str(round(time.time() * 1000))
            secret = self._config.get("DD_BOT_SECRET")
            secret_enc = secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

            url = f'https://oapi.dingtalk.com/robot/send?access_token={self._config.get("DD_BOT_TOKEN")}&timestamp={timestamp}&sign={sign}'
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }

            response = requests.post(
                url=url,
                headers={"Content-Type": "application/json;charset=utf-8"},
                data=json.dumps(data),
                timeout=15
            ).json()

            if response["errcode"] == 0:
                print("钉钉推送成功！")
            else:
                print(f"钉钉推送失败：{response.get('errmsg', '未知错误')}")
        except Exception as e:
            print(f"钉钉推送异常：{str(e)}")

    def _feishu(self, title: str, content: str) -> None:
        """飞书机器人通知"""
        try:
            url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self._config.get("FSKEY")}'
            
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n\n{content}"
                }
            }

            response = requests.post(
                url=url,
                headers={"Content-Type": "application/json;charset=utf-8"},
                data=json.dumps(data),
                timeout=15
            ).json()

            if response["code"] == 0:
                print("飞书推送成功！")
            else:
                print(f"飞书推送失败：{response.get('msg', '未知错误')}")
        except Exception as e:
            print(f"飞书推送异常：{str(e)}")

    def _telegram(self, title: str, content: str) -> None:
        """Telegram 机器人通知"""
        try:
            if self._config.get("TG_API_HOST"):
                url = f"{self._config.get('TG_API_HOST')}/bot{self._config.get('TG_BOT_TOKEN')}/sendMessage"
            else:
                url = f"https://api.telegram.org/bot{self._config.get('TG_BOT_TOKEN')}/sendMessage"

            data = {
                "chat_id": str(self._config.get("TG_USER_ID")),
                "text": f"{title}\n\n{content}",
                "disable_web_page_preview": "true"
            }

            # 设置代理
            proxies = None
            if self._config.get("TG_PROXY_HOST") and self._config.get("TG_PROXY_PORT"):
                proxy_auth = self._config.get("TG_PROXY_AUTH", "")
                if proxy_auth:
                    proxy_auth = f"{proxy_auth}@"
                proxy_url = f"http://{proxy_auth}{self._config.get('TG_PROXY_HOST')}:{self._config.get('TG_PROXY_PORT')}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }

            response = requests.post(
                url=url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
                proxies=proxies,
                timeout=15
            ).json()

            if response["ok"]:
                print("Telegram 推送成功！")
            else:
                print(f"Telegram 推送失败：{response.get('description', '未知错误')}")
        except Exception as e:
            print(f"Telegram 推送异常：{str(e)}")

    def _smtp(self, title: str, content: str) -> None:
        """SMTP 邮件通知"""
        try:
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = formataddr(
                (Header(self._config.get("SMTP_NAME"), 'utf-8').encode(),
                 self._config.get("SMTP_EMAIL"))
            )

            # 设置收件人
            if not self._config.get("SMTP_EMAIL_TO"):
                smtp_email_to = [self._config.get("SMTP_EMAIL")]
                message['To'] = formataddr(
                    (Header(self._config.get("SMTP_NAME"), 'utf-8').encode(),
                     self._config.get("SMTP_EMAIL"))
                )
            else:
                smtp_email_to = self._config.get("SMTP_EMAIL_TO").split(",")
                smtp_name_to = self._config.get("SMTP_NAME_TO", "").split(",")
                message['To'] = ",".join([
                    formataddr((Header(smtp_name_to[i] if len(smtp_name_to) > i else "", 'utf-8').encode(), email_to))
                    for i, email_to in enumerate(smtp_email_to)
                ])

            message['Subject'] = Header(title, 'utf-8')

            # 连接 SMTP 服务器并发送
            smtp_server = (smtplib.SMTP_SSL if self._config.get("SMTP_SSL") == "true" 
                         else smtplib.SMTP)(self._config.get("SMTP_SERVER"))
            smtp_server.login(
                self._config.get("SMTP_EMAIL"),
                self._config.get("SMTP_PASSWORD")
            )
            smtp_server.sendmail(
                self._config.get("SMTP_EMAIL"),
                smtp_email_to,
                message.as_bytes()
            )
            smtp_server.close()
            print("SMTP 邮件推送成功！")
        except Exception as e:
            print(f"SMTP 邮件推送异常：{str(e)}")

    def _server_chan(self, title: str, content: str) -> None:
        """Server酱通知"""
        try:
            push_key = self._config.get("PUSH_KEY")
            match = re.match(r"sctp(\d+)t", push_key)
            if match:
                num = match.group(1)
                url = f'https://{num}.push.ft07.com/send/{push_key}.send'
            else:
                url = f'https://sctapi.ftqq.com/{push_key}.send'

            data = {
                "text": title,
                "desp": content.replace("\n", "\n\n")
            }

            response = requests.post(url, data=data).json()

            if response.get("errno") == 0 or response.get("code") == 0:
                print("Server酱推送成功！")
            else:
                print(f"Server酱推送失败：{response.get('message', '未知错误')}")
        except Exception as e:
            print(f"Server酱推送异常：{str(e)}")

    def _wecom_app(self, title: str, content: str) -> None:
        """企业微信应用通知"""
        try:
            qywx_am = self._config.get("QYWX_AM")
            if not qywx_am:
                return

            params = qywx_am.split(',')
            if len(params) < 4:
                print("企业微信应用参数不足")
                return

            corpid = params[0]
            corpsecret = params[1]
            touser = params[2]
            agentid = params[3]
            media_id = params[4] if len(params) > 4 else None

            # 获取 access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}"
            response = requests.get(token_url).json()
            access_token = response.get("access_token")

            if not access_token:
                print(f"企业微信应用获取 access_token 失败：{response.get('errmsg', '未知错误')}")
                return

            # 发送消息
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            data = {
                "touser": touser,
                "agentid": agentid,
                "msgtype": "mpnews" if media_id else "text",
            }

            if media_id:
                data["mpnews"] = {
                    "articles": [{
                        "title": title,
                        "thumb_media_id": media_id,
                        "content": content.replace('\n', '<br/>'),
                        "digest": content
                    }]
                }
            else:
                data["text"] = {
                    "content": f"{title}\n\n{content}"
                }

            response = requests.post(send_url, json=data).json()

            if response["errcode"] == 0:
                print("企业微信应用推送成功！")
            else:
                print(f"企业微信应用推送失败：{response.get('errmsg', '未知错误')}")
        except Exception as e:
            print(f"企业微信应用推送异常：{str(e)}")

    def _wecom_bot(self, title: str, content: str) -> None:
        """企业微信机器人通知"""
        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self._config.get('QYWX_KEY')}"
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }

            response = requests.post(url, json=data).json()

            if response["errcode"] == 0:
                print("企业微信机器人推送成功！")
            else:
                print(f"企业微信机器人推送失败：{response.get('errmsg', '未知错误')}")
        except Exception as e:
            print(f"企业微信机器人推送异常：{str(e)}")

    def _pushdeer(self, title: str, content: str) -> None:
        """PushDeer通知"""
        try:
            url = (self._config.get("DEER_URL") or "https://api2.pushdeer.com") + f"/message/push"
            data = {
                "pushkey": self._config.get("DEER_KEY"),
                "text": title,
                "desp": content,
                "type": "markdown"
            }

            response = requests.post(url, data=data).json()

            if response["code"] == 0:
                print("PushDeer推送成功！")
            else:
                print(f"PushDeer推送失败：{response.get('message', '未知错误')}")
        except Exception as e:
            print(f"PushDeer推送异常：{str(e)}")

    def _pushplus(self, title: str, content: str) -> None:
        """PushPlus通知"""
        try:
            url = "http://www.pushplus.plus/send"
            data = {
                "token": self._config.get("PUSH_PLUS_TOKEN"),
                "title": title,
                "content": content,
                "topic": self._config.get("PUSH_PLUS_USER", ""),
                "template": "html"
            }

            response = requests.post(url, json=data).json()

            if response["code"] == 200:
                print("PushPlus推送成功！")
            else:
                print(f"PushPlus推送失败：{response.get('msg', '未知错误')}")
        except Exception as e:
            print(f"PushPlus推送异常：{str(e)}")

    def _go_cqhttp(self, title: str, content: str) -> None:
        """go-cqhttp通知"""
        try:
            url = f'{self._config.get("GOBOT_URL")}?access_token={self._config.get("GOBOT_TOKEN")}&{self._config.get("GOBOT_QQ")}&message=标题:{title}\n内容:{content}'
            response = requests.get(url).json()

            if response["status"] == "ok":
                print("go-cqhttp推送成功！")
            else:
                print(f"go-cqhttp推送失败：{response.get('message', '未知错误')}")
        except Exception as e:
            print(f"go-cqhttp推送异常：{str(e)}")

    def _gotify(self, title: str, content: str) -> None:
        """Gotify通知"""
        try:
            url = f'{self._config.get("GOTIFY_URL")}/message?token={self._config.get("GOTIFY_TOKEN")}'
            data = {
                "title": title,
                "message": content,
                "priority": self._config.get("GOTIFY_PRIORITY", 0)
            }

            response = requests.post(url, data=data).json()

            if response.get("id"):
                print("Gotify推送成功！")
            else:
                print(f"Gotify推送失败：{response}")
        except Exception as e:
            print(f"Gotify推送异常：{str(e)}")

    def _igot(self, title: str, content: str) -> None:
        """iGot通知"""
        try:
            url = f'https://push.hellyw.com/{self._config.get("IGOT_PUSH_KEY")}'
            data = {
                "title": title,
                "content": content
            }

            response = requests.post(
                url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data
            ).json()

            if response["ret"] == 0:
                print("iGot推送成功！")
            else:
                print(f"iGot推送失败：{response.get('errMsg', '未知错误')}")
        except Exception as e:
            print(f"iGot推送异常：{str(e)}")

    def _wxpusher(self, title: str, content: str) -> None:
        """wxpusher通知"""
        try:
            url = "http://wxpusher.zjiecode.com/api/send/message"
            data = {
                "appToken": self._config.get("WXPUSHER_APP_TOKEN"),
                "content": f"{title}\n\n{content}",
                "summary": title,  # 消息摘要，显示在微信聊天页面或者模版消息卡片上
                "contentType": 1,  # 1表示文字消息，2表示html，3表示markdown
            }

            # 添加发送目标
            if self._config.get("WXPUSHER_TOPIC_IDS"):
                data["topicIds"] = [int(i) for i in self._config.get("WXPUSHER_TOPIC_IDS").split(",")]
            if self._config.get("WXPUSHER_UIDS"):
                data["uids"] = self._config.get("WXPUSHER_UIDS").split(",")

            response = requests.post(url, json=data).json()

            if response["code"] == 1000:
                print("wxpusher推送成功！")
            else:
                print(f"wxpusher推送失败：{response.get('msg', '未知错误')}")
        except Exception as e:
            print(f"wxpusher推送异常：{str(e)}")

    def send(self, title: str, content: str) -> None:
        """发送通知"""
        if not content:
            print(f"{title} 推送内容为空！")
            return

        # 添加一言
        if str(self._config.get("HITOKOTO", "false")).lower() != "false":
            try:
                hitokoto_resp = requests.get("https://v1.hitokoto.cn/", timeout=5).json()
                content += f"\n\n{hitokoto_resp['hitokoto']}"
            except:
                pass

        # 创建线程发送通知
        threads = [
            threading.Thread(target=func, args=(title, content), name=func.__name__)
            for func in self._notify_functions
        ]
        
        # 启动所有线程
        for t in threads:
            t.start()
            
        # 等待所有线程完成
        for t in threads:
            t.join()

# 创建全局通知管理器实例
notify_manager = NotifyManager() 