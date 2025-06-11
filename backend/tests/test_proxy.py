import asyncio
import aiohttp
from loguru import logger
from utils.http_client import http_client
from utils.config_manager import config_manager

async def test_proxy():
    try:
        # 打印当前代理配置
        config = config_manager.get_config()
        logger.info(f"当前代理配置: http://{config['proxy_host']}:{config['proxy_port']}")
        
        # 测试访问一个国内网站（不需要代理）
        logger.info("测试访问百度...")
        response = await http_client.get("https://www.baidu.com")
        logger.info("百度连接成功")
        
        # 测试访问需要代理的网站
        logger.info("测试访问 Google...")
        try:
            response = await http_client.get(
                "https://www.google.com",
                timeout=10
            )
            logger.info("Google 连接成功")
        except Exception as e:
            logger.error(f"访问 Google 失败: {str(e)}")
        
        # 获取当前 IP
        logger.info("获取当前 IP 地址...")
        try:
            response = await http_client.get(
                "https://api.ipify.org?format=json",
                timeout=10
            )
            logger.info(f"当前IP地址: {response}")
        except Exception as e:
            logger.error(f"获取 IP 地址失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
    finally:
        await http_client.close()

if __name__ == "__main__":
    logger.info("开始代理测试...")
    asyncio.run(test_proxy()) 