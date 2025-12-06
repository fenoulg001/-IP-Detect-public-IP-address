# 🌐 网络监控专业版 (Network Monitor Pro)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()
[![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet)](https://github.com/TomSchimansky/CustomTkinter)

> 一个现代化、高颜值的本地网络出口监控工具。支持代理透视、本地数据库解析、高分屏显示。

---

## 📸 界面预览

![软件运行截图](screenshot.png)

---

## 📖 项目简介

**Network Monitor Pro** 是一个基于 Python `CustomTkinter` 开发的桌面端网络监控工具。

与传统的 IP 查询网页不同，本项目旨在解决“**开了代理不知道自己 IP 到底在哪**”以及“**网页查询有缓存不准确**”的痛点。它通过 HTTP/HTTPS 请求穿透您的代理服务器（Clash, v2ray 等），结合**本地 MaxMind 离线数据库**，实现毫秒级的 IP 归属地、运营商 (ISP) 及 ASN 信息查询。

### ✨ 核心亮点

* **📺 4K 高清适配**：强制开启 Windows High-DPI 支持，字体在 2K/4K 屏幕上锐利清晰，告别模糊。
* **🕵️ 代理透视**：支持读取系统代理或指定端口，精准检测 VPN/代理后的**真实落地 IP**。
* **🚀 极速本地库**：内置 GeoLite2 (City & ASN) 数据库引擎，查询不依赖第三方 API 接口，保护隐私且无频率限制。
* **🎨 现代 UI**：基于暗黑模式的卡片式设计，自带实时刷新倒计时和动态状态指示灯。
* **📋 一键复制**：点击 IP 地址区域即可自动复制到剪贴板。
* **📦 单文件运行**：提供 PyInstaller 打包脚本，可生成不依赖 Python 环境的独立 `.exe` 文件。

---

## 🛠️ 安装与使用

### 1. 克隆仓库
```bash
git clone [https://github.com/你的用户名/NetworkMonitor.git](https://github.com/你的用户名/NetworkMonitor.git)
cd NetworkMonitor
2. 安装依赖
Bash

pip install -r requirements.txt
3. 配置数据库 (⚠️ 重要)
由于 MaxMind 许可协议限制，本项目不包含 .mmdb 数据库文件，您需要手动下载并放入项目根目录：

下载 GeoLite2-City.mmdb 和 GeoLite2-ASN.mmdb。

官方地址：MaxMind 官网

或在 GitHub 搜索关键字："GeoLite2-City.mmdb download"

确保这两个文件位于项目根目录下，文件名必须完全一致。

4. 代理设置 (可选)
打开 NetworkMonitor_Proxy.py 文件，顶部配置区域可修改代理：

Python

# 留空 {} 则自动读取系统代理 (如 VPN 全局模式/Clash Tun模式)
PROXIES = {} 

# 如果您只开启了代理软件但没开TUN，需要指定端口 (例如 Clash 默认 7890)
# PROXIES = {
#     "http":  "[http://127.0.0.1:7890](http://127.0.0.1:7890)",
#     "https": "[http://127.0.0.1:7890](http://127.0.0.1:7890)",
# }
5. 启动运行
Bash

python NetworkMonitor_Proxy.py
📦 打包为 EXE (Windows)
如果您想制作一个发给朋友即开即用的 .exe 程序，请在终端执行以下命令（需要安装 PyInstaller）：

PowerShell

pyinstaller --noconfirm --onefile --windowed --clean --name "NetworkMonitor" --collect-all customtkinter --add-data "GeoLite2-ASN.mmdb;." --add-data "GeoLite2-City.mmdb;." "NetworkMonitor_Proxy.py"
打包成功后，可执行文件位于 dist 文件夹内。

📜 致谢与许可
本项目使用了 MaxMind 创建的 GeoLite2 数据，可从 https://www.maxmind.com 获取。

UI 框架: CustomTkinter

开源协议: MIT License
