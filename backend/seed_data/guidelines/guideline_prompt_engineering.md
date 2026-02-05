# Prompt Engineering Guidelines

## Overview
This document compiles prompt engineering best practices from leading AI organizations: OpenAI, Anthropic, and Google. Use these guidelines when crafting prompts for any language model.

---

## OpenAI Best Practices

### 1. Be Specific and Detailed
- Provide clear, specific, and descriptive instructions
- Include desired context, outcome, length, format, and style
- Avoid ambiguity to ensure accurate and relevant responses

### 2. Structure Your Prompts
- Place instructions at the beginning of the prompt
- Use separators like `###` or `"""` to distinguish instructions from context
- Break down complex tasks into smaller, manageable steps

### 3. Use Examples (Few-Shot)
- Demonstrate the desired output format with examples
- Include 2-3 examples for complex tasks

### 4. Be Positive
- Focus on what TO DO rather than what NOT to do
- Use affirmative instructions: "Use formal language" vs "Don't be informal"

### 5. Code Generation Tips
- Use "leading words" to guide patterns (e.g., start with `import` for Python)
- Specify the programming language and framework
- Include expected inputs and outputs

---

## Anthropic Best Practices

### 1. Be Explicit
- Never assume the AI reads minds
- Structure instructions with explicit requirements
- The more specific you are, the better the results

### 2. Start Simple, Then Iterate
- Begin with a minimal prompt and the best available model
- Add clear instructions based on initial performance
- Identify failure modes and address them

### 3. Give Time to Think
- Include phrases like "Think step by step" for complex reasoning
- Allow the model to process before generating final answers
- Use chain-of-thought prompting for multi-step problems

### 4. Use XML Tags for Structure
- Employ XML tags to specify sections: `<task>`, `<context>`, `<output>`
- Particularly useful for complex tasks or specifying output formats

### 5. Allow "I Don't Know"
- Explicitly tell the model to say if it's unsure
- Reduces hallucinations, especially in RAG applications
- Example: "If you don't know the answer, say 'I don't have enough information'"

### 6. Constraint Cascade
- For multi-step tasks, give one task at a time
- Wait for understanding, then add the next layer of constraints
- Build complexity incrementally

---

## Google Best Practices

### 1. Set Clear Goals
- Use action verbs (analyze, create, explain, summarize)
- Define desired length and format upfront
- Specify the target audience

### 2. Provide Context
- Include relevant facts, data, or references
- Define key terms and domain-specific vocabulary
- Share background information the model needs

### 3. Leverage Few-Shot Prompting
- Provide a few examples of desired input-output pairs
- Demonstrate the desired style, tone, or level of detail

### 4. Use Chain-of-Thought
- Encourage step-by-step reasoning
- Ask the model to explain its thought process
- Useful for math, logic, and complex analysis

### 5. Experiment with Output Formats
- Request structured outputs like JSON, CSV, or Markdown
- Easier for programmatic consumption
- Define schemas explicitly

### 6. Adapt to Model Updates
- Regularly test prompts against new model versions
- LLM behaviors can change between versions
- Document what works for which model version

---

## Universal Principles

| Principle | Description |
|-----------|-------------|
| **Clarity** | Be unambiguous and precise |
| **Specificity** | Include all necessary details |
| **Structure** | Organize prompts logically |
| **Examples** | Show, don't just tell |
| **Iteration** | Refine based on outputs |
| **Positive** | Say what to do, not what to avoid |
| **Format** | Specify output structure explicitly |

---

## When to Apply

Use these guidelines when:
- Creating system prompts for AI assistants
- Building RAG applications
- Designing agent-based systems
- Crafting task-specific prompts
- Training or fine-tuning models
