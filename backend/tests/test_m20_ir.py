# M20 IR Tests
# Tests for IR generation and symbol table
"""
Test suite for M20 IR:
- IR node creation
- Symbol table management
- IR builder (AST to IR)
- Governance metadata propagation
"""

import pytest
from app.policy.compiler.parser import Parser
from app.policy.compiler.grammar import PolicyCategory, ActionType
from app.policy.ir.ir_nodes import (
    IRType,
    IRGovernance,
    IRLoadConst,
    IRLoadVar,
    IRBinaryOp,
    IRCompare,
    IRAction,
    IRJump,
    IRJumpIf,
    IRBlock,
    IRFunction,
    IRModule,
)
from app.policy.ir.symbol_table import Symbol, SymbolType, SymbolTable
from app.policy.ir.ir_builder import IRBuilder


class TestIRNodes:
    """Tests for IR node structures."""

    def test_ir_load_const(self):
        """Test IRLoadConst instruction."""
        instr = IRLoadConst(id=1, value=42)
        assert str(instr) == "%1 = const 42"

    def test_ir_load_var(self):
        """Test IRLoadVar instruction."""
        instr = IRLoadVar(id=2, name="user")
        assert str(instr) == "%2 = load user"

    def test_ir_binary_op(self):
        """Test IRBinaryOp instruction."""
        instr = IRBinaryOp(id=3, op="and", left_id=1, right_id=2)
        assert str(instr) == "%3 = and %1, %2"

    def test_ir_compare(self):
        """Test IRCompare instruction."""
        instr = IRCompare(id=4, op="==", left_id=1, right_id=2)
        assert str(instr) == "%4 = cmp == %1, %2"

    def test_ir_action(self):
        """Test IRAction instruction."""
        instr = IRAction(action=ActionType.DENY)
        assert "action deny" in str(instr)

        instr_route = IRAction(action=ActionType.ROUTE, target="agent_x")
        assert "action route to agent_x" in str(instr_route)

    def test_ir_jump(self):
        """Test IRJump instruction."""
        instr = IRJump(target_block="block_2")
        assert str(instr) == "jump block_2"

    def test_ir_jump_if(self):
        """Test IRJumpIf instruction."""
        instr = IRJumpIf(condition_id=5, true_block="then_1", false_block="else_1")
        assert str(instr) == "jumpif %5, then_1, else_1"


class TestIRBlocks:
    """Tests for IR blocks and functions."""

    def test_ir_block_creation(self):
        """Test creating IR block."""
        block = IRBlock(name="entry")
        block.add_instruction(IRLoadConst(id=1, value=10))
        block.add_instruction(IRLoadConst(id=2, value=20))

        assert len(block.instructions) == 2
        assert not block.is_terminated

    def test_ir_block_termination(self):
        """Test block termination detection."""
        block = IRBlock(name="test")
        block.add_instruction(IRLoadConst(id=1, value=10))
        assert not block.is_terminated

        block.add_instruction(IRJump(target_block="next"))
        assert block.is_terminated

    def test_ir_function_creation(self):
        """Test creating IR function."""
        func = IRFunction(
            name="test_policy",
            params=["ctx"],
            return_type=IRType.ACTION,
        )

        entry = IRBlock(name="entry")
        entry.add_instruction(IRAction(action=ActionType.ALLOW))
        func.add_block(entry)

        assert len(func.blocks) == 1
        assert func.get_block("entry") is not None

    def test_ir_module_creation(self):
        """Test creating IR module."""
        module = IRModule(name="test_module")

        func = IRFunction(
            name="policy_a",
            governance=IRGovernance(
                category=PolicyCategory.SAFETY,
                priority=100,
            ),
        )
        module.add_function(func)

        assert len(module.functions) == 1
        assert PolicyCategory.SAFETY in module.functions_by_category
        assert "policy_a" in module.functions_by_category[PolicyCategory.SAFETY]


class TestIRGovernance:
    """Tests for IR governance metadata."""

    def test_governance_creation(self):
        """Test creating governance metadata."""
        gov = IRGovernance(
            category=PolicyCategory.SAFETY,
            priority=100,
            source_policy="test_policy",
        )

        assert gov.category == PolicyCategory.SAFETY
        assert gov.priority == 100
        assert gov.source_policy == "test_policy"

    def test_governance_to_dict(self):
        """Test governance serialization."""
        gov = IRGovernance(
            category=PolicyCategory.PRIVACY,
            priority=90,
            audit_level=2,
        )

        data = gov.to_dict()
        assert data["category"] == "PRIVACY"
        assert data["priority"] == 90
        assert data["audit_level"] == 2

    def test_module_category_lookup(self):
        """Test module category-based function lookup."""
        module = IRModule(name="test")

        for name, cat, pri in [
            ("safety_1", PolicyCategory.SAFETY, 100),
            ("safety_2", PolicyCategory.SAFETY, 90),
            ("privacy_1", PolicyCategory.PRIVACY, 80),
        ]:
            func = IRFunction(
                name=name,
                governance=IRGovernance(category=cat, priority=pri),
            )
            module.add_function(func)

        safety_funcs = module.get_functions_by_category(PolicyCategory.SAFETY)
        assert len(safety_funcs) == 2
        # Should be sorted by priority (highest first)
        assert safety_funcs[0].name == "safety_1"
        assert safety_funcs[1].name == "safety_2"


class TestSymbolTable:
    """Tests for symbol table."""

    def test_symbol_definition(self):
        """Test defining symbols."""
        st = SymbolTable()

        symbol = Symbol(
            name="test_policy",
            symbol_type=SymbolType.POLICY,
            category=PolicyCategory.SAFETY,
            priority=100,
        )
        st.define(symbol)

        found = st.lookup("test_policy")
        assert found is not None
        assert found.name == "test_policy"
        assert found.category == PolicyCategory.SAFETY

    def test_scope_hierarchy(self):
        """Test scope nesting."""
        st = SymbolTable()

        # Global scope
        st.define(Symbol(name="global_var", symbol_type=SymbolType.VARIABLE))

        # Enter policy scope
        st.enter_scope("test_policy", PolicyCategory.SAFETY)
        st.define(Symbol(name="local_var", symbol_type=SymbolType.VARIABLE))

        # Can see both
        assert st.lookup("global_var") is not None
        assert st.lookup("local_var") is not None

        # Exit scope
        st.exit_scope()

        # Can only see global
        assert st.lookup("global_var") is not None
        assert st.lookup("local_var") is None

    def test_category_indexing(self):
        """Test symbol lookup by category."""
        st = SymbolTable()

        st.define(Symbol(
            name="safety_policy",
            symbol_type=SymbolType.POLICY,
            category=PolicyCategory.SAFETY,
            priority=100,
        ))
        st.define(Symbol(
            name="privacy_policy",
            symbol_type=SymbolType.POLICY,
            category=PolicyCategory.PRIVACY,
            priority=90,
        ))

        safety_symbols = st.get_symbols_by_category(PolicyCategory.SAFETY)
        assert len(safety_symbols) == 1
        assert safety_symbols[0].name == "safety_policy"

    def test_builtin_symbols(self):
        """Test builtin symbols are available."""
        st = SymbolTable()

        # Builtins should be defined
        assert st.lookup("ctx") is not None
        assert st.lookup("contains") is not None
        assert st.lookup("len") is not None

    def test_duplicate_symbol_error(self):
        """Test error on duplicate symbol definition."""
        st = SymbolTable()

        st.define(Symbol(name="test", symbol_type=SymbolType.VARIABLE))

        with pytest.raises(ValueError):
            st.define(Symbol(name="test", symbol_type=SymbolType.VARIABLE))


class TestIRBuilder:
    """Tests for IR builder."""

    def test_build_simple_policy(self):
        """Test building IR from simple policy."""
        source = """
        policy simple: SAFETY {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast, "test_module")

        assert module.name == "test_module"
        assert len(module.functions) == 1
        assert "simple" in module.functions

        func = module.functions["simple"]
        assert func.governance.category == PolicyCategory.SAFETY

    def test_build_policy_with_condition(self):
        """Test building IR from policy with condition."""
        source = """
        policy conditional: OPERATIONAL {
            when user.requests > 100 then deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        func = module.functions["conditional"]
        # Should have multiple blocks (entry, then, else, merge)
        assert len(func.blocks) >= 2

    def test_build_multiple_policies(self):
        """Test building IR from multiple policies."""
        source = """
        policy safety_first: SAFETY { deny }
        policy privacy_next: PRIVACY { allow }
        policy custom_last: CUSTOM { allow }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        assert len(module.functions) == 3
        assert PolicyCategory.SAFETY in module.functions_by_category
        assert PolicyCategory.PRIVACY in module.functions_by_category
        assert PolicyCategory.CUSTOM in module.functions_by_category

    def test_build_with_route_action(self):
        """Test building IR from policy with route action."""
        source = """
        policy router: ROUTING {
            when agent.type == "specialist" then route to expert
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        func = module.functions["router"]
        # Find IRAction with route
        found_route = False
        for block in func.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, IRAction):
                    if instr.action == ActionType.ROUTE:
                        assert instr.target == "expert"
                        found_route = True

        assert found_route

    def test_governance_propagation(self):
        """Test governance metadata propagates through IR."""
        source = """
        policy safety_critical: SAFETY {
            deny
        }
        """
        parser = Parser.from_source(source)
        ast = parser.parse()

        builder = IRBuilder()
        module = builder.build(ast)

        func = module.functions["safety_critical"]
        assert func.governance is not None
        assert func.governance.category == PolicyCategory.SAFETY
        assert func.governance.priority == 100

        # Check action also has governance
        for block in func.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, IRAction):
                    assert instr.governance is not None
