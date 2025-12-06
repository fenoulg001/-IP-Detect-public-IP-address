import customtkinter as ctk
import threading
import requests  # 使用 requests 处理 HTTP 代理
import geoip2.database
import geoip2.errors
import os
import time
import sys
import pyperclip
import random
from datetime import datetime

# --- 【核心】强制开启高DPI支持，解决字体模糊问题 ---
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
# ----------------------------------------------------

# ================= 配置区域 =================
def resource_path(relative_path):
    """ 获取资源绝对路径：适配 PyInstaller 打包后的临时目录 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 数据库路径 (打包时会自动映射)
DB_PATH_CITY = resource_path('GeoLite2-City.mmdb')
DB_PATH_ASN  = resource_path('GeoLite2-ASN.mmdb')

REFRESH_INTERVAL = 3  # 刷新间隔(秒)

# 获取 IP 的接口池 (防止单点故障)
IP_APIS = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com"
]

# --- 代理设置 (重要) ---
# 留空 {} 则自动读取系统代理 (如 VPN 全局模式)
# 如果需要指定端口 (如 Clash 7890)，请取消注释并修改:
PROXIES = {
    # "http":  "http://127.0.0.1:7890",
    # "https": "http://127.0.0.1:7890",
}

# --- 字体配置 ---
FONT_TITLE = ("Microsoft YaHei UI", 24, "bold")
FONT_IP    = ("Roboto Medium", 48)
FONT_TAG   = ("Microsoft YaHei UI", 12, "bold")
FONT_TEXT  = ("Microsoft YaHei UI", 13)
FONT_TIME  = ("Consolas", 14, "bold")
# ===========================================

class NetworkMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 窗口设置
        self.title("网络监控 (代理/VPN透视版)")
        self.geometry("680x520")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # 2. 布局权重
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- 顶部区域 ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="当前网络出口监控", 
                                      font=FONT_TITLE, text_color="#FFFFFF")
        self.title_label.pack(side="left")

        self.time_card = ctk.CTkFrame(self.header_frame, fg_color="#2B2B2B", corner_radius=8)
        self.time_card.pack(side="right")
        self.time_label = ctk.CTkLabel(self.time_card, text="--:--:--", 
                                     font=FONT_TIME, text_color="#60A5FA", width=100)
        self.time_label.pack(padx=10, pady=5)

        # --- IP 显示区域 ---
        self.ip_frame = ctk.CTkFrame(self, fg_color=("gray90", "#1E1E1E"), corner_radius=20, border_width=1, border_color="#333333")
        self.ip_frame.grid(row=1, column=0, sticky="new", padx=30, pady=10)

        ctk.CTkLabel(self.ip_frame, text="Current Public IP (Via Proxy)", font=("Microsoft YaHei UI", 12), text_color="gray").pack(pady=(20, 0))

        self.ip_value = ctk.CTkLabel(self.ip_frame, text="Connecting...", 
                                   font=FONT_IP, text_color="#3B8ED0")
        self.ip_value.pack(pady=5)
        
        self.hint_label = ctk.CTkLabel(self.ip_frame, text="点击 IP 可复制", 
                                     font=("Microsoft YaHei UI", 11), text_color="#666666")
        self.hint_label.pack(pady=(0, 5))

        self.status_label = ctk.CTkLabel(self.ip_frame, text="● 初始化 HTTP 引擎...", 
                                       font=("Microsoft YaHei UI", 13), text_color="orange")
        self.status_label.pack(pady=(0, 20))

        # 绑定点击复制
        self.ip_value.bind("<Button-1>", self.copy_ip)
        self.ip_value.bind("<Enter>", lambda e: self.configure_cursor("hand2"))
        self.ip_value.bind("<Leave>", lambda e: self.configure_cursor("arrow"))

        # --- 详情卡片 ---
        self.info_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.info_grid.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        self.info_grid.grid_columnconfigure((0, 1), weight=1)

        self.loc_card = self.create_card(self.info_grid, "📍 落地位置", 0)
        self.lbl_country = self.add_row(self.loc_card, "国家地区")
        self.lbl_city    = self.add_row(self.loc_card, "城市名称")
        self.lbl_coords  = self.add_row(self.loc_card, "物理坐标")

        self.net_card = self.create_card(self.info_grid, "🌐 代理商信息", 1)
        self.lbl_isp     = self.add_row(self.net_card, "服务商")
        self.lbl_asn     = self.add_row(self.net_card, "ASN 编号")
        self.lbl_tz      = self.add_row(self.net_card, "所在时区")

        # --- 底部进度条 ---
        self.progress = ctk.CTkProgressBar(self, height=3, progress_color="#3B8ED0", fg_color="#222222")
        self.progress.grid(row=3, column=0, sticky="ew")
        self.progress.set(0)

        # --- 启动 ---
        self.configure_cursor = lambda c: self.ip_value.configure(cursor=c)
        self.running = True
        self.last_ip = None

        if not os.path.exists(DB_PATH_CITY):
            self.ip_value.configure(text="数据库缺失", text_color="red")
            self.status_label.configure(text="请检查附加文件是否打包", text_color="red")
        else:
            threading.Thread(target=self.bg_task, daemon=True).start()
            threading.Thread(target=self.anim_task, daemon=True).start()

    def create_card(self, parent, title, col):
        frame = ctk.CTkFrame(parent, fg_color="#2B2B2B", corner_radius=10)
        frame.grid(row=0, column=col, sticky="nsew", padx=10 if col==0 else (10,0))
        ctk.CTkLabel(frame, text=title, font=FONT_TAG, text_color="#DDDDDD").pack(pady=15, padx=20, anchor="w")
        return frame

    def add_row(self, parent, label):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row, text=label, font=FONT_TEXT, text_color="#888888").pack(side="left")
        val = ctk.CTkLabel(row, text="---", font=FONT_TEXT, text_color="#FFFFFF")
        val.pack(side="right")
        return val

    def copy_ip(self, event):
        ip = self.ip_value.cget("text")
        if ip and "..." not in ip:
            pyperclip.copy(ip)
            self.hint_label.configure(text="✅ 已复制!", text_color="#2CC985")
            self.after(2000, lambda: self.hint_label.configure(text="点击 IP 可复制", text_color="#666666"))

    def anim_task(self):
        while self.running:
            for i in range(100):
                if not self.running: break
                time.sleep(REFRESH_INTERVAL/100)
                self.progress.set(i/100)

    def get_http_ip(self):
        """通过 HTTP 请求获取 IP，支持代理"""
        api_url = random.choice(IP_APIS)
        try:
            # 加上时间戳防止缓存
            url = f"{api_url}?t={time.time()}"
            # 3秒超时，避免卡顿
            resp = requests.get(url, proxies=PROXIES, timeout=3)
            resp.raise_for_status()
            return resp.text.strip()
        except Exception:
            return None

    def bg_task(self):
        try:
            with geoip2.database.Reader(DB_PATH_CITY) as city_db, \
                 geoip2.database.Reader(DB_PATH_ASN) as asn_db:
                
                while self.running:
                    # 1. 获取IP
                    ip = self.get_http_ip()

                    # 2. 准备数据
                    data = {"ip": ip, "time": datetime.now().strftime("%H:%M:%S")}
                    
                    if ip:
                        try:
                            c = city_db.city(ip)
                            data['cn'] = c.country.names.get('zh-CN', c.country.name)
                            data['ct'] = c.city.names.get('zh-CN', c.city.name)
                            data['loc'] = f"{c.location.latitude:.2f}, {c.location.longitude:.2f}"
                            data['tz'] = c.location.time_zone
                        except: data['cn'] = "未知"

                        try:
                            a = asn_db.asn(ip)
                            data['isp'] = a.autonomous_system_organization
                            data['asn'] = f"AS{a.autonomous_system_number}"
                        except: data['isp'] = "未知"

                    self.after(0, self.update_ui, data)
                    time.sleep(REFRESH_INTERVAL)
        except Exception as e:
            print(f"Error: {e}")

    def update_ui(self, data):
        self.time_label.configure(text=data['time'])
        
        if data['ip']:
            self.ip_value.configure(text=data['ip'])
            
            if self.last_ip and data['ip'] != self.last_ip:
                self.status_label.configure(text="⚠️ 节点/IP 已变更", text_color="orange")
            else:
                self.status_label.configure(text="● 代理连接正常 (HTTPS)", text_color="#2CC985")

            self.lbl_country.configure(text=data.get('cn', '-'))
            self.lbl_city.configure(text=data.get('ct', '-'))
            self.lbl_coords.configure(text=data.get('loc', '-'))
            
            isp = data.get('isp', '-')
            if len(isp) > 20: isp = isp[:18] + "..."
            self.lbl_isp.configure(text=isp)
            self.lbl_asn.configure(text=data.get('asn', '-'))
            self.lbl_tz.configure(text=data.get('tz', '-'))
            
            self.last_ip = data['ip']
        else:
            self.ip_value.configure(text="连接超时")
            self.status_label.configure(text="● 无法连接代理服务器", text_color="#FF474C")

    def on_closing(self):
        self.running = False
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = NetworkMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()