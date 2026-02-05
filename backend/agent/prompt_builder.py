"""
Prompt builder for synthesizing final prompts from retrieved content.
"""

from typing import Any
from dataclasses import dataclass

from schemas import TargetModel, PromptStyle
from .retriever import RetrievedDocument


@dataclass
class PromptSections:
    """Structured sections of a generated prompt."""

    system: str
    context: str
    skills: str
    security_guardrails: str
    user_instructions: str
    constraints: str
    output_format: str
    # New fields for enhanced agent prompts
    identity: str = ""
    core_features: str = ""
    data_schema: str = ""
    default_roles: str = ""


class PromptBuilder:
    """
    Builds structured prompts from retrieved content.
    Supports different target models and styles.
    """

    # Model-specific system prefixes
    MODEL_PREFIXES = {
        TargetModel.GEMINI: "You are a helpful AI assistant powered by Google Gemini.",
        TargetModel.CLAUDE: "You are Claude, an AI assistant made by Anthropic.",
        TargetModel.GPT: "You are ChatGPT, a helpful AI assistant by OpenAI.",
        TargetModel.GENERIC: "You are a helpful AI assistant.",
    }

    # Style-specific instructions
    STYLE_INSTRUCTIONS = {
        PromptStyle.CONCISE: (
            "Be concise and direct. Provide the essential information without "
            "unnecessary elaboration. Use bullet points where appropriate."
        ),
        PromptStyle.DETAILED: (
            "Provide comprehensive, detailed responses. Include explanations, "
            "examples, and relevant context. Structure your response clearly."
        ),
        PromptStyle.STEP_BY_STEP: (
            "Break down your response into clear, numbered steps. Explain each "
            "step thoroughly before moving to the next. Summarize at the end."
        ),
    }

    def __init__(self):
        """Initialize the prompt builder."""
        pass

    def build_prompt(
        self,
        user_request: str,
        target_model: TargetModel,
        prompt_style: PromptStyle,
        patterns: list[RetrievedDocument],
        skills: list[RetrievedDocument],
        guidelines: list[RetrievedDocument],
        constraints: list[str] | None = None,
        context: str | None = None,
        is_coding_request: bool = False,
    ) -> PromptSections:
        """
        Build a structured prompt from retrieved content.

        Args:
            user_request: The user's original request
            target_model: Target LLM
            prompt_style: Desired output style
            patterns: Retrieved prompt patterns
            skills: Retrieved skill cards
            guidelines: Retrieved security guidelines
            constraints: Additional constraints from user
            context: Optional project context
            is_coding_request: Whether this is a coding task

        Returns:
            PromptSections with all prompt components
        """
        # Build system section
        system = self._build_system_section(target_model, prompt_style)

        # Build context section
        context_section = self._build_context_section(context, patterns, user_request)

        # Build skills section
        skills_section = self._build_skills_section(skills)

        # Build security guardrails section
        security_section = self._build_security_section(guidelines, is_coding_request)

        # Build user instructions section
        user_section = self._build_user_section(user_request)

        # Build constraints section
        constraints_section = self._build_constraints_section(constraints, prompt_style)

        # Build output format section
        output_section = self._build_output_section(prompt_style)

        # Check if this is an agent-building request
        is_agent_request = self._is_agent_request(user_request)

        # Build enhanced sections for agent requests
        identity_section = ""
        core_features_section = ""
        data_schema_section = ""
        default_roles_section = ""

        if is_agent_request:
            identity_section = self._build_identity_section(user_request, patterns)
            core_features_section = self._build_core_features_section(
                user_request, patterns
            )
            data_schema_section = self._build_data_schema_section(patterns)
            default_roles_section = self._build_default_roles_section(patterns)

        return PromptSections(
            system=system,
            context=context_section,
            skills=skills_section,
            security_guardrails=security_section,
            user_instructions=user_section,
            constraints=constraints_section,
            output_format=output_section,
            identity=identity_section,
            core_features=core_features_section,
            data_schema=data_schema_section,
            default_roles=default_roles_section,
        )

    def _build_system_section(
        self, target_model: TargetModel, prompt_style: PromptStyle
    ) -> str:
        """Build the system/role section."""
        prefix = self.MODEL_PREFIXES.get(
            target_model, self.MODEL_PREFIXES[TargetModel.GENERIC]
        )
        style = self.STYLE_INSTRUCTIONS.get(prompt_style, "")

        return f"""# System Role

{prefix}

## Response Style

{style}

## Core Principles

1. **Accuracy**: Provide correct, verified information only
2. **Safety**: Never suggest harmful, unethical, or dangerous actions
3. **Clarity**: Structure responses for easy understanding
4. **Honesty**: Acknowledge limitations and uncertainties
"""

    def _build_context_section(
        self, context: str | None, patterns: list[RetrievedDocument], user_request: str
    ) -> str:
        """Build the context section with patterns and project info."""
        sections = ["# Context and Background"]

        if context:
            sections.append(
                f"""
## Project Context

{context}
"""
            )

        if patterns:
            sections.append("\n## Relevant Patterns and Templates\n")
            for pattern in patterns[:3]:  # Limit to top 3
                sections.append(
                    f"""
### {pattern.title}

{pattern.content}
"""
                )

        return "\n".join(sections)

    def _build_skills_section(self, skills: list[RetrievedDocument]) -> str:
        """Build the skills section with selected skill cards."""
        if not skills:
            return ""

        sections = ["# Selected Skills\n"]
        sections.append(
            "The following skills are relevant to this task. Apply them as appropriate:\n"
        )

        for skill in skills:
            sections.append(
                f"""
## {skill.title}

{skill.content}
"""
            )

        return "\n".join(sections)

    def _build_security_section(
        self, guidelines: list[RetrievedDocument], is_coding_request: bool
    ) -> str:
        """Build the security guardrails section."""
        sections = ["# Security Guardrails\n"]

        # Always include base security requirements
        sections.append(
            """
## Mandatory Security Requirements

1. **No Secrets**: Never output API keys, tokens, passwords, or credentials
2. **Input Validation**: Always validate and sanitize user inputs
3. **Safe Defaults**: Use secure defaults for all configurations
4. **Error Handling**: Handle errors gracefully without exposing internals
"""
        )

        if is_coding_request:
            sections.append(
                """
## Secure Coding Requirements

1. **Parameterized Queries**: Use parameterized queries to prevent SQL injection
2. **Output Encoding**: Encode output to prevent XSS
3. **Authentication**: Use strong, proven authentication mechanisms
4. **Authorization**: Implement proper access controls
5. **Cryptography**: Use established libraries, never roll your own
6. **Logging**: Log security events but never log sensitive data
"""
            )

        if guidelines:
            sections.append("\n## Applicable Security Guidelines\n")
            for guideline in guidelines:
                sections.append(
                    f"""
### {guideline.title}

{guideline.content}
"""
                )

        return "\n".join(sections)

    def _build_user_section(self, user_request: str) -> str:
        """Build the user instructions section."""
        return f"""# User Request

{user_request}
"""

    def _build_constraints_section(
        self, constraints: list[str] | None, prompt_style: PromptStyle
    ) -> str:
        """Build the constraints section."""
        sections = ["# Constraints and Requirements\n"]

        # Add style-based constraints
        if prompt_style == PromptStyle.CONCISE:
            sections.append(
                "- Keep response under 500 words unless more detail is essential"
            )
            sections.append("- Prioritize actionable information over explanations")
        elif prompt_style == PromptStyle.STEP_BY_STEP:
            sections.append("- Number each step clearly")
            sections.append("- Explain the 'why' for each step")
            sections.append("- Include a summary at the end")

        # Add user-provided constraints
        if constraints:
            sections.append("\n## User-Specified Constraints\n")
            for constraint in constraints:
                sections.append(f"- {constraint}")

        return "\n".join(sections)

    def _build_output_section(self, prompt_style: PromptStyle) -> str:
        """Build the output format section."""
        return """# Output Format

Structure your response as follows:

1. **Summary**: Brief overview of your response
2. **Main Content**: Detailed response to the request
3. **Assumptions**: List any assumptions made
4. **Next Steps**: Suggested follow-up actions (if applicable)
"""

    def assemble_plain_prompt(self, sections: PromptSections) -> str:
        """Assemble sections into a plain text prompt."""
        parts = [
            sections.system,
            sections.identity if sections.identity else None,
            sections.context,
            sections.core_features if sections.core_features else None,
            sections.skills if sections.skills else None,
            sections.security_guardrails,
            sections.user_instructions,
            sections.constraints,
            sections.output_format,
            sections.data_schema if sections.data_schema else None,
            sections.default_roles if sections.default_roles else None,
        ]

        return "\n\n---\n\n".join(p for p in parts if p)

    def assemble_json_prompt(self, sections: PromptSections) -> dict[str, Any]:
        """Assemble sections into a JSON structure."""
        result = {
            "system": sections.system,
            "context": sections.context,
            "skills": sections.skills if sections.skills else None,
            "security_guardrails": sections.security_guardrails,
            "user_request": sections.user_instructions,
            "constraints": sections.constraints,
            "output_format": sections.output_format,
        }
        # Include enhanced agent sections if populated
        if sections.identity:
            result["identity"] = sections.identity
        if sections.core_features:
            result["core_features"] = sections.core_features
        if sections.data_schema:
            result["data_schema"] = sections.data_schema
        if sections.default_roles:
            result["default_roles"] = sections.default_roles
        return result

    # ========== Agent Request Detection & Enhanced Builders ==========

    # Keywords that indicate an agent-building request
    AGENT_KEYWORDS = [
        "agent",
        "assistant",
        "bot",
        "ai system",
        "automated",
        "planner",
        "orchestrator",
        "subagent",
        "multi-agent",
        "agentic",
        "autonomous",
        "workflow engine",
    ]

    def _is_agent_request(self, user_request: str) -> bool:
        """Determine if the request is about building an AI agent/system."""
        request_lower = user_request.lower()
        return any(keyword in request_lower for keyword in self.AGENT_KEYWORDS)

    def _build_identity_section(
        self, user_request: str, patterns: list[RetrievedDocument]
    ) -> str:
        """Build the identity/purpose section for an agent prompt."""
        # Extract potential agent name from request
        agent_name = self._extract_agent_name(user_request)

        return f"""# Identity & Purpose

You are **{agent_name}**.

## Primary Goal
{self._extract_primary_goal(user_request)}

## User Value
- Transform vague requests into actionable, structured plans
- Provide execution-ready outputs that other systems can consume
- Reduce ambiguity through explicit assumptions and clarifications
"""

    def _build_core_features_section(
        self, user_request: str, patterns: list[RetrievedDocument]
    ) -> str:
        """Build the core features section for an agent prompt."""
        # Extract features from patterns if available
        pattern_features = self._extract_features_from_patterns(patterns)

        base_features = """# Core Features

## 1) Intake & Clarification
- Ask at most 3 clarifying questions ONLY if required to avoid a wrong output
- Otherwise, infer reasonable assumptions and list them explicitly
- Capture: goal, success criteria, constraints, timeline

## 2) Structured Decomposition
- Break down the goal into logical components or phases
- Identify dependencies and ordering constraints
- Mark items as parallelizable yes/no

## 3) Output Generation
- Produce structured output in the required format
- Include validation checklists for each major component
- Provide clear acceptance criteria
"""
        if pattern_features:
            base_features += (
                f"\n## Additional Features from Patterns\n{pattern_features}"
            )

        return base_features

    def _build_data_schema_section(self, patterns: list[RetrievedDocument]) -> str:
        """Build the data schema section with JSON template."""
        return """# Data Structure (JSON)

Return valid JSON in a code block with this structure:

```json
{
  "goal": "string - the interpreted goal",
  "assumptions": ["array of assumptions made"],
  "components": [
    {
      "id": "C1",
      "title": "string",
      "description": "string",
      "deliverable": "string - concrete output",
      "effort": "S|M|L",
      "dependencies": ["array of component IDs this depends on"],
      "parallelizable": true
    }
  ],
  "execution_order": ["C1", "C2", "C3"],
  "risks": [
    { "description": "string", "mitigation": "string", "severity": "low|med|high" }
  ]
}
```
"""

    def _build_default_roles_section(self, patterns: list[RetrievedDocument]) -> str:
        """Build the default roles section for multi-agent systems."""
        return """# Default Roles

If the task involves delegation or multi-agent execution, use these roles:

- **ResearchAgent**: Requirements gathering, constraint discovery, background research
- **DesignAgent**: Architecture, specifications, interface definitions
- **BuildAgent**: Implementation, scaffolding, code generation
- **QAAgent**: Test planning, validation, acceptance testing
- **OpsAgent**: Deployment, automation, monitoring setup
- **WriterAgent**: Documentation, handoff notes, user guides

Assign each component to the most appropriate role.
"""

    def _extract_agent_name(self, user_request: str) -> str:
        """Extract or generate an agent name from the request."""
        import re

        # Look for explicit name patterns
        patterns = [
            r'called?\s+"?([A-Za-z]+(?:\s+[A-Za-z]+)*)"?',
            r'named?\s+"?([A-Za-z]+(?:\s+[A-Za-z]+)*)"?',
            r"(\w+(?:\s+\w+)*)\s+agent",
            r"(\w+(?:\s+\w+)*)\s+planner",
            r"(\w+(?:\s+\w+)*)\s+assistant",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 2:
                    return f"{name} Agent"

        # Generate based on keywords
        if "plan" in user_request.lower():
            return "Task Planner Agent"
        elif "code" in user_request.lower():
            return "Code Generation Agent"
        elif "review" in user_request.lower():
            return "Review Agent"

        return "AI Assistant Agent"

    def _extract_primary_goal(self, user_request: str) -> str:
        """Extract the primary goal from the user request."""
        # Clean up the request to form a goal statement
        goal = user_request.strip()

        # Remove common prefixes
        prefixes = ["i want to", "i need to", "create", "build", "make", "help me"]
        goal_lower = goal.lower()
        for prefix in prefixes:
            if goal_lower.startswith(prefix):
                goal = goal[len(prefix) :].strip()
                break

        return (
            goal.capitalize() if goal else "Accomplish the user's objective effectively"
        )

    def _extract_features_from_patterns(self, patterns: list[RetrievedDocument]) -> str:
        """Extract feature descriptions from retrieved patterns."""
        if not patterns:
            return ""

        features = []
        for pattern in patterns[:2]:  # Limit to top 2
            # Extract any numbered features from pattern content
            import re

            numbered_items = re.findall(
                r"(?:^|\n)\s*\d+[.)]\s*\*?\*?([^*\n]+)", pattern.content
            )
            if numbered_items:
                features.extend(numbered_items[:3])  # Max 3 per pattern

        if features:
            return "\n".join(f"- {f.strip()}" for f in features)
        return ""
