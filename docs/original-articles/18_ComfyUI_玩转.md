# NVIDIA Jetson系列｜AI走向边缘——玩转ComfyUI

NVIDIA Jetson系列｜AI走向边缘——玩转ComfyUI
原创
Turing门徒
Turing门徒
图灵门徒技术札记
在小说阅读器读本章
去阅读
在小说阅读器中沉浸阅读
Hello 大家好呀！热烈欢迎来到 Turing门徒 的成长世界，一起学习、探索、交流技术 🚀
门徒这两天刚好拿到了一台NVIDIA Jetson Orin NX（16GB ram）(128GB nvme)的算力盒子设备，正好可以安排今天与大家一起学习：如何在NVIDIA Jetson系列平台进行部署ComfyUI，达到免费无限AI生图的目的。
引言
门徒这里拿到的是NVIDIA Jetson系列的Orin NX（16GB ram）(128GB nvme)型号，不过其他型号的同样适用本文所述的步骤流程。
NVIDIA Jetson系列把高性能 GPU 算力、完整 AI 软件栈、低功耗、嵌入式形态整合到一起，让 AI 模型真正能从云端下沉到设备端，实现了实时、离线、安全、低成本的边缘智能。它采用的GPU + CPU + NPU + 深度学习加速器（DLA）的异构架构。
同时具有以下优点：
• 功耗极低：5W–65W 区间，可电池供电，适合移动 / 嵌入式设备
• 算力充足：Orin 系列可达 200+TOPS（门徒手里这台100 TOPS），能运行 LLM 大模型、多目标检测、语义分割、深度估计、Transformer 模型
• CUDA支持：硬件原生支持 CUDA、TensorRT，推理速度远超普通 CPU
升级Jetpack (可选)
门徒手里这台Orin NX，开箱时，厂家就预装好了Ubuntu系统和Jetpack，以及设置了从nvme盘启动系统等基础设置。
以下是初始的Orin NX信息
$ sudo jtop
之后，按下数字"7"，查看INFOjtop信息Jetson Orin NX 16G 硬件&软件信息表
分类
项目
详情
Platform（平台）架构
aarch64
系统
Linux
发行版
Ubuntu 22.04 Jammy Jellyfish
内核版本
5.15.148-tegra
Python版本
3.10.12
Libraries（依赖库）CUDA
12.6.68
L4T
36.4.3
cuDNN
9.3.0.75
TensorRT
10.3.0.30
VPI
3.2.4
Vulkan
1.3.204
OpenCV
4.8.0（无CUDA支持）
Hardware（硬件）型号
NVIDIA Jetson Orin NX Engine
模块
NVIDIA Jetson Orin NX (16G)
SoC
tegra234
CUDA架构
8.7
Jetpack版本
6.2
工具信息工具
jtop 4.3.2
门徒通过在网站jetson repo[1] https://repo.download.nvidia.cn/jetson/ 发现，Jetpack 6.X版本最新为Jetpack 6.2.2，门徒习惯折腾，觉得还是自己先升级一下，即使环境被搞坏了，也可以自己通过NVIDIA SDK Manager来重新烧录固件恢复，这个烧录过程可以后面有时间再写一下。
Jetpack 6.2.2L4T r36.5.0由此可知Jetpack 6.2.2对应着L4T r36.5.0
修改jetson l4t sources
# 先备份一下
$ sudo cp /etc/apt/sources.list.d/nvidia-l4t-apt-source.list /etc/apt/sources.list.d/nvidia-l4t-apt-source.list.bak
# 前面说过Jetpack 6.2.2对应着L4T r36.5.0，diff内容如下：r36.4 改为 r36.5，
$ diff -u /etc/apt/sources.list.d/nvidia-l4t-apt-source.list.bak /etc/apt/sources.list.d/nvidia-l4t-apt-source.list
--- /etc/apt/sources.list.d/nvidia-l4t-apt-source.list.bak      2023-11-21 20:57:26.596000000 +0000
+++ /etc/apt/sources.list.d/nvidia-l4t-apt-source.list  2026-05-20 05:39:02.418569651 +0000
@@ -8,6 +8,6 @@
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
-deb https://repo.download.nvidia.com/jetson/common r36.4 main
-deb https://repo.download.nvidia.com/jetson/t234 r36.4 main
-deb https://repo.download.nvidia.com/jetson/ffmpeg r36.4 main
+deb https://repo.download.nvidia.com/jetson/common r36.5 main
+deb https://repo.download.nvidia.com/jetson/t234 r36.5 main
+deb https://repo.download.nvidia.com/jetson/ffmpeg r36.5 main
# 更新源并升级
$ sudo apt update
$ sudo apt dist-upgrade
# 再安装Jetpack
$ sudo apt -y  install nvidia-jetpack
# 重启机器
$ reboot机器重启后，查看信息
$ sudo jtop
之后，按下数字"7"，查看INFO升级后的jtop可见信息 L4T：r36.5.0 以及 Jetpack：6.2.2，恭喜门徒折腾成功了。
docker信息
机器开箱自带docker了，我们这里选择使用docker的方式来部署ComfyUI，避免污染宿主机的系统环境。
# 把正在使用的账户加到docker组，免得每次执行docker命令都加sudo
$ sudo usermod -aG docker ${USER}
$ newgrp docker
# 重启docker.service
$ sudo systemctl restart docker
# 查看docker info
$ docker info
Client: Docker Engine - Community
Version:    29.5.1
Context:    default
Debug Mode: false
Plugins:
buildx: Docker Buildx (Docker Inc.)
Version:  v0.34.0
Path:     /usr/libexec/docker/cli-plugins/docker-buildx
compose: Docker Compose (Docker Inc.)
Version:  v5.1.3
Path:     /usr/libexec/docker/cli-plugins/docker-compose
...常用的docker命令
命令
说明
docker pull <image>从镜像仓库拉取镜像
docker push <image>将镜像推送到镜像仓库
docker images列出本地所有镜像
docker rmi <image>删除本地一个或多个镜像
docker tag <source> <target>给镜像打标签
docker build -t <name> <path>根据 Dockerfile 构建镜像
docker run <image>创建并启动一个容器
docker run -it <image> bash以交互模式运行容器并进入终端
docker run -d <image>后台运行容器（守护进程）
docker ps列出正在运行的容器
docker ps -a列出所有容器（包括已停止）
docker stop <container>停止一个运行中的容器
docker start <container>启动一个已停止的容器
docker restart <container>重启容器
docker rm <container>删除一个已停止的容器
docker rm -f <container>强制删除运行中的容器
docker exec -it <container> bash进入运行中容器的终端
docker logs <container>查看容器的日志输出
docker cp <src> <dest>在宿主机和容器之间复制文件
docker commit <container> <image>将容器保存为新的镜像
docker network ls列出所有网络
docker network create <name>创建一个自定义网络
docker network connect <network> <container>将容器连接到指定网络
docker volume ls列出所有数据卷
docker volume create <name>创建一个数据卷
docker system prune清理未使用的容器、网络、镜像（加 -a 清理所有未使用镜像）
安装jetson-containers
jetson-containers 是 NVIDIA 官方专为 Jetson 系列边缘 AI 设备打造的容器化工具集，简单说：它让你在 Jetson 上一键运行各种 AI 框架、工具和应用，不用自己折腾复杂的环境配置、依赖冲突、CUDA/cuDNN 兼容等问题。
jetson-containers 可以帮我们解决下述问题：
• 不用自己编译各种包
• 环境隔离，多个项目互不干扰
• 自带硬件加速
• 支持 ROS、DeepStream、YOLO 等几乎所有 Jetson 常用工具（当然也包括我们要的ComfyUI）
# 首先还是先加我们的github代理
$ git config --global url."https://gh.llkk.cc/https://github.com/".insteadOf "https://github.com/"
# 下载jetson-containers并安装
$ git clone https://github.com/dusty-nv/jetson-containers
$ cd jetson-containers
# 必要时，可以使用sudo方式执行
$ bash -x install.sh部署ComfyUI
# 拉取ComfyUI镜像并运行，会自动检测适合当前环境的镜像版本（门徒这里是dustynv/comfyui:r36.4.3）
$ jetson-containers run $(autotag comfyui)等待镜像下载并安装依赖完成（这个看下载速度，还是要等一会的）
ComfyUI运行完成状态ComfyUI监听端口可知，监听的是8188端口。
我们打开浏览器，地址栏输入：IP:8188，以进行访问。
ComfyUI Web UI可以正常打开ComfyUI的Web界面了
浏览器里，点击 "执行" 按钮，进行生图。
但报错了，模型目录models/checkpoints下缺少文件：v1-5-pruned-emaonly-fp16.safetensors。
生图出错
容器错误日志修复错误
查看并进入正在运行的容器
$ docker ps
CONTAINER ID   IMAGE                     COMMAND                  CREATED       STATUS       PORTS     NAMES
9b2cec046f28   dustynv/comfyui:r36.4.3   "/bin/sh -c 'python3…"   2 hours ago   Up 2 hours             jetson_container_20260521_084325
# 进入容器
$ docker exec -it 9b2cec046f28 /bin/bash需要在魔塔（modelscope）上搜索v1-5-pruned-emaonly-fp16[2] https://www.modelscope.cn/models/Qsy5420/v1-5-pruned-emaonly-fp16 并找到下载的文件链接
以下命令是在容器内执行
# 进入对应目录，并下载缺少的模型文件
cd models/checkpoints
wget -c -t 0 https://www.modelscope.cn/models/Qsy5420/v1-5-pruned-emaonly-fp16/resolve/master/v1-5-pruned-emaonly-fp16.safetensors切回浏览器里，再点击 "执行"，再试一次生图。
成功出图
出图日志成功出图了，且耗时10秒左右，我们可以尽情享受免费无限次AI生图了。
最后还是把我们完全可用的容器保存为镜像，方便后续使用
# 查看容器ID
$ docker ps
CONTAINER ID   IMAGE                     COMMAND                  CREATED       STATUS       PORTS     NAMES
9b2cec046f28   dustynv/comfyui:r36.4.3   "/bin/sh -c 'python3…"   3 hours ago   Up 3 hours             jetson_container_20260521_084325
# 将对应容器保存为镜像
$ docker commit 9b2cec046f28 jetson-ok/comfyui:r36.4.3
# 即可得到对应的jetson-ok/comfyui:r36.4.3镜像，可通过docker images查看非常感谢各位看官，耐心陪着门徒一起学习到这。
引用链接
[1] jetson repo: https://repo.download.nvidia.cn/jetson/
[2] v1-5-pruned-emaonly-fp16: https://www.modelscope.cn/models/Qsy5420/v1-5-pruned-emaonly-fp16
预览时标签不可点
微信扫一扫
关注该公众号
知道了
微信扫一扫
使用小程序
取消
允许
取消
允许
取消
允许
×
分析
微信扫一扫可打开此内容，
使用完整服务
：
，
，
，
，
，
，
，
，
，
，
，
，
。
视频
小程序
赞
，轻点两下取消赞
在看
，轻点两下取消在看
分享
留言
收藏
听过