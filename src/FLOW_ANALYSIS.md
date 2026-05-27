# Atmosphere Project - Flow Analysis & Architecture

## 📊 System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                            │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  client.py (run_chat)          │
        │  - Interactive Chat Interface  │
        │  - Query handling              │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  graph.py (build_graph)        │
        │  - LangGraph Workflow          │
        │  - State Machine Setup         │
        │  - SQLite Memory Management    │
        └────────────┬───────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   ┌─────────────┐        ┌──────────────┐
   │ graph_nodes │        │  llm.py      │
   │             │        │              │
   │ - Nodes:    │        │ ChatOpenAI:  │
   │   • agent   │◄──────►│ Gemma4 Model │
   │   • tools   │        │ (Streaming)  │
   └──────┬──────┘        └──────────────┘
          │
          │ Tool calls
          ▼
   ┌──────────────────────┐
   │  tools_lc.py         │
   │                      │
   │ @tool decorators:    │
   │ • get_location       │
   │ • get_forecast_by... │
   │ • get_alerts         │
   └──────────┬───────────┘
              │ HTTP requests
              ▼
   ┌──────────────────────────────────────────┐
   │   weather_mcp_server.py (FastAPI)        │
   │                                          │
   │  ┌──────────────────────────────────┐   │
   │  │  MCP Tools (async):              │   │
   │  │  • get_location()  ┐             │   │
   │  │  • get_forecast()  ├─ FastAPI   │   │
   │  │  • get_alerts()    │  Endpoints │   │
   │  │                    ┘             │   │
   │  └──────────────────────────────────┘   │
   └──────────┬──────────┬──────────┬────────┘
              │          │          │
              ▼          ▼          ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │Nominatim│ │  NWS    │ │  NWS    │
        │Geocoding│ │  Points │ │ Alerts  │
        │  API    │ │ API     │ │ API     │
        └─────────┘ └─────────┘ └─────────┘
            │           │           │
            ▼           ▼           ▼
    ┌───────────────────────────────────────┐
    │   OpenStreetMap & NOAA APIs           │
    │   External Weather Data Sources       │
    └───────────────────────────────────────┘
```

---

## 📁 File Structure Analysis

### ✅ **Current Active Implementation** (LangGraph + LangChain)

```
mcp_client/
├── client.py           → Main entry point (chat interface)
├── graph.py            → LangGraph workflow definition
├── graph_nodes.py      → Agent & Tool nodes with routing logic
├── tools_lc.py         → LangChain @tool decorated functions
├── llm.py              → LLM configuration (ChatOpenAI)
├── state.py            → State type definitions
└── __init__.py         → Empty (package marker)

mcp_server/
├── weather_mcp_server.py → FastAPI + MCP server (3 endpoints)
└── __init__.py         → Empty (package marker)

test/
├── test_weather_mcp_server.py → Unit tests (pytest)
└── __init__.py         → Empty (package marker)
```

### ❌ **Deprecated/Duplicate Files**

| File | Issue | Reason | Action |
|------|-------|--------|--------|
| `agent.py` | Old DSPy agent (not used) | Replaced by LangGraph implementation | **DELETE** |
| `tools.py` | Duplicate of `tools_lc.py` | Same functionality in different style | **DELETE** |
| `src.iml` | JetBrains IDE config | Not needed in version control | **DELETE** |

---

## 🔄 Data Flow

### Query Processing Flow:

```
User Input
    ↓
client.py (Chat Loop)
    ↓
HumanMessage → graph.invoke()
    ↓
graph_nodes.py: agent_node()
    ↓
llm.py: LLM generates response + tool_calls
    ↓
Router: should_call_tools() → decision branch
    ├─ Has tool_calls? → YES
    │   ↓
    │   graph_nodes.py: tools_node()
    │   ↓
    │   tools_lc.py: Execute tool function
    │   ↓
    │   weather_mcp_server.py: HTTP POST to endpoints
    │   ↓
    │   External APIs (Nominatim, NWS)
    │   ↓
    │   Tool Result → Message History
    │   ↓
    │   Loop back to agent_node
    │
    └─ Has tool_calls? → NO
        ↓
        Return final_answer → Display to User
```

---

## 🛠️ Component Details

### **Tools Comparison**

#### tools.py (OLD - DSPy style)
```python
class WeatherTools:
    def get_location(location: str) → str
    def get_forecast(lat, lon) → str
    def get_forecast_by_location(location: str) → str
    def get_alerts(state: str) → str
```
- Used by: `agent.py` (DSPy ReAct)
- Status: **DEPRECATED**

#### tools_lc.py (CURRENT - LangChain style)
```python
@tool
def get_location(location: str) → str

@tool
def get_forecast_by_location(location: str) → str

@tool
def get_alerts(state: str) → str
```
- Used by: `graph_nodes.py` (LangGraph)
- Status: **ACTIVE**

---

## 📋 Files to Remove

### 1. **agent.py** (128 lines)
- **Why**: Old DSPy implementation using `dspy.ReAct()`
- **Replaced by**: `graph.py` + `graph_nodes.py` (LangGraph)
- **Impact**: None - not imported or used

### 2. **tools.py** (120 lines)
- **Why**: Duplicate of `tools_lc.py` with same functionality
- **Replaced by**: `tools_lc.py` (cleaner LangChain decorators)
- **Impact**: None - `tools_lc.py` is the active implementation

### 3. **src.iml** 
- **Why**: JetBrains IDE project file
- **Impact**: None - shouldn't be in version control
- **Keep**: Only in `.gitignore`

### 4. **.env**
- **Why**: Contains sensitive configuration
- **Keep in**: `.gitignore`
- **Note**: Should use `.env.example` instead

---

## ✨ Recommended Actions

### Remove These Files:
```bash
rm src/mcp_client/agent.py
rm src/mcp_client/tools.py
rm src/src.iml
```

### Add to .gitignore:
```
src.iml
.env
__pycache__/
.pytest_cache/
.venv/
```

### Clean up imports:
Since `agent.py` and `tools.py` will be removed, no other files depend on them.

---

## 📊 Project Statistics

### Before Cleanup:
- Python files: 10
- Empty init files: 3
- Test files: 1
- Total lines of code: ~796

### After Cleanup:
- Python files: 7 (removed: agent.py, tools.py)
- Empty init files: 3
- Test files: 1
- Total lines of code: ~576 (removed: 220 lines of duplicate code)

### Reduction: **27.6% reduction** in non-test code

---

## 🔗 Dependencies Between Modules

```
graph.py
  ├── imports: state.py
  └── imports: graph_nodes.py

graph_nodes.py
  ├── imports: tools_lc.py ✓ (ACTIVE)
  ├── imports: llm.py
  └── imports: langgraph.prebuilt.ToolNode

tools_lc.py ✓
  └── imports: langchain_core.tools.@tool

llm.py ✓
  └── imports: langchain_openai.ChatOpenAI

client.py
  ├── imports: graph.py
  └── imports: langchain_core.messages.HumanMessage

agent.py ✗ DEPRECATED
  ├── imports: tools.py ✗ DEPRECATED
  └── imports: dspy

tools.py ✗ DEPRECATED
  └── imports: httpx

state.py ✓
  └── imports: typing

weather_mcp_server.py ✓
  └── imports: mcp, fastapi, httpx, pydantic

test_weather_mcp_server.py ✓
  └── imports: weather_mcp_server.py

✓ = Active and used
✗ = Deprecated and unused
```

---

## 🎯 Summary

**Current Architecture**: LangGraph + LangChain + FastAPI MCP Server

**Key Points**:
1. Single active data flow: `client.py` → `graph.py` → `graph_nodes.py` → `tools_lc.py` → `weather_mcp_server.py`
2. No actual dependencies between agent.py or tools.py and active code
3. Safe cleanup: Remove agent.py and tools.py without affecting functionality
4. Code quality improvement: Consolidate duplicates, reduce ~220 lines of dead code


