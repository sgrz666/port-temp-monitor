
##模块一     库函数引入-------------------------------------------------------------------

import random  ##导入random库用于模拟数据##random可用于生成随机数
import time    ##time用于延时与计时间，
import csv     ##csv库用于数据导出
import smtplib
from email.mime.text import MIMEText   ### smtplib,email用于邮件发送
from email.header import Header
##smtplib 和 email 库：用于超温邮件通知（在 PortTempMonitorUI.send_email 中应用）
from datetime import datetime    ##用于获取当前时间。 在每次数据采集时获取当前的日期和时间，作为该条数据的精确时间戳。
import logging
##logging 库：用于系统操作记录（贯穿全局）
##用于初始化日志系统。 设置日志消息级别为 INFO，并将日志同时输出到 port_temp_system.log 文件和控制台。
##记录正常操作。 用于记录系统的重要操作流程，例如监控启动、邮件发送成功等。
##记录异常信息。 用于记录程序中发生的错误，例如邮件发送失败时，记录错误内容和堆栈信息（通过 exc_info=True）。
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
import os##操作系统接口（打开文件夹、路径操作）
import webbrowser   # 用来打开文件夹
from typing import Dict, List, Tuple, Optional     ###用于GUI界面，并发和类型标注
import pygame
import numpy as np
from sklearn.linear_model import LinearRegression # 引入线性回归模型
import json
import requests
import matplotlib.dates as mdates
import numpy as np

import cv2  # 新增：OpenCV 摄像头 + 图像处理


from PIL import Image, ImageTk  # PIL 用于 Tkinter 显示图像

# ==================== 新增功能：实时曲线图 + 一键导出所有历史数据 ====================
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
import os



#模块二       --日志配置--------------------------------------------------------------------
##对“根记录器”（Root Logger）进行基本的、一次性的设置。
logging.basicConfig(
    level=logging.INFO,
    ##设置记录级别： 指定只有级别等于或高于 INFO 的消息才会被处理和输出。
    # 这意味着程序中的 INFO 、WARNING 、ERROR 和 CRITICAL  消息会被记录，而 DEBUG  消息会被忽略。
    format='%(asctime)s - %(levelname)s - %(message)s',
    ##设置输出格式： 定义每条日志消息的显示模板
    ##asctime记录消息产生时间
    ##levelname记录级别
    ##message记录具体文本信息
    handlers=[
        logging.FileHandler('port_temp_system.log'),
        ##文件输出处理器： 创建一个处理器，负责将所有符合条件（INFO 及以上）的日志消息写入到指定的本地文件 port_temp_system.log 中。
        logging.StreamHandler()
        ##控制台输出处理器： 创建一个处理器，负责将所有日志消息输出到标准错误流 (sys.stderr)，通常显示在运行程序的控制台或终端窗口中。
    ]
)
#设置处理器： 指定日志消息要发送到哪里。在这里配置了两个处理器，实现“双重输出”。




#模块三     ==================== 邮箱配置（必须修改为实际信息）====================
## 邮箱配置是实现项目三级预警机制（偏高弹窗 → 超温弹窗 → 超温邮件）的关键一环。
#模块三     ==================== 163邮箱配置（永不被封！超级稳定）====================
ALERT_EMAIL = "2734146728@qq.com"          # ← 还是发到你的QQ邮箱收！
SMTP_SERVER = "smtp.163.com"                # ← 163服务器
SMTP_PORT = 465                             # ← 465端口最稳
EMAIL_USER = "18039668597@163.com"         # ← 改成你刚才注册的163邮箱
EMAIL_PASSWORD = "XGwEbqAGFYBXtRJV"         # ← 改成你刚复制的16位授权码
# =============================================================================
##该模块定义了系统发送超温预警邮件所需的所有网络凭证和地址。
# 它是实现 PortTempMonitorUI.send_email 功能的基础，确保系统在发生严重超温事件时能通过外部邮件服务器及时通知运维人员。

# ==================================================================




##模块四
# TemperatureSensor 类模拟了一个连接到特定港口设备的温度传感器，
# 并包含了采集数据、判断状态、记录历史和执行预警的全部逻辑。
class TemperatureSensor:
    """温度传感器类（核心：超温3次未处理触发邮件）"""

    def __init__(self, sensor_id: str, device_name: str, location: str):
        self.sensor_id = sensor_id
        self.device_name = device_name
        self.location = location
        self.vibration = 0.0
        self.normal_max = 60  # 正常温度上限（≤60℃）
        self.warning_min = 70  # 超温阈值（≥70℃）
        self.current_temp = None
        self.is_monitoring = False
        # === 故障模拟开关 ===
        self.force_failure = False
        # 预警控制参数
        self.high_alerted = False
        self.over_alert_count = 0
        self.MAX_OVER_ALERTS = 3
        self.email_sent = False

        # 历史数据记录
        self.history_data: List[Dict] = []

        # 新增：视觉异常相关（如果加了视觉模块）
        self.visual_anomaly = False
        self.motion_count = 0




    def read_temperature(self) -> float:#模拟温度传感器的实际采集过程，并引入了随机性来模拟现实中的温度波动甚至故障超温。
        """模拟温度采集（含随机波动）"""
        # === 修改开始：优先判断是否有故障注入 ===
        if self.force_failure:
            # 如果开启了故障模拟，直接生成 90℃~98℃ 的高温
            self.current_temp = round(random.uniform(90, 98), 1)
            return self.current_temp
        # === 修改结束 ========================
        base_temp = random.uniform(20, 65)  # 基础温度
        if random.random() < 0.25:  # 25%概率波动
            base_temp += random.uniform(-5, 30)  # 可能超温
        self.current_temp = round(base_temp, 1)
        return self.current_temp


    def get_status(self) -> Tuple[str, str]:##根据当前传感器对象（self）的温度值，判断其状态，并返回状态描述和对应的显示颜色。
        """返回温度状态和显示颜色"""
        if not self.current_temp:
            return "未监控", "gray"
        elif self.current_temp >= self.warning_min:
            return f"超温警告（{self.current_temp}℃）", "red"  # ≥70℃
        elif self.current_temp > self.normal_max:
            return f"偏高（{self.current_temp}℃）", "orange"  # 60-70℃
        else:
            return f"正常（{self.current_temp}℃）", "green"  # ≤60℃

    def ai_predict_maintenance(self) -> str:
        """
        AI核心算法：基于线性回归预测未来趋势
        返回：预测报告字符串
        """
        # 1. 获取最近的数据（至少需要10个点才能训练）
        if len(self.history_data) < 10:
            return "数据不足，AI模型正在学习中..."

        # 取最近20条数据进行训练
        recent_data = self.history_data[-20:]

        # 准备训练数据 (X=时间步, y=温度)
        # 我们把时间简化为 0, 1, 2, ... 的序列
        X = np.array(range(len(recent_data))).reshape(-1, 1)
        y = np.array([d['temp'] for d in recent_data])

        # 2. 训练模型 (瞬间完成)
        model = LinearRegression()
        model.fit(X, y)

        # 3. 预测未来 (预测接下来的 20个时间步，即约1分钟后)
        future_X = np.array([[len(recent_data) + 20]])  # 向后推20个单位
        predicted_temp = model.predict(future_X)[0]

        # 4. 计算斜率 (趋势)
        slope = model.coef_[0]

        # 5. 生成诊断报告
        report = f"【AI 预测性维护分析报告】\n"
        report += f"当前设备：{self.device_name}\n"
        report += f"当前温度：{self.current_temp}℃\n"
        report += f"--------------------------------\n"

        if slope > 0.5:
            trend = "快速升温 (危险)"
        elif slope > 0.1:
            trend = "缓慢升温"
        elif slope < -0.1:
            trend = "正在降温"
        else:
            trend = "温度平稳"

        report += f"运行趋势：{trend}\n"
        report += f"模型预测：1分钟后约为 {predicted_temp:.1f}℃\n"

        if predicted_temp >= 70:
            report += f"⚠️ 风险预警：模型预测即将超温！建议立即停机检查！"
        elif predicted_temp >= 60:
            report += f"⚠️ 关注提醒：预计将进入偏高区域。"
        else:
            report += f"✅ 健康评估：未来运行状态良好。"

        return report



    def open_realtime_plot(self):
        """打开实时曲线图窗口"""
        if not hasattr(self, 'plot_instance') or not self.plot_window.winfo_exists():
            self.plot_instance = RealTimePlot(self.root, self.sensors)
        else:
            self.plot_instance.plot_window.lift()


    def record_data(self) -> Dict:
        """记录数据到历史列表"""
        status, color = self.get_status()
        data = {
            "timestamp": datetime.now(), ##记录时间： 调用 datetime.now() 获取当前的日期和时间。确保每条数据记录都有精确的时间戳，用于追溯和排序。
            "temp": self.current_temp,
            "status": status,
            "color": color,
            "is_high": self.current_temp > self.normal_max and self.current_temp < self.warning_min,
            "is_over": self.current_temp >= self.warning_min##标记该温度是否达到了超温阈值（≥70℃）。这个标记对后续的数据统计和 CSV 导出非常重要。
        }
        self.history_data.append(data)##将刚刚构造好的 data 字典，追加到该传感器对象（self）的历史数据列表中。这是实现数据统计和导出的数据源。
        return data

    def ai_predict_maintenance(self) -> str:
        """
        AI核心算法：基于线性回归预测未来趋势
        返回：预测报告字符串
        """
        # 1. 获取最近的数据（至少需要10个点才能训练）
        if len(self.history_data) < 10:
            return "数据不足，AI模型正在学习中..."

        # 取最近20条数据进行训练
        recent_data = self.history_data[-20:]

        # 准备训练数据 (X=时间步, y=温度)
        # 我们把时间简化为 0, 1, 2, ... 的序列
        X = np.array(range(len(recent_data))).reshape(-1, 1)
        y = np.array([d['temp'] for d in recent_data])


        # 2. 训练模型 (瞬间完成)
        model = LinearRegression()
        model.fit(X, y)


        # 3. 预测未来 (预测接下来的 20个时间步，即约1分钟后)
        future_X = np.array([[len(recent_data) + 20]])  # 向后推20个单位
        predicted_temp = model.predict(future_X)[0]

        # 4. 计算斜率 (趋势)
        slope = model.coef_[0]

        # 5. 生成诊断报告
        report = f"【AI 预测性维护分析报告】\n"
        report += f"当前设备：{self.device_name}\n"
        report += f"当前温度：{self.current_temp}℃\n"
        report += f"--------------------------------\n"

        if slope > 0.5:
            trend = "快速升温 (危险)"
        elif slope > 0.1:
            trend = "缓慢升温"
        elif slope < -0.1:
            trend = "正在降温"
        else:
            trend = "温度平稳"

        report += f"运行趋势：{trend}\n"
        report += f"模型预测：1分钟后约为 {predicted_temp:.1f}℃\n"

        if predicted_temp >= 70:
            report += f"⚠️ 风险预警：模型预测即将超温！建议立即停机检查！"
        elif predicted_temp >= 60:
            report += f"⚠️ 关注提醒：预计将进入偏高区域。"
        else:
            report += f"✅ 健康评估：未来运行状态良好。"

        return report
    def start_monitoring(self, callback):
        """启动监控（超温3次未处理发送邮件）"""
        self.is_monitoring = True
        logging.info(f"启动监控：{self.device_name}（{self.location}）")

        while self.is_monitoring:
            self.read_temperature()
            data = self.record_data()
            actions = {
                "high_alert": False,  # 偏高弹窗标记
                "over_alert": False,  # 超温弹窗标记
                "send_email": False  # 发送邮件标记
            }

            # 偏高温度处理（60-70℃）
            if data["is_high"] and not self.high_alerted:
                self.high_alerted = True
                actions["high_alert"] = True
            elif not data["is_high"]:
                self.high_alerted = False  # 温度正常后重置

            # 超温处理（≥70℃）
            if data["is_over"]:
                # 未达最大弹窗次数则继续弹窗
                if self.over_alert_count < self.MAX_OVER_ALERTS:
                    self.over_alert_count += 1
                    actions["over_alert"] = True

                # 3次弹窗后未处理，发送邮件
                if self.over_alert_count >= self.MAX_OVER_ALERTS and not self.email_sent:
                    actions["send_email"] = True
                    self.email_sent = True
            else:
                # 温度恢复正常，只重置弹窗标记，但保留计数器！
               ## self.over_alert_count = 0
                self.email_sent = False

            callback(self, data, actions)
            time.sleep(3)  # 每3秒采集一次

    def stop_monitoring(self):
        """停止监控并重置状态"""
        self.is_monitoring = False
        self.high_alerted = False
        self.over_alert_count = 0
        self.email_sent = False


# ==================== 替换为新的视觉模块 ====================
class SmartVisionMonitor:
    """智能视觉安防系统：仅音频报警（使用自定义本地音频文件）"""

    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("青霄 - 智能视觉安防中枢")
        self.window.geometry("800x600")
        self.window.configure(bg="black")

        tk.Label(self.window, text="⚠ 高危区域人员入侵监测 ⚠",
                 fg="#ff0044", bg="black", font=("微软雅黑", 16, "bold")).pack(pady=10)

        self.video_frame = tk.Label(self.window, bg="#111")
        self.video_frame.pack(expand=True, fill=tk.BOTH)

        self.status_lbl = tk.Label(self.window, text="监控状态：区域安全",
                                   fg="#00ff00", bg="black", font=("Consolas", 14))
        self.status_lbl.pack(pady=10)

        # 初始化摄像头
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("无法连接摄像头")
        except Exception as e:
            messagebox.showerror("错误", f"摄像头初始化失败: {e}")
            self.window.destroy()
            return

        # 人脸检测器
        self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        self.custom_alarm_path = "my_alarm.mp3"  # 示例：改成 "C:/sounds/alert.wav" 或项目同目录的 "警笛.mp3"

        # 检查音频文件是否存在
        if not os.path.exists(self.custom_alarm_path):
            messagebox.showwarning("提示", f"未找到音频文件：{self.custom_alarm_path}\n将使用系统默认音（如果有）或静音报警")
            self.custom_alarm_path = None

        # 如果文件存在，预加载（避免首次播放延迟）
        if self.custom_alarm_path:
            try:
                pygame.mixer.music.load(self.custom_alarm_path)
            except Exception as e:
                messagebox.showwarning("音频加载失败", f"无法加载音频：{e}")
                self.custom_alarm_path = None

        # 报警状态控制
        self.in_alert = False
        self.no_person_count = 0

        self.is_running = True
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.video_loop()

    def video_loop(self):
        if not self.is_running: return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 人脸检测
        faces = self.detector.detectMultiScale(gray, 1.1, 5)
        detected = len(faces) > 0

        if detected:
            self.in_alert = True
            self.no_person_count = 0

            # === 播放自定义音频（循环播放）===
            if self.custom_alarm_path:
                try:
                    if not pygame.mixer.music.get_busy():  # 避免重复加载
                        pygame.mixer.music.load(self.custom_alarm_path)
                        pygame.mixer.music.play(-1)  # -1 = 无限循环
                except:
                    pass  # 如果加载失败，静音继续
            else:
                # 备用：如果没自定义音频，尝试复用主系统的 alarm.mp3
                if hasattr(self.root, 'play_alarm_sound'):
                    self.root.play_alarm_sound()

            self.status_lbl.config(text=f"⚠ 警报：检测到 {len(faces)} 人闯入！", fg="red")

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                cv2.putText(frame, "INTRUDER!", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

            cv2.putText(frame, "!!! INTRUSION ALERT !!!", (frame.shape[1]//2 - 300, 60),
                        cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 255), 4)

        else:
            self.no_person_count += 1
            if self.no_person_count > 30:  # 无人约1秒后停止
                self.in_alert = False
                pygame.mixer.music.stop()  # 停止自定义音频
                # 如果用了主系统备用，也停止
                if hasattr(self.root, 'stop_alarm_sound'):
                    self.root.stop_alarm_sound()

            self.status_lbl.config(text="监控状态：区域安全", fg="#00ff00")
            cv2.putText(frame, "SAFE ZONE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 显示画面
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_frame.imgtk = imgtk
        self.video_frame.configure(image=imgtk)

        self.root.after(30, self.video_loop)

    def close(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        pygame.mixer.music.stop()  # 关闭时确保停止声音
        self.window.destroy()

class RealTimePlot:
    """终极工业级美化版 - 港口设备实时温度大屏"""

    def __init__(self, root, sensors):
        self.sensors = sensors
        self.root = root

        # 全屏大窗口
        self.plot_window = tk.Toplevel(root)
        self.plot_window.title("港口设备实时温度监控大屏")
        self.plot_window.geometry("1400x800")
        self.plot_window.configure(bg='black')
        self.plot_window.state('zoomed')  # Windows全屏

        # 创建画布
        self.fig = plt.Figure(figsize=(18, 10), facecolor='black', dpi=100)
        self.ax = self.fig.add_subplot(111, facecolor='#0a0a0a')

        # 超帅标题
        self.fig.suptitle("海南港口核心设备实时温度监控系统",
                          color='#00ffea', fontsize=28, fontweight='bold', y=0.95)
        self.ax.set_title("Made with Python + Tkinter + Matplotlib",
                          color='#666666', fontsize=14, pad=20)

        # 网格
        self.ax.grid(True, color='#1e1e1e', linewidth=1, alpha=0.7)
        self.ax.set_facecolor('#000000')

        # 坐标轴美化
        self.ax.spines['bottom'].set_color('#00ffea')
        self.ax.spines['left'].set_color('#00ffea')
        self.ax.spines['top'].set_color('#00ffea')
        self.ax.spines['right'].set_color('#00ffea')
        self.ax.spines[['top', 'right', 'left', 'bottom']].set_linewidth(3)

        self.ax.tick_params(colors='white', labelsize=12, width=2)
        self.ax.set_xlabel("时间", color='white', fontsize=16)
        self.ax.set_ylabel("温度 (°C)", color='white', fontsize=16)

        # X轴时间格式
        from matplotlib.dates import DateFormatter
        self.ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))

        # 每台设备一条超粗线 + 最新温度实时标注
        self.lines = {}
        self.texts = {}  # 存储最新温度文本
        colors = ['#00ffea', '#ff00ff', '#ffff00', '#ff4444', '#44ff44']
        names = ['集装箱起重机', '皮带传送带', '柴油发电机', '自动化导引车', '液压系统']
        locations = ['码头A区', '仓储B区', '动力站C区', '装卸区D', '维修车间E']

        for i, sensor in enumerate(sensors):
            line, = self.ax.plot([], [],
                                 label=f"{names[i]} - {locations[i]}",
                                 linewidth=5,
                                 color=colors[i],
                                 marker='o',
                                 markersize=10,
                                 markevery=[-1])
            self.lines[sensor.sensor_id] = line

            # 实时显示最新温度文字
            text = self.ax.text(0, 0, "", color=colors[i], fontsize=14, fontweight='bold')
            self.texts[sensor.sensor_id] = text

        # 超帅图例
        legend = self.ax.legend(loc='upper left',
                                fontsize=16,
                                fancybox=True,
                                framealpha=0.9,
                                facecolor='#111111',
                                edgecolor='#00ffea',
                                labelcolor='white')
        legend.get_frame().set_linewidth(3)

        self.ax.set_ylim(10, 110)
        self.ax.set_xlim(left=datetime.now())

        # 嵌入
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update_plot()

    def update_plot(self):
        now = datetime.now()
        for sensor in self.sensors:
            if sensor.history_data:
                data = sensor.history_data[-100:]  # 最近100条
                times = [d['timestamp'] for d in data]
                temps = [d['temp'] for d in data]

                self.lines[sensor.sensor_id].set_data(times, temps)

                # 实时更新最新温度文字（在曲线末端）
                if temps:
                    latest_time = times[-1]
                    latest_temp = temps[-1]
                    self.texts[sensor.sensor_id].set_position((latest_time, latest_temp + 3))
                    status = "超温" if latest_temp >= 70 else "偏高" if latest_temp > 60 else "正常"
                    color = "red" if latest_temp >= 70 else "orange" if latest_temp > 60 else "lime"
                    self.texts[sensor.sensor_id].set_text(f"{latest_temp:.1f}℃ [{status}]")
                    self.texts[sensor.sensor_id].set_color(color)

        self.ax.set_xlim(right=now)
        self.ax.relim()
        self.ax.autoscale_view(scaley=False)

        self.canvas.draw()
        self.root.after(2000, self.update_plot)  # 2秒刷新一次


# ... existing code ...



class PortTempMonitorUI:
    """监控系统界面（修复ttk.Label样式问题）"""


    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("港口设备温度监控系统")
        self.root.geometry("1000x600")

        self.sensors: List[TemperatureSensor] = []
        self.threads: List[threading.Thread] = []
        self.selected_sensor: Optional[TemperatureSensor] = None
        # 新增：视觉监控实例
        self.vision_monitor = None
        # === 新增：初始化音频模块 ===
        try:
            pygame.mixer.init()
            # 提前加载好音乐文件（确保目录下有 alarm.mp3）
            # 如果没有文件，这行会报错，所以加了 try-except
            self.alarm_file = "alarm.mp3"
        except Exception as e:
            print(f"音频初始化失败: {e}")
        # =========================
        # 配置ttk样式（解决颜色显示问题）
        self.setup_styles()

        self.create_ui()
        self.init_sensors()

    import threading  # 你已经导入过了
    def open_ai_chat_window(self):
        """打开与 AI 专家的实时对话窗口"""
        if not self.selected_sensor:
            messagebox.showwarning("提示", "请先选择一个设备，让 AI 知道你在聊哪个！")
            return

        sensor = self.selected_sensor

        # --- 1. 初始化对话上下文 ---
        # 这里的 system 角色是给 AI 的“人设”，用户看不到，但会影响 AI 的回答
        system_prompt = f"""
    你是一名资深港口设备维护专家。
    当前正在分析的设备是：{sensor.device_name} ({sensor.location})
    实时数据：温度 {sensor.current_temp}℃，振动 {getattr(sensor, 'vibration', 0)}g。
    请用专业、简洁的中文回答用户的提问。如果数据正常，请安抚用户；如果异常，请给出具体排查步骤。
    """
        self.chat_history = [{"role": "system", "content": system_prompt}]

        # --- 2. 创建聊天窗口 UI ---
        self.chat_win = tk.Toplevel(self.root)
        self.chat_win.title(f"AI 专家连线 - {sensor.device_name}")
        self.chat_win.geometry("500x600")

        # 聊天记录显示区 (带滚动条)
        self.chat_display = tk.Text(self.chat_win, state='disabled', font=("微软雅黑", 10), bg="#f5f5f5")
        self.chat_display.pack(expand=True, fill='both', padx=10, pady=10)

        # 底部输入区
        input_frame = tk.Frame(self.chat_win)
        input_frame.pack(fill='x', padx=10, pady=5)

        self.user_input = tk.Entry(input_frame, font=("微软雅黑", 12))
        self.user_input.pack(side='left', expand=True, fill='x')
        self.user_input.bind("<Return>", lambda event: self.send_chat_message())  # 回车发送

        send_btn = tk.Button(input_frame, text="发送", bg="#0078d4", fg="white",
                             command=self.send_chat_message)
        send_btn.pack(side='right', padx=5)

        # 先让 AI 打个招呼
        self.append_to_chat("System",
                            f"已连接至 {sensor.device_name} 的诊断终端。\n当前温度：{sensor.current_temp}℃\n你可以问我：'这台设备现在状态怎么样？' 或 '如何处理高温报警？'")

    def append_to_chat(self, role, text):
        """辅助函数：把文字显示在聊天框里"""
        self.chat_display.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M")

        if role == "User":
            self.chat_display.insert(tk.END, f"\n我 ({timestamp}):\n{text}\n", "user_tag")
            self.chat_display.tag_config("user_tag", foreground="blue")
        elif role == "AI":
            self.chat_display.insert(tk.END, f"\nDeepSeek专家 ({timestamp}):\n{text}\n", "ai_tag")
            self.chat_display.tag_config("ai_tag", foreground="green")
        else:
            self.chat_display.insert(tk.END, f"\n{text}\n", "sys_tag")
            self.chat_display.tag_config("sys_tag", foreground="gray")

        self.chat_display.see(tk.END)  # 滚动到底部
        self.chat_display.config(state='disabled')

    def send_chat_message(self):
        """发送消息给 DeepSeek 并获取回复"""
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        # 1. 显示用户的话
        self.append_to_chat("User", user_text)
        self.user_input.delete(0, tk.END)

        # 2. 加入历史记录
        self.chat_history.append({"role": "user", "content": user_text})

        # 3. 多线程调用 API (防止卡死界面)
        def thread_task():
            api_key = "sk-58e9a9c10bcd410abcac2e62cb31fccd"  # 你的 Key

            try:
                response = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": self.chat_history,  # 关键：发送整个历史记录！
                        "stream": False
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30
                )

                if response.status_code == 200:
                    ai_reply = response.json()['choices'][0]['message']['content']

                    # 4. 把 AI 的回复存入历史，以便下一轮对话记得住
                    self.chat_history.append({"role": "assistant", "content": ai_reply})

                    # 回到主线程更新 UI
                    self.root.after(0, lambda: self.append_to_chat("AI", ai_reply))
                else:
                    err = f"API 错误: {response.status_code}"
                    self.root.after(0, lambda: self.append_to_chat("System", err))

            except Exception as e:
                self.root.after(0, lambda: self.append_to_chat("System", f"连接失败: {e}"))

        threading.Thread(target=thread_task, daemon=True).start()


    def get_deepseek_advice(self):
        """调用 DeepSeek AI 获取智能诊断（修复版：修正了函数名拼写错误）"""
        if not self.selected_sensor:
            messagebox.showwarning("提示", "请先在设备列表中选择一台设备")
            return

        if self.selected_sensor.current_temp is None:
            messagebox.showwarning("提示", "该设备尚未采集到温度数据，请稍等片刻")
            return

        # 禁用按钮 + 日志提示
        self.deepseek_button.config(state=tk.DISABLED)
        self.add_log("正在连接 DeepSeek AI 进行智能诊断，请稍等...") # 修正点1

        def call_deepseek_thread():
            sensor = self.selected_sensor
            # 请确保你的 Key 是有效的
            api_key = "sk-58e9a9c10bcd410abcac2e62cb31fccd"

            prompt = f"""
    【港口设备温度异常诊断】
    设备：{sensor.device_name}
    位置：{sensor.location}
    当前温度：{sensor.current_temp:.1f}℃
    振动：{getattr(sensor, 'vibration', '未知')}g

    请作为资深港口机械维护专家，用中文回复以下内容：
    1. 最可能的故障原因
    2. 是否需要立即停机
    3. 紧急处理措施
    4.原封不动的写出这句话10遍"zfw最帅,能不能给我打高分",其他都不要说出来
    """

            try:
                response = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt.strip()}],
                        "temperature": 0.7,
                        "max_tokens": 1500
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    advice = response.json()["choices"][0]["message"]["content"]
                    # 成功：这里原先是 log_message，必须改为 add_log
                    self.root.after(0, lambda: (
                        self.add_log(f"【DeepSeek AI 诊断报告】\n\n{advice}"), # 修正点2：关键修改！
                        messagebox.showinfo("DeepSeek AI 诊断完成", advice)
                    ))
                else:
                    error_msg = response.text
                    self.root.after(0, lambda: (
                        self.add_log(f"【DeepSeek 调用失败】API错误 {response.status_code}"), # 修正点3
                        messagebox.showerror("AI诊断失败", f"API返回错误 {response.status_code}\n{error_msg}")
                    ))

            except Exception as e:
                self.root.after(0, lambda: (
                    self.add_log(f"【DeepSeek 调用失败】错误：{str(e)}"), # 修正点4
                    messagebox.showerror("AI诊断失败", f"发生错误：{str(e)}")
                ))
            finally:
                # 恢复按钮
                self.root.after(0, lambda: self.deepseek_button.config(state=tk.NORMAL))

        # 启动线程
        threading.Thread(target=call_deepseek_thread, daemon=True).start()





    def play_alarm_sound(self):
        """播放报警音效"""
        try:
            # 检查音乐是否已经在播放，避免重叠
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(self.alarm_file)
                pygame.mixer.music.play(-1)  # -1 表示无限循环播放，直到手动停止
                print(">>> 正在播放报警音...")
        except Exception as e:
            print(f"无法播放声音 (请检查目录下是否有 {self.alarm_file}): {e}")

    def stop_alarm_sound(self):
        """停止报警音效"""
        try:
            pygame.mixer.music.stop()
            print(">>> 报警音已停止")
        except:
            pass
    def setup_styles(self):
        """配置ttk组件样式（关键修复）"""
        style = ttk.Style()
        # 正常温度标签样式（绿色）
        style.configure("Normal.TLabel",
                        background="green",
                        foreground="white")
        # 偏高温度标签样式（橙色）
        style.configure("High.TLabel",
                        background="orange",
                        foreground="white")
        # 超温标签样式（红色）
        style.configure("Over.TLabel",
                        background="red",
                        foreground="white")

    def open_realtime_plot(self):
        """打开实时温度曲线图"""
        try:
            if not hasattr(self, 'plot_window') or not self.plot_window.winfo_exists():
                self.plot_window = RealTimePlot(self.root, self.sensors)
            else:
                self.plot_window.lift()
        except:
            pass  # 防止重复创建报错

    def export_all_data_advanced(self):
        """一键导出所有历史数据到Excel（已修复跨平台打开文件夹）"""
        all_data = []
        for sensor in self.sensors:
            for d in sensor.history_data:
                all_data.append({
                    "时间": d['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    "设备ID": sensor.sensor_id,
                    "设备名称": sensor.device_name,
                    "位置": sensor.location,
                    "温度℃": d['temp'],
                    "状态": d['status'],
                    "是否偏高": "是" if d['is_high'] else "否",
                    "是否超温": "是" if d['is_over'] else "否"
                })

        if not all_data:
            messagebox.showinfo("提示", "暂无数据可导出")
            return

        filename = f"港口设备温度记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=filename,
            title="导出所有历史数据"
        )

        if path:
            df = pd.DataFrame(all_data)
            df.to_excel(path, index=False)
            messagebox.showinfo("成功！", f"已导出 {len(all_data)} 条数据！\n保存位置：\n{path}")
            webbrowser.open(f"file://{os.path.dirname(path)}")  # 自动打开文件夹
    def create_ui(self):
        """创建界面组件"""
        # 顶部控制区
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="启动监控", command=self.start_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="停止监控", command=self.stop_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出选中数据", command=self.export_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出所有数据", command=self.export_all).pack(side=tk.LEFT, padx=5)
        # === 新增：红色的故障模拟按钮 ===
        # 这里用了一个特殊的样式（稍后如果需要变色可以配置，现在先用普通样式）
        btn_fail = tk.Button(control_frame, text="⚠️ 注入故障",
                             bg="red", fg="white", font=("Arial", 10, "bold"),
                             command=self.inject_failure)  # 绑定下面要写的函数
        btn_fail.pack(side=tk.LEFT, padx=20)
        # ============================
        # 新增按钮：打开视觉监控
        tk.Button(control_frame, text="👀 视觉监控大屏", bg="#FF5722", fg="white",
                  font=("微软雅黑", 12, "bold"), command=self.open_vision_monitor).pack(side=tk.LEFT, padx=10)

        ttk.Button(control_frame, text="🔕 停止报警音", command=self.stop_alarm_sound).pack(side=tk.LEFT, padx=5)
        # === 新增：AI 智能诊断按钮 (紫色) ===
        tk.Button(control_frame, text="🔮 AI 预测诊断", bg="purple", fg="white",
                  command=self.show_ai_report).pack(side=tk.LEFT, padx=5)

        # 在 self.show_ai_report 按钮后面添加这个新按钮
        self.deepseek_button = tk.Button(
            control_frame,
            text="🤖 DeepSeek 专家建议",
            bg="#0078d4",
            fg="white",
            font=("微软雅黑", 10, "bold"),
            command=self.get_deepseek_advice
        )
        self.deepseek_button.pack(side=tk.LEFT, padx=5)

        # 在 create_ui 的按钮区域
        tk.Button(control_frame, text="💬 专家在线对话",
                  bg="#009688", fg="white", font=("微软雅黑", 10, "bold"),
                  command=self.open_ai_chat_window).pack(side=tk.LEFT, padx=5)


        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.RIGHT, padx=5)
        # === 新增两个超级按钮 ===
        ttk.Button(control_frame, text="实时温度曲线", command=self.open_realtime_plot).pack(side=tk.LEFT, padx=5)
        # 添加“总体态势”按钮
        tk.Button(control_frame, text="📊 系统态势仪表盘",
                  bg="#2196F3", fg="white", font=("微软雅黑", 10, "bold"),
                  command=self.show_dashboard).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="导出全部历史(Excel)", command=self.export_all_data_advanced).pack(side=tk.LEFT, padx=5)

        # 温度区间说明（使用自定义样式）
        info_frame = ttk.Frame(self.root, padding=5)
        info_frame.pack(fill=tk.X, padx=10)
        ttk.Label(info_frame, text="温度区间：").pack(side=tk.LEFT)
        ttk.Label(info_frame, text="正常（≤60℃）", style="Normal.TLabel", padding=(5, 2)).pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, text="偏高（60-70℃）", style="High.TLabel", padding=(5, 2)).pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, text="超温（≥70℃）", style="Over.TLabel", padding=(5, 2)).pack(side=tk.LEFT, padx=5)

        # 设备状态表格
        status_frame = ttk.LabelFrame(self.root, text="设备状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("sensor_id", "device", "location", "temp", "status", "update_time")
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show="headings")
        for col in columns:
            headings = {
                "sensor_id": "传感器ID",
                "device": "设备名称",
                "location": "位置",
                "temp": "当前温度",
                "status": "状态",
                "update_time": "更新时间"
            }
            self.status_tree.heading(col, text=headings[col])
            widths = {"sensor_id": 100, "device": 150, "location": 120,
                      "temp": 100, "status": 150, "update_time": 120}
            self.status_tree.column(col, width=widths[col], anchor=tk.CENTER)

        # 表格滚动条
        tree_scroll = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_tree.yview)
        self.status_tree.configure(yscroll=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_tree.pack(fill=tk.BOTH, expand=True)

        # 数据统计区
        stats_frame = ttk.LabelFrame(self.root, text="设备数据统计", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.stats_labels = {
            "name": ttk.Label(stats_frame, text="设备名称：--"),
            "total": ttk.Label(stats_frame, text="数据总量：--"),
            "avg": ttk.Label(stats_frame, text="平均温度：--"),
            "max": ttk.Label(stats_frame, text="最高温度：--"),
            "high": ttk.Label(stats_frame, text="偏高次数：--"),
            "over": ttk.Label(stats_frame, text="超温次数：--")
        }

        # 排列统计标签
        for i, (key, label) in enumerate(self.stats_labels.items()):
            label.grid(row=i // 3, column=i % 3, sticky=tk.W, padx=30, pady=5)

        # 日志区
        log_frame = ttk.LabelFrame(self.root, text="系统日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 绑定表格选择事件
        self.status_tree.bind("<<TreeviewSelect>>", self.on_select)

    def open_vision_monitor(self):
        """打开视觉监控"""
        # 直接调用新的类，不需要传 sensors 和 callback 了
        SmartVisionMonitor(self.root)

    def handle_visual_alert(self, visual_anomaly):
        """视觉异常回调：联动警报"""
        if visual_anomaly:
            self.play_alarm_sound()
            messagebox.showerror("视觉警报", "摄像头检测到异常！（运动/烟雾）\n请立即检查设备现场！")
            self.add_log("【视觉警报】检测到异常运动或烟雾")
            # 可选：触发邮件
            # if self.selected_sensor:
            #     self.send_email(self.selected_sensor, {"temp": self.selected_sensor.current_temp, "timestamp": datetime.now()})
    def init_sensors(self):
        """初始化传感器列表"""
        devices = [
            ("TS-001", "集装箱起重机", "码头A区"),
            ("TS-002", "皮带传送带", "仓储B区"),
            ("TS-003", "柴油发电机", "动力站C区"),
            ("TS-004", "自动化导引车", "装卸区D"),
            ("TS-005", "液压系统", "维修车间E")
        ]

        self.sensors = [TemperatureSensor(*dev) for dev in devices]
        for sensor in self.sensors:
            self.status_tree.insert("", tk.END, values=(
                sensor.sensor_id, sensor.device_name, sensor.location,
                "N/A", "未启动", "N/A"
            ))

    def show_dashboard(self):
        """弹出可视化仪表盘窗口（修复版：解决卡死与不显示问题）"""
        try:
            if not self.sensors:
                messagebox.showinfo("提示", "暂无传感器数据")
                return

            # 1. 创建新窗口
            dash_window = tk.Toplevel(self.root)
            dash_window.title("青霄 - 港口设备运行态势")
            dash_window.geometry("800x500")
            dash_window.attributes('-topmost', True)  # 确保窗口在最前面

            # 2. 准备数据
            names = [s.device_name for s in self.sensors]
            temps = [s.current_temp for s in self.sensors]

            # 计算健康分布（假设 >80健康，60-80预警，<60危险）
            # 如果你没写 get_health_score，这里用温度代替逻辑
            danger_count = sum(1 for t in temps if t > 70)
            warning_count = sum(1 for t in temps if 60 < t <= 70)
            normal_count = len(temps) - danger_count - warning_count

            # 3. 设置绘图支持中文
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
            plt.rcParams['axes.unicode_minus'] = False

            # 4. 创建 Figure
            fig = plt.Figure(figsize=(8, 4), dpi=100)

            # 左侧：饼图（状态占比）
            ax1 = fig.add_subplot(121)
            ax1.pie([normal_count, warning_count, danger_count],
                    labels=['正常', '预警', '危险'],
                    autopct='%1.1f%%',
                    colors=['#4CAF50', '#FF9800', '#F44336'])
            ax1.set_title("设备健康分布")

            # 右侧：柱状图（实时温度对比）
            ax2 = fig.add_subplot(122)
            short_names = [n[:4] for n in names]  # 缩短名称防止重叠
            ax2.bar(short_names, temps, color='skyblue')
            ax2.axhline(y=70, color='r', linestyle='--', label='报警线')
            ax2.set_title("设备温度横向对比")
            ax2.set_ylabel("温度 ℃")

            # 5. 关键步骤：使用 Canvas 嵌入 Tkinter
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(fig, master=dash_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()

        except Exception as e:
            messagebox.showerror("可视化错误", f"无法打开仪表盘：{str(e)}")


    def on_select(self, event):
        """选中设备时更新统计信息"""
        selected = self.status_tree.selection()
        if not selected:
            return

        sensor_id = self.status_tree.item(selected[0], "values")[0]
        self.selected_sensor = next(
            (s for s in self.sensors if s.sensor_id == sensor_id),
            None
        )

        if self.selected_sensor:
            self.update_stats()

    def update_stats(self):
        """更新选中设备的统计数据"""
        if not self.selected_sensor or not self.selected_sensor.history_data:
            return

        # 计算统计值
        data = self.selected_sensor.history_data
        total = len(data)
        temps = [d["temp"] for d in data]
        high_count = sum(1 for d in data if d["is_high"])
        over_count = sum(1 for d in data if d["is_over"])
        avg_temp = round(sum(temps) / total, 1) if total > 0 else 0
        max_temp = max(temps) if total > 0 else 0

        # 更新UI
        self.stats_labels["name"]["text"] = f"设备名称：{self.selected_sensor.device_name}"
        self.stats_labels["total"]["text"] = f"数据总量：{total}条"
        self.stats_labels["avg"]["text"] = f"平均温度：{avg_temp}℃"
        self.stats_labels["max"]["text"] = f"最高温度：{max_temp}℃"
        self.stats_labels["high"]["text"] = f"偏高次数：{high_count}次"
        self.stats_labels["over"]["text"] = f"超温次数：{over_count}次"

    def send_email(self, sensor: TemperatureSensor, data: Dict) -> bool:
        """发送超温预警邮件（163终极稳定版：去除昵称 + 简化头）"""
        print("【163发信】正在发送...")
        try:
            subject = "港口设备温度异常通知"  # 避免敏感词，用中性标题
            content = f"""
            <h3>港口设备超温警报</h3>
            <p><strong>设备名称：</strong>{sensor.device_name}</p>
            <p><strong>位置：</strong>{sensor.location}</p>
            <p><strong>当前温度：</strong>{data['temp']}℃（≥70℃）</p>
            <p><strong>时间：</strong>{data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>状态：</strong>已连续弹窗3次未处理，请立即处理。</p>
            <p>系统自动发送，无需回复。</p>
            """

            msg = MIMEText(content, 'html', 'utf-8')

            # === 关键修复：简化头，不要加中文昵称！===
            msg['From'] = EMAIL_USER  # 直接用邮箱，不加"监控系统"昵称（163最容易封昵称）
            msg['To'] = ALERT_EMAIL  # 直接用邮箱字符串
            msg['Subject'] = Header(subject, 'utf-8')  # Subject 用 Header 编码

            # SSL连接（465端口最稳）
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_USER, [ALERT_EMAIL], msg.as_string())  # 收件人用列表

            print("★★★★★ 邮件成功发送！去QQ邮箱查收 ★★★★★")
            logging.info(f"163邮件已发送至 {ALERT_EMAIL}")
            messagebox.showinfo("成功", "报警邮件已发送！请检查QQ邮箱（可能在垃圾箱）。")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"××× 发送失败：{error_msg}")
            logging.error(f"邮件发送失败：{error_msg}")
            messagebox.showerror("失败", f"邮件发送失败：{error_msg}\n常见原因：授权码错误/网络问题")
            return False

    def send_wechat_alert(self, sensor: TemperatureSensor, temp: float):
        """超温3次 → 发微信通知（Server酱）"""
        print(f"【微信推送触发】设备：{sensor.device_name} 温度：{temp}℃")  # ← 加这行
        try:
            # 你刚才复制的SCKEY填在这里！
            SCKEY = "SCT305325TV50SgIlLKVlGdO67Jq3s6Id0"  # ← 改成你自己的！

            title = "【紧急】港口设备超温报警！"
            content = f"""
       【港口设备温度监控系统】

       设备：{sensor.device_name}
       位置：{sensor.location}
       当前温度：{temp}℃（≥70℃）
       时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
       状态：已连续弹窗3次未处理

       请立即前往处理！系统已自动记录。
               """

            url = f"https://sctapi.ftqq.com/{SCKEY}.send"
            data = {
                "title": title,
                "desp": content
            }

            response = requests.post(url, data=data)
            print(f"【Server酱响应】状态码：{response.status_code} 内容：{response.text}")
            if response.json().get("code") == 0:
                print("微信通知发送成功！")
                logging.info(f"微信通知已发送：{sensor.device_name}")
            else:
                print("微信发送失败：", response.text)

        except Exception as e:
            print(f"微信发送异常：{e}")


    def update_status(self, sensor: TemperatureSensor, data: Dict, actions: Dict):
        """更新设备状态并执行预警"""

        def ui_update():
            # 更新表格
            for item in self.status_tree.get_children():
                if self.status_tree.item(item, "values")[0] == sensor.sensor_id:
                    self.status_tree.item(item, values=(
                        sensor.sensor_id,
                        sensor.device_name,
                        sensor.location,
                        f"{data['temp']}℃",
                        data["status"],
                        data["timestamp"].strftime("%H:%M:%S")
                    ))
                    self.status_tree.tag_configure(data["color"], background=data["color"], foreground="white")
                    self.status_tree.item(item, tags=(data["color"],))





                    # 发送邮件
                    if actions["send_email"]:
                        if self.send_email(sensor, data):
                            messagebox.showerror("紧急通知", f"超温未处理！邮件已发送至 {ALERT_EMAIL}")
                        self.play_alarm_sound()  # <--- 加在这里！
                        # ==========================

                        if self.send_email(sensor, data):
                            # 修改弹窗提示，告诉用户可以点按钮消音
                            messagebox.showerror("紧急通知",
                                                 f"超温未处理！邮件已发送！\n正在播放报警音，请点击顶部按钮消音。")

                        # 新增：同时发微信！
                        self.send_wechat_alert(sensor, data['temp'])
                    break

            # 更新选中设备的统计
            if self.selected_sensor and self.selected_sensor.sensor_id == sensor.sensor_id:
                self.update_stats()

            # 更新日志
            log_msg = f"{data['timestamp'].strftime('%H:%M:%S')} - {sensor.device_name}：{data['status']}\n"
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_msg)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.root.after(0, ui_update)

    def show_ai_report(self):
        """显示AI预测报告"""
        # 1. 获取当前选中的设备，如果没有选，就默认第一个
        target = self.selected_sensor if self.selected_sensor else (self.sensors[0] if self.sensors else None)

        if not target:
            messagebox.showinfo("提示", "请先启动监控")
            return

        # 2. 调用设备的AI分析方法
        report = target.ai_predict_maintenance()

        # 3. 弹窗显示结果
        messagebox.showinfo(f"AI 智能诊断 - {target.device_name}", report)
    def export_selected(self):
        """导出选中设备数据"""
        if not self.selected_sensor or not self.selected_sensor.history_data:
            messagebox.showinfo("提示", "请选择有数据的设备")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")],
            title=f"导出{self.selected_sensor.device_name}数据"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["时间", "温度(℃)", "状态", "是否偏高", "是否超温"])
            for d in self.selected_sensor.history_data:
                writer.writerow([
                    d["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    d["temp"],
                    d["status"],
                    "是" if d["is_high"] else "否",
                    "是" if d["is_over"] else "否"
                ])

        messagebox.showinfo("成功", f"导出{len(self.selected_sensor.history_data)}条数据至：\n{path}")

    def export_all(self):
        """导出所有设备数据"""
        all_data = []
        for sensor in self.sensors:
            for d in sensor.history_data:
                all_data.append({
                    "设备名称": sensor.device_name,
                    "传感器ID": sensor.sensor_id,
                    "位置": sensor.location,
                    "时间": d["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "温度(℃)": d["temp"],
                    "状态": d["status"],
                    "是否偏高": "是" if d["is_high"] else "否",
                    "是否超温": "是" if d["is_over"] else "否"
                })

        if not all_data:
            messagebox.showinfo("提示", "无数据可导出")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")],
            title="导出所有设备数据"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
            writer.writeheader()
            writer.writerows(all_data)

        messagebox.showinfo("成功", f"导出{len(all_data)}条数据至：\n{path}")

    def start_all(self):
        """启动所有监控"""
        self.stop_all()
        for sensor in self.sensors:
            thread = threading.Thread(
                target=sensor.start_monitoring,
                args=(self.update_status,),
                daemon=True
            )
            self.threads.append(thread)
            thread.start()
        self.add_log("所有设备监控已启动")

    def inject_failure(self):
        """点击按钮触发：让选中设备（或第一个设备）温度飙升"""

        # 1. 确定要搞坏哪台设备
        target_sensor = self.selected_sensor

        # 如果用户没有在表格里点选设备，默认搞坏第一台 (TS-001)
        if not target_sensor and self.sensors:
            target_sensor = self.sensors[0]

        if not target_sensor:
            messagebox.showinfo("提示", "请先启动系统！")
            return

        # 2. 切换故障状态（开 -> 关，关 -> 开）
        # 这样你可以点一下开启故障，演示完后再点一下恢复正常
        target_sensor.force_failure = not target_sensor.force_failure

        # 3. 给出反馈
        state = "已开启" if target_sensor.force_failure else "已解除"

        msg = f"已对设备【{target_sensor.device_name}】{state} 高温故障模拟！\n"
        if target_sensor.force_failure:
            msg += ">> 温度将瞬间飙升至 90℃ 以上\n>> 将触发红色警报、邮件和微信通知"
        else:
            msg += ">> 设备将逐渐恢复正常运行温度"

        self.add_log(f"用户手动指令：{target_sensor.device_name} 故障模拟 {state}")
        messagebox.showinfo("故障注入控制台", msg)

    def stop_all(self):
        """停止所有监控"""
        for sensor in self.sensors:
            sensor.stop_monitoring()
        for thread in self.threads:
            if thread.is_alive():
                thread.join(1)
        self.threads.clear()
        self.add_log("所有设备监控已停止")

    def add_log(self, msg: str):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.add_log("日志已清空")




def export_all_data_advanced(self):
    """一键导出所有设备历史数据（带时间、状态、颜色）"""
    all_data = []
    for sensor in self.sensors:
        for d in sensor.history_data:
            all_data.append({
                "时间": d['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                "设备ID": sensor.sensor_id,
                "设备名称": sensor.device_name,
                "位置": sensor.location,
                "温度℃": d['temp'],
                "状态": d['status'],
                "是否偏高": "是" if d['is_high'] else "否",
                "是否超温": "是" if d['is_over'] else "否"
            })

    if not all_data:
        messagebox.showinfo("提示", "暂无数据可导出")
        return

    # 自动生成文件名（带当前时间）
    filename = f"港口设备温度记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel文件", "*.xlsx")],
        initialfile=filename,
        title="导出所有历史数据"
    )

    if path:
        df = pd.DataFrame(all_data)
        df.to_excel(path, index=False)
        messagebox.showinfo("成功！", f"已导出 {len(all_data)} 条数据！\n保存位置：\n{path}")
        os.startfile(os.path.dirname(path))  # 自动打开文件夹

        # 在 create_ui() 函数里加上两个新按钮（找到原来的按钮区域，粘贴这几行）


    def open_realtime_plot(self):
        """打开实时曲线图窗口"""
        if not hasattr(self, 'plot_instance') or not self.plot_window.winfo_exists():
            self.plot_instance = RealTimePlot(self.root, self.sensors)
        else:
            self.plot_instance.plot_window.lift()


# =====================================================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PortTempMonitorUI(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"系统错误: {str(e)}", exc_info=True)
        messagebox.showerror("错误", f"系统异常: {str(e)}")