"""
Quality gates for validating generated prompts.
Ensures prompts meet minimum requirements before being returned.
"""

import re
from typing import NamedTuple
from dataclasses import dataclass

from .prompt_builder import PromptSections


@dataclass
class QualityCheck:
    """Result of a single quality check."""

    name: str
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"


class QualityGateResult(NamedTuple):
    """Result of all quality gate checks."""

    passed: bool
    checks: list[QualityCheck]
    overall_score: float
    recommendations: list[str]


class QualityGates:
    """
    Validates generated prompts against quality requirements.
    Ensures prompts have necessary components for effective use.
    """

    # Minimum requirements
    MIN_SYSTEM_LENGTH = 100
    MIN_USER_SECTION_LENGTH = 20
    MIN_TOTAL_LENGTH = 200

    def __init__(self):
        """Initialize quality gates."""
        pass

    def evaluate(
        self,
        sections: PromptSections,
        is_coding_request: bool = False,
        is_agent_request: bool = False,
    ) -> QualityGateResult:
        """
        Evaluate a prompt against all quality gates.

        Args:
            sections: The prompt sections to evaluate
            is_coding_request: Whether this is a coding task
            is_agent_request: Whether this is an agent-building request

        Returns:
            QualityGateResult with all check results
        """
        checks = []

        # Run all checks
        checks.append(self._check_role_objective(sections))
        checks.append(self._check_constraints(sections))
        checks.append(self._check_io_requirements(sections))
        checks.append(self._check_security_section(sections, is_coding_request))
        checks.append(self._check_length_requirements(sections, is_agent_request))
        checks.append(self._check_structure(sections))

        # Run agent-specific checks
        if is_agent_request:
            checks.append(self._check_identity_section(sections))
            checks.append(self._check_data_schema(sections))
            checks.append(self._check_core_features(sections))

        # Calculate overall score
        passed_count = sum(1 for c in checks if c.passed)
        overall_score = passed_count / len(checks)

        # Determine if all critical checks passed
        critical_checks = [c for c in checks if c.severity == "error"]
        all_critical_passed = all(c.passed for c in critical_checks)

        # Generate recommendations for failed checks
        recommendations = []
        for check in checks:
            if not check.passed:
                recommendations.append(
                    f"[{check.severity.upper()}] {check.name}: {check.message}"
                )

        return QualityGateResult(
            passed=all_critical_passed and overall_score >= 0.7,
            checks=checks,
            overall_score=overall_score,
            recommendations=recommendations,
        )

    def _check_role_objective(self, sections: PromptSections) -> QualityCheck:
        """Check that the prompt has a clear role and objective."""
        has_role = bool(
            sections.system and len(sections.system) >= self.MIN_SYSTEM_LENGTH
        )
        has_objective = bool(
            sections.user_instructions
            and "request" in sections.user_instructions.lower()
        )

        if has_role and has_objective:
            return QualityCheck(
                name="Role & Objective",
                passed=True,
                message="Clear role and objective defined",
                severity="error",
            )
        elif has_role:
            return QualityCheck(
                name="Role & Objective",
                passed=False,
                message="Role defined but objective unclear",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="Role & Objective",
                passed=False,
                message="Missing clear role or objective",
                severity="error",
            )

    def _check_constraints(self, sections: PromptSections) -> QualityCheck:
        """Check that constraints are defined."""
        has_constraints = bool(sections.constraints and len(sections.constraints) > 50)

        # Look for constraint indicators
        constraint_patterns = [r"must", r"should", r"do not", r"avoid", r"require"]
        constraint_found = any(
            re.search(pattern, sections.constraints or "", re.IGNORECASE)
            for pattern in constraint_patterns
        )

        if has_constraints and constraint_found:
            return QualityCheck(
                name="Constraints",
                passed=True,
                message="Constraints clearly defined",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="Constraints",
                passed=False,
                message="Consider adding more specific constraints",
                severity="warning",
            )

    def _check_io_requirements(self, sections: PromptSections) -> QualityCheck:
        """Check that input/output requirements are specified."""
        output_section = sections.output_format or ""

        has_input_spec = "input" in (sections.user_instructions or "").lower()
        has_output_spec = bool(output_section and len(output_section) > 50)

        if has_output_spec:
            return QualityCheck(
                name="I/O Requirements",
                passed=True,
                message="Output format specified",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="I/O Requirements",
                passed=False,
                message="Output format should be more specific",
                severity="warning",
            )

    def _check_security_section(
        self, sections: PromptSections, is_coding_request: bool
    ) -> QualityCheck:
        """Check that security guardrails are present."""
        security = sections.security_guardrails or ""

        has_security = len(security) > 100
        has_safety_keywords = any(
            keyword in security.lower()
            for keyword in ["security", "safe", "validation", "sanitize", "protect"]
        )

        if is_coding_request:
            # Stricter requirements for coding
            coding_keywords = ["injection", "xss", "authentication", "authorization"]
            has_coding_security = any(
                keyword in security.lower() for keyword in coding_keywords
            )

            if has_security and has_coding_security:
                return QualityCheck(
                    name="Security Guardrails",
                    passed=True,
                    message="Security guidelines include coding-specific rules",
                    severity="error",
                )
            elif has_security:
                return QualityCheck(
                    name="Security Guardrails",
                    passed=True,
                    message="Basic security present; consider adding coding-specific rules",
                    severity="warning",
                )
            else:
                return QualityCheck(
                    name="Security Guardrails",
                    passed=False,
                    message="Coding request requires security guardrails",
                    severity="error",
                )
        else:
            if has_security and has_safety_keywords:
                return QualityCheck(
                    name="Security Guardrails",
                    passed=True,
                    message="Security guardrails present",
                    severity="warning",
                )
            else:
                return QualityCheck(
                    name="Security Guardrails",
                    passed=False,
                    message="Consider adding security guardrails",
                    severity="warning",
                )

    def _check_length_requirements(
        self, sections: PromptSections, is_agent_request: bool = False
    ) -> QualityCheck:
        """Check that the prompt meets minimum length requirements."""
        total_length = sum(
            len(s or "")
            for s in [
                sections.system,
                sections.context,
                sections.skills,
                sections.security_guardrails,
                sections.user_instructions,
                sections.constraints,
                sections.output_format,
                sections.identity,
                sections.core_features,
                sections.data_schema,
                sections.default_roles,
            ]
        )

        # Use higher minimum for agent prompts
        min_length = 1000 if is_agent_request else self.MIN_TOTAL_LENGTH

        if total_length >= min_length:
            return QualityCheck(
                name="Prompt Length",
                passed=True,
                message=f"Prompt length adequate ({total_length} chars)",
                severity="info",
            )
        else:
            return QualityCheck(
                name="Prompt Length",
                passed=False,
                message=f"Prompt may be too short ({total_length} chars, min: {min_length})",
                severity="warning",
            )

    def _check_structure(self, sections: PromptSections) -> QualityCheck:
        """Check that the prompt has good structure."""
        # Count non-empty sections
        non_empty = sum(
            1
            for s in [
                sections.system,
                sections.context,
                sections.skills,
                sections.security_guardrails,
                sections.user_instructions,
                sections.constraints,
                sections.output_format,
            ]
            if s and len(s.strip()) > 0
        )

        if non_empty >= 5:
            return QualityCheck(
                name="Structure",
                passed=True,
                message=f"Well-structured with {non_empty} sections",
                severity="info",
            )
        elif non_empty >= 3:
            return QualityCheck(
                name="Structure",
                passed=True,
                message=f"Adequate structure with {non_empty} sections",
                severity="info",
            )
        else:
            return QualityCheck(
                name="Structure",
                passed=False,
                message=f"Only {non_empty} sections - consider adding more structure",
                severity="warning",
            )

    def enhance_prompt(
        self, sections: PromptSections, result: QualityGateResult
    ) -> PromptSections:
        """
        Attempt to enhance a prompt based on quality gate results.

        Args:
            sections: Original prompt sections
            result: Quality gate evaluation result

        Returns:
            Enhanced prompt sections
        """
        # For now, just return original - could add automatic enhancement
        return sections

    # ========== Agent-Specific Quality Checks ==========

    def _check_identity_section(self, sections: PromptSections) -> QualityCheck:
        """Check that agent prompts have a clear identity section."""
        identity = getattr(sections, "identity", "") or ""

        has_identity = len(identity) >= 50
        has_name = any(
            keyword in identity.lower()
            for keyword in ["you are", "agent", "assistant", "purpose", "goal"]
        )

        if has_identity and has_name:
            return QualityCheck(
                name="Agent Identity",
                passed=True,
                message="Clear agent identity defined",
                severity="error",
            )
        elif has_identity:
            return QualityCheck(
                name="Agent Identity",
                passed=False,
                message="Identity section present but may lack clear purpose",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="Agent Identity",
                passed=False,
                message="Agent prompts must have a clear identity section",
                severity="error",
            )

    def _check_data_schema(self, sections: PromptSections) -> QualityCheck:
        """Check that agent prompts include a data schema."""
        data_schema = getattr(sections, "data_schema", "") or ""

        has_schema = len(data_schema) >= 100
        has_json = "json" in data_schema.lower() or "{" in data_schema

        if has_schema and has_json:
            return QualityCheck(
                name="Data Schema",
                passed=True,
                message="Data schema with JSON structure defined",
                severity="warning",
            )
        elif has_schema:
            return QualityCheck(
                name="Data Schema",
                passed=False,
                message="Data schema present but may lack JSON structure",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="Data Schema",
                passed=False,
                message="Agent prompts should include a data schema for structured output",
                severity="warning",
            )

    def _check_core_features(self, sections: PromptSections) -> QualityCheck:
        """Check that agent prompts have core features defined."""
        core_features = getattr(sections, "core_features", "") or ""

        has_features = len(core_features) >= 100
        # Check for numbered features
        import re

        numbered_pattern = re.compile(r"\d+[.)]|\#\#\s*\d+")
        has_numbered = bool(numbered_pattern.search(core_features))

        if has_features and has_numbered:
            return QualityCheck(
                name="Core Features",
                passed=True,
                message="Core features clearly enumerated",
                severity="warning",
            )
        elif has_features:
            return QualityCheck(
                name="Core Features",
                passed=False,
                message="Core features present but should be numbered",
                severity="warning",
            )
        else:
            return QualityCheck(
                name="Core Features",
                passed=False,
                message="Agent prompts should have numbered core features",
                severity="warning",
            )
