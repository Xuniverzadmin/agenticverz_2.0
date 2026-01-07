# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: AST definition tests
# Reference: PIN-341, PIN-345

"""
Tests for Policy DSL AST definitions.

COVERAGE:
- Immutability enforcement
- Validation constraints
- Serialization correctness
- Hash determinism
"""

import pytest

from app.dsl.ast import (
    PolicyAST,
    PolicyMetadata,
    Clause,
    Predicate,
    ExistsPredicate,
    LogicalCondition,
    WarnAction,
    BlockAction,
    RequireApprovalAction,
    Scope,
    Mode,
    Comparator,
    LogicalOperator,
    is_predicate,
    is_exists_predicate,
    is_logical_condition,
    is_warn_action,
    is_block_action,
    is_require_approval_action,
)


# =============================================================================
# METADATA TESTS
# =============================================================================

class TestPolicyMetadata:
    """Tests for PolicyMetadata node."""

    def test_valid_metadata_creation(self) -> None:
        """Test creating valid metadata."""
        meta = PolicyMetadata(
            name="CostGuard",
            version=1,
            scope=Scope.PROJECT,
            mode=Mode.MONITOR,
        )
        assert meta.name == "CostGuard"
        assert meta.version == 1
        assert meta.scope == Scope.PROJECT
        assert meta.mode == Mode.MONITOR

    def test_metadata_immutability(self) -> None:
        """Test that metadata is immutable."""
        meta = PolicyMetadata(
            name="CostGuard",
            version=1,
            scope=Scope.PROJECT,
            mode=Mode.MONITOR,
        )
        with pytest.raises(AttributeError):
            meta.name = "Modified"  # type: ignore

    def test_metadata_version_must_be_positive(self) -> None:
        """Test that version must be >= 1."""
        with pytest.raises(ValueError, match="Version must be >= 1"):
            PolicyMetadata(
                name="Test",
                version=0,
                scope=Scope.ORG,
                mode=Mode.ENFORCE,
            )

    def test_metadata_name_cannot_be_empty(self) -> None:
        """Test that name cannot be empty."""
        with pytest.raises(ValueError, match="Policy name cannot be empty"):
            PolicyMetadata(
                name="",
                version=1,
                scope=Scope.ORG,
                mode=Mode.ENFORCE,
            )

    def test_metadata_to_dict(self) -> None:
        """Test serialization to dict."""
        meta = PolicyMetadata(
            name="CostGuard",
            version=2,
            scope=Scope.ORG,
            mode=Mode.ENFORCE,
        )
        result = meta.to_dict()
        assert result == {
            "name": "CostGuard",
            "version": 2,
            "scope": "ORG",
            "mode": "ENFORCE",
        }


# =============================================================================
# ACTION TESTS
# =============================================================================

class TestActions:
    """Tests for action nodes."""

    def test_warn_action(self) -> None:
        """Test WarnAction creation and serialization."""
        action = WarnAction(message="Cost exceeded threshold")
        assert action.message == "Cost exceeded threshold"
        assert action.type == "WARN"
        assert action.to_dict() == {
            "type": "WARN",
            "message": "Cost exceeded threshold",
        }

    def test_block_action(self) -> None:
        """Test BlockAction creation and serialization."""
        action = BlockAction()
        assert action.type == "BLOCK"
        assert action.to_dict() == {"type": "BLOCK"}

    def test_require_approval_action(self) -> None:
        """Test RequireApprovalAction creation and serialization."""
        action = RequireApprovalAction()
        assert action.type == "REQUIRE_APPROVAL"
        assert action.to_dict() == {"type": "REQUIRE_APPROVAL"}

    def test_action_immutability(self) -> None:
        """Test that actions are immutable."""
        action = WarnAction(message="Test")
        with pytest.raises(AttributeError):
            action.message = "Modified"  # type: ignore


# =============================================================================
# CONDITION TESTS
# =============================================================================

class TestConditions:
    """Tests for condition nodes."""

    def test_predicate_creation(self) -> None:
        """Test Predicate creation."""
        pred = Predicate(
            metric="cost_per_hour",
            comparator=Comparator.GT,
            value=200,
        )
        assert pred.metric == "cost_per_hour"
        assert pred.comparator == Comparator.GT
        assert pred.value == 200

    def test_predicate_to_dict(self) -> None:
        """Test Predicate serialization."""
        pred = Predicate(
            metric="error_rate",
            comparator=Comparator.GTE,
            value=0.1,
        )
        assert pred.to_dict() == {
            "type": "predicate",
            "metric": "error_rate",
            "comparator": ">=",
            "value": 0.1,
        }

    def test_exists_predicate(self) -> None:
        """Test ExistsPredicate creation and serialization."""
        pred = ExistsPredicate(metric="anomaly_flag")
        assert pred.metric == "anomaly_flag"
        assert pred.to_dict() == {
            "type": "exists",
            "metric": "anomaly_flag",
        }

    def test_logical_condition_and(self) -> None:
        """Test LogicalCondition with AND."""
        left = Predicate("cost", Comparator.GT, 100)
        right = Predicate("error_rate", Comparator.GT, 0.05)
        compound = LogicalCondition(
            left=left,
            operator=LogicalOperator.AND,
            right=right,
        )
        assert compound.operator == LogicalOperator.AND
        result = compound.to_dict()
        assert result["type"] == "logical"
        assert result["operator"] == "AND"

    def test_logical_condition_or(self) -> None:
        """Test LogicalCondition with OR."""
        left = Predicate("cost", Comparator.GT, 100)
        right = ExistsPredicate("safety_flag")
        compound = LogicalCondition(
            left=left,
            operator=LogicalOperator.OR,
            right=right,
        )
        assert compound.operator == LogicalOperator.OR

    def test_nested_logical_conditions(self) -> None:
        """Test deeply nested logical conditions."""
        # (a > 1 AND b < 2) OR c == 3
        a_pred = Predicate("a", Comparator.GT, 1)
        b_pred = Predicate("b", Comparator.LT, 2)
        c_pred = Predicate("c", Comparator.EQ, 3)

        inner = LogicalCondition(a_pred, LogicalOperator.AND, b_pred)
        outer = LogicalCondition(inner, LogicalOperator.OR, c_pred)

        result = outer.to_dict()
        assert result["type"] == "logical"
        assert result["operator"] == "OR"
        assert result["left"]["type"] == "logical"
        assert result["left"]["operator"] == "AND"

    def test_condition_immutability(self) -> None:
        """Test that conditions are immutable."""
        pred = Predicate("cost", Comparator.GT, 100)
        with pytest.raises(AttributeError):
            pred.value = 200  # type: ignore


# =============================================================================
# CLAUSE TESTS
# =============================================================================

class TestClause:
    """Tests for Clause node."""

    def test_clause_creation(self) -> None:
        """Test valid clause creation."""
        clause = Clause(
            when=Predicate("cost", Comparator.GT, 100),
            then=(WarnAction("High cost"),),
        )
        assert is_predicate(clause.when)
        assert len(clause.then) == 1

    def test_clause_multiple_actions(self) -> None:
        """Test clause with multiple actions."""
        clause = Clause(
            when=Predicate("cost", Comparator.GT, 100),
            then=(
                WarnAction("High cost"),
                BlockAction(),
            ),
        )
        assert len(clause.then) == 2

    def test_clause_empty_then_raises(self) -> None:
        """Test that empty then clause raises."""
        with pytest.raises(ValueError, match="at least one action"):
            Clause(
                when=Predicate("cost", Comparator.GT, 100),
                then=(),
            )

    def test_clause_to_dict(self) -> None:
        """Test clause serialization."""
        clause = Clause(
            when=Predicate("cost", Comparator.GT, 100),
            then=(WarnAction("Alert"),),
        )
        result = clause.to_dict()
        assert "when" in result
        assert "then" in result
        assert len(result["then"]) == 1


# =============================================================================
# POLICY AST TESTS
# =============================================================================

class TestPolicyAST:
    """Tests for PolicyAST root node."""

    @pytest.fixture
    def simple_policy(self) -> PolicyAST:
        """Create a simple valid policy AST."""
        return PolicyAST(
            metadata=PolicyMetadata(
                name="CostGuard",
                version=1,
                scope=Scope.PROJECT,
                mode=Mode.MONITOR,
            ),
            clauses=(
                Clause(
                    when=Predicate("cost_per_hour", Comparator.GT, 200),
                    then=(WarnAction("Cost threshold exceeded"),),
                ),
            ),
        )

    def test_policy_creation(self, simple_policy: PolicyAST) -> None:
        """Test valid policy creation."""
        assert simple_policy.name == "CostGuard"
        assert simple_policy.version == 1
        assert simple_policy.scope == Scope.PROJECT
        assert simple_policy.mode == Mode.MONITOR
        assert len(simple_policy.clauses) == 1

    def test_policy_immutability(self, simple_policy: PolicyAST) -> None:
        """Test that policy is immutable."""
        with pytest.raises(AttributeError):
            simple_policy.metadata = PolicyMetadata(  # type: ignore
                name="Modified",
                version=2,
                scope=Scope.ORG,
                mode=Mode.ENFORCE,
            )

    def test_policy_empty_clauses_raises(self) -> None:
        """Test that policy with no clauses raises."""
        with pytest.raises(ValueError, match="at least one clause"):
            PolicyAST(
                metadata=PolicyMetadata(
                    name="Empty",
                    version=1,
                    scope=Scope.ORG,
                    mode=Mode.MONITOR,
                ),
                clauses=(),
            )

    def test_policy_to_dict(self, simple_policy: PolicyAST) -> None:
        """Test policy serialization to dict."""
        result = simple_policy.to_dict()
        assert "metadata" in result
        assert "clauses" in result
        assert result["metadata"]["name"] == "CostGuard"

    def test_policy_to_json(self, simple_policy: PolicyAST) -> None:
        """Test policy serialization to JSON."""
        json_str = simple_policy.to_json()
        assert '"name": "CostGuard"' in json_str
        assert '"version": 1' in json_str

    def test_policy_hash_determinism(self) -> None:
        """Test that same policy produces same hash."""
        policy1 = PolicyAST(
            metadata=PolicyMetadata("Test", 1, Scope.ORG, Mode.MONITOR),
            clauses=(
                Clause(
                    when=Predicate("x", Comparator.GT, 10),
                    then=(WarnAction("Alert"),),
                ),
            ),
        )
        policy2 = PolicyAST(
            metadata=PolicyMetadata("Test", 1, Scope.ORG, Mode.MONITOR),
            clauses=(
                Clause(
                    when=Predicate("x", Comparator.GT, 10),
                    then=(WarnAction("Alert"),),
                ),
            ),
        )
        assert policy1.compute_hash() == policy2.compute_hash()

    def test_policy_hash_changes_with_content(self) -> None:
        """Test that different content produces different hash."""
        policy1 = PolicyAST(
            metadata=PolicyMetadata("Test", 1, Scope.ORG, Mode.MONITOR),
            clauses=(
                Clause(
                    when=Predicate("x", Comparator.GT, 10),
                    then=(WarnAction("Alert"),),
                ),
            ),
        )
        policy2 = PolicyAST(
            metadata=PolicyMetadata("Test", 1, Scope.ORG, Mode.MONITOR),
            clauses=(
                Clause(
                    when=Predicate("x", Comparator.GT, 20),  # Different value
                    then=(WarnAction("Alert"),),
                ),
            ),
        )
        assert policy1.compute_hash() != policy2.compute_hash()


# =============================================================================
# TYPE GUARD TESTS
# =============================================================================

class TestTypeGuards:
    """Tests for type guard functions."""

    def test_is_predicate(self) -> None:
        """Test is_predicate type guard."""
        assert is_predicate(Predicate("x", Comparator.GT, 1))
        assert not is_predicate(ExistsPredicate("x"))
        assert not is_predicate(
            LogicalCondition(
                Predicate("x", Comparator.GT, 1),
                LogicalOperator.AND,
                Predicate("y", Comparator.LT, 2),
            )
        )

    def test_is_exists_predicate(self) -> None:
        """Test is_exists_predicate type guard."""
        assert is_exists_predicate(ExistsPredicate("x"))
        assert not is_exists_predicate(Predicate("x", Comparator.GT, 1))

    def test_is_logical_condition(self) -> None:
        """Test is_logical_condition type guard."""
        compound = LogicalCondition(
            Predicate("x", Comparator.GT, 1),
            LogicalOperator.AND,
            Predicate("y", Comparator.LT, 2),
        )
        assert is_logical_condition(compound)
        assert not is_logical_condition(Predicate("x", Comparator.GT, 1))

    def test_is_warn_action(self) -> None:
        """Test is_warn_action type guard."""
        assert is_warn_action(WarnAction("Test"))
        assert not is_warn_action(BlockAction())

    def test_is_block_action(self) -> None:
        """Test is_block_action type guard."""
        assert is_block_action(BlockAction())
        assert not is_block_action(WarnAction("Test"))

    def test_is_require_approval_action(self) -> None:
        """Test is_require_approval_action type guard."""
        assert is_require_approval_action(RequireApprovalAction())
        assert not is_require_approval_action(BlockAction())


# =============================================================================
# COMPARATOR TESTS
# =============================================================================

class TestComparators:
    """Tests for all comparator types."""

    @pytest.mark.parametrize(
        "comparator,expected_value",
        [
            (Comparator.GT, ">"),
            (Comparator.GTE, ">="),
            (Comparator.LT, "<"),
            (Comparator.LTE, "<="),
            (Comparator.EQ, "=="),
            (Comparator.NEQ, "!="),
        ],
    )
    def test_comparator_values(self, comparator: Comparator, expected_value: str) -> None:
        """Test all comparator enum values."""
        assert comparator.value == expected_value

    @pytest.mark.parametrize(
        "comparator",
        [Comparator.GT, Comparator.GTE, Comparator.LT, Comparator.LTE, Comparator.EQ, Comparator.NEQ],
    )
    def test_predicate_with_all_comparators(self, comparator: Comparator) -> None:
        """Test predicate creation with all comparators."""
        pred = Predicate("metric", comparator, 100)
        assert pred.comparator == comparator
        assert comparator.value in pred.to_dict()["comparator"]
