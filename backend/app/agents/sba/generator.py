# M15.1 SBA Generator
# Auto-generate boilerplate SBA for existing agents
#
# Strategy:
# - winning_aspiration → from agent name + docstring
# - where_to_play → from allowed input types
# - tasks → inferred from routing/capabilities
# - tests → empty list (allowed for retrofitted agents)
# - dependencies → inferred from imported tools
#
# M15.1.1 Strict Mode:
# - Requires explicit orchestrator-provided values for critical fields
# - Validates semantic quality (not just structural correctness)
# - Warns on low-quality auto-generated content

import inspect
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type

from .schema import (
    SBASchema,
    WinningAspiration,
    WhereToPlay,
    HowToWin,
    CapabilitiesCapacity,
    EnablingManagementSystems,
    EnvironmentRequirements,
    GovernanceProvider,
    Dependency,
    DependencyType,
)

logger = logging.getLogger("nova.agents.sba.generator")


# M15.1.1: Generation quality tracking
class GenerationQuality(str, Enum):
    """Quality level of generated SBA content."""
    HIGH = "high"        # All fields from explicit source
    MEDIUM = "medium"    # Mix of explicit and inferred
    LOW = "low"          # Mostly placeholder content


@dataclass
class GenerationReport:
    """
    M15.1.1: Report on SBA generation quality.

    Tracks which fields were auto-generated vs provided,
    enabling audit and enforcement of strict mode.
    """
    agent_id: str
    quality: GenerationQuality
    explicit_fields: List[str] = field(default_factory=list)
    inferred_fields: List[str] = field(default_factory=list)
    placeholder_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    strict_violations: List[str] = field(default_factory=list)

    @property
    def is_strict_compliant(self) -> bool:
        """Check if generation is strict-mode compliant."""
        return len(self.strict_violations) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "quality": self.quality.value,
            "explicit_fields": self.explicit_fields,
            "inferred_fields": self.inferred_fields,
            "placeholder_fields": self.placeholder_fields,
            "warnings": self.warnings,
            "strict_violations": self.strict_violations,
            "is_strict_compliant": self.is_strict_compliant,
        }


# Minimum quality thresholds for strict mode
STRICT_MODE_REQUIREMENTS = {
    "aspiration_min_length": 30,
    "aspiration_forbidden_phrases": [
        "provide reliable",
        "as part of the multi-agent",
        "execute operations",
    ],
    "task_min_count": 1,
    "task_min_length": 10,
    "domain_forbidden": ["general-purpose"],
}


class SBAGenerator:
    """
    Generator for Strategy-Bound Agent schemas.

    Auto-generates boilerplate SBA from:
    - Agent class/function docstrings
    - Input/output type hints
    - Skill dependencies
    - Capability declarations

    M15.1.1: Strict mode support for quality enforcement.
    """

    def __init__(
        self,
        default_orchestrator: str = "system",
        strict_mode: bool = False,
    ):
        """
        Initialize generator.

        Args:
            default_orchestrator: Default orchestrator name
            strict_mode: If True, reject low-quality auto-generated content
        """
        self.default_orchestrator = default_orchestrator
        self.strict_mode = strict_mode

    def generate(
        self,
        agent_id: str,
        agent_class: Optional[Type] = None,
        agent_func: Optional[Callable] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        orchestrator: Optional[str] = None,
        # M15.1.1: Explicit overrides for strict mode
        aspiration_override: Optional[str] = None,
        domain_override: Optional[str] = None,
        tasks_override: Optional[List[str]] = None,
        boundaries_override: Optional[str] = None,
    ) -> SBASchema:
        """
        Generate SBA schema for an agent.

        Args:
            agent_id: Agent identifier
            agent_class: Optional agent class for introspection
            agent_func: Optional agent function for introspection
            capabilities: Existing capabilities dict
            config: Existing config dict
            orchestrator: Orchestrator name (uses default if not provided)
            aspiration_override: M15.1.1 - Explicit aspiration (strict mode)
            domain_override: M15.1.1 - Explicit domain (strict mode)
            tasks_override: M15.1.1 - Explicit tasks (strict mode)
            boundaries_override: M15.1.1 - Explicit boundaries (strict mode)

        Returns:
            Generated SBASchema

        Raises:
            ValueError: If strict_mode=True and quality thresholds not met
        """
        # Track generation report
        report = GenerationReport(agent_id=agent_id, quality=GenerationQuality.HIGH)

        # Extract metadata from various sources
        docstring = self._extract_docstring(agent_class, agent_func)

        # Generate or use override for aspiration
        if aspiration_override:
            aspiration = aspiration_override
            report.explicit_fields.append("winning_aspiration")
        else:
            aspiration = self._generate_aspiration(agent_id, docstring)
            if self._is_placeholder_aspiration(aspiration):
                report.placeholder_fields.append("winning_aspiration")
            else:
                report.inferred_fields.append("winning_aspiration")

        # Generate or use override for domain
        if domain_override:
            domain = domain_override
            report.explicit_fields.append("domain")
        else:
            domain = self._infer_domain(agent_id, docstring, capabilities)
            if domain == "general-purpose":
                report.placeholder_fields.append("domain")
            else:
                report.inferred_fields.append("domain")

        # Generate or use override for tasks
        if tasks_override:
            tasks = tasks_override
            report.explicit_fields.append("tasks")
        else:
            tasks = self._infer_tasks(agent_id, docstring, capabilities, config)
            if self._are_placeholder_tasks(tasks):
                report.placeholder_fields.append("tasks")
            else:
                report.inferred_fields.append("tasks")

        # Generate boundaries
        boundaries = boundaries_override
        if boundaries:
            report.explicit_fields.append("boundaries")
        else:
            report.warnings.append("No boundaries defined - agent has no explicit restrictions")

        # Infer other fields
        dependencies = self._infer_dependencies(capabilities, config)
        allowed_tools = self._infer_allowed_tools(capabilities, config)
        env_requirements = self._infer_env_requirements(config)

        # Compute quality level
        report.quality = self._compute_quality(report)

        # M15.1.1: Strict mode validation
        if self.strict_mode:
            self._validate_strict_mode(report, aspiration, domain, tasks)
            if not report.is_strict_compliant:
                raise ValueError(
                    f"Strict mode violations for {agent_id}: {report.strict_violations}. "
                    "Use explicit overrides (aspiration_override, domain_override, tasks_override) "
                    "or disable strict_mode."
                )

        # Log report
        if report.placeholder_fields:
            logger.warning(
                "sba_generation_low_quality",
                extra={
                    "agent_id": agent_id,
                    "quality": report.quality.value,
                    "placeholder_fields": report.placeholder_fields,
                }
            )

        return SBASchema(
            sba_version="1.0",
            agent_id=agent_id,
            winning_aspiration=WinningAspiration(
                description=aspiration,
            ),
            where_to_play=WhereToPlay(
                domain=domain,
                allowed_tools=allowed_tools,
                allowed_contexts=["job"],
                boundaries=boundaries,
            ),
            how_to_win=HowToWin(
                tasks=tasks,
                tests=[],  # Empty for retrofitted agents
                fulfillment_metric=0.0,
            ),
            capabilities_capacity=CapabilitiesCapacity(
                legacy_dependencies=dependencies,  # Legacy string format
                env=env_requirements,
            ),
            enabling_management_systems=EnablingManagementSystems(
                orchestrator=orchestrator or self.default_orchestrator,
                governance=GovernanceProvider.BUDGETLLM,
            ),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def generate_with_report(
        self,
        agent_id: str,
        **kwargs,
    ) -> tuple[SBASchema, GenerationReport]:
        """
        M15.1.1: Generate SBA with quality report.

        Returns both the schema and the generation report for audit.
        """
        # Track generation report
        report = GenerationReport(agent_id=agent_id, quality=GenerationQuality.HIGH)

        try:
            sba = self.generate(agent_id, **kwargs)

            # Re-compute report (generate() doesn't return it)
            docstring = self._extract_docstring(
                kwargs.get('agent_class'),
                kwargs.get('agent_func'),
            )
            aspiration = sba.winning_aspiration.description
            domain = sba.where_to_play.domain
            tasks = sba.how_to_win.tasks

            if kwargs.get('aspiration_override'):
                report.explicit_fields.append("winning_aspiration")
            elif self._is_placeholder_aspiration(aspiration):
                report.placeholder_fields.append("winning_aspiration")
            else:
                report.inferred_fields.append("winning_aspiration")

            if kwargs.get('domain_override'):
                report.explicit_fields.append("domain")
            elif domain == "general-purpose":
                report.placeholder_fields.append("domain")
            else:
                report.inferred_fields.append("domain")

            if kwargs.get('tasks_override'):
                report.explicit_fields.append("tasks")
            elif self._are_placeholder_tasks(tasks):
                report.placeholder_fields.append("tasks")
            else:
                report.inferred_fields.append("tasks")

            report.quality = self._compute_quality(report)

            return sba, report

        except ValueError as e:
            report.strict_violations.append(str(e))
            raise

    def _is_placeholder_aspiration(self, aspiration: str) -> bool:
        """Check if aspiration is placeholder content."""
        lower = aspiration.lower()
        for phrase in STRICT_MODE_REQUIREMENTS["aspiration_forbidden_phrases"]:
            if phrase in lower:
                return True
        return len(aspiration) < STRICT_MODE_REQUIREMENTS["aspiration_min_length"]

    def _are_placeholder_tasks(self, tasks: List[str]) -> bool:
        """Check if tasks are placeholder content."""
        if len(tasks) < STRICT_MODE_REQUIREMENTS["task_min_count"]:
            return True
        for task in tasks:
            if "execute" in task.lower() and "operations" in task.lower():
                return True
            if len(task) < STRICT_MODE_REQUIREMENTS["task_min_length"]:
                return True
        return False

    def _compute_quality(self, report: GenerationReport) -> GenerationQuality:
        """Compute overall quality from report."""
        total_fields = (
            len(report.explicit_fields) +
            len(report.inferred_fields) +
            len(report.placeholder_fields)
        )
        if total_fields == 0:
            return GenerationQuality.LOW

        explicit_ratio = len(report.explicit_fields) / total_fields
        placeholder_ratio = len(report.placeholder_fields) / total_fields

        if explicit_ratio >= 0.7:
            return GenerationQuality.HIGH
        elif placeholder_ratio >= 0.5:
            return GenerationQuality.LOW
        else:
            return GenerationQuality.MEDIUM

    def _validate_strict_mode(
        self,
        report: GenerationReport,
        aspiration: str,
        domain: str,
        tasks: List[str],
    ) -> None:
        """Validate against strict mode requirements."""
        # Check aspiration
        if self._is_placeholder_aspiration(aspiration):
            report.strict_violations.append(
                f"Aspiration is placeholder content (len={len(aspiration)}, "
                "contains forbidden phrases). Provide aspiration_override."
            )

        # Check domain
        if domain in STRICT_MODE_REQUIREMENTS["domain_forbidden"]:
            report.strict_violations.append(
                f"Domain '{domain}' is too generic. Provide domain_override."
            )

        # Check tasks
        if self._are_placeholder_tasks(tasks):
            report.strict_violations.append(
                f"Tasks are placeholder content ({tasks}). Provide tasks_override."
            )

    def _extract_docstring(
        self,
        agent_class: Optional[Type],
        agent_func: Optional[Callable],
    ) -> str:
        """Extract docstring from agent class or function."""
        if agent_class:
            doc = inspect.getdoc(agent_class)
            if doc:
                return doc

        if agent_func:
            doc = inspect.getdoc(agent_func)
            if doc:
                return doc

        return ""

    def _generate_aspiration(self, agent_id: str, docstring: str) -> str:
        """Generate winning aspiration from agent info."""
        # Try to extract purpose from docstring
        if docstring:
            # Look for purpose-like sentences
            lines = docstring.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('-') and not line.startswith('*'):
                    # First non-list line is likely the purpose
                    if len(line) >= 20:
                        return line[:200]

        # Fall back to name-based generation
        readable_name = self._agent_id_to_readable(agent_id)
        return f"Provide reliable {readable_name} capabilities as part of the multi-agent system"

    def _agent_id_to_readable(self, agent_id: str) -> str:
        """Convert agent_id to human-readable form."""
        # scraper_worker -> scraper worker
        # data-analyzer -> data analyzer
        readable = agent_id.replace('_', ' ').replace('-', ' ')

        # Remove common suffixes
        for suffix in ['worker', 'agent', 'service']:
            if readable.endswith(f' {suffix}'):
                readable = readable[:-len(suffix)-1]

        return readable.strip() or agent_id

    def _infer_domain(
        self,
        agent_id: str,
        docstring: str,
        capabilities: Optional[Dict[str, Any]],
    ) -> str:
        """Infer domain from agent info."""
        # Check capabilities for domain hints
        if capabilities:
            if 'domain' in capabilities:
                return capabilities['domain']
            if 'role' in capabilities:
                return capabilities['role']

        # Infer from agent_id patterns
        domain_patterns = {
            'scraper': 'web-scraping',
            'crawler': 'web-scraping',
            'analyzer': 'data-analysis',
            'processor': 'data-processing',
            'validator': 'validation',
            'checker': 'validation',
            'writer': 'content-generation',
            'generator': 'content-generation',
            'formatter': 'data-transformation',
            'parser': 'data-parsing',
            'extractor': 'data-extraction',
            'aggregator': 'aggregation',
            'orchestrator': 'orchestration',
        }

        agent_lower = agent_id.lower()
        for pattern, domain in domain_patterns.items():
            if pattern in agent_lower:
                return domain

        # Default domain
        return 'general-purpose'

    def _infer_tasks(
        self,
        agent_id: str,
        docstring: str,
        capabilities: Optional[Dict[str, Any]],
        config: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Infer tasks from agent info."""
        tasks = []

        # Extract from capabilities
        if capabilities:
            if 'task' in capabilities:
                tasks.append(capabilities['task'])
            if 'tasks' in capabilities:
                tasks.extend(capabilities['tasks'])

        # Extract from config
        if config:
            if 'task' in config:
                tasks.append(config['task'])

        # Extract from docstring (look for bullet points)
        if docstring:
            lines = docstring.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    task = line[2:].strip()
                    if task and len(task) < 200:
                        tasks.append(task)

        # If no tasks found, generate from agent_id
        if not tasks:
            readable = self._agent_id_to_readable(agent_id)
            tasks.append(f"Execute {readable} operations")

        # Deduplicate while preserving order
        seen = set()
        unique_tasks = []
        for task in tasks:
            if task not in seen:
                seen.add(task)
                unique_tasks.append(task)

        return unique_tasks[:10]  # Limit to 10 tasks

    def _infer_dependencies(
        self,
        capabilities: Optional[Dict[str, Any]],
        config: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Infer dependencies from agent info."""
        deps = []

        if capabilities:
            if 'dependencies' in capabilities:
                deps.extend(capabilities['dependencies'])
            if 'skills' in capabilities:
                deps.extend(capabilities['skills'])
            if 'tools' in capabilities:
                deps.extend(capabilities['tools'])

        if config:
            if 'dependencies' in config:
                deps.extend(config['dependencies'])
            if 'required_skills' in config:
                deps.extend(config['required_skills'])

        # Deduplicate
        return list(set(deps))

    def _infer_allowed_tools(
        self,
        capabilities: Optional[Dict[str, Any]],
        config: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Infer allowed tools from agent info."""
        tools = []

        if capabilities:
            if 'allowed_tools' in capabilities:
                tools.extend(capabilities['allowed_tools'])
            if 'skills' in capabilities:
                tools.extend(capabilities['skills'])

        if config:
            if 'allowed_tools' in config:
                tools.extend(config['allowed_tools'])

        return list(set(tools))

    def _infer_env_requirements(
        self,
        config: Optional[Dict[str, Any]],
    ) -> EnvironmentRequirements:
        """Infer environment requirements from config."""
        env = EnvironmentRequirements()

        if config:
            if 'timeout' in config:
                env.timeout_seconds = config['timeout']
            if 'timeout_per_item' in config:
                env.timeout_seconds = config['timeout_per_item']
            if 'budget_tokens' in config:
                env.budget_tokens = config['budget_tokens']
            if 'llm_budget_cents' in config:
                # Rough conversion: 100 cents ~ 50k tokens for GPT-4
                env.budget_tokens = config['llm_budget_cents'] * 500

        return env


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_sba_from_agent(
    agent_id: str,
    capabilities: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    orchestrator: Optional[str] = None,
) -> SBASchema:
    """
    Generate SBA schema from agent metadata.

    Convenience function for retrofitting existing agents.

    Args:
        agent_id: Agent identifier
        capabilities: Existing capabilities dict
        config: Existing config dict
        orchestrator: Orchestrator name

    Returns:
        Generated SBASchema
    """
    generator = SBAGenerator(default_orchestrator=orchestrator or "system")
    return generator.generate(
        agent_id=agent_id,
        capabilities=capabilities,
        config=config,
        orchestrator=orchestrator,
    )


def generate_sba_from_spawn_input(
    orchestrator_agent: str,
    worker_agent: str,
    task: str,
    config: Dict[str, Any],
) -> SBASchema:
    """
    Generate SBA schema from AgentSpawnInput data.

    Called by agent_spawn to create SBA for workers that don't have one.

    Args:
        orchestrator_agent: Orchestrator agent ID
        worker_agent: Worker agent ID being spawned
        task: Task description
        config: Job config

    Returns:
        Generated SBASchema for the worker
    """
    generator = SBAGenerator(default_orchestrator=orchestrator_agent)

    return generator.generate(
        agent_id=worker_agent,
        capabilities={"task": task, "role": "worker"},
        config=config,
        orchestrator=orchestrator_agent,
    )


def retrofit_existing_agents(
    agents: List[Dict[str, Any]],
    orchestrator: str = "system",
) -> List[SBASchema]:
    """
    Retrofit SBA schemas for a list of existing agents.

    Args:
        agents: List of agent dicts with 'agent_id', 'capabilities', 'config'
        orchestrator: Default orchestrator name

    Returns:
        List of generated SBASchemas
    """
    generator = SBAGenerator(default_orchestrator=orchestrator)
    schemas = []

    for agent in agents:
        sba = generator.generate(
            agent_id=agent.get('agent_id', 'unknown'),
            capabilities=agent.get('capabilities'),
            config=agent.get('config'),
            orchestrator=orchestrator,
        )
        schemas.append(sba)
        logger.info(f"Generated SBA for agent: {agent.get('agent_id')}")

    return schemas
