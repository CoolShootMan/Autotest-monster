# Auto Test Framework v4.0 - 技术指南

## 目录
- [1. 项目架构](#1-项目架构)
- [2. 测试执行流程](#2-测试执行流程)
- [3. AI 自愈系统](#3-ai-自愈系统)
- [4. Action Registry 动作注册表](#4-action-registry-动作注册表)
- [5. 添加新测试用例](#5-添加新测试用例)
- [6. RAG 知识库维护](#6-rag-知识库维护)
- [7. 调试技巧](#7-调试技巧)
- [8. 常见问题](#8-常见问题)

---

## 1. 项目架构

### 1.1 核心组件

```
autotest-monster/
├── test_case/UI/Test_Katana/
│   ├── actions/                # Action Registry (动作注册表)
│   │   ├── __init__.py         # 注册表入口 + get_action()
│   │   ├── base.py             # 基础动作 (smart_click, smart_fill)
│   │   ├── module.py           # 模块相关动作
│   │   ├── product.py          # 产品相关动作
│   │   ├── form.py             # 表单相关动作
│   │   └── layout.py           # 布局验证动作
│   ├── utils/                  # [v4.0] AI 自愈工具集
│   │   ├── ai_vision.py        # Gemini Vision AI 服务
│   │   ├── rag_knowledge.py    # RAG 知识库引擎
│   │   └── Knowledge_Base.md   # 领域知识库文档
│   ├── conftest.py             # Pytest fixtures (环境/认证)
│   ├── test_ui.py              # 核心测试执行引擎
│   └── Katana_curator_smoke_release.yaml  # 测试用例定义
├── page/
│   └── home.py                 # Playwright UI 操作封装
├── tools/
│   ├── __init__.py             # Allure 集成
│   └── get_cookie.py           # Cookie 获取
└── main.py                     # 主启动入口
```

### 1.2 数据流

```
YAML 测试定义
    ↓
conftest.py (pytest fixtures: 浏览器/环境/认证)
    ↓
test_ui.py (步骤解析 → Action Registry 分发 + 执行历史追踪)
    ↓
actions/base.py → smart_click (传统定位 → Legacy Fallback → AI 自愈)
    ↓                                                    ↓
page/home.py (Playwright 操作)              utils/ai_vision.py (Gemini Vision)
    ↓                                            ↓
浏览器自动化                              utils/rag_knowledge.py (RAG 检索)
    ↓
Allure 报告 + 截图/录屏
```

---

## 2. 测试执行流程

### 2.1 完整流程

```bash
python main.py
```

**执行步骤:**
1. `main.py` 配置 logger、Allure 路径
2. 调用 `pytest` 执行 `test_ui.py`
3. `conftest.py` 创建 browser/context fixtures (加载 cookie)
4. `test_ui.py` 的 `test_case` 函数被参数化执行
5. 每个步骤通过 `get_action(key)` 分发到对应的处理函数
6. 成功的步骤被记录到 `_execution_history` 列表
7. 生成 Allure HTML 报告

### 2.2 单个测试用例执行

```bash
# 运行特定用例
pytest test_case/UI/Test_Katana/test_ui.py -k "testT4777" --headed -v --env release --storage-state test_case/UI/Test_Katana/cookie_release.json
```

### 2.3 多环境支持

通过 `--env` 参数切换：
- `--env staging` → 加载 `_staging.yaml`
- `--env release` → 加载 `_release.yaml`

---

## 3. AI 自愈系统

### 3.1 触发机制

`smart_click` (在 `actions/base.py` 中) 实现了三级容错：

```
Level 1: 标准 Playwright 定位 (5s timeout)
    ↓ 失败
Level 2: Legacy Fallback 定位 (15s timeout)
    ↓ 失败
Level 3: AI Self-Healing (Gemini Vision)
```

### 3.2 AI Vision 服务 (`utils/ai_vision.py`)

**AIVisionService 类功能：**
- **多 API Key 轮换**: 支持多个 Gemini API Key，自动在 Rate Limit 时切换
- **SOM 标注**: 在截图上注入 Set-of-Mark 标签，帮助 AI 精确定位元素
- **结构化输出**: AI 返回 JSON 格式的诊断结果，包含：
  - `consciousness_diagnosis`: 当前页面状态诊断
  - `thought_process`: 推理过程
  - `suggested_action`: 建议操作 (GOAL_CLICK / NAVIGATE_BACK 等)
  - `label_id`: 目标元素的 SOM 标签 ID

**Prompt 包含的上下文信息：**
1. 业务背景描述 (Pear 系统概述)
2. 当前步骤的目标描述
3. 已成功执行的步骤列表 (`_execution_history`)
4. RAG 知识库检索结果
5. 测试用例的整体描述

### 3.3 RAG 知识库 (`utils/rag_knowledge.py`)

**技术栈：**
- **FAISS** (faiss-cpu): 向量相似度搜索
- **SentenceTransformers** (all-MiniLM-L6-v2): 文本嵌入模型

**工作流程：**
1. 启动时加载 `Knowledge_Base.md`，按 `##` 标题分块
2. 使用 SentenceTransformers 对每个块进行向量编码
3. 建立 FAISS 索引
4. AI 自愈触发时，根据当前目标 + 执行历史检索 Top-3 相关知识
5. 将检索到的知识注入 AI Prompt

### 3.4 执行历史追踪

`test_ui.py` 在 `page` 对象上维护 `_execution_history` 列表：

```python
page._execution_history = []

# 每步成功后追加
page._execution_history.append(f"Step '{k}': completed successfully")
```

这让 AI 知道"我已经完成了哪些步骤"，避免重复操作或误判当前位置。

---

## 4. Action Registry 动作注册表

### 4.1 架构

`actions/__init__.py` 维护关键字到函数的映射：

```python
ACTIONS = {
    "open": open_url,
    "R_click": smart_click,
    "fill": smart_fill,
    "wait_for_url": wait_for_url,
    # ...
}
```

`test_ui.py` 通过前缀匹配分发：
```python
action_fn = get_action(k)  # 根据键名前缀查找处理函数
action_fn(page, v)          # 执行
```

### 4.2 如何新增测试步骤

1. 在 `actions/` 下找到或新建模块文件
2. 编写处理函数：`def my_action(page: Page, v: dict): ...`
3. 在 `actions/__init__.py` 的 `ACTIONS` 字典中注册
4. 在 YAML 中使用对应的 key

---

## 5. 添加新测试用例

### 5.1 YAML 用例格式

```yaml
testT{编号}:
    description: "用例描述"
    test_step:
        open: "https://release.pear.us/events"
        wait_for_url: { url: "**/events" }
        sleep_after_open: 3000
        R_click_button: { role: 'button', name: 'Submit' }
        sleep_after_click: 2000
    expect_result:
        description: "验证结果"
        assertions:
            - { assertion_type: "element_visible_by_text", text: "Success" }
```

### 5.2 常用步骤速查

| 操作 | YAML 示例 | 说明 |
|------|----------|------|
| 打开页面 | `open: "https://..."` | 导航到 URL |
| 等待 URL | `wait_for_url: { url: "**/events" }` | 等待 URL 匹配 |
| 等待 | `sleep_after_open: 2000` | 毫秒 |
| 点击 (role) | `R_click_btn: { role: "button", name: "Submit" }` | 语义定位 |
| 点击 (text) | `R_click_item: { text: "Link text", exact: false }` | 文本定位 |
| 强制点击 | `R_click_item: { role: "paragraph", name: "...", force: true }` | 穿透遮罩层 |
| 填充 | `fill_email: { role: "textbox", name: "Email", value: "test@test.com" }` | |
| 上传 | `upload_file: { text: "Upload", file_path: "data/img.jpg" }` | |
| 勾选 | `check_agree: { role: "checkbox", name: "I agree" }` | |

### 5.3 断言类型

```yaml
assertions:
    - { assertion_type: "element_visible_by_text", text: "Success" }
    - { assertion_type: "element_text", role: "heading", value: "Title" }
    - { assertion_type: "element_visible", role: "button", visible: true }
```

---

## 6. RAG 知识库维护

### 6.1 文件位置
`test_case/UI/Test_Katana/utils/Knowledge_Base.md`

### 6.2 内容结构
使用 `##` 二级标题分块，每个块是一个独立的知识条目：

```markdown
## 1. System Overview
* 系统架构描述...

## 2. Common Navigation Patterns
* FAB 按钮使用规则...

## 3. UI Element Characteristics
* 定位策略和技巧...

## 4. Known Bugs
* 已知的自动化问题...

## 5. Standard Test Flows
* 标准测试流程模板...
```

### 6.3 何时更新知识库
- AI 自愈频繁误判同类元素时
- 发现新的 UI 模式或导航路径时
- 遇到 MUI 组件的特殊行为时

### 6.4 更新后生效
知识库在测试启动时自动重新索引，无需额外操作。

---

## 7. 调试技巧

### 7.1 查看 AI 自愈日志

AI 每次自愈都会在日志中输出：
```
🧠 AI SOM Thoughts: [AI的推理过程]
✨ AI 'Junior QA' Found Target ID: [元素ID]
🧠 Diagnosis: [页面状态诊断]
🚀 Suggested Action: [建议操作]
```

### 7.2 Headed 模式运行

```bash
pytest test_case/UI/Test_Katana/test_ui.py -k "testT4777" --headed -v
```

### 7.3 查看执行历史

日志中搜索 `>>> Current Step:` 可追踪完整执行路径。

---

## 8. 常见问题

### 8.1 AI 自愈误判

**原因**: 知识库中缺少对应的业务规则
**解决**: 在 `Knowledge_Base.md` 中补充相关知识条目

### 8.2 元素定位超时

**原因**: MUI 组件渲染延迟或遮罩层
**解决**: 使用 `force: true` 穿透遮罩，或增加 `sleep` 等待时间

### 8.3 Session 过期

**原因**: Cookie 文件中的 token 已过期
**解决**: 重新执行 `playwright codegen` 获取新的 cookie

### 8.4 Guest 模式

在 YAML 中添加 `guest: true` 使测试在未登录状态下运行：
```yaml
testT4279:
    guest: true
    description: "访客模式测试"
```

---

## 附录: 安全注意事项

以下文件包含敏感信息，已在 `.gitignore` 中排除，**禁止提交到 Git**：
- `cookie_*.json` — 包含真实的认证 Token
- `.env` — 包含 Gemini API Keys
- `ai_healing_screenshots/` — 包含系统截图（可能暴露业务数据）
