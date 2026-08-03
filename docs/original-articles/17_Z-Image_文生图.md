# Z-Image文生图GGUF模型本地部署--基于8G显存的Jetson终端

Z-Image文生图GGUF模型本地部署--基于8G显存的Jetson终端
原创
launcher
launcher
ETRD
在小说阅读器读本章
去阅读
在小说阅读器中沉浸阅读
引言
近日，阿里巴巴通义实验室开源了一款功能强大且高效的文生图大模型Z-Image，仅有6B参数，官方表示16GB显存即可适配。
当前，个人计算机拥有一块16G显存的显卡显然不是一件奢侈的事情，但我仍然受到局限，仅有一款8GB显存的嵌入式终端（Jetson Orin Nano Super）。
本文将介绍，如何在仅8GB显存的Jetson Orin Nano嵌入式终端，基于ComfyUI本地部署Z-Image文生图大模型。
部署环境
硬件设备：Jetson Orin Nano Super
内存/显存：8GB（一体）
系统：L4T 36.4.4 （Ubuntu 22.04）
Jetpack：6.2.1
CUDA：12.6
内存优化
为预防因内存不足导致的运行崩溃，提前做一下内存的优化，但我不确定这是否真的最终起到了作用。
关闭内存压缩
在SSD上建立一个16G的swap空间
sudo systemctl disable nvzramconfigsudo fallocate -l 16G /swapfilesudo mkswap /swapfilesudo swapon /swapfile
设置开启自动挂载
sudo nano /etc/fstab
末尾添加
/swapfile  none  swap  sw  0  0
ComfyUI安装
构建python虚拟环境
launcher@ubuntu:~/ComfyUI$ python -m venv venv_comfyuilauncher@ubuntu:~/ComfyUI$ source venv_comfyui/bin/activate
安装comfy-cli
(venv_comfyui) launcher@ubuntu:~/ComfyUI$ pip install comfy-cli(venv_comfyui) launcher@ubuntu:~/ComfyUI$ comfy --install-completion
安装comfyui到指定目录
(venv_comfyui) launcher@ubuntu:~/ComfyUI$ comfy --workspace=/home/launcher/ComfyUI/comfy install
启动安装前，会提示选择GPU类型，Jetson自然选择的nvidia。从安装log可以看出，安装comfyui是会自动安装torch组件的，但显然这是不带GPU加速的通用版本。
安装GPU加速支持
以强制重新覆盖安装的方式，从指定网址安装支持Jetpack CUDA加速的torch、torchvision、torchaudio组件：
(venv_comfyui) launcher@ubuntu:~/ComfyUI$ pip install --force-reinstall --no-cache-dir -i https://pypi.jetson-ai-lab.io/jp6/cu126/+simple/ torch torchvision torchaudio
降级numpy
前面默认安装的numpy是最新2.x版本，不兼容，以强制重新覆盖安装的方式安装1.x版本
(venv_comfyui) launcher@ubuntu:~/ComfyUI$ pip install --force-reinstall --no-cache-dir -i https://pypi.jetson-ai-lab.io/jp6/cu126/+simple/ "numpy<2.0"
安装GGUF支持
(venv_comfyui) launcher@ubuntu:~/ComfyUI/comfy/custom_nodes$ git clone https://github.com/city96/ComfyUI-GGUF
将ComfyUI-GGUF仓库clone到目录comfy/custom_nodes下，然后安装gguf依赖组件
(venv_comfyui) launcher@ubuntu:~/ComfyUI/comfy/custom_nodes$ pip install --upgrade gguf
启动ComfyUI
(venv_comfyui) launcher@ubuntu:~/ComfyUI/comfy/models$ comfy launch -- --lowvram  --listen 0.0.0.0 --port 8080
一切就绪，即可启动ComfyUI。启动命令增加了两个参数：
--lowvram：以低显存模式，毕竟我们只有8GB
--listen 0.0.0.0 --port 8080：支持局域网内其它电脑访问ComfyUI
服务运行在Jetson终端，局域网内其它电脑可以通过"IP:端口"的方式访问，这对于自身没有显示设备的终端来说非常方便。
访问ComfyUI
局域网电脑，通过“http://192.168.0.113:8080/”即可访问，其中“192.168.0.113”是Jetson终端的IP地址。
Z-Image量化模型下载及配置
https://huggingface.co/jayn7/Z-Image-Turbo-GGUF
该仓库提供了Z-Image-Turbo的GGUF量化模型，仓库中有两个文件需要关注：
workflow.json文件：该文件是ComfyUI使用Z-Image-Turbo-GGUF的工作流模板，即使对于ComfyUI工作流不了解，也可以直接使用示例模板进行图像生成；
z_image_turbo*.gguf文件：量化的z_image模型文件，根据显存大小选择对应的量化参数。
打开工作流
将example_workflow.json文件下载下来，存放到comfy/user/default/workflows目录：
然后在ComfyUI界面，你应该可以看到并可直接双击打开这个工作流
从工作流的Resources标签中，可以看出，该工作流实际上需要三个模型文件：
text_encoders：qwen_3_4b-Q*.gguf
diffusion_models：z_Image_turbo-Q*.gguf
vae：ae.safetensors
下载模型文件
直接点击上述Resources标签的模型链接，即可进行下载，并按照推荐的目录models/xxx进行存放，本文具体选择的量化模型为：
Qwen3-4B-Q3_K_M.gguf
z_image_turbo-Q3_K_M.gguf
ae.safetensors
配置模型
模型下载到目录后，刷新一下网页，即可在各个工作标签下选择到对应的模型文件。
运行工作流
输入图片的文本描述，并配置像素信息，点击右上角的运行按钮
一切顺利的话，等待一段时间之后，一张图片会生成：
本次生成耗时125s：
备注：最后那步VAE加载貌似会消耗大量内存，如果遇到内存不足崩溃，可以尝试前面的内存优化，并重启系统重新运行。
是的，接下来，你可以生成任意你想要的图片了，它是：
完全免费
完全本地部署，绝对的隐私安全
不受到任何过滤及监管
小结
本文在仅有8GB显存的Jetson Orin Nano嵌入式终端，基于ComfyUI本地部署了Z-Image文生图量化模型，它是完全自由、免费的，并且绝对的隐私安全。该方法及步骤同样适用于其它资源相当的Jetson终端，或具有相当显存的个人计算机。
最后，感谢阿里巴巴为开源大模型做出的卓越贡献。
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