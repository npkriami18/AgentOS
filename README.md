# AgentOS
Event-driven runtime infrastructure for persistent multi-agent AI systems with scheduling, memory, observability, and governance.


AgentOS is an experimental operating system layer for autonomous AI agents.

It provides:
- task orchestration,
- persistent memory,
- agent scheduling,
- tool governance,
- observability,
- and multi-agent coordination.

The project focuses on treating AI agents as persistent software workers instead of stateless prompt executions.

# ARCHITECTURE

```text id="crn6ye"
                ┌─────────────────┐
                │     Frontend    │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │    FastAPI API  │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │   Agent Kernel  │
                │-----------------│
                │ Scheduler       │
                │ Runtime         │
                │ Event Bus       │
                │ Memory Manager  │
                │ Tool Manager    │
                │ Policy Engine   │
                │ Observability   │
                └────────┬────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
┌─────▼─────┐     ┌──────▼─────┐    ┌──────▼─────┐
│Researcher │     │ Planner    │    │ Writer     │
└───────────┘     └────────────┘    └────────────┘
```

---
