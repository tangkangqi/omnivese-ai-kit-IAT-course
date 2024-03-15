[# omnivese-ai-kit-IAT-course

课程目标
本课程旨在向开发者介绍如何使用NVIDIA Omniverse Kit开发AI扩展插件。通过学习Kit的基础概念、API以及环境配置、微服务、调用AI应用、插件发布等知识，学员将能够开发出自己的AI文生贴图插件。
课程时长
总时长：2小时
课程安排
第一部分：Kit基础概念 (30分钟)
- Kit核心组件、架构概览 (10分钟)
- Kit API介绍 (10分钟)
- Kit USD介绍 (10分钟)

第二部分：Kit开发 (45分钟)
- Kit UI交互开发 (15分钟)
  - 演示如何开发用户界面，包括基本的UI组件和交互逻辑。
- Extension.toml介绍 (10分钟)
  - 介绍如何使用Extension.toml文件配置和管理Kit扩展
- 使用AI功能 (20分钟)
  - Kit如何安装python pip包 (5分钟)
    - 介绍在Kit环境中安装和管理Python依赖。
  - Kit微服务开发 (5分钟)
    - 如何开发和使用Kit微服务，以支持复杂的AI功能。
  - 创建和导入Kit插件 (10分钟)
    - 演示如何创建Kit插件，并将其导入到Omniverse中使用

第三部分：案例：AI文生贴图插件开发 (45分钟)
- SDXL文生图代码介绍 (10分钟)
  - 介绍如何利用AI生成图像。
- Kit 新建Object和贴图 (10分钟)
  - 演示如何使用Kit Python API新建对象和应用贴图。
- 插件UI开发和调试 (15分钟)
- 文本生图插件发布 (10分钟)

请注意，课程内容和时间分配可能根据实际情况进行调整。
学员将获得相关的学习材料和代码示例

附录：课程运行环境详细配置

为了确保课程的顺利进行，以下是详细的环境配置要求：

系统环境：
- 操作系统：Windows 10
- GPU驱动：版本 537.13
- CUDA版本：12.3
- Omniverse环境：
  - OVE已安装
  - Omniverse USD Composer版本为2023.2.0
- 开发环境：
  - Visual Studio Code (Vscode)，安装日期为2024年3月12日的最新版本

AI开发环境：
- Python环境管理：
  - Miniconda，安装日期为2024年3月12日的最新版本
  - 在Miniconda中创建Python 3.12环境
- 深度学习库：
  - 安装PyTorch 2.2.0及相关库, 参考安装指南：PyTorch Get Started - Previous Versions
- 文生图模型下载：
  - 从Huggingface下载LCM模型。模型链接：LCM_Dreamshaper_v7
网络环境：
- 需要能够访问Google的网络环境，以便于AI代码运行时能够高速访问GitHub、Huggingface和pip官方源。


注意事项：
- 确保在安装和配置环境之前，您的系统满足上述所有要求。
- 安装CUDA和GPU驱动时，请遵循官方指南，确保版本兼容性。
- 在配置Python环境时，确保使用的是Miniconda创建的指定版本环境，以避免版本冲突。
- 在下载和使用Huggingface模型时，请确保遵守相关使用协议和条件。
- 确保网络环境稳定，以便于顺利完成模型下载和库安装。

附录：
课程运行环境：
Windows 10 系统
GPU Driver: 537.13 
CUDA版本:  12.3 
OVE 已安装，Omniverse USD Composer 2023.2.0
Vscode ， 安装24/3/12 最新版本

AI 环境：
- Miniconda， 安装24/3/12 最新版本
- Miniconda 中创建python 3.12 环境:
- 安装torch2.2.0, 参考： https://pytorch.org/get-started/previous-versions/
- pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
- Huggingface 下载LCM 模型：https://huggingface.co/SimianLuo/LCM_Dreamshaper_v7/tree/main

能够访问google的网络环境 （ AI 代码运行，需要github，huggingface, pip 官方源高速访问）
](https://vj0y7kxa0d.feishu.cn/docx/TKqKdBqHioxUFvx36j9cjZpOnFd)
