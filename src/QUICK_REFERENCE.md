# 🌤️ Atmosphere Project - Quick Reference

## Active Flow (LangGraph + LangChain Implementation)

```
┌─────────────┐
│  User Chat  │
│  (terminal) │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│ client.py                            │
│ • run_chat() function                │
│ • Input loop & config setup          │
└──────────┬───────────────────────────┘
           │
           ▼
    ┌──────────────────┐
    │  graph.invoke()  │
    └──────────┬───────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
  STATE:          LANGGRAPH WORKFLOW:
  • messages       • Setup StateGraph
  • question       • 2 Nodes: agent, tools
  • answer         • Router: should_call_tools
                   • Memory: SQLite checkpointer
    │                        │
    └────────────┬────────────┘
                 │
        ┌────────▼────────┐
        │ First Iteration │
        └────────┬────────┘
                 │
                 ▼
         ┌──────────────────────────┐
         │ graph_nodes.py           │
         │ → agent_node()           │
         │   (reasoning phase)      │
         │                          │
         │ llm.py → ChatOpenAI      │
         │ model: ai/gemma4         │
         │ (generates response +    │
         │  tool_calls if needed)   │
         └──────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────┐
           │ should_call_tools()│
           │                    │
           │ Decision Router:   │
           └─┬──────────────────┘
             │
       ┌─────┴─────┐
       │           │
    Has tools?  Has tools?
       │ YES      │ NO
       ▼           ▼
   ┌────────┐  ┌─────────┐
   │ TOOLS  │  │   END   │
   │ NODE   │  │  (exit) │
   └───┬────┘  └─────────┘
       │
       ▼
   ┌──────────────────────────┐
   │ graph_nodes.py           │
   │ → tools_node()           │
   │                          │
   │ Execute tool from:       │
   │ tools_lc.py              │
   │   • get_location()       │
   │   • get_forecast...()    │
   │   • get_alerts()         │
   └───────┬──────────────────┘
           │
           ▼
   ┌──────────────────────────────┐
   │ ToolNode.invoke()            │
   │ (LangGraph prebuilt)         │
   │                              │
   │ Calls HTTP endpoints:        │
   └───────┬──────────────────────┘
           │
           ▼
   ┌───────────────────────────────┐
   │ weather_mcp_server.py         │
   │ (FastAPI running on :8000)    │
   │                               │
   │ HTTP POST Endpoints:          │
   │  /api/get_location            │
   │  /api/get_forecast            │
   │  /api/get_alerts              │
   │                               │
   │ MCP Tools (on /mcp):          │
   │  get_location()               │
   │  get_forecast()               │
   │  get_alerts()                 │
   └────────┬──────────────────────┘
            │
            ▼
    ┌──────────────────────────┐
    │ External APIs            │
    │                          │
    │ 1. Nominatim Geocoding   │
    │    → Get coordinates     │
    │                          │
    │ 2. NWS API               │
    │    → Forecast data       │
    │                          │
    │ 3. NWS Alerts API        │
    │    → Active alerts       │
    └──────────┬───────────────┘
               │
               ▼
        ┌────────────────┐
        │ Tool Results   │
        │ (as string)    │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Add to messages │
        │ Loop back to    │
        │ agent_node()    │
        │ for synthesis   │
        └────────┬────────┘
                 │
    ┌────────────▼────────────┐
    │ Final LLM Call          │
    │ (synthesize answer)     │
    │ No more tools needed?   │
    │ → YES, return answer    │
    └────────────┬────────────┘
                 │
                 ▼
            ┌────────────┐
            │  Display   │
            │  Answer    │
            │   to User  │
            └────────────┘
```

---

## 📋 Active Files (After Cleanup)

### mcp_client/ (LLM Agent Layer)
```
client.py
├─ Entry point: run_chat()
├─ Interactive chat loop
├─ Uses: graph.py
└─ Lines: 47

graph.py
├─ LangGraph workflow definition
├─ StateGraph setup
├─ 2 nodes (agent, tools)
├─ SQLite memory
├─ Uses: graph_nodes.py, state.py
└─ Lines: 36

graph_nodes.py
├─ agent_node(): LLM reasoning
├─ tools_node(): Execute tools
├─ should_call_tools(): Router
├─ Uses: tools_lc.py, llm.py
└─ Lines: 58

tools_lc.py  ← ONLY TOOLS IMPLEMENTATION
├─ @tool get_location(location)
├─ @tool get_forecast_by_location(location)
├─ @tool get_alerts(state)
├─ HTTP helper: _post()
├─ Uses: weather_mcp_server.py endpoints
└─ Lines: 39

llm.py
├─ get_llm() function
├─ ChatOpenAI configuration
├─ Model: ai/gemma4
├─ Base URL: localhost:12434
└─ Lines: 15

state.py
├─ AgentState: TypedDict
├─ Fields: messages, question, answer
└─ Lines: 7

__init__.py
├─ Empty (package marker)
└─ Lines: 0
```

### mcp_server/ (Weather Data Layer)
```
weather_mcp_server.py
├─ FastAPI application
├─ 3 MCP Tools (async):
│   ├─ get_location()
│   ├─ get_forecast()
│   ├─ get_alerts()
├─ HTTP Endpoints (/api/*):
│   ├─ POST /api/get_location
│   ├─ POST /api/get_forecast
│   ├─ POST /api/get_alerts
├─ Health check & info endpoints
├─ External API calls:
│   ├─ Nominatim (geocoding)
│   ├─ NWS Points API
│   ├─ NWS Forecast API
│   ├─ NWS Alerts API
└─ Lines: 391

__init__.py
├─ Empty (package marker)
└─ Lines: 0
```

### test/
```
test_weather_mcp_server.py
├─ 6 test functions
├─ Tests: get_location, get_forecast, get_alerts
├─ Mock: httpx async calls
├─ Framework: pytest, pytest-asyncio
└─ Lines: 132

__init__.py
├─ Empty (package marker)
└─ Lines: 0
```

---

## 🗑️ Removed Files (After Cleanup)

```
❌ agent.py (128 lines)
   - Old DSPy ReAct agent
   - status: NOT IMPORTED BY ANYTHING
   - Removed: 2026-05-17 13:53 UTC

❌ tools.py (120 lines)
   - Old WeatherTools class (DSPy style)
   - Replaced by: tools_lc.py
   - Removed: 2026-05-17 13:53 UTC

❌ src.iml
   - JetBrains IDE config
   - Should use: .gitignore
   - Removed: 2026-05-17 13:53 UTC
```

---

## 📊 Project Statistics

| Aspect | Count |
|--------|-------|
| Active Python files | 7 |
| Total lines (code) | ~576 |
| Total lines (tests) | 132 |
| Empty __init__.py | 3 |
| Async functions | ~10 |
| HTTP endpoints | 7 |
| External APIs | 3 |
| Dependencies | 12 major packages |
| Removed duplicate code | 248 lines |

---

## 🔗 Module Imports Chain

```
client.py
└─→ graph.py
    └─→ graph_nodes.py
        ├─→ tools_lc.py
        │   └─→ httpx (HTTP calls)
        │       └─→ weather_mcp_server.py (endpoints)
        │           └─→ External APIs
        │
        └─→ llm.py
            └─→ ChatOpenAI (LLM)

test_weather_mcp_server.py
└─→ weather_mcp_server.py
    └─→ External APIs (mocked)
```

---

## 🎯 Running the Application

### Start MCP Server
```bash
cd /Users/hk/local-dev/github/atmosphere/src
python -m uvicorn mcp_server.weather_mcp_server:app --reload
# Server at: http://localhost:8000
# MCP at: http://localhost:8000/mcp
```

### Run Chat Agent
```bash
cd /Users/hk/local-dev/github/atmosphere/src
python -m mcp_client.client
# Interactive weather Q&A with LLM
```

### Run Tests
```bash
cd /Users/hk/local-dev/github/atmosphere/src
pytest test/ -v
```

---

**Created**: 2026-05-17  
**Cleanup**: Complete ✅  
**Status**: Production Ready 🚀

