import requests
import json
import time
import os
import webbrowser
import subprocess
import platform
import pyttsx3
import speech_recognition as sr
import pyautogui
import psutil
import sounddevice as sd
from pycaw.pycaw import AudioUtilities

# ========== 你的API密钥配置 ==========
SILICONFLOW_API_KEY = "sk-ttntybdztnyafubffyqeiozobvkmyzgynvwtemcewrfasmhe"
OPENROUTER_API_KEY = "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"
MODEL_SILICONFLOW = "Qwen/Qwen3-8B"
MODEL_OPENROUTER = "deepseek/deepseek-r1:free"

# 默认平台（1=SiliconFlow, 2=OpenRouter）
current_platform = 1

# ========== 语音引擎初始化 ==========
engine = pyttsx3.init()
recognizer = sr.Recognizer()

# ========== 助手系统提示词 ==========
system_prompt = """
你是一个智能语音助手，能够帮助用户完成各种任务，包括回答问题、控制设备、打开应用程序等。回复要友好、有用、简洁。
"""

# ========== 语音朗读 ==========
def speak(text):
    """电脑朗读文本"""
    print(f"🤖 {text}")
    engine.say(text)
    engine.runAndWait()

# ========== 语音监听 ==========
def listen():
    """电脑监听麦克风"""
    with sr.Microphone() as source:
        print("️ 我在听...（5秒内说话）")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio, language='zh-CN')
            print(f"你说: {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"❌ 识别错误: {e}")
            return ""

# ========== 系统控制功能 ==========
def system_control(command):
    """高级系统控制功能"""
    command = command.lower()
    
    # 音量控制
    if "调大音量" in command or "音量+" in command:
        pyautogui.press('volumeup')
        return "✅ 音量已调大"
    
    elif "调小音量" in command or "音量-" in command:
        pyautogui.press('volumedown')
        return "✅ 音量已调小"
    
    elif "静音" in command:
        pyautogui.press('volumemute')
        return "✅ 已静音"
    
    # 屏幕亮度（Windows专用）
    elif "调亮" in command and platform.system() == "Windows":
        os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 80)")
        return "✅ 亮度已调亮"
    
    elif "调暗" in command and platform.system() == "Windows":
        os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 30)")
        return "✅ 亮度已调暗"
    
    # 锁屏/关机
    elif "锁定电脑" in command or "锁屏" in command:
        if platform.system() == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        return "✅ 电脑已锁定"
    
    elif "关机" in command:
        os.system("shutdown /s /t 5" if platform.system() == "Windows" else "sudo shutdown -h now")
        return "⚠️ 电脑将在5秒后关机"
    
    # 窗口控制
    elif "回到桌面" in command:
        pyautogui.hotkey('win', 'd')
        return "✅ 已回到桌面"
    
    elif "切换窗口" in command:
        pyautogui.hotkey('alt', 'tab')
        return "✅ 已切换窗口"
    
    # 多媒体控制
    elif "暂停" in command or "继续播放" in command:
        pyautogui.press('space')
        return "✅ 播放状态已切换"
    
    elif "快进" in command:
        pyautogui.press('right')
        return "✅ 已快进"
    
    elif "后退" in command:
        pyautogui.press('left')
        return "✅ 已后退"
    
    elif "全屏" in command:
        pyautogui.press('f11')
        return "✅ 已切换全屏"
    
    return None  # 如果不是系统指令，返回None

# ========== 音频设备切换功能 ==========
def get_audio_devices():
    """获取系统音频设备列表"""
    devices = AudioUtilities.GetSpeakers()
    device_list = []
    for device in devices:
        device_list.append({
            'name': device.GetFriendlyName(),
            'id': device.GetId()
        })
    return device_list

def switch_microphone(device_name):
    """切换麦克风设备"""
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device_name.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                sd.default.device[0] = i  # 设置默认输入设备
                return f"✅ 已切换到麦克风: {device['name']}"
        return f"❌ 未找到包含 '{device_name}' 的麦克风设备"
    except Exception as e:
        return f"❌ 切换麦克风失败: {e}"

def switch_speaker(device_name):
    """切换扬声器设备"""
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device_name.lower() in device['name'].lower() and device['max_output_channels'] > 0:
                sd.default.device[1] = i  # 设置默认输出设备
                return f"✅ 已切换到扬声器: {device['name']}"
        return f"❌ 未找到包含 '{device_name}' 的扬声器设备"
    except Exception as e:
        return f"❌ 切换扬声器失败: {e}"

# ========== 本地功能 ==========
def open_application(app_name):
    app_name = app_name.lower()
    
    # ========== 希沃全系应用映射表 ==========
    app_map = {
        # 希沃核心教学三件套
        "白板": "EasiNote5.exe",
        "希沃白板": "EasiNote5.exe",
        "班级优化": "EasiCare.exe",
        "班级优化大师": "EasiCare.exe",
        "授课助手": "SeewoLink.exe",
        "希沃授课助手": "SeewoLink.exe",
        
        # 希沃官网全系软件
        "品课": "seewoPinco.exe",
        "希沃品课": "seewoPinco.exe",
        "管家": "Seewo Service.exe",
        "希沃管家": "Seewo Service.exe",
        "易启学学生": "SeewoYiQiXueStudent.exe",
        "易启学教师": "SeewoYiQiXueTeacher.exe",
        "快传": "SeewoFileTransfer.exe",
        "希沃快传": "SeewoFileTransfer.exe",
        "电脑助手": "SeewoPCAssistant.exe",
        "希沃电脑助手": "SeewoPCAssistant.exe",
        "希象传屏": "ExceedShare.exe",
        "幼教助手": "SeewoEduAssistant.exe",
        "视频展台": "EasiCamera.exe",
        "轻白板": "EasiNote3C.exe",
        "远程互动": "AirTeach.exe",
        "导播助手": "EasiDirector.exe",
        "易课堂": "EasiClassPC.exe",
        "集控": "SeewoHugoSetup.exe",
        "掌上看班": "SeewoHugoKanbanWebApp.exe",
        "反馈器": "EasiQuizManager.exe",
        "轻录播": "EasiRecorder.exe",
        "剪辑师": "EasiAction.exe",
        "希沃输入法": "seewoinput.exe",
        "智能笔": "SmartpenServiceSetup.exe",
        
        # 系统自带应用
        "计算器": "calc.exe" if platform.system() == "Windows" else "Calculator",
        "记事本": "notepad.exe" if platform.system() == "Windows" else "TextEdit",
        "浏览器": "chrome.exe" if platform.system() == "Windows" else "Google Chrome",
        "音乐": "spotify.exe" if platform.system() == "Windows" else "Spotify",
        "设置": "ms-settings:" if platform.system() == "Windows" else "Settings",
        "cmd": "cmd.exe" if platform.system() == "Windows" else "Terminal",
    }
    
    try:
        if app_name in app_map:
            target = app_map[app_name]
            subprocess.Popen(target, shell=True)
            return f"正在启动: {app_name}"
        else:
            subprocess.Popen(app_name, shell=True)
            return f"尝试启动: {app_name}"
    except Exception as e:
        return f"启动失败: {e}"

def open_website(site_name):
    site_map = {
        "百度": "https://www.baidu.com",
        "谷歌": "https://www.google.com",
        "b站": "https://www.bilibili.com",
        "淘宝": "https://www.taobao.com",
    }
    
    if site_name in site_map:
        webbrowser.open(site_map[site_name])
        return f"已打开: {site_name}"
    else:
        return f"暂不支持打开: {site_name}"

# ========== 调用AI API ==========
def call_ai_api(user_input):
    headers = {"Content-Type": "application/json"}
    
    if current_platform == 1:  # SiliconFlow
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers["Authorization"] = f"Bearer {SILICONFLOW_API_KEY}"
        data = {
            "model": MODEL_SILICONFLOW,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "stream": False
        }
    else:  # OpenRouter
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"
        data = {
            "model": MODEL_OPENROUTER,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"API错误: {response.status_code}"
    except Exception as e:
        return f"请求失败: {e}"

# ========== 指令处理器 ==========
def process_command(user_input):
    # 修复点：global声明必须放在函数最前面
    global current_platform
    
    user_input = user_input.lower()
    
    # 1. 先检查是否是系统控制指令
    system_result = system_control(user_input)
    if system_result:
        return system_result
    
    # 2. 切换麦克风
    if "切换麦克风" in user_input:
        # 提取设备名称（例如：切换麦克风 内置麦克风）
        parts = user_input.split("切换麦克风")
        if len(parts) > 1 and parts[1].strip():
            device_name = parts[1].strip()
            return switch_microphone(device_name)
        else:
            return "❌ 请指定要切换的麦克风设备名称，例如：切换麦克风 内置麦克风"
    
    # 3. 切换扬声器
    elif "切换扬声器" in user_input:
        parts = user_input.split("切换扬声器")
        if len(parts) > 1 and parts[1].strip():
            device_name = parts[1].strip()
            return switch_speaker(device_name)
        else:
            return "❌ 请指定要切换的扬声器设备名称，例如：切换扬声器 内置扬声器"
    
    # 4. 打开应用程序
    elif "打开" in user_input and ("应用" in user_input or "软件" in user_input):
        app = user_input.replace("打开", "").replace("应用", "").replace("软件", "").strip()
        return open_application(app)
    
    # 5. 打开网站
    elif "打开" in user_input and ("网站" in user_input or "网页" in user_input):
        site = user_input.replace("打开", "").replace("网站", "").replace("网页", "").strip()
        return open_website(site)
    
    # 6. 数字切换平台
    elif "1" in user_input or "一号" in user_input:
        current_platform = 1
        return "✅ 已切换到 1号平台 (SiliconFlow)"
    
    elif "2" in user_input or "二号" in user_input:
        current_platform = 2
        return "✅ 已切换到 2号平台 (OpenRouter)"
    
    # 7. 其他问题交给AI
    else:
        return call_ai_api(user_input)

# ========== 主循环 ==========
def main():
    print(" 电脑版智能语音助手已启动！（全功能版）")
    print(" 唤醒词: '小小助手'")
    print(" 当前平台: 1号 (SiliconFlow)")
    print(" 支持功能: 希沃全系软件、音量控制、亮度调节、多媒体控制等")
    speak("小小助手已就绪，请说话")

    while True:
        # 监听语音
        user_text = listen()
        if not user_text:
            continue

        if "退出" in user_text or "结束" in user_text:
            speak("再见")
            break

        # 唤醒检测 - 修改为"小小助手"
        if "小小助手" in user_text:
            real_question = user_text.replace("小小助手", "").strip()
            if real_question:
                print("🤔 处理中...")
                result = process_command(real_question)
                speak(result)  # 电脑会朗读回复
        else:
            print("⚠️ 请说'小小助手'唤醒我")

if __name__ == "__main__":
    main()
