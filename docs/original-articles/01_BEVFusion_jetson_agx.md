# 基于jetson agx实现  BEVFusion

基于jetson agx实现 BEVFusion - MKY-门可意 - 博客园
会员
周边
新闻
博问
闪存
赞助商
Chat2DB
所有博客
当前博客
我的博客
我的园子
账号设置
会员中心
简洁模式 ...
退出登录
注册
登录
MKY-技术驿站
博客园
首页
新随笔
联系
订阅
管理
基于jetson agx实现 BEVFusion
项目背景:
自动驾驶感知任务中，相机与激光雷达是核心传感器，二者具有极强的互补性，但存在异构数据难以对齐的关键问题：相机具备高语义密度，可清晰捕捉红绿灯、行人姿态等细节信息，却缺乏深度感知能力；激光雷达能提供高精度几何信息，测距稳定，但其点云数据稀疏、语义表达薄弱。传统多传感器融合方法要么会丢失图像语义信息，要么存在几何畸变问题，且早期鸟瞰图（BEV）融合方案效率低下，无法满足自动驾驶实时部署的实际需求。
鸟瞰图（BEV），又称俯视空间、上帝视角，是从上往下俯瞰整个场景的表征形式，作为自动驾驶感知的理想统一表征空间，可兼顾几何一致性与多任务通用性。而Fusion在自动驾驶感知领域特指多模态信息融合，即整合不同传感器、不同类型的数据（如图像与毫米波雷达、图像与激光雷达点云的融合）。在此背景下，BEVFusion框架应运而生，其本质是相机图像与激光雷达点云两种模态在BEV鸟瞰视角下完成的多传感器融合算法，核心目的是通过高效的多模态BEV投影与融合方式，解决传统融合“语义丢失、几何不准、速度缓慢”的痛点，实现自动驾驶感知的精准与实时性。
目的
本研究的具体目标包括：
实现BEVFusion模型在Jetson AGX Orin边缘计算平台上的完整部署流程，明确部署关键步骤，确保流程规范、可复现。
在Jetson AGX Orin平台上，基于TensorRT（TRT）完成BEVFusion模型加速优化，实现模型快速推理，显著提升推理效率。
完成真实场景下6路摄像头的接入与协同推理，实现多摄像头数据与BEVFusion模型的高效适配，保障推理过程的稳定性与实时性。
开展BEVFusion模型源码深度解读，梳理核心模块（BEV表征、多模态融合）的实现逻辑，为后续模型优化与二次开发提供理论支撑。
模型架构:
模块拆解与数据流（从左到右）
输入层：双模态传感器数据
Images（相机图像）：多路车载摄像头采集的 RGB 图像，提供场景的纹理、颜色、语义信息。
Point Cloud（激光雷达点云）：激光雷达输出的三维点云数据，提供精准的距离、位置和形状信息。
图像分支（Camera Branch）
Backbone ResNet50（TRT-native）
用 ResNet50 作为图像骨干网络，提取 2D 图像特征。
关键优化：原生支持 TensorRT（TRT），可直接做 FP16/INT8 量化和推理加速。
View Transform BEV Pooling（CUDA-Kernel）
这是图像到 BEV 的关键模块，通过 CUDA 核实现高效的视图变换与 BEV 池化。
输出：Cam Feature Map (B, C_CAM, BEV_H, BEV_W) —— 与激光雷达分支同尺寸的 BEV 特征图。
激光雷达分支（LiDAR Branch）
Points2Voxel + Dense2Sparse（CUDA-Kernel）
把稀疏点云转换为体素（Voxel），再从稠密表示转为稀疏格式，适配后续的稀疏卷积网络。
完全用 CUDA 核实现，保证点云预处理的高效性。
Backbone SparseConvNet（SPCONV-SCN）
用稀疏卷积网络（SparseConvNet）提取点云特征，专门针对点云的稀疏性优化，计算效率远高于普通 3D 卷积。
2. 输出：Lidar Feature Map (B, C_LIDAR, BEV_H, BEV_W) —— 与图像分支同尺寸的 BEV 特征图。
融合与解码层（核心模块）
Postprocess TransDecoder（TRT & CUDA）
接收两路同尺寸的 BEV 特征图（相机 + 激光雷达），在统一的鸟瞰空间中完成特征融合。
同时基于 TensorRT 和 CUDA 做后处理与解码，将融合后的 BEV 特征映射为最终任务输出。
输出层：双任务结果
Detection（3D 目标检测）：输出目标的 3D 包围盒、类别、位置、朝向等信息，图中以点云上的蓝色 / 红色框可视化。
Segmentation（语义分割）：输出场景的 BEV 级语义分割结果，图中以不同颜色区分道路、车道线、障碍物等区域。
架构的关键亮点（NVIDIA 优化重点）
双分支并行设计：相机与激光雷达数据采用并行处理模式，最终统一到相同尺寸的BEV空间，为特征级融合奠定基础，提升整体处理效率。
全链路硬件加速： 图像骨干网络：TRT原生支持，可直接量化部署，适配Jetson AGX Orin平台的加速特性。
视图变换、点云预处理：通过CUDA核实现，消除Python运行开销，提升处理速度。
点云骨干网络：SparseConvNet稀疏卷积，精准适配点云稀疏特性，降低算力消耗。
后处理解码：TRT与CUDA联合优化，进一步降低端到端推理延迟，满足实时部署需求。
单模型双任务输出：一套BEV融合特征同时支持3D目标检测与BEV语义分割，适配自动驾驶感知系统的多任务需求，降低部署复杂度与硬件资源占用。
部署:
1硬件设备
设备名称
型号规格
核心参数
数量
Jetson AGX Orin
Jetson AGX Orin 64GB
• 275 TOPS AI算力• 32GB LPDDR5• 64GB eMMC 5.1• 8核Cortex-A78AE
1
摄像头
gsml2
1080P/4K
6
RoboSense
Helios
32线
1
2系统版本:
jetson agx 64G
- JetPack 版本: 6.2.1+b38
- L4T 版本: R36.4.7 (Release 36, Revision 4.7)
- Ubuntu 版本: 22.04.5 LTS (Jammy)
- 内核版本: 5.15.148-tegra
- 架构: aarch64 (ARM64)
3克隆项目:
git clone https://github.com/NVIDIA-AI-IOT/Lidar_AI_Solution.git
安装环境
apt install libprotobuf-dev
pip install onnx
4配置变量:
root@nvidia-desktop:/storage/Lidar_AI_Solution/CUDA-BEVFusion# cat tool/environment.sh|grep export|grep -v "^#"|head -n10
export TensorRT_Lib=/usr/lib/aarch64-linux-gnu
export TensorRT_Inc=/usr/include/aarch64-linux-gnu
export TensorRT_Bin=/usr/src/tensorrt/bin
export CUDA_Lib=/usr/local/cuda/lib64
export CUDA_Inc=/usr/local/cuda/include
export CUDA_Bin=/usr/local/cuda/bin
export CUDA_HOME=/usr/local/cuda
export CUDNN_Lib=/usr/lib/aarch64-linux-gnu
export SPCONV_CUDA_VERSION=12.8
export DEBUG_MODEL=resnet50int8
5加载变量
root@nvidia-desktop:/storage/Lidar_AI_Solution/CUDA-BEVFusion# source tool/environment.sh
==========================================================
|| MODEL: resnet50int8
|| PRECISION: int8
|| DATA: example-data
|| USEPython: ON
|| TRT_USE_DLA: OFF
|| TRT_VARIANT: default
||
|| TensorRT: /usr/lib/aarch64-linux-gnu
|| CUDA: /usr/local/cuda
|| CUDNN: /usr/lib/aarch64-linux-gnu
==========================================================
Find Python_Inc: /usr/include/python3.10
Find Python_Lib: /usr/lib/aarch64-linux-gnu
Find Python_Soname: libpython3.10.so
Try to get the current device SM
Current CUDA SM: 87
Configuration done!
6生成tensorRT模型
bash tool/build_trt_engine.sh
root@nvidia-desktop:/storage/Lidar_AI_Solution/CUDA-BEVFusion# tree model/
model/
└── resnet50int8
├── bevfusion_ptq.pth
├── build
│   ├── camera.backbone.dla0.json
│   ├── camera.backbone.dla0.log
│   ├── camera.backbone.dla0.plan
│   ├── camera.backbone.json
│   ├── camera.backbone.log
│   ├── camera.backbone.plan
│   ├── camera.vtransform.json
│   ├── camera.vtransform.log
│   ├── camera.vtransform.plan
│   ├── fuser.json
│   ├── fuser.log
│   ├── fuser.plan
│   ├── head.bbox.json
│   ├── head.bbox.log
│   └── head.bbox.plan
├── camera.backbone.onnx
├── camera.vtransform.onnx
├── default.yaml
├── fuser.onnx
├── head.bbox.layernormplugin.onnx
├── head.bbox.onnx
└── lidar.backbone.xyz.onnx
7生成 Protobuf 代码
bash src/onnx/make_pb.sh
8运行测试
bash tool/run.sh
------------------------------------------------------
Camerea Backbone 🌱 is Static Shape model
Inputs: 2
0.img : {1 x 6 x 3 x 256 x 704} [float16]
1.depth : {1 x 6 x 1 x 256 x 704} [float16]
Outputs: 2
0.camera_feature : {6 x 32 x 88 x 80} [float16]
1.camera_depth_weights : {6 x 118 x 32 x 88} [float16]
------------------------------------------------------
------------------------------------------------------
Camerea VTransform 🌱 is Static Shape model
Inputs: 1
0.feat_in : {1 x 80 x 360 x 360} [float16]
Outputs: 1
0.feat_out : {1 x 80 x 180 x 180} [float16]
------------------------------------------------------
------------------------------------------------------
Transfusion 🌱 is Static Shape model
Inputs: 2
0.camera : {1 x 80 x 180 x 180} [float16]
1.lidar : {1 x 256 x 180 x 180} [float16]
Outputs: 1
0.middle : {1 x 512 x 180 x 180} [float16]
------------------------------------------------------
------------------------------------------------------
BBox 🌱 is Static Shape model
Inputs: 1
0.middle : {1 x 512 x 180 x 180} [float16]
Outputs: 6
0.score : {1 x 10 x 200} [float16]
1.rot : {1 x 2 x 200} [float16]
2.dim : {1 x 3 x 200} [float16]
3.reg : {1 x 2 x 200} [float16]
4.height : {1 x 1 x 200} [float16]
5.vel : {1 x 2 x 200} [float16]
------------------------------------------------------
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 1.17706 ms
[⏰ [NoSt] ImageNrom]: 13.99770 ms
[⏰ Lidar Backbone]: 32.52976 ms
[⏰ Camera Depth]: 6.59030 ms
[⏰ Camera Backbone]: 93.31933 ms
[⏰ Camera Bevpool]: 12.96054 ms
[⏰ VTransform]: 7.25910 ms
[⏰ Transfusion]: 13.42362 ms
[⏰ Head BoundingBox]: 25.67571 ms
Total: 191.758 ms
=============================================
==================Detections==================
Detected objects: 33
[00] class="pedestrian"(8) score=0.813 center=(-10.687, -3.975, -0.823) size=(w=0.649, l=0.767, h=1.759) yaw=-3.007 vel=(0.083, 1.021)
[01] class="pedestrian"(8) score=0.791 center=(5.138, -10.275, -1.118) size=(w=0.685, l=0.839, h=1.730) yaw=0.061 vel=(-0.084, -1.289)
[02] class="car"(0) score=0.765 center=(-11.625, -36.722, -1.264) size=(w=2.044, l=4.832, h=1.905) yaw=2.876 vel=(-0.000, 0.000)
[03] class="car"(0) score=0.761 center=(11.775, 17.513, -0.676) size=(w=1.887, l=4.512, h=1.589) yaw=1.292 vel=(-12.984, -3.695)
[04] class="motorcycle"(6) score=0.741 center=(1.463, -18.956, -1.391) size=(w=0.803, l=2.136, h=1.671) yaw=-3.087 vel=(0.162, 4.309)
[05] class="car"(0) score=0.730 center=(-0.112, -10.125, -1.324) size=(w=1.863, l=4.464, h=1.479) yaw=-3.139 vel=(-0.101, 1.982)
[06] class="car"(0) score=0.726 center=(-19.669, -18.112, -0.338) size=(w=1.956, l=4.743, h=1.748) yaw=2.868 vel=(-0.000, 0.000)
[07] class="pedestrian"(8) score=0.692 center=(-3.825, 31.125, -0.492) size=(w=0.657, l=0.699, h=1.754) yaw=-1.899 vel=(1.049, 0.349)
[08] class="pedestrian"(8) score=0.647 center=(-9.862, -4.575, -0.903) size=(w=0.604, l=0.712, h=1.749) yaw=2.998 vel=(-0.117, 0.998)
[09] class="barrier"(5) score=0.600 center=(16.988, 33.975, -0.598) size=(w=1.990, l=0.436, h=1.001) yaw=-0.168 vel=(-0.000, 0.000)
[10] class="car"(0) score=0.567 center=(-16.387, -37.987, -0.916) size=(w=1.894, l=4.606, h=1.600) yaw=2.825 vel=(-0.000, 0.000)
[11] class="pedestrian"(8) score=0.566 center=(-21.656, -1.950, -0.363) size=(w=0.666, l=0.792, h=1.791) yaw=1.224 vel=(-1.428, -0.516)
[12] class="car"(0) score=0.505 center=(-20.906, -39.947, -0.813) size=(w=1.924, l=4.482, h=1.640) yaw=2.844 vel=(-0.000, 0.000)
[13] class="pedestrian"(8) score=0.501 center=(-9.262, -4.425, -0.877) size=(w=0.627, l=0.680, h=1.736) yaw=2.830 vel=(-0.177, 0.771)
[14] class="barrier"(5) score=0.451 center=(18.788, 34.200, -0.616) size=(w=1.945, l=0.448, h=0.961) yaw=-0.132 vel=(-0.000, 0.000)
[15] class="car"(0) score=0.442 center=(-31.144, -21.412, -0.329) size=(w=1.972, l=4.517, h=1.727) yaw=2.738 vel=(-0.000, 0.000)
[16] class="car"(0) score=0.409 center=(-24.694, -19.425, -0.321) size=(w=1.874, l=4.391, h=1.637) yaw=2.896 vel=(-0.000, 0.000)
[17] class="barrier"(5) score=0.408 center=(15.338, 33.150, -0.639) size=(w=1.980, l=0.470, h=1.007) yaw=-0.522 vel=(-0.000, 0.000)
[18] class="car"(0) score=0.351 center=(-22.200, -18.694, -0.316) size=(w=1.884, l=4.425, h=1.620) yaw=2.835 vel=(-0.000, 0.000)
[19] class="pedestrian"(8) score=0.312 center=(15.150, -17.962, -0.836) size=(w=0.644, l=0.693, h=1.798) yaw=-0.058 vel=(0.073, -1.159)
[20] class="car"(0) score=0.252 center=(1.388, -26.531, -1.507) size=(w=1.929, l=4.442, h=1.714) yaw=-3.102 vel=(0.122, 5.391)
[21] class="barrier"(5) score=0.248 center=(15.975, 35.100, -0.572) size=(w=1.975, l=0.443, h=1.016) yaw=1.465 vel=(-0.000, 0.000)
[22] class="car"(0) score=0.240 center=(-25.931, -40.669, -0.736) size=(w=1.887, l=4.344, h=1.676) yaw=2.907 vel=(-0.000, 0.000)
[23] class="pedestrian"(8) score=0.207 center=(-5.325, -28.575, -1.410) size=(w=0.620, l=0.686, h=1.717) yaw=-0.137 vel=(0.195, -0.986)
[24] class="car"(0) score=0.199 center=(-28.425, -21.244, -0.335) size=(w=1.939, l=4.434, h=1.665) yaw=2.774 vel=(-0.000, 0.000)
[25] class="barrier"(5) score=0.191 center=(16.275, 36.225, -0.568) size=(w=1.965, l=0.465, h=1.013) yaw=1.804 vel=(-0.000, 0.000)
[26] class="car"(0) score=0.188 center=(-23.569, -40.106, -0.716) size=(w=1.902, l=4.412, h=1.659) yaw=2.906 vel=(-0.000, 0.000)
[27] class="barrier"(5) score=0.186 center=(20.175, 34.425, -0.646) size=(w=2.028, l=0.449, h=0.983) yaw=-0.147 vel=(-0.000, 0.000)
[28] class="barrier"(5) score=0.174 center=(34.500, 37.500, -0.620) size=(w=2.004, l=0.438, h=1.056) yaw=-0.194 vel=(-0.000, 0.000)
[29] class="barrier"(5) score=0.171 center=(36.375, 37.800, -0.742) size=(w=1.996, l=0.452, h=1.095) yaw=-0.158 vel=(-0.000, 0.000)
[30] class="barrier"(5) score=0.167 center=(32.175, 36.975, -0.575) size=(w=1.989, l=0.439, h=1.056) yaw=-0.125 vel=(-0.000, 0.000)
[31] class="pedestrian"(8) score=0.130 center=(-17.719, -7.125, -0.557) size=(w=0.631, l=0.771, h=1.196) yaw=-1.928 vel=(-0.001, -0.000)
[32] class="barrier"(5) score=0.120 center=(17.625, 42.975, -0.096) size=(w=2.142, l=0.494, h=1.045) yaw=1.691 vel=(-0.000, 0.000)
==============================================
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 0.53923 ms
[⏰ [NoSt] ImageNrom]: 5.74054 ms
[⏰ Lidar Backbone]: 19.23155 ms
[⏰ Camera Depth]: 0.16438 ms
[⏰ Camera Backbone]: 16.61341 ms
[⏰ Camera Bevpool]: 2.55866 ms
[⏰ VTransform]: 2.77117 ms
[⏰ Transfusion]: 7.06438 ms
[⏰ Head BoundingBox]: 15.00925 ms
Total: 63.413 ms
=============================================
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 0.55696 ms
[⏰ [NoSt] ImageNrom]: 5.28090 ms
[⏰ Lidar Backbone]: 30.91427 ms
[⏰ Camera Depth]: 0.17165 ms
[⏰ Camera Backbone]: 15.24282 ms
[⏰ Camera Bevpool]: 2.57878 ms
[⏰ VTransform]: 2.81680 ms
[⏰ Transfusion]: 13.77715 ms
[⏰ Head BoundingBox]: 12.91584 ms
Total: 78.417 ms
=============================================
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 0.61331 ms
[⏰ [NoSt] ImageNrom]: 6.13907 ms
[⏰ Lidar Backbone]: 31.54410 ms
[⏰ Camera Depth]: 0.17827 ms
[⏰ Camera Backbone]: 15.39754 ms
[⏰ Camera Bevpool]: 4.53443 ms
[⏰ VTransform]: 4.05770 ms
[⏰ Transfusion]: 9.82406 ms
[⏰ Head BoundingBox]: 7.59840 ms
Total: 73.134 ms
=============================================
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 0.59190 ms
[⏰ [NoSt] ImageNrom]: 5.96733 ms
[⏰ Lidar Backbone]: 28.54320 ms
[⏰ Camera Depth]: 0.14890 ms
[⏰ Camera Backbone]: 13.63533 ms
[⏰ Camera Bevpool]: 2.51645 ms
[⏰ VTransform]: 4.72758 ms
[⏰ Transfusion]: 12.64218 ms
[⏰ Head BoundingBox]: 9.39517 ms
Total: 71.609 ms
=============================================
==================BEVFusion===================
[⏰ [NoSt] CopyLidar]: 0.70038 ms
[⏰ [NoSt] ImageNrom]: 6.50742 ms
[⏰ Lidar Backbone]: 20.20282 ms
[⏰ Camera Depth]: 0.14195 ms
[⏰ Camera Backbone]: 23.13091 ms
[⏰ Camera Bevpool]: 2.61030 ms
[⏰ VTransform]: 2.73066 ms
[⏰ Transfusion]: 6.92064 ms
[⏰ Head BoundingBox]: 13.80426 ms
Total: 69.542 ms
=============================================
Save to build/cuda-bevfusion.jpg
9结果分析
[⏰ [NoSt] CopyLidar]: 0.70038 ms
[⏰ [NoSt] ImageNrom]: 6.50742 ms
[⏰ Lidar Backbone]: 20.20282 ms
[⏰ Camera Depth]: 0.14195 ms
[⏰ Camera Backbone]: 23.13091 ms
[⏰ Camera Bevpool]: 2.61030 ms
[⏰ VTransform]: 2.73066 ms
[⏰ Transfusion]: 6.92064 ms
[⏰ Head BoundingBox]: 13.80426 ms
Total: 69.542 ms
字段
含义
CopyLidar
激光雷达点云数据拷贝、内存预处理耗时
ImageNrom
图像归一化、预处理耗时
Lidar Backbone
激光雷达骨干网络（SPCONV-SCN）特征提取耗时
Camera Depth
相机深度估计分支前处理 / 编码耗时
Camera Backbone
相机 ResNet50 骨干网络特征提取耗时
Camera Bevpool
相机特征 BEV 池化、视图映射耗时
VTransform
视图变换模块，将 2D 图像特征转为 BEV 鸟瞰特征耗时
Transfusion
相机 BEV + 激光雷达 BEV 特征融合模块耗时
Head BoundingBox
检测头，输出 3D 框、类别、置信度、尺寸、朝向、速度耗时
Total
单帧完整端到端推理总耗时
共推理检测了 6 帧平均：71.18 ms / 帧，帧率约 14.05 FPS
10推理结果展示:
整合源码解读成果与技术实现要点，形成系统化的技术细节整理输出，为二次开发提供清晰的技术支撑。
数据集
BEVFusion 推理所需的「一帧 nuScenes 样本」打包数据，自采 6 路相机 + LiDAR 生成
example-data 目录文件总表
一、6 路相机原始图像
0-FRONT.jpg
前视相机
1-FRONT_RIGHT.jpg
右前相机
2-FRONT_LEFT.jpg
左前相机
3-BACK.jpg
后视相机
4-BACK_LEFT.jpg
左后相机
5-BACK_RIGHT.jpg
右后相机
二、点云数据
文件
含义
points.tensor
LiDAR 点云（fp16， 5 维：x, y, z, intensity, time_lag）
三、标定 / 坐标变换矩阵（main.cpp 实际使用）
文件
形状
含义
camera2lidar.tensor
[1,6,4,4]
各相机坐标系 → LiDAR 坐标系外参，用于相机 frustum 反投影到 BEV
camera_intrinsics.tensor
[1,6,4,4]
各相机内参（齐次形式），求逆后用于像素 → 相机射线
lidar2image.tensor
[1,6,4,4]
LiDAR → 图像像素整体变换，用于深度图生成 + 可视化投影
img_aug_matrix.tensor
[1,6,4,4]
图像数据增强（resize/crop/flip）矩阵，对 704×256 输入做坐标补偿
源码解析
结合example-data数据来看一下源码是如何输入的
一、run.sh 启动链路
tool/run.sh 做三件事：
source tool/environment.sh —— 设定 DEBUG_DATA=example-data、DEBUG_MODEL=resnet50int8、DEBUG_PRECISION=int8（environment.sh#L56-L60）。
cmake .. && make -j —— 用根目录 CMakeLists.txt 编译，产物 build/bevfusion。
./build/bevfusion $DEBUG_DATA $DEBUG_MODEL $DEBUG_PRECISION —— 即 main.cpp:260 main(argc, argv)，三个 argv 分别填入 data / model / precision。
二、example-data 各文件 → 源码入口点
下面按文件名给出"从入口 main.cpp 出发的调用链 → 最终落地位置"，仅列出 main.cpp 真正读取的文件。
1. camera2lidar.tensor、camera_intrinsics.tensor、img_aug_matrix.tensor（相机几何参数）
main.cpp:284-289 读入 → 调用 Core::update。
main.cpp::main
└─ core->update(camera2lidar, camera_intrinsics, lidar2image, img_aug_matrix, stream)
└─ bevfusion.cpp::CoreImplement::update (bevfusion.cpp:227)
├─ camera_depth_->update(img_aug_matrix, lidar2image) → camera-depth.cu:103
└─ camera_geometry_->update(camera2lidar, camera_intrinsics, img_aug_matrix)
→ camera-geometry.cu:218
具体使用：
camera-geometry.cu：把 img_aug_matrix 求逆、camera_intrinsics 求逆，连同 camera2lidar 拷到 GPU，在 compute_geometry_kernel 里把每个相机像素 frustum 反投影到 LiDAR 坐标系，生成 BEVPool 用的 indices/intervals。这是 相机分支特征→BEV 体素 的核心几何依据。
camera-depth.cu：img_aug_matrix + lidar2image 在 compute_depth_kernel 里把 LiDAR 点投到 6 路相机像素平面，生成 depth.tensor（即每路相机的稀疏深度图），喂给 camera_backbone_->forward。
2. lidar2image.tensor
两个用途：
推理路径：和上面一起进入 camera-depth.cu，承担"LiDAR → 像素"投影。
可视化：main.cpp:307 调用 visualize()，写入 ImageArtistParameter::viewport_nx4x4，由 visualize.cu 的 image_artist 把 3D 检测框投回到每张相机图。
3. points.tensor（LiDAR 点云）
main.cpp:294, 298 读入并直接传给：
core->forward(images, lidar_points, num_points, stream)
└─ bevfusion.cpp::CoreImplement::forward_only / forward_timer (bevfusion.cpp:104 / 136)
├─ cudaMemcpyAsync → lidar_points_device_ (bevfusion.cpp:114-116)
├─ lidar_scn_->forward(lidar_points_device_, num_points) → lidar-scn.cpp:43
│ └─ voxelization_->forward(...) → lidar-voxelization.cu
└─ camera_depth_->forward(lidar_points_device_, num_points, 5)→ camera-depth.cu
即 points.tensor 同时被 LiDAR 主干（SCN/体素化）和相机深度生成模块共享。
4. 6 张 -FRONT/BACK.jpg
main.cpp::load_images 用 stbi_load 读入 → forward() → normalizer_->forward（camera-normalization.cu）做 resize/归一化，得到 fp16 张量，传递给 camera_backbone_->forward（camera-backbone.cu）。
三、整体数据流
example-data/
*.jpg ─► load_images ─► normalizer ─► camera_backbone ─┐
img_aug_matrix ─► core->update ─► camera_depth.update ─┐ │
lidar2image ─► core->update ─► camera_depth.update ─┤ │
▼ │
points.tensor ─► core->forward ─┬─► camera_depth.forward (生成 depth) ──────┤
│ ▼
└─► lidar_scn.forward ─► voxelization ─► sparse conv ─┐
camera2lidar ─► core->update ─► camera_geometry.update ──┐ │
camera_intrinsics ─► core->update ─► camera_geometry.update ──┴─► bevpool indices ────┤
img_aug_matrix ─► core->update ─► camera_geometry.update ─ │
▼
transfusion → transbbox → BoundingBox
lidar2image ─► main.cpp::visualize (3D 框投回相机图)
实时推理展示
检测话题
root@nvidia-desktop:/storage/Lidar_AI_Solution/CUDA-BEVFusion# ros2 topic echo /perception/bevfusion/detections_3d
header:
stamp:
sec: 1779094886
nanosec: 884146690
frame_id: rslidar
objects:
- class_id: 2
class_name: construction_vehicle
score: 0.1416015625
x: 2.8875021934509277
y: -2.1749980449676514
z: -0.25576984882354736
w: 1.282772183418274
l: 2.6892380714416504
h: 2.0388834476470947
yaw: -0.017806081101298332
vx: -9.47713851928711e-06
vy: 5.364418029785156e-07
---
检测频率
这个频率跟雷达保持一致
root@nvidia-desktop:/storage/Lidar_AI_Solution/CUDA-BEVFusion# ros2 topic hz /perception/bevfusion/detections_3d
WARNING: topic [/perception/bevfusion/detections_3d] does not appear to be published yet
average rate: 4.958
min: 0.101s max: 0.317s std dev: 0.06317s window: 6
average rate: 6.409
min: 0.093s max: 0.386s std dev: 0.08582s window: 16
average rate: 7.503
min: 0.092s max: 0.386s std dev: 0.07172s window: 27
average rate: 7.166
min: 0.092s max: 0.386s std dev: 0.07297s window: 33
average rate: 7.230
min: 0.092s max: 0.386s std dev: 0.07167s window: 42
average rate: 7.636
min: 0.092s max: 0.386s std dev: 0.06620s window: 52
使用自己真实的场景测试
posted @
2026-07-01 15:29
MKY-门可意
阅读(62)
评论(0)
收藏
举报
刷新页面返回顶部
公告
博客园
©  2004-2026
浙公网安备 33010602011771号
浙ICP备2021040463号-3