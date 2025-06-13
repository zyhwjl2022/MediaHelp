"""天翼云盘错误类定义"""

class Cloud189Error(Exception):
    """天翼云盘基础错误类"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class AuthError(Cloud189Error):
    """认证错误"""
    pass

class InvalidRefreshTokenError(AuthError):
    """无效的刷新令牌"""
    pass

class ShareError(Cloud189Error):
    """分享相关错误"""
    pass

class FileError(Cloud189Error):
    """文件操作错误"""
    pass

class NetworkError(Cloud189Error):
    """网络请求错误"""
    pass

class TaskError(Cloud189Error):
    """任务相关错误"""
    pass

def check_error(response: dict) -> None:
    """
    检查响应中是否包含错误
    :param response: 响应数据
    :raises: Cloud189Error 当响应中包含错误时
    """
    # 检查认证相关错误
    if "result" in response and "msg" in response:
        result = response["result"]
        msg = response["msg"]
        
        if result == 0:
            return
        elif result == -117:
            raise InvalidRefreshTokenError(msg)
        else:
            raise AuthError(msg)
            
    # 检查API错误
    if "res_code" in response:
        code = response["res_code"]
        msg = response.get("res_message", "未知错误")
        
        if code != 0:
            raise Cloud189Error(msg, str(code)) 