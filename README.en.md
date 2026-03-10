## Auto Test Framework v4.0
> UI Automation Testing with AI Self-Healing using Python + Pytest + Playwright + Allure + Gemini Vision AI

English | [简体中文](./README.md)

## Features
- **Keyword-Driven Testing**: Define test cases in YAML — no coding required
- **Action Registry Pattern**: Modular action registry supporting team collaboration
- **AI Self-Healing**: When traditional locators fail, Gemini Vision AI automatically identifies and repairs element targeting
- **RAG Knowledge Base**: FAISS + SentenceTransformers powered domain knowledge retrieval for AI context
- **Execution History Tracking**: Records successful steps to provide AI with current test flow state
- **Multi-Environment Support**: Switch between staging/release via `--env` parameter
- **Dynamic Assertions**: Multiple assertion types (text visibility, element existence, etc.)
- **Auto-generated Allure Reports**

## Architecture Overview

```
YAML Test Definitions
    ↓
test_ui.py (Step Dispatcher + Execution History Tracker)
    ↓
actions/ (Action Registry)
    ├── base.py → smart_click / smart_fill (with AI Fallback)
    ├── module.py / product.py / form.py ...
    ↓
┌─ Traditional Playwright Locators (role/text/locator)
│   Success → Continue
│   Failure ↓
└─ AI Self-Healing Engine (utils/ai_vision.py)
       ├── Screenshot + SOM Overlay
       ├── RAG Knowledge Base Query (utils/rag_knowledge.py)
       ├── Execution History Context Injection
       └── Gemini Vision Analysis → Target Element ID
              ↓
         Healed Action Continues
              ↓
         Allure Report + Screenshots/Recordings
```

## Directory Structure
```shell
├─config
│  └─config.yaml          # Configuration file
├─page
│  └─home.py              # UI layer base encapsulation
├─recordings              # Playwright codegen recorded scripts
├─test_case
│  └─UI
│    └─Test_Katana
│       ├─actions/         # Action Registry
│       │  ├─__init__.py   # Registry entry point
│       │  ├─base.py       # Base actions (smart_click, smart_fill, AI Fallback)
│       │  ├─module.py     # Module-related actions
│       │  ├─product.py    # Product-related actions
│       │  ├─form.py       # Form-related actions
│       │  └─layout.py     # Layout verification actions
│       ├─utils/           # [NEW v4.0] AI Self-Healing Toolkit
│       │  ├─ai_vision.py  # Gemini Vision AI Service (SOM + Multi API Key Rotation)
│       │  ├─rag_knowledge.py  # RAG Knowledge Base (FAISS + SentenceTransformers)
│       │  └─Knowledge_Base.md # Domain Knowledge Document
│       ├─conftest.py      # Pytest fixtures (multi-env + auth)
│       ├─test_ui.py       # Core test execution engine (with execution history)
│       └─Katana_curator_smoke_release.yaml  # Release environment test cases
├─tools                    # Utilities
│  ├─__init__.py           # Allure integration
│  └─get_cookie.py         # Cookie retrieval
├─requirements.txt         # Project dependencies
└─main.py                  # Main entry point
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file (or set environment variables) with Gemini API Keys:
```
GEMINI_API_KEYS=key1,key2,key3
```

### 3. Run Tests
```bash
# Run a specific test case (headed mode)
pytest test_case/UI/Test_Katana/test_ui.py -k "testT4777" --headed -v --env release --storage-state test_case/UI/Test_Katana/cookie_release.json

# Run all test cases and generate reports
python main.py
```

### 4. View Reports
Allure reports open automatically after test completion.

## V4.0 AI Self-Healing Architecture

### Core Flow
1. `smart_click` first tries traditional Playwright locators (role/name/text)
2. If timeout after 5s, triggers Legacy Fallback (15s)
3. If still failing, triggers **AI Self-Healing**:
   - Screenshots current page with SOM (Set-of-Mark) overlay
   - Queries RAG knowledge base for relevant business context
   - Sends screenshot + target description + execution history + RAG knowledge to Gemini Vision
   - AI returns diagnosis and target element ID
   - Clicks the AI-identified element

### RAG Knowledge Base
`utils/Knowledge_Base.md` stores business rules and UI navigation patterns including:
- System architecture and module overview
- Common navigation patterns (FAB button, event management, etc.)
- UI element characteristics and locator strategies
- Known automation pitfalls and solutions

### How to Extend the Knowledge Base
When AI self-healing makes incorrect decisions, add the corresponding business rules to `Knowledge_Base.md`. The AI will automatically retrieve and reference them next time.

## Multi-Environment Support
```bash
# Staging environment
pytest --env staging ...

# Release environment
pytest --env release ...
```
