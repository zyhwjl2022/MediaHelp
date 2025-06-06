import argparse
import os
import uvicorn

def parse_args():
    parser = argparse.ArgumentParser(description='MediaHelper Backend 服务启动脚本')
    parser.add_argument(
        '--env',
        type=str,
        choices=['dev', 'prod'],
        default='dev',
        help='运行环境: dev (开发环境) 或 prod (生产环境)'
    )
    parser.add_argument(
        '--host',
        type=str,
        help='主机地址 (可选，将覆盖配置文件中的设置)'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='端口号 (可选，将覆盖配置文件中的设置)'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 设置环境变量
    os.environ['ENV'] = args.env
    
    # 导入配置（在设置环境变量后导入）
    from crud.config import settings
    
    # 确定主机和端口
    host = args.host or settings.server_config['host']
    port = args.port or settings.server_config['port']
    
    # 启动服务
    print(f"启动服务于 {host}:{port}")
    print(f"运行环境: {args.env}")
    print(f"调试模式: {settings.app_config['debug']}")
    
    uvicorn.run(
        "main:app",  # 使用导入字符串而不是应用实例
        host=host,
        port=port,
        reload=settings.app_config['debug']
    )

if __name__ == '__main__':
    main() 