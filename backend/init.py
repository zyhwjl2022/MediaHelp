import argparse
import os
from utils.init_db import init_database

def parse_args():
    parser = argparse.ArgumentParser(description='MediaHelper Backend 数据库初始化脚本')
    parser.add_argument(
        '--env',
        type=str,
        choices=['dev', 'prod'],
        default='dev',
        help='运行环境: dev (开发环境) 或 prod (生产环境)'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 设置环境变量
    os.environ['ENV'] = args.env
    
    print(f"开始初始化数据库 (环境: {args.env})")
    init_database()
    print("数据库初始化完成")

if __name__ == "__main__":
    main() 