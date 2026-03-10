## Auto Test 框架 v4.0
> pytest + playwright + allure + Gemini AI 实现 UI 自动化测试 + AI 自愈

简体中文 | [English](./README.en.md)

## 实现功能
- **关键字驱动**: YAML 定义测试用例，无需编码即可编写 UI 自动化测试
- **Action Registry 模式**: 模块化动作注册表，支持多人协作开发
- **AI 自愈 (Self-Healing)**: 当传统定位器失效时，基于 Gemini Vision 的 AI 自动识别并修复元素定位
- **RAG 知识库增强**: 使用 FAISS + SentenceTransformers 构建领域知识库，为 AI 提供业务上下文
- **执行历史追踪**: 自动记录已成功执行的步骤，为 AI 提供当前测试流程状态
- **多环境支持**: 通过 `--env` 参数切换 staging/release 环境
- **动态多断言**: 支持多种断言类型（文本可见性、元素存在性等）
- **测试完成自动生成 Allure 测试报告**

## 架构概览

```
YAML 测试定义
    ↓
test_ui.py (步骤分发器 + 执行历史追踪)
    ↓
actions/ (Action Registry 动作注册表)
    ├── base.py → smart_click / smart_fill (含 AI Fallback)
    ├── module.py / product.py / form.py ...
    ↓
┌─ 传统 Playwright 定位 (role/text/locator)
│   成功 → 继续执行
│   失败 ↓
└─ AI 自愈引擎 (utils/ai_vision.py)
       ├── 截图 + SOM 标注
       ├── RAG 知识库检索 (utils/rag_knowledge.py)
       ├── 执行历史上下文注入
       └── Gemini Vision 分析 → 输出目标元素 ID
              ↓
         修复后继续执行
              ↓
         Allure 报告 + 截图/录屏
```

## 目录结构
```shell
├─config
│  └─config.yaml          # 配置文件
├─page
│  └─home.py              # UI 层基础封装
├─recordings              # playwright codegen 录制脚本
├─test_case
│  └─UI
│    └─Test_Katana
│       ├─actions/         # Action Registry (动作注册表)
│       │  ├─__init__.py   # 注册表入口
│       │  ├─base.py       # 基础动作 (smart_click, smart_fill, AI Fallback)
│       │  ├─module.py     # 模块相关动作
│       │  ├─product.py    # 产品相关动作
│       │  ├─form.py       # 表单相关动作
│       │  └─layout.py     # 布局验证动作
│       ├─utils/           # [NEW v4.0] AI 自愈工具集
│       │  ├─ai_vision.py  # Gemini Vision AI 服务 (SOM + 多 API Key 轮换)
│       │  ├─rag_knowledge.py  # RAG 知识库 (FAISS + SentenceTransformers)
│       │  └─Knowledge_Base.md # 领域知识库文档
│       ├─conftest.py      # Pytest fixtures (多环境 + 认证)
│       ├─test_ui.py       # 核心测试执行引擎 (含执行历史追踪)
│       └─Katana_curator_smoke_release.yaml  # Release 环境用例
├─tools                    # 工具包
│  ├─__init__.py           # Allure 集成等
│  └─get_cookie.py         # Cookie 获取
├─requirements.txt         # 项目依赖
└─main.py                  # 主启动文件
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境配置
创建 `.env` 文件（或设置环境变量），配置 Gemini API Keys：
```
GEMINI_API_KEYS=key1,key2,key3
```

### 3. 运行测试

```bash
# 运行特定用例 (headed 模式)
pytest test_case/UI/Test_Katana/test_ui.py -k "testT4777" --headed -v --env release --storage-state test_case/UI/Test_Katana/cookie_release.json

# 运行全部用例并生成报告
python main.py
```

### 4. 查看报告
运行完成后 Allure 报告会自动打开。

## V4.0 AI 自愈架构

### 核心流程
1. `smart_click` 先尝试传统 Playwright 定位 (role/name/text)
2. 如果 5s 内超时，触发 Legacy Fallback (15s)
3. 如果仍然失败，触发 **AI Self-Healing**：
   - 对当前页面截图并注入 SOM (Set-of-Mark) 标注
   - 查询 RAG 知识库获取相关业务上下文
   - 将截图 + 目标描述 + 执行历史 + RAG 知识 发送至 Gemini Vision
   - AI 返回诊断结果和目标元素 ID
   - 根据 AI 指引点击目标元素

### RAG 知识库
`utils/Knowledge_Base.md` 存储了系统的业务规则和 UI 导航模式，包括：
- 系统架构和模块概述
- 常见导航模式（FAB 按钮、事件管理等）
- UI 元素特征和定位策略
- 已知的自动化陷阱和解决方案

### 如何补充知识库
当 AI 自愈出现误判时，在 `Knowledge_Base.md` 中添加对应的业务规则，AI 下次会自动检索并参考。

## 多环境支持
```bash
# Staging 环境
pytest --env staging ...

# Release 环境
pytest --env release ...
```
