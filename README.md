# Jetson Reverse Engineer — NVIDIA 边缘AI 19项目逆向工程库

> 对 NVIDIA Jetson 2026 开发者征文 19 个真实项目进行逆向分析、架构还原与 CPU 可运行复刻。

纯技术视角。仅关注：项目架构 → 核心算法 → 数据流 → 可运行复刻。不涉及任何个人或组织信息。

## 项目概览

19 个项目 × 8 大赛道，每个项目提供：

- **原文归档** (`docs/original-articles/`)：抓取/重建的原始文章
- **逆向分析** (`docs/reverse-analysis/`)：架构逆向 + 核心洞察 + 可复用组件
- **可运行demo** (`src/`)：CPU 可运行的架构模拟（无 Jetson 硬件依赖）
- **自动测试** (`tests/`)：一键全量验证

## 赛道分布

| # | 赛道 | 项目 |
|---|------|------|
| 1 | 自动驾驶/车载感知 | BEVFusion 多传感器融合、DeepStream 跟车距离预警 |
| 2 | 工业/巡检机器人 | Thor+Orbbec 3D巡检、轻量化缺陷检测、PanoTwin 高斯泼溅孪生 |
| 3 | 无障碍穿戴设备 | VisionLink 视障AI眼镜 |
| 4 | 小型智能机器人 | 全人形陪伴机器人、ROS2 循迹小车、Vosk 手势语音陪伴 |
| 5 | 边缘视觉检测/Agent | YOLO26 Vision Agent、手势识别3D游戏、驾驶员行为监测 |
| 6 | 边缘数字员工 | 数字员工、HyClaw 远程mini机、Hermes Agent 部署 |
| 7 | 离线多模态/语音 | 可打断语音助手、Z-Image GGUF 文生图 |
| 8 | 创意交互/渲染 | ComfyUI 边缘部署、仿生脸说话 |

## 快速开始

```bash
# 环境: Python 3.10+, 仅需 numpy (部分demo用OpenCV, 缺失自动降级mock)

# 运行单个demo (01=BEVFusion, 09=OpenClaw陪伴, 19=仿生脸...)
python3 src/01_bevfusion_demo.py

# 全量测试 (19/19)
python3 tests/run_all_tests.py

# 查看逆向分析
cat docs/reverse-analysis/逆向分析总报告.md
```

## 19项目索引

| # | 项目 | 硬件 | 核心算法 | demo |
|:--:|------|------|----------|:----:|
| 01 | BEVFusion | AGX | TensorRT静态shape+FP16 | `src/01_bevfusion_demo.py` |
| 02 | DeepStream跟车 | Orin Nano | nvstreammux+TensorRT | `src/02_deepstream_follow_demo.py` |
| 03 | Thor+Orbbec巡检 | AGX Thor | YOLO+VLM+RAG+LLM | `src/03_inspection_robot_demo.py` |
| 04 | 缺陷检测 | Orin NX | INT8/FP16混合精度 | `src/04_defect_inspection_demo.py` |
| 05 | PanoTwin孪生 | Orin NX 16G | CO-Calib+DAP+D²GS | `src/05_panotwin_demo.py` |
| 06 | VisionLink眼镜 | Orin Nano | 多模态+YOLO+LLM | `src/06_visionlink_demo.py` |
| 07 | 全人形机器人 | Orin NX | GearSonic(GR00T) | `src/07_humanoid_demo.py` |
| 08 | ROS2循迹 | Nano | ROS2+视觉巡线 | `src/08_ros2_car_demo.py` |
| 09 | Vosk陪伴 | Nano | STT+TTS+MediaPipe | `src/09_openclaw_companion_demo.py` |
| 10 | YOLO26 Agent | Orin Nano Super | OpenClaw+YOLO26 | `src/10_yolo26_agent_demo.py` |
| 11 | 手势3D游戏 | Orin Nano Super | TensorRT+CUDA+OpenGL | `src/11_gesture3d_demo.py` |
| 12 | 驾驶员监测 | Orin Nano | MediaPipe行为识别 | `src/12_driver_monitor_demo.py` |
| 13 | 数字员工 | Orin NX | Skill调度+Agent编排 | `src/13_digital_employee_demo.py` |
| 14 | HyClaw mini机 | Nano | mDNS+SSH+Web | `src/14_hyclaw_demo.py` |
| 15 | Hermes Agent | Nano | uv+Ollama | `src/15_hermes_agent_demo.py` |
| 16 | 可打断语音 | Orin | VAD→STT→NLU→TTS | `src/16_voice_assistant_demo.py` |
| 17 | Z-Image文生图 | Orin 8G | GGUF量化 | `src/17_zimage_demo.py` |
| 18 | ComfyUI边缘 | Orin NX | 节点化工作流 | `src/18_comfyui_demo.py` |
| 19 | 仿生脸说话 | Orin NX | TTS→音素→Viseme | `src/19_bionic_face_demo.py` |

## 架构共性模式

```
感知层(传感器/摄像头) → 推理层(TensorRT/ONNX) → 决策层(规则/状态机/LLM) → 执行层(UI/执行器)
```

### 关键部署经验（从19个项目提炼）

1. **静态Shape** 是 Jetson TensorRT 部署关键（动态shape拖慢kernel选择）
2. **FP16** 精度足够多数场景，INT8 需仔细校准（缺陷检测中关键层保留FP16反而更好）
3. **DeepStream 插件化管线** 适合实时视频流（nvstreammux批处理）
4. **规则+模型混合架构** 在生产环境更可靠（巡检RAG规则兜底LLM幻觉）
5. **Producer-Consumer 解耦** 防丢帧（缺陷检测32帧环形缓冲）
6. **离线方案**（uv+SD卡/mDNS）实现即插即用

## 测试

```bash
cd tests && python3 run_all_tests.py
# 预期输出: 19/19 通过
```

## 声明

- 所有 demo 为 **CPU 模拟版**，在 x86 环境验证核心架构闭环，无 NVIDIA 硬件依赖
- 真实 Jetson 部署需 NVIDIA 栈：TensorRT / CUDA / DeepStream / JetPack
- 部分原文平台（CSDN/知乎/微信公众号）存在反爬，归档为知识重建版本并已注记
- 本项目为学习研究用途，原文版权归原作者所有

## License

MIT
