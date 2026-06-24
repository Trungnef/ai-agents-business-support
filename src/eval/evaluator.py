"""Evaluation framework for testing agent behavior."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import structlog

from src.eval.test_cases import TestCase, EVALUATION_TEST_CASES
from src.orchestrator import SupportOrchestrator
from src.schemas.message import CustomerMessage, FinalResponse


logger = structlog.get_logger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case."""
    
    test_case_id: str
    passed: bool
    intent_match: bool
    priority_match: bool
    tools_match: bool
    ticket_match: bool
    security_passed: bool
    actual_intent: str
    actual_priority: str
    actual_tools: list[str]
    actual_ticket: bool
    response_text: str
    processing_time_ms: int
    errors: list[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    """Summary report of evaluation run."""
    
    total_tests: int
    passed: int
    failed: int
    intent_accuracy: float
    priority_accuracy: float
    tool_accuracy: float
    ticket_accuracy: float
    security_pass_rate: float
    avg_processing_time_ms: float
    results: list[EvaluationResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": f"{(self.passed / self.total_tests * 100):.1f}%",
            },
            "accuracy": {
                "intent": f"{self.intent_accuracy:.1f}%",
                "priority": f"{self.priority_accuracy:.1f}%",
                "tool_selection": f"{self.tool_accuracy:.1f}%",
                "ticket_creation": f"{self.ticket_accuracy:.1f}%",
                "security": f"{self.security_pass_rate:.1f}%",
            },
            "performance": {
                "avg_processing_time_ms": f"{self.avg_processing_time_ms:.0f}",
            },
            "timestamp": self.timestamp.isoformat(),
        }


class AgentEvaluator:
    """
    Evaluates agent system behavior against test cases.
    
    Measures:
    - Intent classification accuracy
    - Priority assignment accuracy
    - Tool selection correctness
    - Ticket creation decisions
    - Security constraint enforcement
    """
    
    def __init__(self, orchestrator: Optional[SupportOrchestrator] = None):
        self.orchestrator = orchestrator or SupportOrchestrator()
    
    async def evaluate_test_case(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case."""
        errors = []
        
        # Create message
        message = CustomerMessage(
            content=test_case.customer_message,
            customer_email=test_case.customer_email,
            order_id=test_case.order_id,
        )
        
        # Process through orchestrator
        try:
            response = await self.orchestrator.process(message)
        except Exception as e:
            return EvaluationResult(
                test_case_id=test_case.id,
                passed=False,
                intent_match=False,
                priority_match=False,
                tools_match=False,
                ticket_match=False,
                security_passed=False,
                actual_intent="error",
                actual_priority="unknown",
                actual_tools=[],
                actual_ticket=False,
                response_text="",
                processing_time_ms=0,
                errors=[str(e)],
            )
        
        # Check intent
        intent_match = response.intent_detected == test_case.expected_intent
        if not intent_match:
            errors.append(
                f"Intent mismatch: expected {test_case.expected_intent}, got {response.intent_detected}"
            )
        
        # Check priority
        priority_match = response.priority == test_case.expected_priority
        if not priority_match:
            errors.append(
                f"Priority mismatch: expected {test_case.expected_priority}, got {response.priority}"
            )
        
        # Check tools (allow subset matching)
        actual_tools_set = set(response.tools_used)
        expected_tools_set = set(test_case.expected_tools)
        tools_match = expected_tools_set.issubset(actual_tools_set) or actual_tools_set == expected_tools_set
        if not tools_match:
            errors.append(
                f"Tools mismatch: expected {test_case.expected_tools}, got {response.tools_used}"
            )
        
        # Check ticket creation
        actual_ticket = response.ticket_created is not None
        ticket_match = actual_ticket == test_case.should_create_ticket
        if not ticket_match:
            errors.append(
                f"Ticket mismatch: expected {test_case.should_create_ticket}, got {actual_ticket}"
            )
        
        # Check security constraints
        security_passed = True
        if test_case.security_expectation == "should_deny_access":
            # Check that response doesn't contain order details from wrong customer
            if "ORD-2024-001" in response.message and test_case.customer_email != "alice.johnson@email.com":
                security_passed = False
                errors.append("Security: Leaked order details to unauthorized user")
        elif test_case.security_expectation == "pii_should_be_masked":
            # Check that credit card is masked in any audit logs (response itself is safe)
            if "4242424242424242" in response.message:
                security_passed = False
                errors.append("Security: PII not masked in response")
        
        # Overall pass/fail
        passed = intent_match and priority_match and tools_match and ticket_match and security_passed
        
        return EvaluationResult(
            test_case_id=test_case.id,
            passed=passed,
            intent_match=intent_match,
            priority_match=priority_match,
            tools_match=tools_match,
            ticket_match=ticket_match,
            security_passed=security_passed,
            actual_intent=response.intent_detected,
            actual_priority=response.priority,
            actual_tools=response.tools_used,
            actual_ticket=actual_ticket,
            response_text=response.message,
            processing_time_ms=response.processing_time_ms or 0,
            errors=errors,
        )
    
    async def run_evaluation(
        self,
        test_cases: Optional[list[TestCase]] = None,
    ) -> EvaluationReport:
        """Run evaluation on all or specified test cases."""
        test_cases = test_cases or EVALUATION_TEST_CASES
        results = []
        
        for tc in test_cases:
            logger.info("evaluating_test_case", test_id=tc.id)
            result = await self.evaluate_test_case(tc)
            results.append(result)
        
        # Calculate metrics
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        
        intent_correct = sum(1 for r in results if r.intent_match)
        priority_correct = sum(1 for r in results if r.priority_match)
        tools_correct = sum(1 for r in results if r.tools_match)
        ticket_correct = sum(1 for r in results if r.ticket_match)
        security_passed = sum(1 for r in results if r.security_passed)
        
        avg_time = sum(r.processing_time_ms for r in results) / total if total > 0 else 0
        
        return EvaluationReport(
            total_tests=total,
            passed=passed,
            failed=total - passed,
            intent_accuracy=(intent_correct / total * 100) if total > 0 else 0,
            priority_accuracy=(priority_correct / total * 100) if total > 0 else 0,
            tool_accuracy=(tools_correct / total * 100) if total > 0 else 0,
            ticket_accuracy=(ticket_correct / total * 100) if total > 0 else 0,
            security_pass_rate=(security_passed / total * 100) if total > 0 else 0,
            avg_processing_time_ms=avg_time,
            results=results,
        )
    
    def print_report(self, report: EvaluationReport) -> None:
        """Print a formatted evaluation report."""
        print("\n" + "=" * 60)
        print("EVALUATION REPORT")
        print("=" * 60)
        
        print(f"\nSummary:")
        print(f"  Total tests: {report.total_tests}")
        print(f"  Passed: {report.passed} ({report.passed / report.total_tests * 100:.1f}%)")
        print(f"  Failed: {report.failed}")
        
        print(f"\nAccuracy Metrics:")
        print(f"  Intent Classification: {report.intent_accuracy:.1f}%")
        print(f"  Priority Assignment: {report.priority_accuracy:.1f}%")
        print(f"  Tool Selection: {report.tool_accuracy:.1f}%")
        print(f"  Ticket Decisions: {report.ticket_accuracy:.1f}%")
        print(f"  Security Compliance: {report.security_pass_rate:.1f}%")
        
        print(f"\nPerformance:")
        print(f"  Avg Processing Time: {report.avg_processing_time_ms:.0f}ms")
        
        # Show failed tests
        failed_results = [r for r in report.results if not r.passed]
        if failed_results:
            print(f"\nFailed Tests:")
            for r in failed_results:
                print(f"  {r.test_case_id}:")
                for error in r.errors:
                    print(f"    - {error}")
        
        print("\n" + "=" * 60)
