# -*- coding: utf-8 -*-
# --- 授权配置 ---
# 请在此处设置授权截止日期，格式为 "YYYY-MM-DD"
# 程序将在该日期之后停止工作。
授权截止日期 = "2025-10-01"
# --- 授权配置结束 ---

import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from urllib.parse import quote
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
import random
import requests
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import json
import os
import sys
from urllib.parse import quote
import logging
from datetime import datetime, date

# --- 全局变量定义 ---

class 移动浏览器模拟器:
    """一个使用Tkinter和Selenium实现的移动浏览器模拟器，支持代理和多线程。"""

    def __init__(self, 根窗口):
        """初始化模拟器应用。"""
        self.根窗口 = 根窗口
        self.根窗口.title("移动浏览器模拟器")
        self.根窗口.geometry("1000x750")

        # --- 初始化变量 ---
        self.目标网站 = tk.StringVar()
        self.调用次数 = tk.IntVar(value=100)
        self.调用间隔 = tk.IntVar(value=5)
        self.停留时间 = tk.IntVar(value=10)
        self.代理列表 = []
        self.当前代理索引 = 0
        self.是否正在运行 = False
        self.访问线程 = None

        self.创建组件()

    def 创建组件(self):
        """创建并布局GUI组件。"""
        # 创建一个PanedWindow来实现可拖动的上下布局
        主窗格 = ttk.PanedWindow(self.根窗口, orient=VERTICAL)
        主窗格.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # --- 创建上半部分的Notebook ---
        上半部分 = ttk.Frame(主窗格)
        主窗格.add(上半部分, weight=3) # 上半部分占主要空间

        标签控制器 = ttk.Notebook(上半部分)
        标签控制器.pack(fill="both", expand=True)

        # --- 创建下半部分的日志区域 ---
        下半部分 = ttk.Frame(主窗格)
        主窗格.add(下半部分, weight=1) # 下半部分占次要空间

        # --- 创建标签页 (不再需要日志页) ---
        主控制页 = ttk.Frame(标签控制器, padding="10")
        代理配置页 = ttk.Frame(标签控制器, padding="10")

        标签控制器.add(主控制页, text='主控制')
        标签控制器.add(代理配置页, text='代理配置')

        # --- 主控制页组件 ---
        控制框架 = ttk.Labelframe(主控制页, text="核心控制", padding="10")
        控制框架.pack(fill=X, pady=5)

        ttk.Label(控制框架, text="目标网站:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(控制框架, textvariable=self.目标网站, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        ttk.Label(控制框架, text="调用次数:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(控制框架, textvariable=self.调用次数, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=W)

        ttk.Label(控制框架, text="调用间隔(秒):").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(控制框架, textvariable=self.调用间隔, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=W)

        ttk.Label(控制框架, text="停留时间(秒):").grid(row=3, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(控制框架, textvariable=self.停留时间, width=10).grid(row=3, column=1, padx=5, pady=5, sticky=W)

        按钮框架 = ttk.Frame(主控制页, padding="10")
        按钮框架.pack(fill=X, pady=10)

        self.开始按钮 = ttk.Button(按钮框架, text="开始访问", command=self.开始访问, bootstyle=SUCCESS)
        self.开始按钮.pack(side=LEFT, padx=5)

        self.停止按钮 = ttk.Button(按钮框架, text="停止访问", command=self.停止访问, bootstyle=DANGER, state=DISABLED)
        self.停止按钮.pack(side=LEFT, padx=5)

        # --- 代理配置页组件 ---
        代理框架 = ttk.Labelframe(代理配置页, text="代理管理", padding="10")
        代理框架.pack(fill=BOTH, expand=True, pady=5)

        代理按钮框架 = ttk.Frame(代理框架)
        代理按钮框架.pack(fill=X, pady=5)

        ttk.Button(代理按钮框架, text="从文件导入代理", command=self.导入代理列表).pack(side=LEFT, padx=5)
        ttk.Button(代理按钮框架, text="测试当前代理", command=self.测试代理连接).pack(side=LEFT, padx=5)

        列表框架 = ttk.Frame(代理框架)
        列表框架.pack(fill=BOTH, expand=True, pady=5)

        self.代理列表框 = scrolledtext.ScrolledText(列表框架, wrap=tk.WORD, height=15, state=DISABLED)
        self.代理列表框.pack(fill=BOTH, expand=True)

        # --- 日志组件 (现在位于下半部分) ---
        日志框架 = ttk.Labelframe(下半部分, text="程序日志", padding="10")
        日志框架.pack(fill=BOTH, expand=True, pady=5)

        self.日志文本框 = scrolledtext.ScrolledText(日志框架, wrap=tk.WORD, height=10, state=DISABLED)
        self.日志文本框.pack(fill=BOTH, expand=True)

    def 导入代理列表(self):
        """打开文件对话框以导入代理列表。"""
        文件路径 = filedialog.askopenfilename(
            title="请选择代理文件",
            filetypes=(("文本文件", "*.txt"), ("所有文件", "*.*"))
        )
        if not 文件路径:
            self.记录日志("取消了文件选择。")
            return

        try:
            with open(文件路径, 'r', encoding='utf-8') as 文件:
                原始代理 = [行.strip() for 行 in 文件 if 行.strip()]
            
            self.代理列表.clear()
            for 代理字符串 in 原始代理:
                try:
                    地址, 端口, 账号, 密码 = 代理字符串.split(':')
                    self.代理列表.append({
                        "地址": 地址,
                        "端口": int(端口),
                        "账号": 账号,
                        "密码": 密码,
                        "原始字符串": 代理字符串
                    })
                except ValueError:
                    self.记录日志(f"警告：代理格式不正确，已跳过 -> {代理字符串}")
            
            self.更新代理列表框()
            self.记录日志(f"成功导入 {len(self.代理列表)} 个代理。")

        except Exception as e:
            messagebox.showerror("导入错误", f"无法读取或解析代理文件：\n{e}")
            self.记录日志(f"错误：导入代理文件失败，原因：{e}")

    def 更新代理列表框(self):
        """用当前代理列表的内容刷新代理列表框。"""
        self.代理列表框.config(state=NORMAL)
        self.代理列表框.delete('1.0', tk.END)
        if not self.代理列表:
            self.代理列表框.insert(tk.END, "尚未导入代理。")
        else:
            for 索引, 代理 in enumerate(self.代理列表):
                self.代理列表框.insert(tk.END, f"{索引 + 1}. {代理['原始字符串']}\n")
        self.代理列表框.config(state=DISABLED)

    def 测试代理连接(self):
        """手动触发，测试下一个将要使用的代理的连通性。"""
        if not self.代理列表:
            self.记录日志("错误：代理列表为空，无法测试。")
            messagebox.showwarning("无代理", "请先导入代理列表。")
            return

        if self.当前代理索引 >= len(self.代理列表):
            self.记录日志("提示：所有代理已使用完毕，无法测试。若要重测，请重新导入。")
            messagebox.showinfo("测试完成", "所有代理都已轮换完毕。")
            return

        代理 = self.代理列表[self.当前代理索引]
        self.记录日志(f"开始手动测试代理: {代理['原始字符串']}")

        # 使用线程以避免UI阻塞
        测试线程 = threading.Thread(target=self._实际执行代理检测, args=(代理, True), daemon=True)
        测试线程.start()

    def _实际执行代理检测(self, 代理, 是否手动触发=False):
        """
        执行实际的代理检测逻辑。
        返回 (是否成功, IP地址或错误信息).
        """
        代理地址 = 代理["地址"]
        代理端口 = 代理["端口"]
        代理账号 = 代理["账号"]
        代理密码 = 代理["密码"]

        # 配置SOCKS5代理
        # 使用 socks5h 以便通过代理解析DNS
        代理设置 = {
            'http': f'socks5h://{quote(代理账号)}:{quote(代理密码)}@{代理地址}:{代理端口}',
            'https': f'socks5h://{quote(代理账号)}:{quote(代理密码)}@{代理地址}:{代理端口}'
        }
        
        测试网址 = "https://httpbin.org/ip" # 使用https
        try:
            self.记录日志(f"正在通过代理 {代理地址}:{代理端口} 请求IP地址...")
            响应 = requests.get(测试网址, proxies=代理设置, timeout=15) # 增加超时
            响应.raise_for_status()  # 如果状态码不是200-299，则引发HTTPError
            
            返回的IP = 响应.json()["origin"]
            self.记录日志(f"✅ 代理测试成功！IP: {返回的IP}")
            if 是否手动触发:
                messagebox.showinfo("测试成功", f"代理可用！\n检测到的IP地址是：{返回的IP}")
            return True, 返回的IP

        except requests.exceptions.ProxyError as e:
            错误消息 = f"代理连接错误: {e}"
            self.记录日志(f"❌ 代理测试失败: {错误消息}")
            if 是否手动触发:
                messagebox.showerror("测试失败", f"代理连接失败！\n错误详情: {错误消息}")
            return False, "代理连接错误"
        except requests.exceptions.ConnectTimeout:
            错误消息 = "连接超时"
            self.记录日志(f"❌ 代理测试失败: {错误消息}。")
            if 是否手动触发:
                messagebox.showerror("测试失败", f"代理连接超时！\n请检查代理服务器地址、端口和网络连接。")
            return False, 错误消息
        except requests.exceptions.RequestException as e:
            错误消息 = f"请求异常: {e}"
            self.记录日志(f"❌ 代理测试失败: {错误消息}")
            if 是否手动触发:
                messagebox.showerror("测试失败", f"请求失败！\n错误详情: {错误消息}")
            return False, 错误消息
        except Exception as e:
            错误消息 = f"发生未知错误: {e}"
            self.记录日志(f"❌ 代理测试失败: {错误消息}")
            if 是否手动触发:
                messagebox.showerror("测试失败", f"发生未知错误！\n错误详情: {错误消息}")
            return False, 错误消息


    def 开始访问(self):
        """开始自动化访问流程"""
        if self.是否正在运行:
            messagebox.showwarning("提示", "访问任务正在运行中。")
            return

        目标网站 = self.目标网站.get().strip()
        if not 目标网站:
            messagebox.showerror("错误", "请填写目标网站地址。")
            return

        try:
            self.调用次数.get()
            self.调用间隔.get()
            self.停留时间.get()
        except (tk.TclError, ValueError):
            messagebox.showerror("错误", "调用次数、调用间隔和停留时间必须是有效的整数。")
            return

        if not self.代理列表:
            messagebox.showwarning("无代理", "代理列表为空，无法开始任务。")
            return

        self.是否正在运行 = True
        self.开始按钮.config(state=DISABLED)
        self.停止按钮.config(state=NORMAL)
        self.记录日志("自动化访问任务开始。")
        self.当前代理索引 = 0  # 每次开始都从第一个代理开始

        self.访问线程 = threading.Thread(target=self.运行访问循环, daemon=True)
        self.访问线程.start()

    def 停止访问(self):
        """停止自动化访问流程"""
        if not self.是否正在运行:
            return
        self.是否正在运行 = False
        self.记录日志("用户请求停止访问... 任务将在当前循环结束后终止。")
        # UI状态由_访问任务结束后的清理函数统一处理，以避免竞态条件
        self.停止按钮.config(state=DISABLED) # 立即禁用停止按钮，防止重复点击

    def 运行访问循环(self):
        """在后台线程中执行实际的访问逻辑"""
        # 注意: 此功能需要安装 selenium-wire (`pip install selenium-wire`)
        # 并且需要在文件顶部添加 `from seleniumwire import webdriver`

        调用次数 = self.调用次数.get()
        调用间隔 = self.调用间隔.get()
        停留时间 = self.停留时间.get()
        目标网站 = self.目标网站.get().strip()

        for i in range(调用次数):
            if not self.是否正在运行:
                self.记录日志("检测到停止信号，访问流程终止。")
                break

            self.记录日志(f"--- 开始第 {i + 1}/{调用次数} 轮访问 ---")

            if self.当前代理索引 >= len(self.代理列表):
                self.记录日志("所有代理已使用完毕，任务结束。")
                break

            代理信息 = self.代理列表[self.当前代理索引]
            self.记录日志(f"正在使用代理: {代理信息['原始字符串']}")

            # 自动进行代理连通性检测
            成功, _ = self._实际执行代理检测(代理信息, 是否手动触发=False)
            if not 成功:
                self.记录日志(f"代理 {代理信息['原始字符串']} 检测失败，跳过。")
                self.当前代理索引 += 1
                continue

            driver = None
            try:
                # --- selenium-wire 代理配置 ---
                seleniumwire_options = {
                    'proxy': {
                        'http': f'socks5h://{代理信息["账号"]}:{代理信息["密码"]}@{代理信息["地址"]}:{代理信息["端口"]}',
                        'https': f'socks5h://{代理信息["账号"]}:{代理信息["密码"]}@{代理信息["地址"]}:{代理信息["端口"]}',
                        'no_proxy': 'localhost,127.0.0.1'
                    },
                    'verify_ssl': False  # 禁用SSL证书验证，作为解决连接问题的辅助手段
                }

                chrome_options = ChromeOptions()
                chrome_options.add_argument(f'--user-agent={UserAgent().random}')
                chrome_options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
                chrome_options.add_argument("--ignore-certificate-errors") # 浏览器级别也忽略证书错误

                # 创建driver实例，并传入selenium-wire的选项
                driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)

                self.记录日志(f"浏览器已启动，通过selenium-wire代理访问: {目标网站}")
                driver.get(目标网站)

                self.记录日志(f"页面加载成功，将停留 {停留时间} 秒。")
                time.sleep(停留时间)

            except Exception as e:
                self.记录日志(f"❌ 访问过程中发生错误: {e}")
            finally:
                if driver:
                    driver.quit()
                    self.记录日志("浏览器已关闭。")

            self.当前代理索引 += 1

            if i < 调用次数 - 1 and self.是否正在运行:
                self.记录日志(f"本轮访问结束，将等待 {调用间隔} 秒后继续。")
                time.sleep(调用间隔)

        self.根窗口.after(0, self._访问任务结束后的清理)

    def _访问任务结束后的清理(self):
        """在主线程中执行访问任务结束后的UI清理工作"""
        self.是否正在运行 = False
        self.开始按钮.config(state=NORMAL)
        self.停止按钮.config(state=DISABLED)
        
        if not self.代理列表 or self.当前代理索引 >= len(self.代理列表):
             self.记录日志("自动化访问任务完成。所有可用代理均已使用。")
        else:
             self.记录日志("自动化访问任务完成。")
        
        messagebox.showinfo("完成", "自动化访问任务已完成。")

    def 记录日志(self, 消息):
        """向日志文本框中添加一条带时间戳的日志。"""
        时间戳 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.日志文本框.config(state=NORMAL)
        self.日志文本框.insert(tk.END, f"[{时间戳}] {消息}\n")
        self.日志文本框.config(state=DISABLED)
        self.日志文本框.see(tk.END)

if __name__ == "__main__":
    try:
        截止日期 = datetime.strptime(授权截止日期, "%Y-%m-%d").date()
        今天 = date.today()

        if 今天 > 截止日期:
            # 使用一个临时的tk根窗口来显示messagebox，然后销毁它
            临时根窗口 = tk.Tk()
            临时根窗口.withdraw() # 隐藏临时窗口
            messagebox.showerror("授权已过期", f"您的软件使用授权已于 {授权截止日期} 到期，请联系管理员续期。")
            临时根窗口.destroy()
            sys.exit() # 退出程序

    except (ValueError, NameError):
        # 如果日期格式错误或变量不存在，也阻止程序运行
        临时根窗口 = tk.Tk()
        临时根窗口.withdraw()
        messagebox.showerror("授权配置错误", "授权配置文件损坏或格式不正确，请联系管理员。")
        临时根窗口.destroy()
        sys.exit()

    根窗口 = ttk.Window(themename="superhero")
    应用 = 移动浏览器模拟器(根窗口)
    根窗口.mainloop()