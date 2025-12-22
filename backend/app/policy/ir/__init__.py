# M20 Policy IR - Intermediate Representation
# Category-aware IR for policy compilation
#
# IR v2.0 features:
# - M19 category awareness
# - Governance metadata propagation
# - Symbol table with policy hierarchy
# - SSA-like form for optimization

from app.policy.ir.ir_builder import (
    IRBuilder,
)
from app.policy.ir.ir_nodes import (
    IRAction,
    IRBinaryOp,
    # Blocks
    IRBlock,
    IRCall,
    IRCheckPolicy,
    IRCompare,
    IREmitIntent,
    IRFunction,
    # Metadata
    IRGovernance,
    # Instructions
    IRInstruction,
    IRJump,
    IRJumpIf,
    IRLoadConst,
    IRLoadVar,
    IRModule,
    # Base
    IRNode,
    IRReturn,
    IRStoreVar,
    IRType,
    IRUnaryOp,
)
from app.policy.ir.symbol_table import (
    Scope,
    Symbol,
    SymbolTable,
    SymbolType,
)

__all__ = [
    # Base
    "IRNode",
    "IRType",
    # Instructions
    "IRInstruction",
    "IRLoadConst",
    "IRLoadVar",
    "IRStoreVar",
    "IRBinaryOp",
    "IRUnaryOp",
    "IRCompare",
    "IRJump",
    "IRJumpIf",
    "IRCall",
    "IRReturn",
    "IRAction",
    "IRCheckPolicy",
    "IREmitIntent",
    # Blocks
    "IRBlock",
    "IRFunction",
    "IRModule",
    # Metadata
    "IRGovernance",
    # Symbol table
    "Symbol",
    "SymbolType",
    "SymbolTable",
    "Scope",
    # Builder
    "IRBuilder",
]
