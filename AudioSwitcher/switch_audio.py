import os
import subprocess
import keyboard
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import time
import sys
import warnings
import threading
import winshell
from win32com.client import Dispatch

import comtypes
from pycaw.pycaw import AudioUtilities
from pycaw.constants import DEVICE_STATE, EDataFlow

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "app_config.txt")

last_switch_time = 0
_com_thread_local = threading.local()


def ensure_com_initialized():
    """pycaw(comtypes)はスレッド毎にCOM初期化が必要。二重初期化は無害に握りつぶす"""
    if not getattr(_com_thread_local, "initialized", False):
        try:
            comtypes.CoInitialize()
        except OSError:
            pass  # 既に初期化済みのスレッド
        _com_thread_local.initialized = True

def kill_previous_instances():
    """裏で既に動いている古いAudioSwitcherのプロセスをすべて安全に終了させる"""
    try:
        current_pid = os.getpid()
        target_process = "AudioSwitcher.exe"
        if getattr(sys, 'frozen', False):
            subprocess.run(
                f'taskkill /F /IM {target_process} /FI "PID ne {current_pid}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except Exception:
        pass

def get_device_info():
    """pycaw(Windows Core Audio API)経由でデバイスリストと現在のデフォルトを取得（外部exe不要）"""
    try:
        ensure_com_initialized()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            devices = AudioUtilities.GetAllDevices(
                data_flow=EDataFlow.eRender.value,
                device_state=DEVICE_STATE.ACTIVE.value,
            )
            default_device = AudioUtilities.GetSpeakers()

        default_id = getattr(default_device, "id", None)

        device_dict = {}
        current_default_name = None

        for dev in devices:
            display_name = (dev.FriendlyName or dev.id or "").strip()
            if not display_name:
                continue

            # 同名デバイスが複数ある場合はIDの末尾を付けて衝突を回避
            if display_name in device_dict:
                display_name = f"{display_name} ({dev.id[-8:]})"

            device_dict[display_name] = dev.id

            if default_id and dev.id == default_id:
                current_default_name = display_name

        return device_dict, current_default_name
    except Exception:
        return {}, None

def load_config():
    """設定ファイルの読み込み"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if len(lines) >= 4:
                return lines[0], lines[1], lines[2], lines[3]
            elif len(lines) == 3:
                return lines[0], lines[1], lines[2], "0"
    return "", "", "ctrl+alt+a", "0"

def save_config(dev_a, dev_b, key, startup_val):
    """設定ファイルの保存とスタートアップ制御"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f"{dev_a}\n{dev_b}\n{key}\n{startup_val}")
    manage_startup(startup_val)

def manage_startup(startup_val):
    """Windowsのスタートアップフォルダへの自動登録・解除（生スクリプト/exeハイブリッド対応・エラー修正版）"""
    try:
        startup_dir = winshell.startup()
        shortcut_path = os.path.join(startup_dir, "AudioSwitcher.lnk")
        
        if startup_val == "1":
            if getattr(sys, 'frozen', False):
                target = sys.executable
                arguments = "/background"
                icon_target = target  # exe化されている時は自身のexeアイコンを使う
            else:
                target = sys.executable
                arguments = f'"{os.path.abspath(__file__)}" /background'
                icon_target = None    # 生スクリプトの時はアイコン設定をパスする（エラー回避）
                
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = BASE_DIR
            
            # 生スクリプト実行時（icon_targetがNone）は設定をスキップしてクラッシュを防ぐ
            if icon_target:
                shortcut.IconLocation = icon_target
                
            shortcut.save()
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
    except Exception as e:
        tk.messagebox.showerror("Startup Error", f"Failed to update startup folder: {str(e)}")

def show_toast(device_name):
    """【極限解像度】画面最右下（時計完全オーバーレイ） ＋ フェードアニメーション"""
    toast = tk.Tk()
    toast.overrideredirect(True)  
    toast.attributes("-topmost", True)  
    toast.attributes("-alpha", 0.0)  
    
    BG_COLOR = "#0f131a"
    BORDER_COLOR = "#1e293b"
    TEXT_MAIN = "#f8fafc"
    TEXT_SUB = "#3b82f6"  

    toast.configure(bg=BG_COLOR)

    frame = tk.Frame(toast, bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
    frame.pack(fill="both", expand=True)

    label_title = tk.Label(frame, text="AUDIO ROUTING LAYER SWITCHED", bg=BG_COLOR, fg=TEXT_SUB, font=("Segoe UI", 7, "bold"), anchor="w")
    label_title.pack(fill="x", padx=14, pady=(10, 2))

    if len(device_name) > 32:
        display_text = device_name[:30] + "..."
    else:
        display_text = device_name

    label_body = tk.Label(frame, text=f"Switched to: {display_text}", bg=BG_COLOR, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold"), anchor="w")
    label_body.pack(fill="x", padx=14, pady=(0, 12))

    toast.update_idletasks()
    width = 310
    height = 62
    screen_width = toast.winfo_screenwidth()
    screen_height = toast.winfo_screenheight()
    
    # 💥 【時計完全隠し配置】マージンをすべて排除し、物理的な画面の右下最奥にハメ込む
    x = screen_width - width
    y = screen_height - height
    toast.geometry(f"{width}x{height}+{x}+{y}")

    current_alpha = 0.0

    def fade_in():
        nonlocal current_alpha
        if current_alpha < 0.95:
            current_alpha += 0.1  
            toast.attributes("-alpha", min(current_alpha, 0.95))
            toast.after(20, fade_in)
        else:
            toast.after(3000, start_fade_out)

    def start_fade_out():
        fade_out()

    def fade_out():
        nonlocal current_alpha
        if current_alpha > 0.0:
            current_alpha -= 0.05  
            toast.attributes("-alpha", max(current_alpha, 0.0))
            toast.after(20, fade_out)
        else:
            toast.destroy()  

    toast.after(10, fade_in)
    toast.mainloop()

def switch_audio():
    """固有IDを用いた実態ベースのオーディオ切り替え"""
    global last_switch_time
    current_time = time.time()
    
    if current_time - last_switch_time < 0.6:
        return
    last_switch_time = current_time

    dev_a, dev_b, _, _ = load_config()
    device_dict, current_default = get_device_info()
    
    if not current_default:
        target_display_name = dev_a
    else:
        if current_default == dev_a:
            target_display_name = dev_b
        else:
            target_display_name = dev_a
            
    target_id = device_dict.get(target_display_name)
    if target_id:
        try:
            ensure_com_initialized()
            # roles=NoneでeConsole/eMultimedia/eCommunicationsの全ロールに設定（SoundVolumeViewの"all"相当）
            AudioUtilities.SetDefaultDevice(target_id)
            show_toast(target_display_name)
        except Exception:
            pass

def start_backend():
    """バックグラウンドでのキーボード監視開始"""
    _, _, shortcut_key, _ = load_config()
    keyboard.add_hotkey(shortcut_key, switch_audio, trigger_on_release=False)
    keyboard.wait()

def open_setting_window():
    """2重起動防止・ハイブリッドスタートアップ自動生成付き設定UI"""
    kill_previous_instances()

    device_dict, current_default = get_device_info()
    devices = list(device_dict.keys())

    if not devices:
        root_err = tk.Tk()
        root_err.withdraw()
        tk.messagebox.showerror(
            "Error",
            "再生デバイスを取得できませんでした。\nオーディオドライバの状態を確認してください。"
        )
        devices = ["Speakers", "Headphones"]
    
    saved_a, saved_b, saved_key, saved_startup = load_config()
    devices_b_options = ["Select device..."] + devices

    root = tk.Tk()
    root.title("AudioSwitcher")
    root.geometry("520x440") 
    root.resizable(False, False)
    root.attributes("-topmost", True)
    
    BG_COLOR = "#07090e"         
    CARD_COLOR = "#0f131a"       
    INPUT_BG = "#141a24"         
    TEXT_MAIN = "#f8fafc"        
    TEXT_SUB = "#64748b"         
    BORDER_MAIN = "#1e293b"      
    BORDER_FOCUS = "#3b82f6"     

    root.configure(bg=BG_COLOR)

    style = ttk.Style()
    style.theme_use('clam')  
    style.configure(".", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 9))
    style.configure("TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG, foreground=TEXT_MAIN, arrowcolor=TEXT_SUB, borderwidth=0, padding=6)
    style.map("TCombobox", fieldbackground=[('readonly', INPUT_BG)], foreground=[('readonly', TEXT_MAIN)])
    style.configure("TCheckbutton", background=BG_COLOR, foreground=TEXT_SUB, font=("Segoe UI", 9))
    style.map("TCheckbutton", foreground=[('selected', TEXT_MAIN)], background=[('active', BG_COLOR)])

    # ヘッダー
    header = tk.Frame(root, bg=BG_COLOR)
    header.pack(fill="x", padx=28, pady=(28, 16))
    tk.Label(header, text="AudioSwitcher", bg=BG_COLOR, fg=TEXT_MAIN, font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
    tk.Label(header, text="Set active routing layers and global trigger shortcut.", bg=BG_COLOR, fg=TEXT_SUB, font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(2, 0))

    # コンテナ
    container = tk.Frame(root, bg=CARD_COLOR, highlightbackground=BORDER_MAIN, highlightthickness=1, bd=0)
    container.pack(fill="both", expand=True, padx=28, pady=0)

    # デバイス A
    tk.Label(container, text="DEVICE LAYER A", bg=CARD_COLOR, fg=TEXT_SUB, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=22, pady=(18, 4))
    combo_a = ttk.Combobox(container, values=devices, width=50, state="readonly")
    combo_a.pack(fill="x", padx=22, pady=(0, 14))
    if saved_a in devices: combo_a.set(saved_a)
    elif current_default in devices: combo_a.set(current_default)  
    else: combo_a.current(0)

    # デバイス B
    tk.Label(container, text="DEVICE LAYER B", bg=CARD_COLOR, fg=TEXT_SUB, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=22, pady=(4, 4))
    combo_b = ttk.Combobox(container, values=devices_b_options, width=50, state="readonly")
    combo_b.pack(fill="x", padx=22, pady=(0, 14))
    if saved_b in devices_b_options and saved_b != "Select device...": combo_b.set(saved_b)
    else: combo_b.current(0)  

    # ホットキー
    tk.Label(container, text="GLOBAL TRIGGER HOTKEY", bg=CARD_COLOR, fg=TEXT_SUB, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=22, pady=(4, 4))
    key_border_box = tk.Frame(container, bg=INPUT_BG, highlightbackground=BORDER_MAIN, highlightthickness=1, bd=0)
    key_border_box.pack(fill="x", padx=22, pady=(0, 18))
    entry_key = tk.Entry(key_border_box, bg=INPUT_BG, fg=TEXT_MAIN, insertbackground=TEXT_MAIN, bd=0, highlightthickness=0, font=("Consolas", 10, "bold"), justify="center", state="readonly", readonlybackground=INPUT_BG)
    entry_key.pack(fill="both", padx=10, ipady=7)
    entry_key.config(state="normal")
    entry_key.insert(0, saved_key)
    entry_key.config(state="readonly")

    current_keys = set()
    is_recording = False
    temp_shortcut = saved_key

    def on_key_press(event):
        nonlocal is_recording, temp_shortcut
        if not is_recording: return "break"
        if event.keysym == "Escape":
            temp_shortcut = saved_key  
            root.focus_set()           
            return "break"
        key_map = {"Control_L": "ctrl", "Control_R": "ctrl", "Alt_L": "alt", "Alt_R": "alt", "Shift_L": "shift", "Shift_R": "shift", "Win_L": "win", "Win_R": "win"}
        key_name = key_map.get(event.keysym, event.keysym.lower())
        if "caps" in key_name or "lock" in key_name or "num_" in key_name: return "break"
        current_keys.add(key_name)
        ordered_combination = []
        for modifier in ["ctrl", "alt", "shift", "win"]:
            if modifier in current_keys: ordered_combination.append(modifier)
        for k in sorted(current_keys):
            if k not in ["ctrl", "alt", "shift", "win"]: ordered_combination.append(k)
        temp_shortcut = "+".join(ordered_combination)
        entry_key.config(state="normal")
        entry_key.delete(0, tk.END)
        entry_key.insert(0, temp_shortcut)
        entry_key.config(state="readonly")
        return "break"

    def on_key_release(event):
        nonlocal is_recording
        if not is_recording: return "break"
        if temp_shortcut and temp_shortcut != "Press Keys...":
            is_recording = False
            root.focus_set() 
        return "break"

    def on_focus_in(e):
        nonlocal is_recording, current_keys
        is_recording = True
        current_keys.clear()
        key_border_box.config(highlightbackground=BORDER_FOCUS)
        entry_key.config(state="normal")
        entry_key.delete(0, tk.END)
        entry_key.insert(0, "Press Keys...")  
        entry_key.config(state="readonly", fg=BORDER_FOCUS)

    def on_focus_out(e):
        nonlocal is_recording, temp_shortcut
        is_recording = False
        key_border_box.config(highlightbackground=BORDER_MAIN)
        entry_key.config(fg=TEXT_MAIN)
        entry_key.config(state="normal")
        entry_key.delete(0, tk.END)
        if temp_shortcut == "Press Keys..." or not temp_shortcut:
            entry_key.insert(0, saved_key)
            temp_shortcut = saved_key
        else:
            entry_key.insert(0, temp_shortcut)
        entry_key.config(state="readonly")
        
    entry_key.bind("<FocusIn>", on_focus_in)
    entry_key.bind("<FocusOut>", on_focus_out)
    entry_key.bind("<KeyPress>", on_key_press)
    entry_key.bind("<KeyRelease>", on_key_release)

    # ボトム
    bottom_bar = tk.Frame(root, bg=BG_COLOR)
    bottom_bar.pack(fill="x", padx=28, pady=(18, 28))
    startup_var = tk.StringVar(value=saved_startup)
    check_startup = ttk.Checkbutton(bottom_bar, text="Start on boot", variable=startup_var, onvalue="1", offvalue="0", style="TCheckbutton")
    check_startup.pack(anchor="w", side="left", pady=5)

    btn_frame = tk.Frame(bottom_bar, bg=BG_COLOR)
    btn_frame.pack(side="right")

    def on_save_only():
        if combo_b.get() == "Select device...":
            tk.messagebox.showwarning("Routing Incomplete", "Please select a valid target for Device Layer B.")
            return
        save_config(combo_a.get(), combo_b.get(), temp_shortcut, startup_var.get())
        root.destroy()
        sys.exit(0)

    btn_save_only = tk.Button(btn_frame, text="Save only", command=on_save_only, bg=BG_COLOR, fg=TEXT_SUB, activebackground=INPUT_BG, activeforeground=TEXT_MAIN, font=("Segoe UI", 9, "bold"), bd=1, relief="solid", highlightthickness=0, highlightbackground=BORDER_MAIN, cursor="hand2", padx=14, pady=5)
    btn_save_only.pack(side="left", padx=(0, 10))

    def on_save_and_run():
        if combo_b.get() == "Select device...":
            tk.messagebox.showwarning("Routing Incomplete", "Please select a valid target for Device Layer B.")
            return
        save_config(combo_a.get(), combo_b.get(), temp_shortcut, startup_var.get())
        root.destroy()
        start_backend()

    btn_save_run = tk.Button(btn_frame, text="Save & Run", command=on_save_and_run, bg=TEXT_MAIN, fg=BG_COLOR, activebackground=TEXT_MAIN, activeforeground=BG_COLOR, font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2", padx=18, pady=6)
    btn_save_run.pack(side="right")

    def on_enter_only(e): btn_save_only.config(fg=TEXT_MAIN, bg=INPUT_BG)
    def on_leave_only(e): btn_save_only.config(fg=TEXT_SUB, bg=BG_COLOR)
    def on_enter_run(e):  btn_save_run.config(bg="#e2e8f0")
    def on_leave_run(e):  btn_save_run.config(bg=TEXT_MAIN)
    btn_save_only.bind("<Enter>", on_enter_only)
    btn_save_only.bind("<Leave>", on_leave_only)
    btn_save_run.bind("<Enter>", on_enter_run)
    btn_save_run.bind("<Leave>", on_leave_run)

    root.mainloop()

if __name__ == "__main__":
    if "/background" in sys.argv:
        if os.path.exists(CONFIG_FILE): start_backend()
        else: open_setting_window()
    else:
        open_setting_window()