这份 `README.md` 文档完整涵盖了项目的**核心功能、安装步骤、使用指南以及技术原理**。您可以直接将以下内容保存为 `README.md` 文件，放在项目根目录下。

---

# ☁️ OneDrive Gallery Pro (本地高清索引版)

一个轻量级、高性能的 OneDrive 与 SharePoint 直链管理工具。
它不仅是一个链接记录器，更是一个**本地化的资源管理器**。通过在本地生成高清缩略图，实现了秒级预览，同时智能处理各种复杂的云盘直链转换。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

## ✨ 核心功能

*   **🚀 智能直链转换**：
    *   **SharePoint**：自动识别企业版链接，正则提取 Token，强制转换为 `download.aspx` 直链，且**自动直连**（不走代理）以保证满速。
    *   **OneDrive 个人版**：自动跟踪短链 (`1drv.ms`) 跳转，智能识别并替换 `/redir` 网关为 `/download`，**彻底解决 403 Forbidden 反爬问题**。
*   **🖼️ 本地高清索引**：
    *   添加链接时自动下载原图，本地压缩为 **1280px 高清预览图**。
    *   以后查看无需消耗云端流量，加载速度飞快。
    *   支持鼠标**悬停放大**预览，无遮挡交互。
*   **⚡ 网络分流与代理**：
    *   内置代理设置（支持 HTTP/SOCKS5），解决个人版 OneDrive 无法连接的问题。
    *   **智能分流**：SharePoint 链接自动绕过代理，个人版链接自动走代理。
*   **🏷️ 标签与搜索**：
    *   支持多标签管理，文件名/标签实时搜索。
*   **📂 真实文件名解析**：
    *   自动解析 HTTP Header (`Content-Disposition`) 和 URL 路径，完美还原中文文件名。
*   **📋 一键复制**：
    *   支持复制 **直链 URL** 或 **Markdown 格式** (`![name](url)`)。

## 🛠️ 安装与运行

### 1. 环境准备
确保您的电脑已安装 [Python 3](https://www.python.org/downloads/)。

### 2. 安装依赖
在项目文件夹中打开终端（CMD/PowerShell），运行以下命令安装必要的库：

```bash
pip install requests Pillow
```

### 3. 启动程序
*   **方法 A**：直接双击运行app.py。
*   **方法 B**：在终端中运行 `python app.py`。

启动成功后，浏览器会自动访问：`http://localhost:8000`

## 📖 使用指南

### 1. 添加图片
1.  点击右上角的 **"＋ 添加新资源"**。
2.  粘贴 OneDrive 或 SharePoint 的分享链接（支持嵌入代码中的链接、短链等）。
3.  (可选) 输入标签，如 `风景 素材`。
4.  点击 **"开始处理"**。
    *   *程序会自动下载图片、生成缩略图并保存记录。成功后会自动弹出复制窗口。*

### 2. 设置代理 (解决个人版无法下载)
如果您的网络无法直接访问 OneDrive 个人版，请点击右上角的 **"⚙️ 设置"**：
1.  输入您的代理地址，例如：
    *   Clash (HTTP): `http://127.0.0.1:7890`
    *   v2rayN (HTTP): `http://127.0.0.1:10809`
2.  点击 **"⚡ 测试连接"** 确保代理可用。
3.  点击 **"保存配置"**。
    *   *注：SharePoint 链接会自动忽略此代理，强制直连。*

### 3. 复制链接
*   **点击图片**：弹出复制选项框，选择复制直链或 Markdown。
*   **悬停预览**：鼠标停留在图片上，卡片会放大预览。

### 4. 删除资源
*   点击卡片右上角的 **红色 ×**。
*   程序会**彻底删除**数据库记录以及本地的缩略图文件，不留垃圾。

## 📂 项目结构

```text
OneDriveGalleryPro/
├── app.py           # 后端核心 (Python HTTP Server)
├── index.html       # 前端界面 (HTML/CSS/JS)
├── db.json          # 数据存储 (自动生成)
├── config.json      # 代理配置 (自动生成)
├── thumbnails/      # 缩略图文件夹 (自动生成)
└── 启动.bat         # 快捷启动脚本
```

## ❓ 常见问题

**Q: SharePoint 链接显示 "Failed to fetch"？**
A: 通常是因为网络超时。新版已优化为强制直连，请检查您的网络是否能直接访问 SharePoint。

**Q: 个人版链接添加时显示 "403 Forbidden"？**
A: 程序已内置自动修复机制（替换 `redir` 为 `download`），且会模拟浏览器 Header。如果依然报错，请检查代理设置是否正确。

**Q: 缩略图看起来像马赛克或错位？**
A: 这是因为 Pillow 库的 `optimize` 参数在某些环境下不兼容。最新版已默认关闭此参数，确保图片清晰。

## 📄 许可证

MIT License. 这是一个开源项目，您可以随意修改和分发。
