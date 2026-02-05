# Pattern: Multi-Agent System Design

## Context
Use this pattern when designing AI systems with multiple specialized agents that need to coordinate, delegate tasks, and collaborate on complex workflows.

---

## Agent Design Patterns

### 1. ReAct (Reason and Act)
The fundamental agent pattern where the LLM cycles through:
1. **Think**: Analyze what to do
2. **Decide**: Choose an action
3. **Execute**: Perform the action
4. **Observe**: Review the result
5. **Repeat**: Continue until task complete

### 2. Orchestrator-Worker Pattern
A central orchestrator assigns tasks to worker agents:
- Orchestrator: Manages workflow, tracks progress, handles escalation
- Workers: Execute specific tasks based on their specialization
- Best for: Task delegation with centralized control

### 3. Hierarchical Agent Pattern
Agents organized in layers:
- Higher-level agents oversee and delegate
- Lower-level agents execute specialized tasks
- Best for: Complex problems that can be decomposed

### 4. Blackboard Pattern
Shared knowledge base that agents read from and write to:
- Asynchronous collaboration without direct communication
- Best for: Problems requiring incremental solution building

### 5. Market-Based Pattern
Agents negotiate and compete:
- Decentralized task allocation
- Best for: Resource optimization and load balancing

### 6. Swarm Pattern
Multiple agents collaboratively refine solutions:
- All-to-all communication
- Iterative refinement
- Best for: Complex problems requiring diverse perspectives

---

## Best Practices

### Define Clear Roles
- Each agent should have a specific, well-defined role
- Avoid overlapping responsibilities
- Document each agent's inputs, outputs, and capabilities

### Ensure Modularity
- Agents should work independently
- Connect only when necessary
- Allow individual evolution without rebuilding the system

### Manage Shared Context
- Use shared memory for task status and business rules
- Implement local memory to prevent token overload
- Define clear data schemas for agent communication

### Implement Effective Orchestration
- Central coordinator for task assignment and tracking
- Auto-discovery and service registration
- Clear escalation paths for failures

### Human-in-the-Loop (HITL)
- Allow human oversight for critical decisions
- Escalate unclear or high-risk decisions
- Use human feedback for continuous improvement

### Observability
- Comprehensive monitoring and logging from day one
- Action logs and decision traces
- Alerts for anomalous behavior

---

## Communication Patterns

### Synchronous
```
Agent A --request--> Agent B
Agent A <--response-- Agent B
```

### Asynchronous (Event-Driven)
```
Agent A --publishes--> Event Bus
Event Bus --notifies--> Agent B, Agent C
```

### Handoff
```
Agent A --task+context--> Agent B
Agent B --result--> Agent A
```

---

## Default Agent Roles

| Role | Responsibilities |
|------|-----------------|
| **ResearchAgent** | Requirements gathering, constraint discovery, research |
| **DesignAgent** | Architecture, specifications, interface definitions |
| **BuildAgent** | Implementation, scaffolding, code generation |
| **QAAgent** | Test planning, validation, acceptance testing |
| **OpsAgent** | Deployment, automation, monitoring setup |
| **WriterAgent** | Documentation, handoff notes, user guides |
| **OrchestratorAgent** | Task assignment, progress tracking, escalation |

---

## Anti-Patterns to Avoid

1. **God Agent**: One agent doing too much
2. **Tight Coupling**: Agents depending on internal details of others
3. **Infinite Loops**: Agents calling each other without termination
4. **Context Explosion**: Passing too much irrelevant data
5. **Silent Failures**: Agents failing without proper logging

---

## When to Use Multi-Agent

**Good Candidates**:
- Complex workflows with distinct phases
- Tasks requiring different specialized skills
- Parallel execution opportunities
- Need for human oversight at specific points

**Better as Single Agent**:
- Simple, linear tasks
- When latency is critical
- Low complexity requirements
