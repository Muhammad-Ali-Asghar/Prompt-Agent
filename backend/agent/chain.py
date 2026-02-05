"""
LangChain chain for the RAG prompt generation pipeline.
Orchestrates the full flow from request to final prompt.
"""

import logging
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import get_settings
from schemas import (
    GeneratePromptRequest,
    GeneratePromptResponse,
    Citation,
    SelectedSkill,
    SafetyCheck,
    OutputFormat,
)
from security import (
    detect_injection,
    validate_user_request,
    validate_constraints,
    validate_context,
    redact_secrets,
)
from vectorstore import ChromaVectorStore
from .retriever import MultiSourceRetriever, RetrievedDocument
from .prompt_builder import PromptBuilder
from .quality_gates import QualityGates

logger = logging.getLogger(__name__)


class PromptGenerationChain:
    """
    LangChain-based pipeline for generating high-quality prompts.

    Flow:
    1. Parse and validate request
    2. Classify intent
    3. Retrieve relevant documents
    4. Filter for injection attempts
    5. Build prompt sections
    6. Run quality gates
    7. Return structured response
    """

    # Keywords that indicate a coding-related request
    CODING_KEYWORDS = [
        "code",
        "program",
        "function",
        "class",
        "api",
        "script",
        "implement",
        "develop",
        "build",
        "create",
        "write",
        "python",
        "javascript",
        "java",
        "typescript",
        "sql",
        "database",
        "backend",
        "frontend",
        "server",
        "client",
    ]

    def __init__(self, vector_store: ChromaVectorStore):
        """
        Initialize the prompt generation chain.

        Args:
            vector_store: Vector store for retrieval
        """
        self.settings = get_settings()
        self.vector_store = vector_store
        self.retriever = MultiSourceRetriever(vector_store)
        self.prompt_builder = PromptBuilder()
        self.quality_gates = QualityGates()

        # Initialize LLM for intent classification
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=0.3,
        )

        # Intent classification prompt
        self.intent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an intent classifier for a prompt generation system.
Analyze the user request and classify it into one of these categories:
- code_generation: Writing new code
- code_review: Reviewing or improving existing code
- documentation: Writing docs, README, comments
- debugging: Fixing bugs or errors
- security: Security-related tasks
- design: System design, architecture
- agent_building: Creating an AI agent, assistant, or automated system
- general: Other requests

Also identify:
- domain: The technical domain (web, data, ml, devops, ai, etc.)
- complexity: low/medium/high
- is_agent: true if this is about building an AI agent/system, false otherwise

Respond in format:
intent: <intent>
domain: <domain>
complexity: <complexity>
is_agent: <true/false>
""",
                ),
                ("user", "{request}"),
            ]
        )

        self.intent_chain = self.intent_prompt | self.llm | StrOutputParser()

        # Agent prompt synthesis prompt (for agent-building requests)
        self.synthesis_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert prompt engineer specializing in AI agent design.

Given a user request and retrieved knowledge, synthesize a COMPLETE, PRODUCTION-READY system prompt for the requested agent.

Your output MUST include ALL of these sections:

1. **IDENTITY & PURPOSE**: Clear agent name, primary goal, user value
2. **CORE FEATURES**: 4-6 numbered capabilities with bullet point details
3. **OUTPUT REQUIREMENTS**: Exact sections the agent must produce (lettered A, B, C...)
4. **DATA SCHEMA**: Complete JSON schema for structured output
5. **VISUAL REPRESENTATION**: Mermaid diagram if relevant (flowchart, graph TD)
6. **TONE & STYLE**: Concise guidelines for response style
7. **DEFAULT ROLES**: If multi-agent, define subagent roles

CRITICAL RULES:
- Be execution-focused and practical
- Every task must have a concrete deliverable (no vague instructions)
- Include acceptance criteria for major outputs
- Prefer parallel execution when safe
- Make outputs machine-parseable where possible

Use the retrieved patterns and skills as inspiration, but produce a COMPLETE prompt that stands alone.
""",
                ),
                (
                    "user",
                    """User Request: {user_request}

Retrieved Context:
{context}

Generate the complete agent system prompt:""",
                ),
            ]
        )

        self.synthesis_chain = self.synthesis_prompt | self.llm | StrOutputParser()

    async def generate(self, request: GeneratePromptRequest) -> GeneratePromptResponse:
        """
        Generate a high-quality prompt from the request.

        Args:
            request: The prompt generation request

        Returns:
            GeneratePromptResponse with the generated prompt
        """
        safety_checks = []
        assumptions = []
        warnings = []

        # Step 1: Validate and sanitize input
        validation = validate_user_request(request.user_request)
        if not validation.is_valid:
            raise ValueError(f"Invalid request: {', '.join(validation.errors)}")

        user_request = validation.sanitized_text
        warnings.extend(validation.warnings)

        # Check for injection in user request
        injection_check = detect_injection(user_request)
        if injection_check.is_injection:
            safety_checks.append(
                SafetyCheck(
                    check_name="User Input Injection Check",
                    passed=False,
                    details=f"Potential injection detected: {injection_check.reason}",
                )
            )
            # Don't block, but flag it
            logger.warning(
                f"Injection attempt in user request: {injection_check.reason}"
            )
        else:
            safety_checks.append(
                SafetyCheck(
                    check_name="User Input Injection Check",
                    passed=True,
                    details="No injection patterns detected",
                )
            )

        # Validate constraints
        if request.constraints:
            constraint_validation = validate_constraints(request.constraints)
            warnings.extend(constraint_validation.warnings)

        # Validate context
        context = None
        if request.context:
            context_validation = validate_context(request.context)
            context = context_validation.sanitized_text
            warnings.extend(context_validation.warnings)

        # Step 2: Classify intent
        try:
            intent_result = await self._classify_intent(user_request)
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            intent_result = {
                "intent": "general",
                "domain": "unknown",
                "complexity": "medium",
            }

        is_coding_request = self._is_coding_request(user_request, intent_result)

        # Step 3: Retrieve relevant documents
        retrieval_result = self.retriever.retrieve_for_intent(
            query=user_request,
            intent=intent_result.get("intent", "general"),
            is_coding_request=is_coding_request,
        )

        warnings.extend(retrieval_result.warnings)

        if retrieval_result.filtered_count > 0:
            safety_checks.append(
                SafetyCheck(
                    check_name="Retrieved Content Filter",
                    passed=True,
                    details=f"Filtered {retrieval_result.filtered_count} potentially unsafe documents",
                )
            )

        # Step 4: Build prompt sections
        sections = self.prompt_builder.build_prompt(
            user_request=user_request,
            target_model=request.target_model,
            prompt_style=request.prompt_style,
            patterns=retrieval_result.prompt_patterns,
            skills=retrieval_result.skill_cards,
            guidelines=retrieval_result.security_guidelines,
            constraints=request.constraints,
            context=context,
            is_coding_request=is_coding_request,
        )

        # Step 5: Run quality gates
        # Determine if this is an agent request for quality gate checks
        is_agent_check = intent_result.get("is_agent", "false").lower() == "true"
        quality_result = self.quality_gates.evaluate(
            sections=sections,
            is_coding_request=is_coding_request,
            is_agent_request=is_agent_check,
        )

        for check in quality_result.checks:
            safety_checks.append(
                SafetyCheck(
                    check_name=f"Quality: {check.name}",
                    passed=check.passed,
                    details=check.message,
                )
            )

        if quality_result.recommendations:
            assumptions.extend(
                [
                    f"Quality recommendation: {rec}"
                    for rec in quality_result.recommendations[:3]
                ]
            )

        # Step 6: Assemble final prompt (or synthesize for agent requests)
        is_agent_request = intent_result.get("is_agent", "false").lower() == "true"

        if is_agent_request:
            # Use LLM to synthesize a detailed agent prompt
            logger.info("Agent request detected - using synthesis chain")
            try:
                # Build context from retrieved documents
                synthesis_context = self._build_synthesis_context(
                    retrieval_result.prompt_patterns,
                    retrieval_result.skill_cards,
                    retrieval_result.security_guidelines,
                )

                # === DEBUG: Log the full prompt being sent to LLM ===
                logger.info("=" * 80)
                logger.info("PROMPT SENT TO LLM AFTER RAG:")
                logger.info("=" * 80)
                logger.info(f"USER REQUEST: {user_request}")
                logger.info("-" * 40)
                logger.info(f"SYNTHESIS CONTEXT (from RAG):\n{synthesis_context}")
                logger.info("-" * 40)
                logger.info("SYSTEM PROMPT:")
                logger.info(self.synthesis_prompt.messages[0].prompt.template)
                logger.info("=" * 80)
                # === END DEBUG ===

                # Invoke synthesis chain
                synthesized_prompt = await self.synthesis_chain.ainvoke(
                    {
                        "user_request": user_request,
                        "context": synthesis_context,
                    }
                )

                final_prompt = synthesized_prompt
                assumptions.append(
                    "Used AI synthesis to generate detailed agent prompt"
                )
            except Exception as e:
                logger.error(f"Synthesis chain failed: {e}, falling back to template")
                if request.output_format == OutputFormat.JSON:
                    final_prompt = self.prompt_builder.assemble_json_prompt(sections)
                else:
                    final_prompt = self.prompt_builder.assemble_plain_prompt(sections)
        else:
            # Standard assembly for non-agent requests
            # === DEBUG: Log the assembled prompt ===
            logger.info("=" * 80)
            logger.info("ASSEMBLED PROMPT (template-based, non-agent):")
            logger.info("=" * 80)
            logger.info(f"USER REQUEST: {user_request}")
            logger.info("-" * 40)
            logger.info(f"RETRIEVED PATTERNS: {len(retrieval_result.prompt_patterns)}")
            logger.info(f"RETRIEVED SKILLS: {len(retrieval_result.skill_cards)}")
            logger.info(
                f"RETRIEVED GUIDELINES: {len(retrieval_result.security_guidelines)}"
            )
            logger.info("=" * 80)
            # === END DEBUG ===

            if request.output_format == OutputFormat.JSON:
                final_prompt = self.prompt_builder.assemble_json_prompt(sections)
            else:
                final_prompt = self.prompt_builder.assemble_plain_prompt(sections)

        # Step 7: Redact any secrets that might have slipped through
        if isinstance(final_prompt, str):
            final_prompt = redact_secrets(final_prompt)

        safety_checks.append(
            SafetyCheck(
                check_name="Secret Redaction",
                passed=True,
                details="Applied secret redaction to final output",
            )
        )

        # Build citations
        citations = self._build_citations(
            retrieval_result.prompt_patterns,
            retrieval_result.skill_cards,
            retrieval_result.security_guidelines,
        )

        # Build selected skills
        selected_skills = self._build_selected_skills(retrieval_result.skill_cards)

        # Add assumptions based on what was retrieved
        if not retrieval_result.prompt_patterns:
            assumptions.append(
                "No specific prompt patterns found; using general templates"
            )
        if not retrieval_result.skill_cards:
            assumptions.append("No matching skill cards found; using base capabilities")
        if not retrieval_result.security_guidelines and is_coding_request:
            assumptions.append("Applied default security guidelines for coding tasks")

        return GeneratePromptResponse(
            final_prompt=final_prompt,
            assumptions=assumptions,
            safety_checks=safety_checks,
            citations=citations,
            selected_skills=selected_skills,
            metadata={
                "target_model": request.target_model.value,
                "prompt_style": request.prompt_style.value,
                "is_coding_request": is_coding_request,
                "intent": intent_result,
                "quality_score": quality_result.overall_score,
                "retrieved_docs": {
                    "patterns": len(retrieval_result.prompt_patterns),
                    "skills": len(retrieval_result.skill_cards),
                    "guidelines": len(retrieval_result.security_guidelines),
                },
            },
        )

    async def _classify_intent(self, request: str) -> dict[str, str]:
        """Classify the intent of a user request."""
        try:
            result = await self.intent_chain.ainvoke({"request": request})

            # Parse the result
            intent_data = {}
            for line in result.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    intent_data[key.strip().lower()] = value.strip().lower()

            return intent_data
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"intent": "general", "domain": "unknown", "complexity": "medium"}

    def _is_coding_request(self, request: str, intent: dict[str, str]) -> bool:
        """Determine if the request is coding-related."""
        request_lower = request.lower()

        # Check keywords in request
        keyword_match = any(kw in request_lower for kw in self.CODING_KEYWORDS)

        # Check intent classification
        intent_match = intent.get("intent", "") in [
            "code_generation",
            "code_review",
            "debugging",
        ]

        domain_match = intent.get("domain", "") in [
            "web",
            "backend",
            "frontend",
            "data",
            "ml",
            "devops",
        ]

        return keyword_match or intent_match or domain_match

    def _build_citations(
        self,
        patterns: list[RetrievedDocument],
        skills: list[RetrievedDocument],
        guidelines: list[RetrievedDocument],
    ) -> list[Citation]:
        """Build citations from retrieved documents."""
        citations = []

        for doc in patterns:
            citations.append(
                Citation(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=doc.section,
                    reason_used=f"Prompt pattern (relevance: {doc.relevance_score:.2f})",
                )
            )

        for doc in skills:
            citations.append(
                Citation(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=doc.section,
                    reason_used=f"Skill card (relevance: {doc.relevance_score:.2f})",
                )
            )

        for doc in guidelines:
            citations.append(
                Citation(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=doc.section,
                    reason_used=f"Security guideline (relevance: {doc.relevance_score:.2f})",
                )
            )

        return citations

    def _build_selected_skills(
        self, skills: list[RetrievedDocument]
    ) -> list[SelectedSkill]:
        """Build selected skills list from retrieved skill cards."""
        selected = []

        for doc in skills:
            # Try to extract skill metadata from content
            name = doc.title
            description = (
                doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            )

            # Look for when_to_use in content
            when_to_use = "When relevant to the current task"
            when_match = re.search(
                r"when_to_use:\s*(.+?)(?:\n|$)", doc.content, re.IGNORECASE
            )
            if when_match:
                when_to_use = when_match.group(1).strip()

            selected.append(
                SelectedSkill(
                    id=doc.doc_id,
                    name=name,
                    description=description,
                    when_to_use=when_to_use,
                    relevance_score=doc.relevance_score,
                )
            )

        return selected

    def _build_synthesis_context(
        self,
        patterns: list[RetrievedDocument],
        skills: list[RetrievedDocument],
        guidelines: list[RetrievedDocument],
    ) -> str:
        """Build context string from retrieved documents for synthesis chain."""
        context_parts = []

        if patterns:
            context_parts.append("## Relevant Prompt Patterns\n")
            for p in patterns[:3]:
                context_parts.append(f"### {p.title}\n{p.content[:500]}...\n")

        if skills:
            context_parts.append("\n## Relevant Skill Cards\n")
            for s in skills[:3]:
                context_parts.append(f"### {s.title}\n{s.content[:500]}...\n")

        if guidelines:
            context_parts.append("\n## Security Guidelines\n")
            for g in guidelines[:2]:
                context_parts.append(f"### {g.title}\n{g.content[:300]}...\n")

        if not context_parts:
            return "No specific patterns or skills retrieved. Generate a comprehensive agent prompt based on best practices."

        return "\n".join(context_parts)
