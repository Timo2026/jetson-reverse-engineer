# 在 Jetson Nano 上使用 uv 和 SD 卡部署 Hermes Agent

在 Jetson Nano 上使用 uv 和 SD 卡部署 Hermes Agent-腾讯云开发者社区-腾讯云
IT蜗壳-Tango
在 Jetson Nano 上使用 uv 和 SD 卡部署 Hermes Agent
原创
关注作者
腾讯云
开发者社区
文档建议反馈控制台登录/注册
首页学习
活动
专区
圈层
工具
MCP广场
文章/答案/技术大牛搜索
搜索关闭
发布
IT蜗壳-Tango
社区首页 >专栏 >在 Jetson Nano 上使用 uv 和 SD 卡部署 Hermes Agent
在 Jetson Nano 上使用 uv 和 SD 卡部署 Hermes Agent
原创
IT蜗壳-Tango
关注
发布于 2026-07-15 16:30:35
发布于 2026-07-15 16:30:35
1800
举报
本文记录一次真实的 Hermes Agent 部署过程：目标设备是 Jetson Nano eMMC 版，系统为 JetPack 4.6.6 / L4T R32.7.6 / Ubuntu 18.04。由于 eMMC 只有 16GB，同时系统自带 Python 3.6、glibc 版本较旧，因此我们将 Hermes、Python 3.11、uv 缓存和 Docker 数据全部放到一张 32GB SD 卡中。
文章不仅给出最终可行步骤，也保留了 Node.js 与 GitHub、PyPI、Docker Hub 网络问题的排查过程。
一、最终效果
完成后的环境如下：
项目
结果
设备
NVIDIA Jetson Nano Developer Kit
系统
Ubuntu 18.04.6 / L4T R32.7.6
架构
aarch64
Hermes Agent
v0.18.2
Python
3.11.15，由 uv 独立管理
Hermes 数据目录
/srv/hermes/home
uv 缓存
/srv/hermes/cache/uv
Docker 数据目录
/srv/hermes/docker
SD 卡挂载点
/srv/hermes
SD 卡剩余空间
约 27GB
Hermes 官方文档提供 Linux 一键安装器，并说明安装器会自动配置 uv、Python 3.11 和 Node.js。但 Jetson Nano 的 Ubuntu 18.04 / glibc 2.27 无法直接运行当前 Node.js 22 官方二进制，所以本文采用“官方源码 + uv 精简安装”的兼容方案。
Hermes Agent 官方安装文档NousResearch/hermes-agent 官方仓库二、环境与准备工作
先确认当前设备：
代码语言：bash
复制
hostnamectl
uname -a
free -h
df -h /
ldd --version | head -1
python3 --version
git --version
本次设备的关键结果是：
代码语言：bash
复制
Operating System: Ubuntu 18.04.6 LTS
Kernel: Linux 4.9.337-tegra
Architecture: arm64
Memory: 3.9G
Root filesystem: /dev/mmcblk0p1
glibc: 2.27
Python: 3.6.9
Jetson Nano 系统基线
安装基础工具：
代码语言：bash
复制
sudo apt update
sudo apt install -y curl ca-certificates xz-utils gdisk
不要执行 do-release-upgrade。Jetson Nano 官方支持的最终版本是 JetPack 4.6.6 / L4T R32.7.6，强行升级 Ubuntu 大版本可能破坏 NVIDIA 内核、CUDA 和驱动。
三、识别并格式化 32GB SD 卡
1. 确认设备名
先检查块设备：
代码语言：bash
复制
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT
findmnt /
sudo blkid
本次环境中：
/dev/mmcblk0：Jetson 板载 eMMC，系统根目录位于 /dev/mmcblk0p1/dev/sda：插入的 32GB SD 卡必须根据自己的 lsblk 输出确认设备名。下面的格式化命令会清空目标磁盘，绝对不能把 /dev/mmcblk0 写成目标。
2. 备份旧分区表
如果 SD 卡中没有需要保留的数据，可以先备份 GPT：
代码语言：bash
复制
mkdir -p ~/hermes-agent-tutorial/logs
sudo sgdisk --backup=$HOME/hermes-agent-tutorial/logs/sda-gpt-before-hermes.bin /dev/sda
3. 清空 SD 卡并建立单分区
代码语言：bash
复制
sudo umount /dev/sda* 2>/dev/null || true
sudo sgdisk --zap-all /dev/sda
sudo sgdisk -n 1:1MiB:0 -t 1:8300 -c 1:HERMES_DATA /dev/sda
sudo partprobe /dev/sda
sudo mkfs.ext4 -F -L HERMES_DATA /dev/sda1
创建挂载点：
代码语言：bash
复制
sudo mkdir -p /srv/hermes
UUID=$(sudo blkid -s UUID -o value /dev/sda1)
echo "UUID=$UUID /srv/hermes ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab
sudo mount /srv/hermes
sudo chown "$USER:$USER" /srv/hermes
mkdir -p /srv/hermes/{workspace,cache,docker,logs,screenshots}
验证：
代码语言：bash
复制
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT /dev/sda
df -hT /srv/hermes
findmnt /srv/hermes
整张 SD 卡格式化并挂载
本次结果为：
代码语言：bash
复制
/dev/sda1 ext4 30G /srv/hermes
四、为什么没有直接使用一键安装器
官方安装器可以先下载到本地审阅，而不是直接执行远程管道：
代码语言：bash
复制
curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
-o /srv/hermes/workspace/install-hermes.sh
chmod 755 /srv/hermes/workspace/install-hermes.sh
sha256sum /srv/hermes/workspace/install-hermes.sh
/srv/hermes/workspace/install-hermes.sh --help
我们尝试将所有内容定向到 SD 卡：
代码语言：bash
复制
export HERMES_HOME=/srv/hermes/home
export UV_CACHE_DIR=/srv/hermes/cache/uv
export XDG_CACHE_HOME=/srv/hermes/cache
/srv/hermes/workspace/install-hermes.sh \
--hermes-home /srv/hermes/home \
--dir /srv/hermes/home/hermes-agent \
--skip-browser \
--skip-setup
安装器成功安装了：
代码语言：bash
复制
uv 0.11.28
Python 3.11.15
官方安装器成功安装 uv 与 Python
但在 Node.js 阶段失败：
代码语言：bash
复制
node: /lib/aarch64-linux-gnu/libc.so.6:
version `GLIBC_2.28' not found
原因是当前 Jetson 系统只有 glibc 2.27，而 Node.js 22 ARM64 官方二进制要求至少 glibc 2.28。即使传入 --skip-browser，当前安装器仍会先检查 Node.js。
不要为了 Node.js 强行替换系统 glibc。正确做法是跳过 Node/浏览器组件，使用 uv 安装 Hermes 核心 CLI。
五、下载 Hermes Agent 官方源码
GitHub 直连下载速度只有约 54KB/s，浅克隆长时间无进展。我们只对公开源码下载临时使用代理，不修改全局 Git 配置。
先从 GitHub 官方 API 记录当前主分支提交：
代码语言：bash
复制
curl -fsSL https://api.github.com/repos/NousResearch/hermes-agent/commits/main
本次记录的提交为：
代码语言：bash
复制
6997dc81cd21dc88c6cb808a1fb3626b6ce71254
使用实测可用的下载代理：
代码语言：bash
复制
curl -fL --retry 5 --retry-delay 2 \
https://ghproxy.vip/https://codeload.github.com/NousResearch/hermes-agent/tar.gz/refs/heads/main \
-o /srv/hermes/workspace/hermes-agent-main.tar.gz
校验并解压：
代码语言：bash
复制
sha256sum /srv/hermes/workspace/hermes-agent-main.tar.gz
tar -tzf /srv/hermes/workspace/hermes-agent-main.tar.gz >/dev/null \
&& echo "archive integrity: OK"
tar -xzf /srv/hermes/workspace/hermes-agent-main.tar.gz \
-C /srv/hermes/workspace
mv /srv/hermes/workspace/hermes-agent-main \
/srv/hermes/home/hermes-agent
第三方代理只用于传输公开源码。生产环境应记录官方提交号、保留 SHA-256，并优先使用可信网络或内部镜像。
六、使用 uv 在 SD 卡创建 Python 3.11 环境
设置环境变量：
代码语言：bash
复制
export HERMES_HOME=/srv/hermes/home
export UV_CACHE_DIR=/srv/hermes/cache/uv
export UV_PYTHON_INSTALL_DIR=/srv/hermes/cache/uv/python
export UV_LINK_MODE=copy
使用官方安装器已经放到 SD 卡中的 uv：
代码语言：bash
复制
cd /srv/hermes/home/hermes-agent
/srv/hermes/home/bin/uv python install 3.11
/srv/hermes/home/bin/uv python find 3.11
/srv/hermes/home/bin/uv venv venv --python 3.11
./venv/bin/python --version
在 SD 卡创建 uv 与 Python 3.11 环境
这里不要替换 /usr/bin/python3，Jetson 系统工具仍然依赖原有 Python 3.6。Hermes 只使用自己的 venv。
七、安装 Hermes 核心依赖
第一次使用 PyPI 官方源解析成功，但下载多个 wheel 时速度很慢。中止后切换清华 PyPI 镜像，uv 会自动复用已经下载到 SD 卡的缓存：
代码语言：bash
复制
export HERMES_HOME=/srv/hermes/home
export UV_CACHE_DIR=/srv/hermes/cache/uv
export UV_PYTHON_INSTALL_DIR=/srv/hermes/cache/uv/python
export UV_LINK_MODE=copy
cd /srv/hermes/home/hermes-agent
/srv/hermes/home/bin/uv pip install \
--python venv/bin/python \
--default-index https://pypi.tuna.tsinghua.edu.cn/simple \
-e .
使用 PyPI 镜像完成 Hermes 安装
这里安装的是基础项目 -e .，没有使用 -e ".[all]"。这样可以避开 Nano 暂时不需要的浏览器、语音、消息平台等大体积或架构敏感依赖。
八、配置命令入口与永久环境变量
建立命令软链接：
代码语言：bash
复制
mkdir -p ~/.local/bin
ln -sfn /srv/hermes/home/hermes-agent/venv/bin/hermes \
~/.local/bin/hermes
将以下内容加入 ~/.bashrc：
代码语言：bash
复制
# Hermes Agent on SD card
export HERMES_HOME=/srv/hermes/home
export UV_CACHE_DIR=/srv/hermes/cache/uv
export UV_PYTHON_INSTALL_DIR=/srv/hermes/cache/uv/python
export PATH="$HOME/.local/bin:/srv/hermes/home/bin:$PATH"
使其立即生效：
代码语言：bash
复制
source ~/.bashrc
九、验证 Hermes Agent
执行：
代码语言：bash
复制
cd /srv/hermes/home/hermes-agent
/srv/hermes/home/bin/uv pip check --python venv/bin/python
hermes version
hermes doctor
关键结果：
代码语言：bash
复制
All installed packages are compatible
Hermes Agent v0.18.2
Python: 3.11.15
No active security advisories
SSL CA certificate bundle is valid
~/.local/bin/hermes → correct target
Hermes Agent 版本与 doctor 验证
hermes doctor 提示 .env 和模型 API 尚未配置属于正常现象。本文只完成基础安装，下一步再执行：
代码语言：bash
复制
hermes setup --portal
或者使用 hermes model 配置 OpenRouter、OpenAI、Ollama 等提供商。
十、将 Docker 数据迁移到 SD 卡
检查 Docker 环境：
代码语言：bash
复制
sudo docker info --format 'Root={{.DockerRootDir}} Driver={{.Driver}}'
sudo docker ps -a
sudo docker images
本次 Docker 没有已有容器或镜像，因此可以直接迁移。创建 /etc/docker/daemon.json：
代码语言：json
复制
{
"data-root": "/srv/hermes/docker"
}
应用配置：
代码语言：bash
复制
sudo mkdir -p /srv/hermes/docker /etc/docker
sudo usermod -aG docker "$USER"
sudo systemctl restart docker
sudo docker info --format 'Root={{.DockerRootDir}} Driver={{.Driver}}'
重新登录后，tango 用户可以不加 sudo 使用 Docker。
十一、配置 Docker Hub 镜像代理
Docker Hub 直连测试在 15 秒后超时：
Docker 数据迁移成功但直连超时
我们测试了多个镜像端点的 /v2/ 健康状态，并把可用候选写入 /etc/docker/daemon.json：
代码语言：json
复制
{
"data-root": "/srv/hermes/docker",
"registry-mirrors": [
"https://docker.1ms.run",
"https://dockerproxy.net",
"https://docker.m.daocloud.io"
]
}
重启并验证：
代码语言：bash
复制
sudo systemctl restart docker
sudo docker info --format 'Root={{.DockerRootDir}} Mirrors={{json .RegistryConfig.Mirrors}}'
sudo docker pull hello-world
sudo docker run --rm hello-world
结果成功拉取 ARM64 镜像并运行容器：
Docker 镜像代理和 ARM64 容器验证成功
公共镜像代理的可用性会变化，不应盲目照抄。建议先执行 /v2/ 健康检查，并仅拉取公开镜像；重要镜像应记录并校验 digest。
十二、最终目录结构
代码语言：bash
复制
/srv/hermes/
├── cache/
│ └── uv/ # uv wheel 与 Python 缓存
├── docker/ # Docker data-root
├── home/
│ ├── bin/ # Hermes 管理的 uv
│ ├── hermes-agent/ # 源码与 venv
│ ├── logs/
│ ├── memories/
│ ├── sessions/
│ └── skills/
├── logs/
├── screenshots/
└── workspace/
存储占用：
代码语言：bash
复制
/srv/hermes/home 约 568MB
/srv/hermes/cache 约 310MB
/srv/hermes 约 945MB，剩余约 27GB
十三、常见问题
1. 为什么不升级 Ubuntu 20.04？
Jetson Nano 的官方最终软件栈是 JetPack 4.6.6 / L4T R32.7.6 / Ubuntu 18.04。直接升级发行版可能导致 NVIDIA 内核、CUDA 和驱动失效。
2. Node.js 22 报 GLIBC_2.28 not found 怎么办？
不要替换系统 glibc。对于基础 Hermes CLI，跳过 Node 和浏览器组件，使用本文的 uv 精简安装方案。确实需要浏览器功能时，更适合迁移到更新的 ARM64 主机，或另行评估兼容 Node 构建。
3. 为什么不使用 .[all]？
.[all] 会安装更多消息平台、Web、MCP 和工具依赖，增加磁盘、内存和 ARM64 兼容风险。先保证核心 CLI 可用，再按实际需求增加 extras 更稳妥。
4. 重启后 /srv/hermes 没有挂载怎么办？
检查：
代码语言：bash
复制
grep /srv/hermes /etc/fstab
sudo mount -a
findmnt /srv/hermes
如果 SD 卡没有挂载，不要启动 Hermes 或 Docker，避免它们在 eMMC 上误建同名目录并占满空间。
5. 如何进行下一步？
选择模型提供商并完成首次对话：
代码语言：bash
复制
hermes setup --portal
# 或
hermes model
配置完成后再次运行：
代码语言：bash
复制
hermes doctor
hermes
至此，Hermes Agent 的核心运行环境已经成功部署在 Jetson Nano 的 SD 卡上，系统 eMMC 和原有 NVIDIA 软件栈保持不变。
原创声明：本文系作者授权腾讯云开发者社区发表，未经许可，不得转载。
如有侵权，请联系 cloudcommunity@tencent.com 删除。
Hermes Agent
目录
一、最终效果二、环境与准备工作三、识别并格式化 32GB SD 卡1. 确认设备名2. 备份旧分区表3. 清空 SD 卡并建立单分区四、为什么没有直接使用一键安装器五、下载 Hermes Agent 官方源码六、使用 uv 在 SD 卡创建 Python 3.11 环境七、安装 Hermes 核心依赖八、配置命令入口与永久环境变量九、验证 Hermes Agent十、将 Docker 数据迁移到 SD 卡十一、配置 Docker Hub 镜像代理十二、最终目录结构十三、常见问题1. 为什么不升级 Ubuntu 20.04？2. Node.js 22 报 GLIBC_2.28 not found 怎么办？3. 为什么不使用 .[all]？4. 重启后 /srv/hermes 没有挂载怎么办？5. 如何进行下一步？
社区
技术文章技术问答技术沙龙技术视频学习中心技术百科技术专区
活动
自媒体同步曝光计划邀请作者入驻自荐上首页技术竞赛
圈层
腾讯云最具价值专家腾讯云架构师技术同盟腾讯云创作之星腾讯云TDP
关于
社区规范免责声明联系我们友情链接MCP广场开源版权声明
腾讯云开发者
扫码关注腾讯云开发者
领取腾讯云代金券
热门产品
域名注册云服务器区块链服务消息队列网络加速云数据库域名解析云存储视频直播
热门推荐
人脸识别腾讯会议企业云CDN加速视频通话图像分析MySQL 数据库SSL 证书语音识别
更多推荐
数据安全负载均衡短信文字识别云点播大数据小程序开发网站监控数据迁移
Copyright © 2013 - 2026 Tencent Cloud. All Rights Reserved. 腾讯云 版权所有
深圳市腾讯计算机系统有限公司 ICP备案/许可证号：粤B2-20090059 粤公网安备44030502008569号
腾讯云计算（北京）有限责任公司 京ICP证150476号 |  京ICP备11018762号
问题归档专栏文章快讯文章归档关键词归档开发者手册归档开发者手册 Section 归档