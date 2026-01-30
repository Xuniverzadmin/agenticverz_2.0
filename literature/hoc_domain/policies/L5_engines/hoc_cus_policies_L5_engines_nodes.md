# hoc_cus_policies_L5_engines_nodes

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/nodes.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy AST node definitions (pure data structures)

## Intent

**Role:** Policy AST node definitions (pure data structures)
**Reference:** PIN-470, Policy System
**Callers:** policy/compiler, policy/engine

## Purpose

AST nodes for PLang v2.0.

---

## Classes

### `GovernanceMetadata`
- **Docstring:** M19 Governance metadata attached to AST nodes.
- **Methods:** merge_with
- **Class Variables:** category: PolicyCategory, priority: int, source_policy: Optional[str], source_rule: Optional[str], provenance: Optional[str]

### `ASTNode(ABC)`
- **Docstring:** Base class for all AST nodes.
- **Methods:** accept, location
- **Class Variables:** line: int, column: int, governance: Optional[GovernanceMetadata]

### `ExprNode(ASTNode)`
- **Docstring:** Base class for expression nodes.

### `ProgramNode(ASTNode)`
- **Docstring:** Root node representing a complete PLang program.
- **Methods:** accept
- **Class Variables:** statements: List[ASTNode]

### `PolicyDeclNode(ASTNode)`
- **Docstring:** Policy declaration node.
- **Methods:** __post_init__, accept
- **Class Variables:** name: str, category: PolicyCategory, body: List[ASTNode]

### `RuleDeclNode(ASTNode)`
- **Docstring:** Rule declaration node.
- **Methods:** __post_init__, accept
- **Class Variables:** name: str, category: PolicyCategory, body: List[ASTNode]

### `ImportNode(ASTNode)`
- **Docstring:** Import statement node.
- **Methods:** accept
- **Class Variables:** path: str

### `RuleRefNode(ASTNode)`
- **Docstring:** Reference to a named rule.
- **Methods:** accept
- **Class Variables:** name: str

### `PriorityNode(ASTNode)`
- **Docstring:** Priority declaration node.
- **Methods:** accept
- **Class Variables:** value: int

### `ConditionBlockNode(ASTNode)`
- **Docstring:** When/then condition block.
- **Methods:** accept
- **Class Variables:** condition: Optional[ExprNode], action: Optional['ActionBlockNode']

### `ActionBlockNode(ASTNode)`
- **Docstring:** Action block (deny, allow, escalate, route).
- **Methods:** accept
- **Class Variables:** action: ActionType, target: Optional['RouteTargetNode']

### `RouteTargetNode(ASTNode)`
- **Docstring:** Route target specification.
- **Methods:** accept
- **Class Variables:** target: str

### `BinaryOpNode(ExprNode)`
- **Docstring:** Binary operation (and, or, ==, !=, etc.).
- **Methods:** accept
- **Class Variables:** op: str, left: Optional[ExprNode], right: Optional[ExprNode]

### `UnaryOpNode(ExprNode)`
- **Docstring:** Unary operation (not).
- **Methods:** accept
- **Class Variables:** op: str, operand: Optional[ExprNode]

### `ValueNode(ExprNode)`
- **Docstring:** Base class for value nodes.

### `IdentNode(ValueNode)`
- **Docstring:** Identifier node.
- **Methods:** accept
- **Class Variables:** name: str

### `LiteralNode(ValueNode)`
- **Docstring:** Literal value node (number, string, boolean).
- **Methods:** accept
- **Class Variables:** value: Any

### `FuncCallNode(ExprNode)`
- **Docstring:** Function call node.
- **Methods:** accept
- **Class Variables:** callee: Optional[ExprNode], args: List[ExprNode]

### `AttrAccessNode(ExprNode)`
- **Docstring:** Attribute access node (obj.attr).
- **Methods:** accept
- **Class Variables:** obj: Optional[ExprNode], attr: str

### `ASTVisitor(ABC)`
- **Docstring:** Abstract base class for AST visitors.
- **Methods:** visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.compiler.grammar` |

## Callers

policy/compiler, policy/engine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GovernanceMetadata
      methods: [merge_with]
    - name: ASTNode
      methods: [accept, location]
    - name: ExprNode
      methods: []
    - name: ProgramNode
      methods: [accept]
    - name: PolicyDeclNode
      methods: [accept]
    - name: RuleDeclNode
      methods: [accept]
    - name: ImportNode
      methods: [accept]
    - name: RuleRefNode
      methods: [accept]
    - name: PriorityNode
      methods: [accept]
    - name: ConditionBlockNode
      methods: [accept]
    - name: ActionBlockNode
      methods: [accept]
    - name: RouteTargetNode
      methods: [accept]
    - name: BinaryOpNode
      methods: [accept]
    - name: UnaryOpNode
      methods: [accept]
    - name: ValueNode
      methods: []
    - name: IdentNode
      methods: [accept]
    - name: LiteralNode
      methods: [accept]
    - name: FuncCallNode
      methods: [accept]
    - name: AttrAccessNode
      methods: [accept]
    - name: ASTVisitor
      methods: [visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
