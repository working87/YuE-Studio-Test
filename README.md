# YuE Studio Test

基于 [YuE2](https://github.com/multimodal-art-projection/YuE)（M-A-P 等机构开源的音乐生成模型）的**本地 AI 作曲桌面程序**，Windows + NVIDIA 显卡。
哼一段旋律变成歌、写词作曲、生成纯音乐、给参考歌曲换词或换风格，全部在自己电脑上跑；内置 AI 助手，也能通过 MCP 交给任何 Agent 来操作。

> 这是一个**非官方**的社区项目（测试版），与 YuE / M-A-P 官方无关。模型、论文和原始代码的版权归原作者，见文末[致谢与引用](#致谢与引用)。
> 目前只在 **Windows 11 + RTX 5070 Ti 16GB** 上完整测试过，其他显卡的支持情况见[显卡要求](#显卡要求与自动识别)。

- 一键安装：`install.bat` 自动识别显卡，所有下载都走**国内镜像**（清华 PyPI、阿里云 PyTorch、npmmirror、ModelScope），不需要代理，不装任何系统级软件
- 不需要自己装 CUDA、Python、FFmpeg，也不需要 WSL、ComfyUI 或浏览器
- 装好后约占 15 GB（一个 Python 环境约 5 GB + 模型约 10 GB），全部放在项目文件夹里

## 功能

| 功能 | 做什么 | 实测（RTX 5070 Ti 16GB） |
|---|---|---|
| 哼唱 → 带词歌曲 | 按你哼的旋律成曲并填词演唱（自己写词，或按每句音符数让 AI 写） | 旋律跟随 68~97%，长度跟随哼唱 |
| 哼唱 → 纯音乐 | 乐器演奏你哼的旋律，无人声（需哼 20 秒以上） | 干净旋律跟随 77~99%；真人哼唱约半数版本仍会带轻微哼唱，默认一次出 4 版挑选 |
| 写词作曲 | 风格 + 歌词 → 先出旋律与和弦谱，再出歌（乐谱可继续精修） | 3 分钟的歌约 2 分钟生成 |
| 纯音乐 | 风格 + 主奏乐器，无人声 | 按段落裁到目标长度，演奏完乐谱自然收尾 |
| 参考歌曲改编 | 保留原曲旋律；歌词框粘原词就按原词唱、写新词就是换词（也可留空，扒谱后按每句音符数再填）；曲风保持或换新（换新时可选重新配和声或保留原和声）；演唱者任选。原词可直接粘 SRT/LRC 字幕 | 旋律跟随 85%（保留原和声）~ 92%（重新配和声） |
| 改谱精修 | 在已有作品上改速度 / 换风格 / 改词 / 手动改 ABC 乐谱 | |

- **预设**：曲风 61 种（8 组）、情绪 17 种、人声 20 种、主奏乐器 18 种，常用的是按钮，其余在下拉菜单；也可以自由描述。
- **AI 助手**：填一个兼容 OpenAI 的接口（豆包/火山方舟、DeepSeek、通义千问……），说一句"伤感的粤语女声，词你帮我写"，它会一次把参数填好，只追问缺的。
- **MCP**：程序本身就是一个 MCP 服务，复制配置给 Claude、Cursor、Trae、Coze 等 Agent 就能用。
- 语言：普通话、英语（官方支持）；粤语、日语、韩语（实验）。

## 显卡要求与自动识别

安装脚本第一步会运行 `scripts\detect_gpu.ps1` 识别显卡，按下表决定能不能装、用什么配置（也可以单独运行它看结果）：

| 显卡 | 结果 | 配置 |
|---|---|---|
| 显存 ≥ 23 GB（RTX 3090/4090/5090 等） | 支持 | `24g`：官方无损配置，最快 |
| 显存 15~23 GB（RTX 4080/5070 Ti/5080、4060 Ti 16G 等） | **支持（已测试）** | `16g`：无损；窗口顶部可切"省显存"（`16g-safe`，慢约 40%） |
| 12 GB，RTX 40/50 系 | 可用但慢 | `12g`：FP8 量化 + 卸载，30 秒的歌约 2 分钟 |
| 12 GB，RTX 30 系及更早 | 实验性，未测试 | `12g-safe`：无损 + 卸载（这些卡不支持 FP8） |
| 显存 < 12 GB | 不支持 | 见下方 [8GB 显卡](#8gb-显卡) |
| RTX 20 系 / Volta | 实验性，未测试 | 没有原生 BF16，可能很慢 |
| GTX 10 系及更早 | 不支持 | PyTorch 2.10 不再支持 |
| 驱动低于 570 | 先更新驱动 | CUDA 12.8 需要 570+，[NVIDIA 驱动下载](https://www.nvidia.cn/drivers) |

程序运行时也会按显卡自动选配置，界面上只有一个"快速 / 省显存"开关，不需要懂显存档位。
"快速"让模型常驻显存；"省显存"在合成声音阶段把用不到的那部分权重挪到内存，音质完全一样，只是慢一些。
显存被其他程序占用导致不够时，"快速"会自动改用"省显存"重跑。

### 8GB 显卡

本项目使用官方 PyTorch 实现，8GB 显卡跑不动。社区已有 GGUF 量化版（**本项目未集成、未测试**，仅供参考）：
[yue2.cpp](https://github.com/ServeurpersoCom/yue2.cpp)（Q8/Q5/Q4，CUDA/Vulkan，权重 [Serveurperso/YuE2-GGUF](https://huggingface.co/Serveurperso/YuE2-GGUF)，需自行编译）、
[yuey.cpp](https://github.com/betweentwomidnights/yuey.cpp)（Q4_K_M 面向 8GB 笔记本，权重 [thepatch/YuE2-3B-GGUF](https://huggingface.co/thepatch/YuE2-3B-GGUF)）、
[audio-cpp/Yue2-3B-GGUF](https://huggingface.co/audio-cpp/Yue2-3B-GGUF)。

## 安装

**需要：** Windows 10/11 64 位、NVIDIA 显卡和 570 以上的驱动、约 20 GB 可用磁盘空间（装好后占约 15 GB；多出的约 5 GB 是安装时的临时下载缓存，放在项目文件夹里，装完自动清掉）、能访问国内镜像的网络。
不需要提前装 Python、CUDA、FFmpeg 或 git。

1. 下载本项目：点页面上的 **Code → Download ZIP** 解压，或 `git clone`。放在剩余空间充足的盘，路径里最好不要有中文和空格。
2. 双击 **`install.bat`**。它会依次：
   1. 识别显卡（不满足要求会直接说明原因并停止）
   2. 从清华 PyPI 镜像下载 uv（Python 包管理器）
   3. 从 npmmirror 下载 Python 3.12，建立 `.venv` 环境；从清华 PyPI 和阿里云 PyTorch 镜像安装依赖（torch 自带 CUDA 运行库）
   4. 准备 FFmpeg（清华 PyPI 上的 `imageio-ffmpeg`）
   5. 检查 PyTorch 能否使用显卡
   6. 从 ModelScope 下载模型（约 10 GB）
   7. 自检（`python -m studio doctor`）

   中途断网的话，重新双击 `install.bat` 即可，已完成的步骤会跳过，模型会断点续传。完整日志在 `install.log`。
3. 双击 **`start.bat`** 打开程序。

所有东西都装在项目文件夹里（`.venv\` 约 4.7 GB、`tools\` 约 0.2 GB、`models\` 约 9.8 GB），不往 C 盘写缓存，卸载就是删掉整个文件夹。

| 下载内容 | 来源（国内镜像） | 大小 |
|---|---|---|
| uv | 清华 PyPI `pypi.tuna.tsinghua.edu.cn` | 约 20 MB |
| Python 3.12 | npmmirror `registry.npmmirror.com/-/binary/python-build-standalone` | 约 20 MB |
| torch / torchaudio 2.10（含 CUDA 12.8） | 阿里云 `mirrors.aliyun.com/pytorch-wheels/cu128` | 约 3 GB |
| 其他 Python 依赖、FFmpeg | 清华 PyPI | 约 0.5 GB |
| YuE2-3B、YuE2-Vae、SheetSage2、MERT-v2 | ModelScope `modelscope.cn`（与 Hugging Face 上的文件逐字节一致） | 约 10 GB |
| YuE2 官方代码 | 已包含在本仓库 `vendor/YuE` | |

能直接访问 Hugging Face 的话，也可以 `install.bat -ModelSource hf`。

### 让 AI Agent 帮你部署

把下面这段话发给 Claude Code、Cursor、Trae 等能执行命令的 Agent：

> 请按照这个仓库的 AGENTS.md 在我的电脑上部署 YuE Studio：先检测显卡再决定怎么装，所有下载都用国内镜像，装完运行自检并告诉我结果。

[AGENTS.md](AGENTS.md) 里写了检测显卡、判断能否安装、安装、自检、排错的完整步骤。

## 使用

- **手动创作**：左边选功能，右边按按钮/下拉菜单选预设，点生成。作品卡片里可以试听、看乐谱、下载 FLAC。
- **AI 助手**：顶部切到「AI 助手」→「设置」，填接口地址（默认火山方舟 `https://ark.cn-beijing.volces.com/api/v3`）、模型 ID（必须支持工具调用）和你自己的 API Key（只存在本机 `data\settings.json`）。
- **给外部 Agent 用（MCP）**：程序开着时，它就是一个 MCP 服务 `http://127.0.0.1:7860/agent/mcp`（Streamable HTTP）。点顶部「接入 Agent (MCP)」可以一键复制配置和说明。只支持 stdio 的客户端：

  ```json
  {
    "mcpServers": {
      "yue-studio": {
        "command": "<项目目录>\\.venv\\Scripts\\python.exe",
        "args": ["-m", "studio", "mcp"],
        "cwd": "<项目目录>"
      }
    }
  }
  ```

  提供 10 个工具：`wizard_start`、`wizard_fill`、`wizard_answer`、`wizard_back`、`submit_song`、`get_job`、`list_jobs`、`provide_lyrics`、`cancel_job`、`style_reference`。
  `style_reference` 可以查 [studio/style_guide.md](studio/style_guide.md)：官方演示的 99 段风格描述写法、段落标签用法、全部预设。
- **Claude Code**：仓库自带技能 [.claude/skills/yue-studio](.claude/skills/yue-studio/SKILL.md)，在项目目录里对 Claude Code 说"帮我做首歌"即可。
- **命令行**：`.venv\Scripts\python.exe -m studio --help`（`doctor` 自检、`flow` 向导、`submit`、`job` 等）。
- 想要一个 exe：运行 `scripts\build_exe.ps1`，会在项目目录生成 `YuEStudio.exe`（只包含界面，仍然使用旁边的 `.venv` 和 `models`）。

## 已知限制

- **纯音乐会偶尔带哼唱**：YuE2 没有纯音乐开关，即使乐谱人声部全是休止、风格写了 `instrumental, no vocals`，也可能哼几句。
  这是模型本身的限制，程序不做事后去人声（人声分离会连弦乐、萨克斯一起减掉）。建议一次出多版挑选。
- **哼唱太短**（扒出的旋律短于 20 秒）时，纯音乐模式会让你哼长一些：太短时模型多半会自己把旋律唱出来。
- **长度**：YuE2 没有时长参数，程序先让模型写谱，再改谱控制长度。纯音乐按段落把乐谱裁到目标长度（保留尾奏）；
  哼唱、参考歌曲跟随原音频长度。这些情况下会要求模型把乐谱完整演奏完、再留 2 秒余音，实测都在乐谱结尾自然收尾
  （做法与 [yuey.cpp](https://github.com/betweentwomidnights/yuey.cpp) 的 score-aligned generation 相同）。
  带歌词的歌由模型自己规划结构，长度波动很大（同样 6 句歌词实测 74~207 秒，模型有时会加很长的器乐段）。
- **每次生成都不一样**：即使随机种子相同，结果也会不同。
- **男声偏高**：YuE2 常把男声写得和女声一样高（实测 250~310 Hz）。"男女对唱"只会唱出一个声部。
- **语言**：唱的就是歌词本身，所选语言必须和歌词一致（不一致会被拦下，可以一键翻译）。粤语、日语、韩语为实验性。
- 同一张显卡一次只跑一个任务，其余排队。
- 实验数据和方法见 [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)。

## 目录结构

```
install.bat / install.ps1   一键安装（识别显卡 → uv → Python → 依赖 → FFmpeg → 模型 → 自检）
start.bat                   打开程序
studio/                     程序本体：界面服务、任务队列、向导、AI 助手、MCP、生成流程
web/                        界面（本地文件，不依赖 CDN）
scripts/                    detect_gpu.ps1、download_models.py、patch_windows.py、build_exe.ps1 等
vendor/YuE/                 YuE2 官方推理代码（yue2-infer 0.1.6，Apache-2.0，未修改）
.claude/skills/yue-studio/  Claude Code 技能
tests/                      不需要显卡的单元测试 + 旋律跟随测量工具
docs/                       实验记录
（安装后生成，不在仓库里）.venv/  tools/  models/  data/（你的作品）
```

一首歌的流程：音频 → FFmpeg 转码 → SheetSage2 扒谱（ABC 乐谱）→ 按需改谱（速度、裁剪、换声部）→ YuE2 规划与生成 → 音频。
每个模型在单独的子进程里运行，前一步的显存完全释放后才开始下一步。

## 致谢与引用

本项目只是一个外壳和工作流，核心能力全部来自以下项目，感谢原作者：

- **[YuE / YuE2](https://github.com/multimodal-art-projection/YuE)**（HKUST、M-A-P 等）：音乐生成模型与推理代码。
  代码 Apache-2.0（本仓库 `vendor/YuE` 未经修改地收录了官方 main 分支 2026 年 9 月的版本，即 yue2-infer 0.1.6，来源说明见 [vendor/YUE_SOURCE.md](vendor/YUE_SOURCE.md)，许可见 [vendor/YuE/LICENSE](vendor/YuE/LICENSE)）；
  权重 [YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)、[YuE2-Vae](https://huggingface.co/m-a-p/YuE2-Vae) 为 CC BY-NC 4.0，另附个人创作者许可（见 [vendor/YuE/MODEL_LICENSE](vendor/YuE/MODEL_LICENSE)）。
  官方演示：<https://map-yue2.github.io/>
- **[SheetSage2](https://huggingface.co/m-a-p/SheetSage2)**：扒谱（音频 → 旋律与和弦），权重 CC BY-NC 4.0。
- **[MERT-v2](https://huggingface.co/m-a-p/MERT-v2-FullSong)**：SheetSage2 使用的音频编码器，权重 CC BY-NC 4.0。
- [studio/style_guide.md](studio/style_guide.md) 第 4、5 节的风格描述原文摘自 [YuE2 官方演示页](https://map-yue2.github.io/)（不含歌词），版权归原作者。
- [abcjs](https://github.com/paulrosen/abcjs)（MIT）：乐谱显示。
- 国内镜像：[清华大学开源软件镜像站](https://mirrors.tuna.tsinghua.edu.cn/)、[阿里云镜像站](https://developer.aliyun.com/mirror/)、[npmmirror](https://npmmirror.com/)、[ModelScope 魔搭社区](https://modelscope.cn/)。

使用本项目生成的作品或研究时，请引用 YuE：

```bibtex
@article{yuan2025yue,
  title   = {{YuE}: Scaling Open Foundation Models for Long-Form Music Generation},
  author  = {Yuan, Ruibin and Lin, Hanfeng and Guo, Shuyue and Zhang, Ge and others},
  journal = {arXiv preprint arXiv:2503.08638},
  year    = {2025},
  url     = {https://arxiv.org/abs/2503.08638}
}
@article{li2023mert,
  title   = {{MERT}: Acoustic Music Understanding Model with Large-Scale Self-supervised Training},
  author  = {Li, Yizhi and Yuan, Ruibin and Zhang, Ge and others},
  journal = {arXiv preprint arXiv:2306.00107},
  year    = {2023},
  url     = {https://arxiv.org/abs/2306.00107}
}
```

## 许可

- 本项目自己的代码：[Apache-2.0](LICENSE)。
- **模型权重不属于本项目**，由安装脚本从 ModelScope 下载，遵守各自的许可（CC BY-NC 4.0）。
  按 YuE2 的个人创作者许可，个人用户和创作者可以免费用它生成作品并发布、出售；**公司商用模型权重需要另外联系 YuE 团队取得授权**。
  SheetSage2、MERT-v2（扒谱用）的权重许可是 CC BY-NC 4.0，没有这项额外条款；涉及商业用途请自行阅读原许可评估。
- 改编他人的歌曲请只用于个人学习，不要发布或冒充原唱。
