# 微信公众号爬虫 (WeMediaSpider)

<div align="center">

![Logo](gnivu-cfd69-001.ico)

一个功能强大的微信公众号文章爬虫工具，支持图形界面操作，让数据采集变得简单高效。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ 功能特性

- 🎨 **现代化 GUI 界面** - 基于 PyQt6 和 Fluent Design，支持暗黑主题
- 🔐 **二维码登录** - 安全便捷的微信扫码登录
- 🔍 **智能搜索** - 支持关键词搜索公众号文章
- 📝 **内容抓取** - 批量抓取文章标题、链接、正文和图片
- 💾 **结果导出** - 支持导出为 JSON、Markdown 等多种格式
- ⚡ **异步处理** - 高效的异步爬取机制
- 🗄️ **智能缓存** - 内置缓存系统，减少重复请求
- 📊 **历史管理** - 完整的搜索历史记录功能

## 📋 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.8 或更高版本
- **浏览器**: Chrome（用于 Selenium 自动化）
- **网络**: 稳定的网络连接

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/vag-Zhao/WeMediaSpider.git
cd WeMediaSpider

# 安装依赖包
pip install -r requirements.txt
```

### 运行程序

```bash
# 开发环境运行
python run_gui.py
```

### 使用打包版本

如果你想创建独立可执行文件：

```bash
# 构建可执行文件
cd script
build.bat

# 创建安装程序
build_installer.bat
```

## 📖 使用说明

### 1. 登录

- 启动程序后，在登录页面使用微信扫描二维码
- 等待登录成功提示

### 2. 搜索文章

- 在搜索页面输入关键词
- 设置搜索参数（页数、时间范围等）
- 点击开始搜索

### 3. 查看结果

- 在结果页面查看抓取的文章列表
- 可以预览文章内容
- 支持批量导出

### 4. 设置配置

在 `config.json` 中可以调整以下参数：

```json
{
  "max_pages": 1,              // 最大抓取页数
  "request_interval": 10,      // 请求间隔（秒）
  "max_workers": 5,            // 最大并发数
  "include_content": true,     // 是否包含正文
  "cache_expire_hours": 96     // 缓存过期时间（小时）
}
```

## 📁 项目结构

```
WeMediaSpider/
├── gui/                      # GUI 图形界面模块
│   ├── pages/               # 各个功能页面
│   │   ├── login_page.py   # 登录页面
│   │   ├── content_search_page.py  # 搜索页面
│   │   ├── results_page.py         # 结果页面
│   │   └── ...
│   ├── main_window.py      # 主窗口
│   ├── workers.py          # 工作线程
│   └── ...
├── spider/                  # 爬虫核心模块
│   ├── wechat/             # 微信爬虫
│   │   ├── login.py        # 登录逻辑
│   │   ├── scraper.py      # 爬取逻辑
│   │   ├── async_utils.py  # 异步工具
│   │   └── ...
│   └── log/                # 日志模块
├── script/                  # 构建脚本
│   ├── build.bat           # PyInstaller 打包脚本
│   └── installer.nsi       # NSIS 安装脚本
├── config.json             # 配置文件
├── requirements.txt        # 依赖列表
└── run_gui.py             # 程序入口
```

## 🛠️ 技术栈

- **GUI 框架**: PyQt6 + PyQt-Fluent-Widgets
- **浏览器自动化**: Selenium
- **异步处理**: asyncio + aiohttp
- **HTML 解析**: BeautifulSoup4 + lxml
- **内容转换**: markdownify
- **日志**: loguru
- **打包工具**: PyInstaller + NSIS

## ⚙️ 配置说明

### 环境变量

无需配置特殊环境变量，程序开箱即用。

### 浏览器驱动

程序会自动管理 ChromeDriver，无需手动下载。

### 缓存管理

- 缓存文件存储在项目目录的 `.cache/` 文件夹中
- 默认缓存有效期为 96 小时
- 可通过配置文件调整缓存策略

## 📝 注意事项

1. **合法使用**: 请遵守相关法律法规，仅用于学习和研究目的
2. **频率限制**: 建议设置合理的请求间隔，避免被限制
3. **数据安全**: 登录信息会被加密缓存，请妥善保管
4. **网络要求**: 需要稳定的网络连接才能正常使用

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 Python GUI 框架
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - 优雅的 Fluent Design 组件库
- [Selenium](https://www.selenium.dev/) - 浏览器自动化工具

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/vag-Zhao/WeMediaSpider/issues)
- 发送邮件到：zgs3344@hunnu.edu.cn

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！**

</div>
