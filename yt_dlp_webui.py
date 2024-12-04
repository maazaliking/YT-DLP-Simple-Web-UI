import gradio as gr
import re
import os
import subprocess
import time
from yt_dlp import YoutubeDL
import urllib.parse
import datetime
import os
import json
import shutil
from typing import List, Tuple
from starlette.responses import FileResponse  # 添加导入
from fastapi import FastAPI
import uvicorn

# 在 Gradio 应用中添加自定义路由
app = FastAPI()
@app.get("/ping")
async def ping():
    return {"message": "pong"}
#子目录
@app.get("/file/{folder}/{filename}")
async def serve_file(folder: str, filename: str):
    file_path = get_video_path(folder, filename)
    print(f"Requested file path: {file_path}")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    else:
        print(f"File not found: {file_path}")
        return gr.Response(status_code=404, content={"detail": f"File not allowed: {folder}/{filename}."})
#主目录
@app.get("/file/{filename}")
async def serve_root_file(filename: str):
    file_path = get_video_path("", filename)
    print(f"Requested root file path: {file_path}")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    else:
        print(f"File not found: {file_path}")
        return {"detail": f"File not found: {filename}"}


os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
# 全局变量
BASE_VIDEO_DIR = os.path.join(os.getcwd(), "videos")
should_stop = False
current_process = None


def get_file(filename):
    """创建文件下载响应"""
    # 检查filename中是否包含文件夹路径
    if '/' in filename:
        folder, name = filename.split('/', 1)
        file_path = os.path.join(BASE_VIDEO_DIR, folder, name)
    else:
        file_path = os.path.join(BASE_VIDEO_DIR, filename)
        
    if os.path.exists(file_path):
        return file_path
    return None
# 添加新的辅助函数
def get_video_folders() -> List[str]:
    """获取视频目录下的所有文件夹"""
    folders = [""]  # 空字符串代表根目录
    for item in os.listdir(BASE_VIDEO_DIR):
        if os.path.isdir(os.path.join(BASE_VIDEO_DIR, item)):
            folders.append(item)
    return sorted(folders)

def get_videos_in_folder(folder: str) -> List[Tuple[str, float, str]]:
    """获取指定文件夹中的视频文件信息"""
    folder_path = os.path.join(BASE_VIDEO_DIR, folder)
    videos = []
    video_extensions = ('.mp4', '.webm', '.mkv', '.avi')
    
    try:
        for file in os.listdir(folder_path):
            if file.lower().endswith(video_extensions):
                file_path = os.path.join(folder_path, file)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
                mod_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                       time.localtime(os.path.getmtime(file_path)))
                videos.append((file, size_mb, mod_time))
    except Exception as e:
        print(f"Error reading folder {folder}: {str(e)}")
        return []
    
    return sorted(videos)

def delete_video_file(folder: str, filename: str) -> str:
    """删除视频文件"""
    try:
        file_path = os.path.join(BASE_VIDEO_DIR, folder, filename)
        os.remove(file_path)
        return f"Successfully deleted: {filename}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"
def get_video_path(folder: str, filename: str) -> str:
    """获取视频文件的完整路径"""
    if folder.strip():
        return os.path.abspath(os.path.join(BASE_VIDEO_DIR, folder, filename))
    return os.path.abspath(os.path.join(BASE_VIDEO_DIR, filename))
# 确保基本视频目录存在
if not os.path.exists(BASE_VIDEO_DIR):
    os.makedirs(BASE_VIDEO_DIR)

# 加载配置文件
config_file_path = os.path.join(os.getcwd(), 'config.json')
if os.path.exists(config_file_path):
    with open(config_file_path, 'r') as f:
        config = json.load(f)
else:
    config = {
        'proxy': '',
        'video_format': '',
        'merge_format': '',
        'output_template': '%(id)s',
        'extra_params': '',
        'username': '',
        'password': ''
    }

def clear_video_preview():
    return None
def validate_youtube_url(url):
    if not url.strip():
        return False, "URL cannot be empty."
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        if 'youtube.com' in domain:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                return True, video_id
            else:
                return False, "No video ID found in the URL."
        else:
            return False, "Invalid domain. Please enter a valid YouTube video URL."
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"
def get_video_info(url, proxy):
    is_valid, message = validate_youtube_url(url)
    if not is_valid:
        return message

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    if proxy:
        ydl_opts['proxy'] = proxy

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'N/A')
            channel = info.get('channel', 'N/A')
            duration = info.get('duration', 'N/A')
            view_count = info.get('view_count', 'N/A')
            upload_date = info.get('upload_date', 'N/A')
            
            result = f"ID : {message}\nTitle: {title}\nChannel: {channel}\nDuration: {duration} seconds\nViews: {view_count}\nUpload Date: {upload_date}"
            
            result += "\n\nAvailable Formats:\n"
            for format in info.get('formats', []):
                format_id = format.get('format_id', 'N/A')
                ext = format.get('ext', 'N/A')
                resolution = format.get('resolution', 'N/A')
                fps = format.get('fps', 'N/A')
                result += f"Format ID: {format_id}, Extension: {ext}, Resolution: {resolution}, FPS: {fps}\n"
            
            return result
    except Exception as e:
        return f"An error occurred: {str(e)}"

def download_video(url, video_format, merge_format, output_template, proxy, save_dir, extra_params):
    global should_stop, current_process

    # 验证 URL
    is_valid, message = validate_youtube_url(url)
    if not is_valid:
        yield message, None
        return
    video_id= message
    should_stop = False
    
    # 确定保存目录
    if save_dir.strip():
        video_dir = os.path.join(BASE_VIDEO_DIR, save_dir.strip())
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
    else:
        video_dir = BASE_VIDEO_DIR

    output_file = os.path.join(video_dir, output_template)
    cmd = [
        "yt-dlp",
        "-f", video_format,
        "--merge-output-format", merge_format,
        "-o", output_file,
        url
    ]
    
    # 添加扩展参数
    if extra_params.strip():
        cmd.extend(extra_params.split())

    if proxy.strip():  # 确保proxy不为空
        cmd.extend(["--proxy", proxy])
    print(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    try:
        current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            if should_stop:
                current_process.terminate()
                print("Download stopped by user.")
                yield "Download stopped by user.", None
                break
            
            output = current_process.stdout.readline()
            if output == '' and current_process.poll() is not None:
                break
            if output:
                print(output.strip())  # 直接打印到控制台
                elapsed_time = time.time() - start_time
                yield f"Downloading... Elapsed time: {elapsed_time:.2f} seconds\n{output.strip()} ({time.strftime('%Y-%m-%d %H:%M:%S')})", None
        
        if not should_stop:
            current_process.wait()
            if current_process.returncode == 0:
                message = f"Download completed successfully. Video saved in: {video_dir} ({time.strftime('%Y-%m-%d %H:%M:%S')})"
                # 查找包含video_id的视频文件
                video_file = None
                for file in os.listdir(video_dir):
                    if file.endswith(('.mp4', '.webm', '.mkv')) and video_id in file:
                        video_file = file
                        break
                if video_file:
                    video_path = f"/file/{save_dir}/{video_file}" if save_dir.strip() else f"/file/{video_file}"
                    # 生成HTML视频预览标签
                    preview_html = f"""
                    <div style="max-width: 800px; margin: 0 auto;">
                        <video controls style="width: 100%;">
                            <source src="{video_path}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    """
                    yield message, preview_html
                else:
                    yield message, ""
    except Exception as e:
        error_message = f"An error occurred: {str(e)} ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        print(error_message)
        yield error_message, None
    finally:
        current_process = None
        
def stop_download():
    global should_stop, current_process
    should_stop = True
    if current_process:
        current_process.terminate()
        print("Download stopped. The process has been terminated.")
        return "Download stopped. The process has been terminated."
    else:
        return "No active download to stop."

def update_proxy(proxy):
    if not proxy.strip():
        return "", "Not using proxy"
    return proxy, f"Current proxy: {proxy}"
def load_default_videos():
    """加载默认的视频列表（主目录）"""
    videos = get_videos_in_folder("")
    html_content = create_video_list_html("", videos)
    return html_content
# Gradio界面
with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown("# 🎥 YouTube Video Downloader and Info Extractor")
    gr.Markdown(f"📁 Videos will be saved in subdirectories of: {BASE_VIDEO_DIR}")
    
    proxy = gr.State(config.get('proxy', ''))

    with gr.Row():
        proxy_input = gr.Textbox(
            label="Proxy Settings",
            value=config.get('proxy', ''),
        )
        proxy_update_btn = gr.Button("Update Proxy", variant="secondary")
        
    current_proxy_display = gr.Textbox(
        label="Current Proxy",
        value=f"Current proxy: {config.get('proxy', '')}",
        interactive=False
    )
    def update_proxy_state(new_proxy):
        proxy_value, display_value = update_proxy(new_proxy)
        config['proxy'] = proxy_value
        with open(config_file_path, 'w') as f:
            json.dump(config, f)
        return proxy_value, display_value
    proxy_update_btn.click(update_proxy_state, inputs=[proxy_input], outputs=[proxy, current_proxy_display])
    with gr.Tabs():

        #下载视频
        with gr.TabItem("Download Video"):
            with gr.Row():
                with gr.Column(scale=3):
                    url_input = gr.Textbox(label="YouTube URL", placeholder="Enter YouTube URL here...")
                with gr.Column(scale=1):
                    download_button = gr.Button("🚀 Download Video", variant="primary")
                    stop_button = gr.Button("🛑 Stop Download", variant="stop")
            
            with gr.Row():
                with gr.Column():
                    save_dir = gr.Textbox(
                        label="Save Directory",
                        value=lambda: datetime.datetime.now().strftime("%m%d"),
                        placeholder="Leave empty for root directory"
                    )
                    output_template = gr.Textbox(
                        label="Output Template",
                        value=config.get('output_template', '%(id)s-%(title)s.%(ext)s')
                    )
                with gr.Column():
                    # 将 Video Format 的文本框改为可编辑的下拉选择框
                    video_format = gr.Dropdown(
                        label="Video Format",
                        allow_custom_value=True,
                        value=config.get('video_format', 'bestvideo[height<=480]+bestaudio/best[height<=480]'),
                        choices=[
                            "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                            "bestvideo[height<=720]+bestaudio/best[height<=720]",
                            "bestvideo[height<=480]+bestaudio/best[height<=480]"
                        ]
                     
                    )
                    merge_format = gr.Textbox(
                        label="Merge Output Format",
                        value=config.get('merge_format', 'mp4')
                    )
            
            extra_params = gr.Textbox(
                label="Extra Parameters",
                value=config.get('extra_params', '--restrict-filenames --abort-on-unavailable-fragment')
            )
            
            output = gr.Textbox(label="Download Status", lines=10)
            video_preview = gr.HTML(label="Video Preview")
  
                
        # 视频信息
        with gr.TabItem("Video Info"):
            with gr.Row():
                with gr.Column(scale=3):
                    info_url_input = gr.Textbox(label="YouTube URL", placeholder="Enter YouTube URL here...")
                with gr.Column(scale=1):
                    info_button = gr.Button("ℹ️ Get Video Info", variant="secondary")
            
            info_output = gr.Textbox(label="Video Information", lines=15)
        #视频管理
        with gr.TabItem("Video Manager"):
            with gr.Row():
                with gr.Column(scale=1):
                    folder_dropdown = gr.Dropdown(
                        label="Select Folder",
                        choices=get_video_folders(),
                        value="",
                        interactive=True
                    )
                    refresh_button = gr.Button("🔄 Refresh", variant="secondary")
                    
                    # 使用HTML组件显示视频列表
                    video_list = gr.HTML()
        
        # 添加页脚
        with gr.Row():
            gr.Markdown("---")  # 添加一条分隔线
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("[YT-DLP](https://github.com/yt-dlp/yt-dlp)")  
            with gr.Column(scale=1):
                gr.Markdown("[YT-DLP-Simple-Web-UI](https://github.com/zergtant/YT-DLP-Simple-Web-UI)") 
            with gr.Column(scale=1):
                gr.Markdown("[YouTube](https://www.youtube.com)")
                
    # 更新视频列表的函数
    def update_video_list(folder):
        """更新视频列表"""
        videos = get_videos_in_folder(folder)
        html_content = create_video_list_html(folder, videos)  # 传递folder参数
        return html_content
    def create_video_list_html(folder, videos):
        """生成视频列表的HTML"""
        if not videos:
            return '<div class="p-4 text-center text-gray-500">当前文件夹没有视频文件</div>'
        
        html = '<div class="p-4"><div class="grid gap-4">'
        
        for video in videos:
            filename, size_mb, mod_time = video
            download_link = f"/file/{filename}" if not folder else f"/file/{folder}/{filename}"
            html += f'''
            <div class="bg-white rounded-lg shadow-sm border p-4 flex items-center justify-between">
                <div class="flex-1">
                    <h3 class="font-medium text-gray-900 mb-1">{filename}</h3>
                    <div class="text-sm text-gray-500 space-y-1">
                        <p>Size: {size_mb:.2f} MB</p>
                        <p>Modified: {mod_time}</p>
                    </div>
                </div>
                <a href="{download_link}" 
                download
                class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                style="text-decoration:none;">
                    📥 Download
                </a>
            </div>
            '''
        
        html += '</div></div>'
        return html

    def preview_selected_video(folder: str, evt: gr.SelectData) -> str:
        """
        处理视频预览
        folder: 当前选择的文件夹
        evt: Gradio的选择事件数据
        """
        try:
            row_idx,col_idx = evt.index
            print(evt.index)
            if col_idx is None or col_idx!=0:
                print("Invalid column index")
                return None
            # 第一列是文件名
            filename = evt.value
            
            # 构建完整的视频路径
            video_path = get_video_path(folder, filename)
            print(f"Selected file: {filename}")
            print(f"Loading video from path: {video_path}")
            return video_path
        except Exception as e:
            print(f"Error in preview_selected_video: {str(e)}")
            return None

    # 删除视频的函数
    def delete_selected_video(folder: str, evt: gr.SelectData) -> Tuple[str, List[Tuple[str, float, str]], None]:
        if evt.index[0] is None:
            return "No video selected", None, None
        filename = evt.value[0]
        status = delete_video_file(folder, filename)
        updated_videos = get_videos_in_folder(folder)
        return status, updated_videos, None

    # 刷新文件夹列表
    def refresh_folders():
        """刷新文件夹列表"""
        folders = get_video_folders()
        return gr.update(choices=folders, value="")  # Use gr.update instead of gr.Dropdown.update

    # 设置事件处理
    folder_dropdown.change(
        update_video_list,
        inputs=[folder_dropdown],
        outputs=[video_list]
    )
    refresh_button.click(
        refresh_folders,
        outputs=[folder_dropdown]
    )
    download_button.click(
        download_video,
        inputs=[url_input, video_format, merge_format, output_template, proxy, save_dir, extra_params],
        outputs=[output, video_preview]
    )
    stop_button.click(
        stop_download,
        outputs=output
    )
    info_button.click(
        get_video_info,
        inputs=[info_url_input, proxy],
        outputs=info_output
    )
  
    iface.load(
        fn=load_default_videos,
        outputs=video_list,
    )
    if config["username"] and config["password"]:
        app = gr.mount_gradio_app(app, iface, path="/",auth=(config["username"], config["password"]))
    else:
        app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
