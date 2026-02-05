"""
Document schemas for knowledge base items.
"""

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class SkillCard(BaseModel):
    """
    Schema for Skill Cards (Claude-like reusable instruction modules).
    Matches the required YAML structure from the spec.
    """
    
    id: str = Field(..., description="Unique skill identifier (skill_xxx)")
    name: str = Field(..., description="Human-readable skill name")
    description: str = Field(..., description="Brief description of the skill")
    when_to_use: str = Field(..., description="Conditions for applying this skill")
    inputs: list[str] = Field(default_factory=list, description="Required inputs")
    outputs: list[str] = Field(default_factory=list, description="Expected outputs")
    steps: list[str] = Field(default_factory=list, description="Step-by-step instructions")
    do_not: list[str] = Field(default_factory=list, description="Anti-patterns to avoid")
    security_notes: list[str] = Field(default_factory=list, description="Security considerations")
    example: str | None = Field(None, description="Usage example")
    
    def to_prompt_section(self) -> str:
        """Convert skill card to a prompt section format."""
        lines = [
            f"### Skill: {self.name}",
            f"**ID**: {self.id}",
            f"**Description**: {self.description}",
            f"**When to Use**: {self.when_to_use}",
        ]
        
        if self.inputs:
            lines.append(f"**Inputs**: {', '.join(self.inputs)}")
        
        if self.outputs:
            lines.append(f"**Outputs**: {', '.join(self.outputs)}")
        
        if self.steps:
            lines.append("**Steps**:")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"  {i}. {step}")
        
        if self.do_not:
            lines.append("**Do NOT**:")
            for item in self.do_not:
                lines.append(f"  - {item}")
        
        if self.security_notes:
            lines.append("**Security Notes**:")
            for note in self.security_notes:
                lines.append(f"  - {note}")
        
        return "\n".join(lines)


class PromptPattern(BaseModel):
    """Schema for Prompt Patterns (templates and examples)."""
    
    id: str = Field(..., description="Unique pattern identifier")
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="What this pattern is for")
    template: str = Field(..., description="The prompt template")
    variables: list[str] = Field(default_factory=list, description="Template variables")
    use_cases: list[str] = Field(default_factory=list, description="Applicable use cases")
    example_output: str | None = Field(None, description="Example of expected output")
    
    def to_prompt_section(self) -> str:
        """Convert pattern to a prompt section format."""
        lines = [
            f"### Pattern: {self.name}",
            f"**ID**: {self.id}",
            f"**Description**: {self.description}",
        ]
        
        if self.variables:
            lines.append(f"**Variables**: {', '.join(self.variables)}")
        
        if self.use_cases:
            lines.append("**Use Cases**:")
            for case in self.use_cases:
                lines.append(f"  - {case}")
        
        lines.append("**Template**:")
        lines.append(f"```\n{self.template}\n```")
        
        return "\n".join(lines)


class SecurityGuideline(BaseModel):
    """Schema for Secure Coding Guidelines."""
    
    id: str = Field(..., description="Unique guideline identifier")
    name: str = Field(..., description="Guideline name")
    category: str = Field(..., description="Category (e.g., injection, auth, secrets)")
    severity: str = Field(default="medium", description="Severity level")
    description: str = Field(..., description="What this guideline addresses")
    rules: list[str] = Field(default_factory=list, description="Specific rules to follow")
    examples_good: list[str] = Field(default_factory=list, description="Good practice examples")
    examples_bad: list[str] = Field(default_factory=list, description="Anti-pattern examples")
    references: list[str] = Field(default_factory=list, description="OWASP/CWE references")
    
    def to_prompt_section(self) -> str:
        """Convert guideline to a prompt section format."""
        lines = [
            f"### Security Guideline: {self.name}",
            f"**ID**: {self.id}",
            f"**Category**: {self.category}",
            f"**Severity**: {self.severity}",
            f"**Description**: {self.description}",
        ]
        
        if self.rules:
            lines.append("**Rules**:")
            for rule in self.rules:
                lines.append(f"  - {rule}")
        
        if self.examples_good:
            lines.append("**Good Practices**:")
            for example in self.examples_good:
                lines.append(f"  ✓ {example}")
        
        if self.examples_bad:
            lines.append("**Avoid**:")
            for example in self.examples_bad:
                lines.append(f"  ✗ {example}")
        
        return "\n".join(lines)


class DocumentMetadata(BaseModel):
    """Metadata stored with each document chunk."""
    
    doc_id: str = Field(..., description="Parent document ID")
    title: str = Field(..., description="Document title")
    doc_type: str = Field(..., description="Document type identifier")
    version: str = Field(default="1.0", description="Document version")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Creation timestamp"
    )
    chunk_index: int = Field(default=0, description="Chunk index within document")
    total_chunks: int = Field(default=1, description="Total chunks in document")
    section: str | None = Field(None, description="Section name if applicable")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for vector store metadata."""
        return self.model_dump()
