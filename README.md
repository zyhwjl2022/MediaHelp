# MediaHelper

<div align="center">
    <img src="/frontend/apps/web-antd/public/icon.png" alt="MediaHelper Logo" width="200" height="150" />
    <h1>MediaHelper</h1>
    <p>🎬 一站式媒体资源管理助手</p>
    
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://hub.docker.com/r/rongyunmu/mediahelp)
    
</div>

## 📖 简介

MediaHelper 是一个强大的媒体资源管理工具，支持多个主流网盘的资源转存和管理功能。它能帮助你更高效地管理和组织你的媒体资源。

## ✨ 核心特性

- 🔍 **智能资源搜索**
  - 集成 TG 频道资源搜索
  - 支持动态配置搜索参数
  - 快速定位所需资源

- 📱 **多网盘支持**
  - 支持夸克网盘
  - 支持天翼云盘
  - 统一管理界面

- 🔐 **自动化转存**
  - 支持定时任务配置
  - 自动化资源转存
  - 批量处理能力

- 🎭 **媒体管理** (开发中)
  - Emby 集成支持
  - 媒体库管理
  - 更多功能持续开发

## 🚀 快速开始

### Docker 部署

```bash
docker run -d \
  -p 3300:80 \
  -v /你的配置目录:/app/backend/config \
  rongyunmu/mediahelp
```

### 默认账户
- 用户名：`admin`
- 密码：`admin`

> ⚠️ 注意：建议私有化部署，因为涉及个人网盘信息安全

## 🤝 支持项目

如果您觉得这个项目对您有帮助，可以通过以下方式支持我们：

1. 给项目一个 ⭐️ Star
2. 扫描下方二维码进行打赏支持

<div align="center">
    <img src="wiki/img/bea32a55-6743-468a-9193-10d52b068729.png" alt="打赏二维码" width="200"/>
</div>

## 📝 免责声明

- 本项目为个人兴趣开发，旨在提高网盘使用效率
- 项目仅封装现有网盘 API，未进行任何破解行为
- 所有数据均来自网盘官方 API
- 开发者不对网盘内容及 API 变动负责
- 仅供学习与交流使用，未经授权禁止商业使用
- 严禁用于任何非法用途

## 📄 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

---

<div align="center">
    <p>Made with ❤️ by MediaHelper Team</p>
</div> 