import os
import json
import pytest
from app.agent import process_incoming_event
from framework.config import config
from framework.base_evaluator import evaluate_response_quality
from tests.conftest import SESSION_METRICS

def load_golden_cases():
    with open(config.GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

GOLDEN_CASES = load_golden_cases()

class TestDeepEvalRAGQuality:

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
    def test_golden_dataset_quality_gate(self, case):
        """
        Evaluates System Under Test (AIVOA Ops Agent) on the Golden Dataset.
        Enforces Faithfulness >= 0.70, Relevancy >= 0.70, and Hallucination <= 0.30.
        """
        query = case["input"]
        sender = f"test_{case['id'].lower()}@customer.com"
        expected_intent = case["intent"]
        expected_ticket = case["ticket_expected"]

        # Run the agent pipeline
        result = process_incoming_event(
            incoming_text=query,
            sender=sender,
            channel="email"
        )

        response_text = result["response"]
        retrieved_context = case["context"]

        # Evaluate RAG Quality Metrics
        eval_result = evaluate_response_quality(
            input_text=query,
            actual_output=response_text,
            retrieval_context=retrieved_context,
            expected_output=case.get("expected_output")
        )

        # Record metrics for report generation
        SESSION_METRICS["eval_cases"].append({
            "id": case["id"],
            "category": case.get("category", "GENERAL"),
            "input": query,
            "faithfulness": eval_result.faithfulness,
            "answer_relevancy": eval_result.answer_relevancy,
            "hallucination": eval_result.hallucination,
            "passed": eval_result.passed
        })

        # Quality Gate Assertions
        assert eval_result.faithfulness >= config.FAITHFULNESS_THRESHOLD, (
            f"[{case['id']}] Faithfulness score {eval_result.faithfulness:.2f} "
            f"fell below minimum quality gate threshold of {config.FAITHFULNESS_THRESHOLD}!"
        )

        assert eval_result.answer_relevancy >= config.ANSWER_RELEVANCY_THRESHOLD, (
            f"[{case['id']}] Answer Relevancy score {eval_result.answer_relevancy:.2f} "
            f"fell below minimum quality gate threshold of {config.ANSWER_RELEVANCY_THRESHOLD}!"
        )

        assert eval_result.hallucination <= config.HALLUCINATION_MAX_THRESHOLD, (
            f"[{case['id']}] Hallucination score {eval_result.hallucination:.2f} "
            f"exceeded maximum tolerance threshold of {config.HALLUCINATION_MAX_THRESHOLD}!"
        )

        # Functional Routing Assertions
        assert result["intent"] == expected_intent, (
            f"[{case['id']}] Expected intent '{expected_intent}', but got '{result['intent']}'."
        )

        if expected_ticket:
            assert result.get("ticket") is not None, (
                f"[{case['id']}] Expected support ticket creation, but no ticket was generated."
            )
