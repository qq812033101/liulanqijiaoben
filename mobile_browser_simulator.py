import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import json
import os
import sys
from urllib.parse import quote
import logging
import ssl

class MobileBrowserSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JB")
        self.root.geometry("800x800")  # 增加高度以容纳代理列表
        self.root.resizable(True, True)
        
        # 配置变量
        self.target_url = tk.StringVar(value="")
        self.visit_count = tk.IntVar(value=100)
        self.visit_interval = tk.IntVar(value=30)
        self.stay_time = tk.IntVar(value=10)
        # 新增：HTTP模式（不打开浏览器）
        self.use_http_mode = tk.BooleanVar(value=False)
        
        # IPFOXY代理配置
        self.proxy_host = tk.StringVar(value="127.0.0.1")
        self.proxy_port = tk.StringVar(value="1080")
        self.proxy_username = tk.StringVar(value="")
        self.proxy_password = tk.StringVar(value="")
        self.proxy_string = tk.StringVar(value="")
        
        # 新增：代理列表管理
        self.proxy_list = []  # 存储所有导入的代理
        self.current_proxy_index = 0  # 当前使用的代理索引
        
        # 运行状态
        self.is_running = False
        self.current_visits = 0
        self.driver = None
        self.consecutive_failures = 0
        # 运行期代理协议判定（'socks5h' 或 'http'）
        self.runtime_proxy_scheme = None
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 目标网站配置
        ttk.Label(main_frame, text="目标网站:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.target_url, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 访问配置标题
        ttk.Label(main_frame, text="访问配置", font=("Arial", 12, "bold")).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # 访问次数
        ttk.Label(main_frame, text="访问次数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.visit_count, width=20).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 访问间隔
        ttk.Label(main_frame, text="访问间隔(秒):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.visit_interval, width=20).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 页面停留时间
        ttk.Label(main_frame, text="最大停留时间(秒):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.stay_time, width=20).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 新增：访问模式（HTTP不打开浏览器）
        ttk.Label(main_frame, text="访问模式:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(main_frame, text="使用HTTP请求模式(不打开浏览器)", variable=self.use_http_mode).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # IPFOXY代理配置标题
        # IPFOXY代理配置
        ttk.Label(main_frame, text="代理配置", font=("Arial", 12, "bold")).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # 代理地址输入框（支持完整格式）
        # 代理地址输入和解析
        ttk.Label(main_frame, text="代理地址:").grid(row=row, column=0, sticky=tk.W, pady=2)
        proxy_frame = ttk.Frame(main_frame)
        proxy_frame.grid(row=row, column=1, sticky=tk.W, pady=2)
        
        ttk.Entry(proxy_frame, textvariable=self.proxy_string, width=30).pack(side=tk.LEFT)
        ttk.Button(proxy_frame, text="解析", command=self.parse_proxy_string).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(proxy_frame, text="导入", command=self.import_proxies).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # 格式提示
        ttk.Label(main_frame, text="格式: host:port:username:password", font=("Arial", 8), foreground="gray").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 代理列表显示区域
        proxy_list_frame = ttk.LabelFrame(main_frame, text="代理列表", padding="5")
        proxy_list_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        proxy_list_frame.columnconfigure(0, weight=1)
        
        # 代理总数显示
        self.proxy_count_label = ttk.Label(proxy_list_frame, text="总数: 0")
        self.proxy_count_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # 代理列表框
        list_frame = ttk.Frame(proxy_list_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        list_frame.columnconfigure(0, weight=1)
        
        # 创建列表框和滚动条
        self.proxy_listbox = tk.Listbox(list_frame, height=6, width=50)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.proxy_listbox.yview)
        self.proxy_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.proxy_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        row += 1
        
        # 详细配置标题
        ttk.Label(main_frame, text="详细配置 (自动解析)", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # 代理主机
        ttk.Label(main_frame, text="代理主机:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.proxy_host, width=20, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 代理端口
        ttk.Label(main_frame, text="代理端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.proxy_port, width=20, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 代理用户名
        ttk.Label(main_frame, text="用户名:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.proxy_username, width=20, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 代理密码
        ttk.Label(main_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.proxy_password, width=20, show="*", state="readonly").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # 开始按钮
        self.start_button = ttk.Button(button_frame, text="开始访问", command=self.start_browsing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_button = ttk.Button(button_frame, text="停止访问", command=self.stop_browsing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 保存配置按钮
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # 测试代理按钮
        ttk.Button(button_frame, text="测试代理", command=self.test_proxy).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="5")
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="就绪", foreground="green")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_label = ttk.Label(status_frame, text="访问进度: 0/0")
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        row += 1
        
        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主框架的行权重
        main_frame.rowconfigure(row, weight=1)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        print(log_entry.strip())  # 同步输出到控制台，便于排查无GUI时的问题
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, status, color="black"):
        """更新状态显示"""
        self.status_label.config(text=status, foreground=color)
        self.root.update_idletasks()
        
    def update_progress(self):
        """更新进度显示"""
        self.progress_label.config(text=f"访问进度: {self.current_visits}/{self.visit_count.get()}")
        self.root.update_idletasks()
        
    def parse_proxy_string(self):
        """解析代理字符串"""
        try:
            proxy_str = self.proxy_string.get().strip()
            if not proxy_str:
                messagebox.showwarning("警告", "请输入代理地址")
                return
                
            # 解析格式: host:port:username:password
            parts = proxy_str.split(':')
            
            if len(parts) < 2:
                messagebox.showerror("错误", "代理地址格式不正确\n正确格式: host:port:username:password")
                return
                
            # 提取主机和端口
            host = parts[0]
            port = parts[1]
            
            # 提取用户名和密码（如果有的话），用户名可能包含冒号
            username = ""
            password = ""
            if len(parts) >= 4:
                # username 可能包含多个冒号，password 为最后一段
                username = ":".join(parts[2:-1])
                password = parts[-1]
            elif len(parts) == 3:
                # 只有用户名没有密码
                username = parts[2]
                
            # 更新界面
            self.proxy_host.set(host)
            self.proxy_port.set(port)
            self.proxy_username.set(username)
            self.proxy_password.set(password)
            
            # 记录日志
            self.log_message(f"代理解析成功: {host}:{port}")
            if username:
                self.log_message(f"用户名: {username}")
            if password:
                self.log_message("已设置密码(已隐藏)")
            
            messagebox.showinfo("成功", "代理地址解析成功！")
            
        except Exception as e:
            self.log_message(f"代理解析失败: {str(e)}")
            messagebox.showerror("错误", f"代理解析失败: {str(e)}")
        
    def get_mobile_user_agent(self):
        """获取随机的手机User-Agent"""
        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        ]
        return random.choice(mobile_agents)
        
    def detect_proxy_scheme(self):
        """设置代理协议：优先使用 socks5h，其次 socks5，然后 https，最后 http"""
        try:
            if not (self.proxy_host.get() and self.proxy_port.get()):
                self.runtime_proxy_scheme = None
                return None
            
            # 直接设置代理协议，不进行网络测试
            # 优先级：socks5h > socks5 > https > http
            self.runtime_proxy_scheme = 'socks5h'  # 默认使用 socks5h
            
            self.log_message(f"代理协议设置为: {self.runtime_proxy_scheme}")
            return self.runtime_proxy_scheme
            
        except Exception as e:
            self.log_message(f"代理协议设置异常: {e}")
            self.runtime_proxy_scheme = None
            return None
    
    def switch_proxy_protocol(self):
        """智能切换代理协议，用于处理SSL/TLS错误"""
        try:
            current_scheme = self.runtime_proxy_scheme
            
            # 协议切换顺序：socks5h -> socks5 -> https -> http
            if current_scheme == 'socks5h':
                self.runtime_proxy_scheme = 'socks5'
            elif current_scheme == 'socks5':
                self.runtime_proxy_scheme = 'https'
            elif current_scheme == 'https':
                self.runtime_proxy_scheme = 'http'
            else:
                self.runtime_proxy_scheme = 'socks5h'  # 循环回到开始
            
            self.log_message(f"🔄 代理协议从 {current_scheme} 切换到 {self.runtime_proxy_scheme}")
            return self.runtime_proxy_scheme
            
        except Exception as e:
            self.log_message(f"代理协议切换异常: {e}")
            return None
    
    def setup_driver(self):
        """设置Chrome驱动器"""
        try:
            chrome_options = Options()
            # 记录当前 Python 解释器，排查依赖装在哪个环境
            try:
                self.log_message(f"Python解释器: {sys.executable}")
            except Exception:
                pass
            
            # 手机模拟设置 - iPhone 14 Pro Max
            mobile_emulation = {
                "deviceMetrics": {
                    "width": 430,      # iPhone 14 Pro Max 宽度
                    "height": 932,     # iPhone 14 Pro Max 高度
                    "pixelRatio": 3.0  # iPhone 14 Pro Max 像素比
                },
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # 设置浏览器窗口为手机尺寸
            chrome_options.add_argument("--window-size=430,932")  # 设置窗口大小为手机尺寸
            chrome_options.add_argument("--force-device-scale-factor=1")  # 强制设备缩放比例
            use_seleniumwire = False
            seleniumwire_options = None
            if self.proxy_host.get() and self.proxy_port.get():
                # 先判定代理协议
                scheme = self.detect_proxy_scheme()
                proxy_host = self.proxy_host.get()
                proxy_port = self.proxy_port.get()
                proxy_username = self.proxy_username.get()
                proxy_password = self.proxy_password.get()

                # 预检函数：在启动浏览器前用 requests 按同样代理配置连通 httpbin
                def preflight_proxy(test_scheme: str, u: str | None, p: str | None, h: str, pt: str) -> bool:
                    try:
                        if u and p:
                            u_enc = quote(u, safe=''); p_enc = quote(p, safe='')
                            url = f"{test_scheme}://{u_enc}:{p_enc}@{h}:{pt}"
                        else:
                            url = f"{test_scheme}://{h}:{pt}"
                        proxies = {"http": url, "https": url}
                        self.log_message(f"[预检] 以 {test_scheme} 代理测试 https://httpbin.org/ip ...")
                        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10, verify=False)
                        self.log_message(f"[预检] 返回: {r.status_code} {'OK' if 200 <= r.status_code < 300 else ''}")
                        return 200 <= r.status_code < 300
                    except Exception as e:
                        self.log_message(f"[预检] 失败: {e}")
                        # 附加 PySocks 版本信息（如可用）
                        try:
                            import socks
                            self.log_message(f"[预检] PySocks 版本: {getattr(socks, '__version__', 'unknown')}")
                        except Exception:
                            self.log_message("[预检] 未安装 PySocks (requests 的 socks 支持)")
                        return False

                if scheme:
                    if scheme.startswith('socks'):
                        # SOCKS 代理：无论是否认证，优先使用 selenium-wire 以保证 SOCKS5H 远程 DNS 与稳定性
                        import seleniumwire
                        from seleniumwire import webdriver as wire_webdriver  # 延迟导入
                        use_seleniumwire = True
                        if proxy_username and proxy_password:
                            u = quote(proxy_username, safe='')
                            p = quote(proxy_password, safe='')
                            auth = f"{u}:{p}@"
                            cred_log = "(已提供认证; 凭据已URL编码)"
                        else:
                            auth = ""
                            cred_log = "(无认证)"
                        proxy_url = f"{scheme}://{auth}{proxy_host}:{proxy_port}"
                        seleniumwire_options = {
                            'proxy': {
                                'http': proxy_url,
                                'https': proxy_url,
                                'no_proxy': 'localhost,127.0.0.1'
                            }
                        }
                        # 打开 selenium-wire DEBUG 日志，便于定位上游 SOCKS 失败原因
                        try:
                            logger = logging.getLogger('seleniumwire')
                            logger.setLevel(logging.DEBUG)
                            if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
                                sh = logging.StreamHandler()
                                sh.setLevel(logging.DEBUG)
                                formatter = logging.Formatter('[selenium-wire] %(levelname)s: %(message)s')
                                sh.setFormatter(formatter)
                                logger.addHandler(sh)
                        except Exception:
                            pass
                        self.log_message(f"已检测到 selenium-wire {getattr(seleniumwire, '__version__', '')}，使用上游 SOCKS 代理: {scheme}://{proxy_host}:{proxy_port} {cred_log}")
                        # 预检连通性（避免浏览器里才报 ERR_SOCKS_CONNECTION_FAILED）
                        ok = preflight_proxy(scheme, proxy_username or None, proxy_password or None, proxy_host, proxy_port)
                        if not ok:
                            self.log_message("❌ 预检失败：上游 SOCKS 代理不可用，请检查IP、端口或凭据。中止浏览器启动。")
                            return False
                    else:
                        # HTTP 代理
                        if proxy_username and proxy_password:
                            # HTTP 带认证也使用 selenium-wire 处理认证
                            import seleniumwire
                            from seleniumwire import webdriver as wire_webdriver  # 延迟导入
                            use_seleniumwire = True
                            u = quote(proxy_username, safe='')
                            p = quote(proxy_password, safe='')
                            proxy_url = f"http://{u}:{p}@{proxy_host}:{proxy_port}"
                            seleniumwire_options = {
                                'proxy': {
                                    'http': proxy_url,
                                    'https': proxy_url,
                                    'no_proxy': 'localhost,127.0.0.1'
                                }
                            }
                            self.log_message(f"已检测到 selenium-wire {getattr(seleniumwire, '__version__', '')}，使用上游 HTTP 代理（带认证; 凭据已URL编码）")
                            # 预检
                            ok = preflight_proxy('http', proxy_username, proxy_password, proxy_host, proxy_port)
                            if not ok:
                                self.log_message("❌ 预检失败：HTTP 代理不可用，请检查配置。中止浏览器启动。")
                                return False
                        else:
                            # HTTP 无认证，直接让 Chrome 使用
                            chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")
                            self.log_message(f"使用代理: {proxy_host}:{proxy_port} (协议: http)")
            else:
                self.log_message("❌ 代理不可达，已放弃为浏览器设置代理")
            
            # 其他Chrome选项
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
            chrome_options.add_experimental_option('useAutomationExtension', False)
            # 可选：忽略证书错误，避免个别代理链路的证书告警阻断
            chrome_options.add_argument('--ignore-certificate-errors')
            
            # 创建驱动器
            if use_seleniumwire and seleniumwire_options:
                from seleniumwire import webdriver as wire_webdriver
                self.log_message("使用 selenium-wire 启动 Chrome，并设置上游代理")
                self.driver = wire_webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
            else:
                self.log_message("使用原生 Selenium 启动 Chrome")
                self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 如果使用了代理，检查当前IP地址
            if self.proxy_host.get() and self.proxy_port.get():
                self.check_current_ip()
            
            return True
            
        except Exception as e:
            self.log_message(f"驱动器设置失败: {str(e)}")
            return False
    
    def check_current_ip(self):
        """检查当前IP地址"""
        try:
            self.log_message("正在检查当前IP地址...")
            
            # 使用浏览器访问IP检查服务
            self.driver.get("https://httpbin.org/ip")
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面内容
            page_source = self.driver.page_source
            
            # 尝试从页面源码中提取IP
            import re
            ip_pattern = r'"origin":\s*"([^"]+)"'
            match = re.search(ip_pattern, page_source)
            
            if match:
                current_ip = match.group(1)
                self.log_message(f"🌐 当前IP地址: {current_ip}")
            else:
                # 如果无法解析JSON，尝试获取页面文本
                try:
                    body_element = self.driver.find_element(By.TAG_NAME, "body")
                    body_text = body_element.text
                    self.log_message(f"🌐 IP检查结果: {body_text}")
                except:
                    self.log_message("⚠️ 无法获取IP地址信息")
                    
        except Exception as e:
            self.log_message(f"⚠️ IP地址检查失败: {str(e)}")
    
    def is_session_valid(self):
        """检查浏览器会话是否有效"""
        try:
            if not self.driver:
                return False
            # 尝试获取当前URL来检测会话是否有效
            current_url = self.driver.current_url
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['invalid session', 'session not found', 'no such session']):
                self.log_message(f"⚠️ 检测到会话失效: {str(e)}")
                return False
            return True
    
    def restart_driver(self):
        """重启浏览器驱动"""
        try:
            self.log_message("🔄 正在重启浏览器...")
            
            # 清理旧的驱动
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            # 重新设置驱动
            if self.setup_driver():
                self.log_message("✅ 浏览器重启成功")
                return True
            else:
                self.log_message("❌ 浏览器重启失败")
                return False
                
        except Exception as e:
            self.log_message(f"❌ 重启浏览器时出错: {str(e)}")
            return False
            
    def visit_website(self):
        """访问网站"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查会话是否有效
                if not self.is_session_valid():
                    self.log_message("🔄 会话失效，尝试重启浏览器...")
                    if not self.restart_driver():
                        retry_count += 1
                        if retry_count < max_retries:
                            self.log_message(f"⏳ 第 {retry_count} 次重启失败，等待 5 秒后重试...")
                            time.sleep(5)
                        continue
                
                url = self.target_url.get()
                self.log_message(f"正在访问: {url}")
                
                self.driver.get(url)
                
                # 随机停留时间
                stay_duration = random.randint(1, self.stay_time.get())
                self.log_message(f"页面停留时间: {stay_duration}秒")
                
                time.sleep(stay_duration)
                
                # 模拟一些随机操作
                try:
                    # 随机滚动
                    scroll_height = random.randint(100, 500)
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                    time.sleep(random.uniform(0.5, 2))
                    
                    # 随机点击（如果有可点击元素）
                    clickable_elements = self.driver.find_elements(By.TAG_NAME, "a")
                    if clickable_elements and random.choice([True, False]):
                        element = random.choice(clickable_elements[:5])  # 只考虑前5个链接
                        try:
                            element.click()
                            time.sleep(random.uniform(1, 3))
                            self.driver.back()
                        except:
                            pass
                            
                except Exception as e:
                    self.log_message(f"模拟操作时出错: {str(e)}")
                    
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                self.log_message(f"访问网站失败: {str(e)}")
                
                # 检查是否是会话相关错误
                if any(keyword in error_msg for keyword in ['invalid session', 'session not found', 'no such session']):
                    self.log_message("🔄 检测到会话错误，尝试重启浏览器...")
                    if self.restart_driver():
                        retry_count += 1
                        if retry_count < max_retries:
                            self.log_message(f"⏳ 第 {retry_count} 次重试...")
                            time.sleep(2)
                        continue
                
                # 其他错误也进行重试
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ 第 {retry_count} 次访问失败，等待 3 秒后重试...")
                    time.sleep(3)
                else:
                    self.log_message(f"❌ 访问失败，已达到最大重试次数 ({max_retries})")
                    
        return False
        
    # 新增：HTTP方式访问网站（不打开浏览器）
    def visit_website_http(self):
        """使用requests通过代理以手机UA访问网站，不打开浏览器"""
        max_retries = 3
        retry_count = 0
        url = self.target_url.get()
        
        # 构建请求头（手机UA）
        headers = {
            'User-Agent': self.get_mobile_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'close'
        }
        
        # 代理
        proxy_dict = None
        try:
            if self.proxy_host.get() and self.proxy_port.get():
                host = self.proxy_host.get()
                port = self.proxy_port.get()
                user = self.proxy_username.get()
                pwd = self.proxy_password.get()
                # 使用探测到的协议（socks5h -> socks5 -> http）
                scheme = self.runtime_proxy_scheme or self.detect_proxy_scheme()
                if scheme:
                    if user and pwd:
                        u = quote(user, safe='')
                        p = quote(pwd, safe='')
                        proxy_url = f"{scheme}://{u}:{p}@{host}:{port}"
                    else:
                        proxy_url = f"{scheme}://{host}:{port}"
                    proxy_dict = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                    self.log_message(f"HTTP模式代理协议: {scheme}（凭据已URL编码）")
                else:
                    self.log_message("⚠️ 代理不可达，HTTP模式将不会使用代理")
        except Exception as e:
            self.log_message(f"构建代理配置失败: {str(e)}")
        
        while retry_count < max_retries and self.is_running:
            try:
                self.log_message(f"正在以HTTP模式访问: {url}")
                
                # 设置适配器以处理SSL问题
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                from urllib3.util.ssl_ import create_urllib3_context
                
                # 创建自定义SSL上下文，支持更多TLS版本
                class CustomHTTPSAdapter(HTTPAdapter):
                    def init_poolmanager(self, *args, **kwargs):
                        context = create_urllib3_context()
                        # 允许所有TLS版本
                        context.set_ciphers('DEFAULT@SECLEVEL=1')
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        # 支持TLS 1.0, 1.1, 1.2, 1.3
                        context.minimum_version = ssl.TLSVersion.TLSv1
                        context.maximum_version = ssl.TLSVersion.TLSv1_3
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)
                
                retry_strategy = Retry(
                    total=2,
                    status_forcelist=[429, 500, 502, 503, 504],
                    method_whitelist=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=1
                )
                
                # 使用自定义HTTPS适配器
                https_adapter = CustomHTTPSAdapter(max_retries=retry_strategy)
                http_adapter = HTTPAdapter(max_retries=retry_strategy)
                
                session = requests.Session()
                session.mount("http://", http_adapter)
                session.mount("https://", https_adapter)
                
                resp = session.get(
                    url, 
                    headers=headers, 
                    proxies=proxy_dict, 
                    timeout=20, 
                    allow_redirects=True,
                    verify=False
                )
                
                status = resp.status_code
                if 200 <= status < 400:
                    content_len = len(resp.content) if resp.content is not None else 0
                    self.log_message(f"✅ HTTP访问成功，状态码: {status}，内容长度: {content_len}")
                    # 模拟停留
                    stay_duration = random.randint(1, self.stay_time.get())
                    self.log_message(f"停留 {stay_duration} 秒（HTTP模式）")
                    time.sleep(stay_duration)
                    return True
                else:
                    self.log_message(f"HTTP访问失败，状态码: {status}")
                    retry_count += 1
                    if retry_count < max_retries:
                        self.log_message(f"⏳ 第 {retry_count} 次失败，3秒后重试（HTTP模式）...")
                        time.sleep(3)
                        
            except requests.exceptions.SSLError as e:
                error_msg = str(e).lower()
                self.log_message(f"🔒 SSL/TLS错误: {str(e)}")
                
                if "wrong version number" in error_msg:
                    self.log_message("🔍 检测到SSL版本号错误 - 这通常表示代理返回了非HTTPS响应")
                    self.log_message("💡 建议：1) 代理可能不支持HTTPS 2) 尝试切换到HTTP协议代理 3) 更换代理服务器")
                    
                    # 尝试自动切换代理协议
                    if hasattr(self, 'runtime_proxy_scheme') and self.runtime_proxy_scheme == 'socks5h':
                        self.log_message("🔄 尝试自动切换代理协议从 SOCKS5 到 HTTP...")
                        self.runtime_proxy_scheme = 'http'
                        # 重新构建代理配置
                        if self.proxy_host.get() and self.proxy_port.get():
                            host = self.proxy_host.get()
                            port = self.proxy_port.get()
                            user = self.proxy_username.get()
                            pwd = self.proxy_password.get()
                            if user and pwd:
                                u = quote(user, safe='')
                                p = quote(pwd, safe='')
                                proxy_url = f"http://{u}:{p}@{host}:{port}"
                            else:
                                proxy_url = f"http://{host}:{port}"
                            proxy_dict = {
                                'http': proxy_url,
                                'https': proxy_url
                            }
                            self.log_message("✅ 已切换到HTTP代理协议，继续重试...")
                            
                elif "packet length too long in error_msg":
                    self.log_message("💡 建议：代理可能不支持HTTPS，尝试使用HTTP协议或更换代理")
                elif "certificate verify failed in error_msg":
                    self.log_message("💡 建议：SSL证书验证失败，已自动禁用证书验证")
                elif "handshake failure in error_msg":
                    self.log_message("💡 建议：SSL握手失败，可能是代理或目标服务器SSL配置问题")
                elif "record layer failure in error_msg":
                    self.log_message("💡 建议：SSL记录层失败，尝试更换代理或检查网络连接")
                    
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ SSL错误第 {retry_count} 次，5秒后重试...")
                    time.sleep(5)
                    
            except requests.exceptions.ProxyError as e:
                self.log_message(f"🌐 代理错误: {str(e)}")
                self.log_message("💡 建议：检查代理服务器是否正常工作，或尝试更换代理")
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ 代理错误第 {retry_count} 次，5秒后重试...")
                    time.sleep(5)
                    
            except requests.exceptions.ConnectionError as e:
                self.log_message(f"🔌 连接错误: {str(e)}")
                if "TlsProtocolException" in str(e):
                    self.log_message("💡 TLS协议异常：可能是代理服务器不支持目标网站的SSL版本")
                    self.log_message("💡 建议：尝试更换代理或使用HTTP版本的目标URL")
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ 连接错误第 {retry_count} 次，5秒后重试...")
                    time.sleep(5)
                    
            except requests.exceptions.Timeout as e:
                self.log_message(f"⏰ 请求超时: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ 超时第 {retry_count} 次，3秒后重试...")
                    time.sleep(3)
                    
            except Exception as e:
                self.log_message(f"❌ HTTP访问异常: {str(e)}")
                # 检查是否是TLS相关错误
                if any(keyword in str(e).lower() for keyword in ['tls', 'ssl', 'handshake', 'certificate']):
                    self.log_message("🔒 检测到TLS/SSL相关错误")
                    self.log_message("💡 建议：1) 检查代理是否支持HTTPS 2) 尝试HTTP版本 3) 更换代理服务器")
                
                retry_count += 1
                if retry_count < max_retries:
                    self.log_message(f"⏳ 第 {retry_count} 次异常，3秒后重试（HTTP模式）...")
                    time.sleep(3)
                else:
                    self.log_message(f"❌ HTTP访问失败，已达到最大重试次数 ({max_retries})")
        return False

    def browsing_thread(self):
        """浏览线程"""
        try:
            # 根据模式初始化
            if self.use_http_mode.get():
                self.update_status("HTTP模式: 不启动浏览器", "blue")
            else:
                self.update_status("正在初始化浏览器...", "blue")
                
                if not self.setup_driver():
                    self.update_status("浏览器初始化失败", "red")
                    self.stop_browsing()
                    return
                
            self.update_status("正在运行", "green")
            self.log_message("开始自动访问")
            
            target_visits = self.visit_count.get()
            interval = self.visit_interval.get()
            
            for i in range(target_visits):
                if not self.is_running:
                    break
                    
                self.current_visits = i + 1
                self.update_progress()
                
                # 在每次访问前切换代理（从第二次访问开始）
                if i > 0 and self.proxy_list and len(self.proxy_list) > 1:
                    # 关闭当前浏览器
                    if not self.use_http_mode.get():
                        self.log_message("🔄 关闭当前浏览器，准备切换代理...")
                        try:
                            if hasattr(self, 'driver') and self.driver:
                                self.driver.quit()
                                self.driver = None
                        except Exception as e:
                            self.log_message(f"关闭浏览器时出错: {str(e)}")
                        
                        # 等待一下
                        time.sleep(2)
                    
                    # 切换到下一个代理
                    if not self.get_next_proxy():
                        # 如果没有更多代理，停止程序
                        self.log_message("🛑 所有代理已用完，程序自动停止")
                        self.update_status("所有代理已用完，程序已停止", "orange")
                        break
                    
                    # 重新初始化浏览器（非HTTP模式）
                    if not self.use_http_mode.get() and self.is_running:
                        self.log_message("🚀 重新启动浏览器...")
                        if not self.setup_driver():
                            self.log_message("❌ 重新启动浏览器失败")
                            # 如果重启失败，尝试继续下一次访问
                            continue
                        else:
                            self.log_message("✅ 浏览器重新启动成功")
                
                # 根据模式选择访问方式
                if self.use_http_mode.get():
                    success = self.visit_website_http()
                else:
                    success = self.visit_website()
                
                if success:
                    self.log_message(f"✅ 第 {self.current_visits} 次访问完成")
                    # 成功时重置失败计数
                    self.consecutive_failures = 0
                    
                    # 访问完成后立即关闭浏览器（非HTTP模式）
                    if not self.use_http_mode.get():
                        self.log_message("🔄 访问完成，关闭浏览器...")
                        try:
                            if hasattr(self, 'driver') and self.driver:
                                self.driver.quit()
                                self.driver = None
                                self.log_message("✅ 浏览器已关闭")
                        except Exception as e:
                            self.log_message(f"关闭浏览器时出错: {str(e)}")
                else:
                    self.log_message(f"❌ 第 {self.current_visits} 次访问失败")
                    
                    # 如果连续失败多次，尝试自恢复
                    if hasattr(self, 'consecutive_failures'):
                        self.consecutive_failures += 1
                    else:
                        self.consecutive_failures = 1
                        
                    if self.consecutive_failures >= 3:
                        if not self.use_http_mode.get():
                            self.log_message("⚠️ 连续失败3次，尝试重启浏览器...")
                            if self.restart_driver():
                                self.consecutive_failures = 0
                            else:
                                self.log_message("❌ 浏览器重启失败，继续尝试...")
                        else:
                            self.log_message("⚠️ 连续失败3次（HTTP模式），请检查代理/目标站点，稍后继续重试...")
                            time.sleep(5)
                
                # 如果不是最后一次访问，等待间隔时间
                if i < target_visits - 1 and self.is_running:
                    self.log_message(f"等待 {interval} 秒后进行下一次访问...")
                    for _ in range(interval):
                        if not self.is_running:
                            break
                        time.sleep(1)
        except Exception as e:
            self.log_message(f"运行出错: {str(e)}")
            self.update_status("运行出错", "red")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """清理资源"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass
            
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def start_browsing(self):
        """开始浏览"""
        if not self.target_url.get():
            messagebox.showerror("错误", "请输入目标网站URL")
            return
            
        if self.visit_count.get() <= 0:
            messagebox.showerror("错误", "访问次数必须大于0")
            return
            
        self.is_running = True
        self.current_visits = 0
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 启动浏览线程
        thread = threading.Thread(target=self.browsing_thread, daemon=True)
        thread.start()
        
    def stop_browsing(self):
        """停止浏览"""
        self.is_running = False
        self.update_status("正在停止...", "orange")
        self.log_message("正在停止访问...")
        
    def test_proxy(self):
        """测试代理连接"""
        try:
            if not self.proxy_host.get() or not self.proxy_port.get():
                messagebox.showwarning("警告", "请先配置代理服务器")
                return
            self.log_message("正在测试代理连接...")
            scheme = self.detect_proxy_scheme()
            if not scheme:
                messagebox.showerror("错误", "代理不可达，请检查配置")
                return
            proxy_host = self.proxy_host.get(); proxy_port = self.proxy_port.get()
            proxy_username = self.proxy_username.get(); proxy_password = self.proxy_password.get()
            if proxy_username and proxy_password:
                u = quote(proxy_username, safe='')
                p = quote(proxy_password, safe='')
                proxy_url = f"{scheme}://{u}:{p}@{proxy_host}:{proxy_port}"
            else:
                proxy_url = f"{scheme}://{proxy_host}:{proxy_port}"
            proxy_dict = {'http': proxy_url, 'https': proxy_url}
            self.log_message(f"代理配置: {proxy_host}:{proxy_port} (协议: {scheme})")
            if proxy_username:
                self.log_message("使用认证: ****** (已URL编码)")
            response_local = requests.get('https://httpbin.org/ip', timeout=10, verify=False)
            local_ip = response_local.json().get('origin', '未知')
            self.log_message(f"本地IP地址: {local_ip}")
            response_proxy = requests.get('https://httpbin.org/ip', proxies=proxy_dict, timeout=15, verify=False)
            if response_proxy.status_code == 200:
                proxy_ip = response_proxy.json().get('origin', '未知')
                self.log_message(f"✅ 代理IP地址: {proxy_ip}")
                if proxy_ip != local_ip:
                    self.log_message("✅ 代理连接成功！IP地址已切换")
                    messagebox.showinfo("成功", f"代理测试成功！\n代理IP: {proxy_ip}\n协议: {scheme}")
                else:
                    self.log_message("⚠️ 代理IP与本地IP相同，可能代理未生效")
                    messagebox.showwarning("警告", "代理IP与本地IP相同，请检查代理配置")
            else:
                self.log_message(f"❌ 代理测试失败: HTTP {response_proxy.status_code}")
                messagebox.showerror("错误", f"代理测试失败: HTTP {response_proxy.status_code}")
            # 追加：测试目标站点
            target = self.target_url.get().strip()
            if target:
                self.log_message(f"正在通过代理测试目标站点: {target}")
                try:
                    r2 = requests.get(target, proxies=proxy_dict, timeout=20, verify=False, allow_redirects=True)
                    self.log_message(f"目标站点返回: {r2.status_code}，长度: {len(r2.content) if r2.content is not None else 0}")
                    if r2.status_code >= 400:
                        self.log_message("⚠️ 目标站点通过代理访问失败，可能被站点或代理屏蔽")
                except Exception as te:
                    self.log_message(f"❌ 目标站点代理访问异常: {te}")
                    messagebox.showwarning("提示", f"目标站点代理访问异常: {te}")
            messagebox.showinfo("完成", "代理测试完成（已包含目标站点连通性）")
        except requests.exceptions.ProxyError as e:
            self.log_message(f"❌ 代理连接失败: {str(e)}")
            messagebox.showerror("错误", f"代理连接失败: {str(e)}")
        except requests.exceptions.Timeout:
            self.log_message("❌ 代理连接超时")
            messagebox.showerror("错误", "代理连接超时，请检查代理服务器状态")
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ 网络请求失败: {str(e)}")
            messagebox.showerror("错误", f"网络请求失败: {str(e)}")
        except Exception as e:
            self.log_message(f"❌ 代理测试失败: {str(e)}")
            messagebox.showerror("错误", f"代理测试失败: {str(e)}")

    def save_config(self):
        """保存配置"""
        config = {
            "target_url": self.target_url.get(),
            "visit_count": self.visit_count.get(),
            "visit_interval": self.visit_interval.get(),
            "stay_time": self.stay_time.get(),
            "proxy_string": self.proxy_string.get(),
            "proxy_host": self.proxy_host.get(),
            "proxy_port": self.proxy_port.get(),
            "proxy_username": self.proxy_username.get(),
            "proxy_password": self.proxy_password.get(),
            "use_http_mode": self.use_http_mode.get()
        }
        
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已保存")
            self.log_message("配置已保存到 config.json")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                self.target_url.set(config.get("target_url", "https://www.example.com"))
                self.visit_count.set(config.get("visit_count", 100))
                self.visit_interval.set(config.get("visit_interval", 30))
                self.stay_time.set(config.get("stay_time", 10))
                self.proxy_string.set(config.get("proxy_string", ""))
                self.proxy_host.set(config.get("proxy_host", "127.0.0.1"))
                self.proxy_port.set(config.get("proxy_port", "1080"))
                self.proxy_username.set(config.get("proxy_username", ""))
                self.proxy_password.set(config.get("proxy_password", ""))
                self.use_http_mode.set(config.get("use_http_mode", False))
                
                self.log_message("配置已从 config.json 加载")
        except Exception as e:
            self.log_message(f"加载配置失败: {str(e)}")

    def run(self):
        """运行应用"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """关闭应用时的处理"""
        if self.is_running:
            if messagebox.askokcancel("退出", "正在运行中，确定要退出吗？"):
                self.stop_browsing()
                self.cleanup()
                self.root.destroy()
        else:
            self.root.destroy()

    def import_proxies(self):
        """从文件导入代理列表"""
        try:
            # 使用文件对话框让用户选择文件
            file_path = filedialog.askopenfilename(
                title="选择代理文件",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ],
                initialdir=os.path.dirname(os.path.abspath(__file__))
            )
            
            # 如果用户取消选择，直接返回
            if not file_path:
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("错误", f"文件不存在: {file_path}")
                return
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析代理列表
            imported_proxies = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # 跳过空行和注释
                    continue
                
                # 解析代理格式: host:port:username:password
                parts = line.split(':')
                if len(parts) >= 2:
                    proxy_info = {
                        'host': parts[0],
                        'port': parts[1],
                        'username': ':'.join(parts[2:-1]) if len(parts) >= 4 else (parts[2] if len(parts) == 3 else ''),
                        'password': parts[-1] if len(parts) >= 4 else '',
                        'full_string': line
                    }
                    imported_proxies.append(proxy_info)
                else:
                    self.log_message(f"跳过无效代理格式 (第{line_num}行): {line}")
            
            if not imported_proxies:
                messagebox.showwarning("警告", "未找到有效的代理配置")
                return
            
            # 更新代理列表
            self.proxy_list = imported_proxies
            self.current_proxy_index = 0
            
            # 更新界面显示
            self.update_proxy_list_display()
            
            # 自动设置第一个代理
            if self.proxy_list:
                self.set_current_proxy(0)
            
            self.log_message(f"✅ 成功从 {os.path.basename(file_path)} 导入 {len(imported_proxies)} 个代理配置")
            messagebox.showinfo("成功", f"成功导入 {len(imported_proxies)} 个代理配置！")
            
        except Exception as e:
            self.log_message(f"导入代理失败: {str(e)}")
            messagebox.showerror("错误", f"导入代理失败: {str(e)}")
    
    def update_proxy_list_display(self):
        """更新代理列表显示"""
        try:
            # 清空列表框
            self.proxy_listbox.delete(0, tk.END)
            
            # 添加代理到列表框
            for i, proxy in enumerate(self.proxy_list):
                display_text = f"{i+1}. {proxy['host']}:{proxy['port']}"
                if proxy['username']:
                    display_text += f" ({proxy['username']})"
                
                # 标记当前使用的代理
                if i == self.current_proxy_index:
                    display_text += " [当前]"
                
                self.proxy_listbox.insert(tk.END, display_text)
            
            # 更新总数显示
            self.proxy_count_label.config(text=f"总数: {len(self.proxy_list)}")
            
            # 选中当前代理
            if self.proxy_list and 0 <= self.current_proxy_index < len(self.proxy_list):
                self.proxy_listbox.selection_set(self.current_proxy_index)
                self.proxy_listbox.see(self.current_proxy_index)
                
        except Exception as e:
            self.log_message(f"更新代理列表显示失败: {str(e)}")
    
    def set_current_proxy(self, index):
        """设置当前使用的代理"""
        try:
            if not self.proxy_list or index < 0 or index >= len(self.proxy_list):
                return False
            
            proxy = self.proxy_list[index]
            self.current_proxy_index = index
            
            # 更新代理配置变量
            self.proxy_host.set(proxy['host'])
            self.proxy_port.set(proxy['port'])
            self.proxy_username.set(proxy['username'])
            self.proxy_password.set(proxy['password'])
            self.proxy_string.set(proxy['full_string'])
            
            # 更新显示
            self.update_proxy_list_display()
            
            self.log_message(f"🔄 切换到代理 {index+1}: {proxy['host']}:{proxy['port']}")
            return True
            
        except Exception as e:
            self.log_message(f"设置代理失败: {str(e)}")
            return False
    
    def get_next_proxy(self):
        """获取下一个代理（顺序切换，不循环）"""
        if not self.proxy_list:
            return False
        
        # 切换到下一个代理
        next_index = self.current_proxy_index + 1
        
        # 检查是否还有可用代理
        if next_index >= len(self.proxy_list):
            self.log_message("⚠️ 所有代理已用完")
            return False
        
        # 设置下一个代理
        return self.set_current_proxy(next_index)

if __name__ == "__main__":
    app = MobileBrowserSimulator()
    app.run()