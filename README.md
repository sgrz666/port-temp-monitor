# 港口设备智能温度监控系统

![项目预览](https://via.placeholder.com/800x400?text=项目主界面预览)  


## 项目简介

本项目是一个基于 Python 的**港口设备温度监控系统**，模拟港口核心设备（如起重机、发电机等）的实时温度采集与智能预警。  
系统结合**温度监测**、**AI趋势预测**、**计算机视觉安防**、**多渠道通知**（弹窗、邮件、微信、报警音），实现预测性维护与双模态（温感+视感）智能预警。
。  
核心技术：Tkinter GUI + Matplotlib + OpenCV + scikit-learn + DeepSeek API

## 主要功能

- **实时温度监控**：模拟5台设备，每3秒采集温度，支持随机波动
- **三级预警机制**：
  - 偏高（60-70℃）：橙色弹窗
  - 超温（≥70℃）：连续3次弹窗 → 自动发送163邮件 + Server酱微信通知 + 报警音
- **故障注入演示**：一键让设备温度飙升至90+℃，完整展示预警全流程
- **AI预测性维护**：
  - 线性回归模型预测1分钟后温度趋势
  - DeepSeek大模型API提供专家级故障诊断建议
- **计算机视觉安防**：
  - 实时摄像头人脸检测
  - 检测到入侵 → 红框标记 + 自定义本地音频报警
- **数据可视化与导出**：
  - 工业风实时温度曲线大屏（多设备对比、末端温度标注）
  - 一键导出Excel/CSV（支持所有历史数据）
- **其他**：系统日志、数据统计、停止报警音按钮





- 主界面  
  ![主界面](https://via.placeholder.com/800x600?text=主界面+设备表格)

- 实时曲线大屏  
  ![曲线大屏](https://via.placeholder.com/1000x600?text=实时温度曲线大屏)

- 视觉监控（入侵报警）  
  ![视觉监控](https://via.placeholder.com/800x600?text=人脸检测+报警音频触发)

- AI预测报告  
  ![AI报告](https://via.placeholder.com/600x400?text=AI预测诊断弹窗)

## 安装依赖

项目基于 Python 3.11+，推荐使用 Anaconda 或虚拟环境。

```bash
# 克隆仓库
git clone https://github.com/你的用户名/port-temp-monitor.git
cd port-temp-monitor

# 安装依赖（推荐创建虚拟环境）
pip install numpy pandas matplotlib opencv-python pygame scikit-learn requests

