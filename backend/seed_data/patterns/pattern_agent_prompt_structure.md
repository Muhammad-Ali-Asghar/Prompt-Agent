# Prompt Pattern: Agent System Prompt Structure

## Context
Use this pattern when the user wants to build an AI agent, assistant, or automated system. This pattern teaches you how to generate **detailed, structured, production-ready system prompts**.

## Required Output Sections

When generating a prompt for an AI agent, you MUST include ALL of the following sections in this order:

### 1. IDENTITY & PRIMARY PURPOSE
- Give the agent a clear name (e.g., "TaskGraph Planner", "CodeReview Agent")
- State its primary goal in one sentence
- Describe what value it provides to the user

### 2. CORE FEATURES (numbered list)
- List 4-6 major capabilities
- Each feature should have:
  - A descriptive title
  - 2-3 bullet points explaining what it does
  - Any sub-features if applicable

### 3. OUTPUT STRUCTURE REQUIREMENTS
- Define the exact sections the agent must produce
- Use letters (A, B, C) or numbers to order them
- Be specific about what each section must contain

### 4. DATA SCHEMA (JSON)
- Provide a complete JSON schema for structured output
- Include all fields with types and valid values
- Use comments to explain complex fields
- Example:
```json
{
  "goal": "string",
  "tasks": [
    {
      "id": "string",
      "title": "string",
      "effort": "S|M|L",
      "parallelizable": true
    }
  ]
}
```

### 5. VISUAL REPRESENTATION (Mermaid)
- Include a Mermaid diagram if the output involves:
  - Workflows or processes
  - Dependencies or relationships
  - Hierarchies or trees
- Use `graph TD` or `flowchart LR` syntax

### 6. TONE & STYLE GUIDELINES
- Be concise, practical, and execution-focused
- Prefer parallel work when safe
- Make tasks small enough to complete independently
- Never output vague instructions; every task must have a concrete deliverable

### 7. DEFAULT ROLES (if applicable)
- Define specialized roles/agents if the system involves delegation
- For each role, specify:
  - Role name
  - Responsibilities
  - When to use

## Example Output Structure

```
# [Agent Name]

## Identity & Purpose
You are [Agent Name]. Your goal is to [primary purpose].

## Primary User Value
- [Value 1]
- [Value 2]

## Core Features

### 1) [Feature Name]
- [Detail 1]
- [Detail 2]

### 2) [Feature Name]
- [Detail 1]
- [Detail 2]

## Output Requirements
Always produce the following sections:
A) [Section 1]
B) [Section 2]
C) [Section 3]

## Data Structure (JSON)
[JSON schema block]

## Visual Representation
[Mermaid diagram block]

## Tone & Style
- [Guideline 1]
- [Guideline 2]

## Default Roles
- **[Role 1]**: [Responsibility]
- **[Role 2]**: [Responsibility]
```

## When NOT to Use This Pattern
- Simple one-off tasks (e.g., "summarize this text")
- Non-agent requests (e.g., "explain this concept")
- Requests that don't involve building a reusable system
