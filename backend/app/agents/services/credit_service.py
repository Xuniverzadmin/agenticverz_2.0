# M12 Credit Service
# Per-skill and per-item credit billing with reservation, spend, and refund
#
# Credit Pricing:
# - agent_spawn: 5 credits
# - agent_invoke: 10 credits
# - blackboard_read: 1 credit
# - blackboard_write: 1 credit
# - blackboard_lock: 2 credits
# - agent_message: 2 credits
# - per job_item: 2 credits (reserved, refund on failure)

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("nova.agents.credit_service")

# Credit costs per skill
CREDIT_COSTS = {
    "agent_spawn": Decimal("5"),
    "agent_invoke": Decimal("10"),
    "blackboard_read": Decimal("1"),
    "blackboard_write": Decimal("1"),
    "blackboard_lock": Decimal("2"),
    "agent_message": Decimal("2"),
    "job_item": Decimal("2"),  # Per item cost
}


@dataclass
class CreditBalance:
    """Current credit balance for a tenant."""
    tenant_id: str
    total_credits: Decimal
    reserved_credits: Decimal
    spent_credits: Decimal
    available_credits: Decimal


@dataclass
class CreditOperation:
    """Result of a credit operation."""
    success: bool
    operation: str  # reserve, spend, refund
    amount: Decimal
    balance_after: Optional[Decimal] = None
    reason: Optional[str] = None


class CreditService:
    """
    Credit management for M12 multi-agent system.

    Supports:
    - Pre-flight credit checks
    - Per-item credit reservation
    - Skill-level deductions
    - Failure refunds
    - Credit ledger tracking
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for CreditService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)

    def get_skill_cost(self, skill: str) -> Decimal:
        """Get credit cost for a skill."""
        return CREDIT_COSTS.get(skill, Decimal("1"))

    def check_credits(
        self,
        tenant_id: str,
        required_credits: Decimal,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if tenant has sufficient credits.

        Args:
            tenant_id: Tenant to check
            required_credits: Credits needed

        Returns:
            Tuple of (has_credits, reason_if_not)
        """
        balance = self.get_balance(tenant_id)
        if balance is None:
            # No balance record = unlimited credits (for testing)
            return True, None

        if balance.available_credits >= required_credits:
            return True, None

        return False, f"Insufficient credits: {balance.available_credits} available, need {required_credits}"

    def get_balance(self, tenant_id: str) -> Optional[CreditBalance]:
        """Get current credit balance for tenant."""
        with self.Session() as session:
            try:
                # Check if credit_balances table exists
                result = session.execute(
                    text("""
                        SELECT total_credits, reserved_credits, spent_credits
                        FROM agents.credit_balances
                        WHERE tenant_id = :tenant_id
                    """),
                    {"tenant_id": tenant_id}
                )
                row = result.fetchone()

                if not row:
                    return None

                total = Decimal(str(row[0]))
                reserved = Decimal(str(row[1]))
                spent = Decimal(str(row[2]))

                return CreditBalance(
                    tenant_id=tenant_id,
                    total_credits=total,
                    reserved_credits=reserved,
                    spent_credits=spent,
                    available_credits=total - reserved - spent,
                )
            except Exception as e:
                # Table might not exist yet
                logger.debug(f"Credit balance check failed: {e}")
                return None

    def check_reservation(
        self,
        tenant_id: str,
        item_count: int,
        skill_cost: Decimal = CREDIT_COSTS["agent_spawn"],
    ) -> CreditOperation:
        """
        Pre-flight check: verify tenant has sufficient credits for a job.

        This is called BEFORE job creation to validate credits.

        Args:
            tenant_id: Tenant to check
            item_count: Number of items
            skill_cost: Base spawn cost

        Returns:
            CreditOperation with result (amount = total needed)
        """
        item_credits = CREDIT_COSTS["job_item"] * item_count
        total_reserve = skill_cost + item_credits

        # Check available credits
        has_credits, reason = self.check_credits(tenant_id, total_reserve)
        if not has_credits:
            return CreditOperation(
                success=False,
                operation="check",
                amount=total_reserve,
                reason=reason,
            )

        return CreditOperation(
            success=True,
            operation="check",
            amount=total_reserve,
        )

    def log_reservation(
        self,
        job_id: UUID,
        tenant_id: str,
        amount: Decimal,
    ) -> CreditOperation:
        """
        Log credit reservation to the ledger.

        MUST be called AFTER job creation to avoid FK violation.

        Args:
            job_id: Job that was just created
            tenant_id: Tenant being charged
            amount: Amount reserved

        Returns:
            CreditOperation with result
        """
        with self.Session() as session:
            try:
                # Log the reservation to credit_ledger
                session.execute(
                    text("""
                        INSERT INTO agents.credit_ledger (
                            job_id, tenant_id, operation, skill, amount, created_at
                        ) VALUES (
                            CAST(:job_id AS UUID), :tenant_id, 'reserve', 'agent_spawn', :amount, now()
                        )
                    """),
                    {
                        "job_id": str(job_id),
                        "tenant_id": tenant_id,
                        "amount": float(amount),
                    }
                )

                session.commit()

                logger.info(
                    "credits_reserved",
                    extra={
                        "job_id": str(job_id),
                        "tenant_id": tenant_id,
                        "amount": float(amount),
                    }
                )

                return CreditOperation(
                    success=True,
                    operation="reserve",
                    amount=amount,
                )

            except Exception as e:
                session.rollback()
                logger.warning(f"Credit ledger insert failed: {e}")
                # Don't fail the operation - ledger is for auditing
                return CreditOperation(
                    success=True,
                    operation="reserve",
                    amount=amount,
                    reason=f"Ledger logging bypassed: {str(e)[:50]}",
                )

    def reserve_for_job(
        self,
        job_id: UUID,
        tenant_id: str,
        item_count: int,
        skill_cost: Decimal = CREDIT_COSTS["agent_spawn"],
    ) -> CreditOperation:
        """
        DEPRECATED: Use check_reservation() before job creation
        and log_reservation() after job creation.

        This method is kept for backwards compatibility but uses
        the new split approach internally.
        """
        # Pre-flight check
        check_result = self.check_reservation(tenant_id, item_count, skill_cost)
        if not check_result.success:
            return check_result

        # Log reservation (job_id may not exist yet - this is legacy behavior)
        return self.log_reservation(job_id, tenant_id, check_result.amount)

    def spend_for_item(
        self,
        job_id: UUID,
        item_id: UUID,
        tenant_id: str,
    ) -> CreditOperation:
        """
        Deduct credits for completed item.

        Called when a job item completes successfully.
        """
        amount = CREDIT_COSTS["job_item"]

        with self.Session() as session:
            try:
                # Update job credits_spent
                session.execute(
                    text("""
                        UPDATE agents.jobs
                        SET credits_spent = credits_spent + :amount
                        WHERE id = :job_id
                    """),
                    {
                        "job_id": str(job_id),
                        "amount": float(amount),
                    }
                )

                session.commit()

                return CreditOperation(
                    success=True,
                    operation="spend",
                    amount=amount,
                )

            except Exception as e:
                session.rollback()
                logger.warning(f"Credit spend failed: {e}")
                return CreditOperation(
                    success=True,  # Don't block on credit errors
                    operation="spend",
                    amount=amount,
                    reason=str(e)[:100],
                )

    def refund_for_item(
        self,
        job_id: UUID,
        item_id: UUID,
        tenant_id: str,
    ) -> CreditOperation:
        """
        Refund credits for failed item.

        Called when a job item fails.
        """
        amount = CREDIT_COSTS["job_item"]

        with self.Session() as session:
            try:
                # Update job credits_refunded
                session.execute(
                    text("""
                        UPDATE agents.jobs
                        SET credits_refunded = credits_refunded + :amount
                        WHERE id = :job_id
                    """),
                    {
                        "job_id": str(job_id),
                        "amount": float(amount),
                    }
                )

                session.commit()

                logger.info(
                    "credits_refunded",
                    extra={
                        "job_id": str(job_id),
                        "item_id": str(item_id),
                        "amount": float(amount),
                    }
                )

                return CreditOperation(
                    success=True,
                    operation="refund",
                    amount=amount,
                )

            except Exception as e:
                session.rollback()
                logger.warning(f"Credit refund failed: {e}")
                return CreditOperation(
                    success=True,
                    operation="refund",
                    amount=amount,
                    reason=str(e)[:100],
                )

    def charge_skill(
        self,
        skill: str,
        tenant_id: str,
        job_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CreditOperation:
        """
        Charge credits for a skill invocation.

        Args:
            skill: Skill name (agent_invoke, blackboard_read, etc.)
            tenant_id: Tenant to charge
            job_id: Optional job context
            context: Optional additional context

        Returns:
            CreditOperation result
        """
        amount = self.get_skill_cost(skill)

        # Check credits
        has_credits, reason = self.check_credits(tenant_id, amount)
        if not has_credits:
            return CreditOperation(
                success=False,
                operation="charge",
                amount=amount,
                reason=reason,
            )

        with self.Session() as session:
            try:
                # Log to ledger
                session.execute(
                    text("""
                        INSERT INTO agents.credit_ledger (
                            job_id, tenant_id, operation, skill, amount, context, created_at
                        ) VALUES (
                            CAST(:job_id AS UUID), :tenant_id, 'charge', :skill, :amount,
                            CAST(:context AS JSONB), now()
                        )
                    """),
                    {
                        "job_id": str(job_id) if job_id else None,
                        "tenant_id": tenant_id,
                        "skill": skill,
                        "amount": float(amount),
                        "context": "{}" if not context else str(context),
                    }
                )

                session.commit()

                return CreditOperation(
                    success=True,
                    operation="charge",
                    amount=amount,
                )

            except Exception as e:
                session.rollback()
                logger.debug(f"Credit charge logging failed: {e}")
                # Don't block on credit logging errors
                return CreditOperation(
                    success=True,
                    operation="charge",
                    amount=amount,
                )


# Singleton instance
_service: Optional[CreditService] = None


def get_credit_service() -> CreditService:
    """Get singleton credit service instance."""
    global _service
    if _service is None:
        _service = CreditService()
    return _service
