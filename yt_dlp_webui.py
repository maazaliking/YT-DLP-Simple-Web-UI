import gradio as gr
import re
import os
import subprocess
import time
from yt_dlp import YoutubeDL
import urllib.parse
import datetime
import os
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
# 全局变量
BASE_VIDEO_DIR = os.path.join(os.getcwd(), "videos")
should_stop = False
current_process = None

# 确保基本视频目录存在
if not os.path.exists(BASE_VIDEO_DIR):
    os.makedirs(BASE_VIDEO_DIR)


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
                for file in os.listdir(video_dir):
                    if file.endswith(('.mp4', '.webm', '.mkv')) and video_id in file  :  # 添加其他可能的视频格式
                        video_path = os.path.join(video_dir, file)
                        yield message, video_path
                        return 
                yield message, None
            else:
                message = f"Download failed with return code: {current_process.returncode}( {time.strftime('%Y-%m-%d %H:%M:%S')})"
                print(message)
                yield message, None
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

# Gradio界面
with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown("# 🎥 YouTube Video Downloader and Info Extractor")
    gr.Markdown(f"📁 Videos will be saved in subdirectories of: {BASE_VIDEO_DIR}")
    
    proxy = gr.State("socks5://127.0.0.1:8082")
    
    with gr.Row():
        proxy_input = gr.Textbox(label="Proxy Settings", value="socks5://127.0.0.1:8082")
        proxy_update_btn = gr.Button("Update Proxy", variant="secondary")
        
    current_proxy_display = gr.Textbox(label="Current Proxy", value="Current proxy: socks5://127.0.0.1:8082", interactive=False)
    def update_proxy_state(new_proxy):
        proxy_value, display_value = update_proxy(new_proxy)
        return proxy_value, display_value
    proxy_update_btn.click(update_proxy_state, inputs=[proxy_input], outputs=[proxy, current_proxy_display])
    with gr.Tabs():
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
                    output_template = gr.Textbox(label="Output Template", value="%(id)s-%(title)s.%(ext)s")
                with gr.Column():
                    # 将 Video Format 的文本框改为可编辑的下拉选择框
                    video_format = gr.Dropdown(
                        label="Video Format",
                        value="bestvideo[height<=480]+bestaudio/best[height<=480]",
                        choices=[
                            "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                            "bestvideo[height<=720]+bestaudio/best[height<=720]",
                            "bestvideo[height<=480]+bestaudio/best[height<=480]"
                        ]
                     
                    )
                    merge_format = gr.Textbox(label="Merge Output Format", value="mp4")
            
            extra_params = gr.Textbox(label="Extra Parameters", value="--restrict-filenames --abort-on-unavailable-fragment")
            
            output = gr.Textbox(label="Download Status", lines=10)
            with gr.Column():
                with gr.Row():
                    gr.Markdown("## Video Preview")
                    clear_preview_button = gr.Button("🗑️ Clear Preview", variant="secondary", size="sm")
                video_preview = gr.Video(label="", interactive=False)
  
                

        with gr.TabItem("Video Info"):
            with gr.Row():
                with gr.Column(scale=3):
                    info_url_input = gr.Textbox(label="YouTube URL", placeholder="Enter YouTube URL here...")
                with gr.Column(scale=1):
                    info_button = gr.Button("ℹ️ Get Video Info", variant="secondary")
            
            info_output = gr.Textbox(label="Video Information", lines=15)
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
    clear_preview_button.click(
    clear_video_preview,
    outputs=video_preview
)   

if __name__ == "__main__":
    iface.launch(share=False,auth=("username", "password"))