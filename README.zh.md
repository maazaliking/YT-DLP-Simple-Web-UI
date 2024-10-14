# YT-DLP-Simple-Web-UI

> **注意**：本项目（包括代码和此 README）是由 Anthropic 公司开发的 AI 语言模型 Claude 的生成的。虽然内容已针对此特定项目进行了定制，但它展示了 AI 在软件开发和文档编写方面的潜力。

YT-DLP-Simple-Web-UI 是流行的 YouTube 下载工具 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的用户友好型 Web 界面。本项目提供了一个基于 Gradio 的简单图形用户界面，用于下载 YouTube 视频和提取视频信息。

## 功能特点

- 🎥 支持自定义格式选项的 YouTube 视频下载
- ℹ️ 提取 YouTube 视频的详细信息
- 🌐 支持代理设置
- 🎛️ 为高级用户提供进阶选项
- 🖼️ 视频预览功能
- 🛑 能够停止正在进行的下载

## 截图

### 主界面
![主界面](placeholder_main_interface.png)
*描述：YT-DLP-Simple-Web-UI 的主界面，显示 URL 输入框、下载选项和状态显示。*

### 视频信息
![视频信息](placeholder_video_info.png)
*描述：视频信息标签页，显示 YouTube 视频的详细元数据。*



## 安装

1. 克隆此仓库：
   ```
   git clone https://github.com/yourusername/YT-DLP-Simple-Web-UI.git
   cd YT-DLP-Simple-Web-UI
   ```

2. 安装所需依赖：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行应用程序：
   ```
   python yt_dlp_webui.py
   ```

2. 打开网页浏览器，访问控制台中显示的 URL（通常是 `http://127.0.0.1:7860`）。

3. 输入 YouTube URL 并根据需要自定义下载设置。

4. 点击"下载视频"开始下载过程。

## 配置

- **代理设置**：在"代理设置"字段中输入您的代理 URL，然后点击"更新代理"。
- **视频格式**：自定义视频格式字符串（默认：`bestvideo[height<=1080]+bestaudio/best[height<=1080]`）
- **输出模板**：修改输出文件名模板（默认：`%(id)s-%(title)s.%(ext)s`）
- **额外参数**：根据需要添加任何其他 yt-dlp 命令行参数

## 高级用法

### 自定义输出目录
您可以为下载指定自定义输出目录。只需在"保存目录"字段中输入所需的子目录名称。视频将被保存在基本视频目录的子目录中。

### 格式选择
对于高级用户，您可以使用 yt-dlp 格式字符串微调视频格式选择。例如：
- `bestvideo[height<=720]+bestaudio/best[height<=720]`：最高质量的 720p 视频
- `worstvideo+worstaudio/worst`：可用的最低质量（用于测试）

### 下载故障排除
如果遇到下载问题，请尝试以下方法：
1. 如果您在防火墙后面，请更新代理设置
2. 使用"获取视频信息"功能检查可用格式
3. 如果遇到网络问题，尝试在额外参数中添加 `--force-ipv4`

## 贡献

欢迎贡献！以下是您可以为 YT-DLP-Simple-Web-UI 做出贡献的方式：

1. Fork 这个仓库
2. 创建新的分支（`git checkout -b feature/AmazingFeature`）
3. 提交您的更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 打开一个 Pull Request

请确保您的代码符合项目的编码标准，并包含适当的测试。

## 许可证

本项目采用 MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) 提供核心下载功能
- [Gradio](https://www.gradio.app/) 提供 Web UI 框架
- Anthropic 公司的 Claude AI 协助生成本项目

## 免责声明

本项目仅用于教育目的。使用此工具时，请遵守 YouTube 的服务条款和版权法。

## 未来增强

- [ ] 批量下载功能
- [ ] 保存配置选项


随时欢迎您的反馈和改进建议！
