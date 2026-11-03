"""
Regression Workflow: Production Failure to Quality Gate Test Converter
======================================================================
This tool implements the process of taking customer-reported issues,
anomalous traces, or production audit logs and converting them into
permanent regression tests in the Golden or Adversarial datasets.
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional
from framework.config import config

def load_dataset(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def save_dataset(filepath: str, data: List[Dict[str, Any]]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_golden_regression_case(
    case_id: str,
    category: str,
    input_text: str,
    expected_output: str,
    context: List[str],
    intent: str = "INQUIRY",
    urgency: str = "LOW",
    ticket_expected: bool = False
) -> Dict[str, Any]:
    """Adds a verified production edge case to datasets/golden.json."""
    dataset = load_dataset(config.GOLDEN_DATASET_PATH)

    # Prevent duplicate IDs
    existing_ids = {c.get("id") for c in dataset}
    if case_id in existing_ids:
        raise ValueError(f"Case with ID '{case_id}' already exists in golden dataset.")

    new_case = {
        "id": case_id,
        "category": category.upper(),
        "input": input_text,
        "expected_output": expected_output,
        "context": context,
        "intent": intent.upper(),
        "urgency": urgency.upper(),
        "ticket_expected": ticket_expected
    }

    dataset.append(new_case)
    save_dataset(config.GOLDEN_DATASET_PATH, dataset)
    print(f"[SUCCESS] Successfully added regression test '{case_id}' to {config.GOLDEN_DATASET_PATH}")
    return new_case

def add_adversarial_regression_case(
    case_id: str,
    attack_type: str,
    prompt: str,
    expected_refusal_keyword: str = "cannot fulfill this request"
) -> Dict[str, Any]:
    """Adds a new adversarial attack pattern to datasets/adversarial.json."""
    dataset = load_dataset(config.ADVERSARIAL_DATASET_PATH)

    existing_ids = {c.get("id") for c in dataset}
    if case_id in existing_ids:
        raise ValueError(f"Case with ID '{case_id}' already exists in adversarial dataset.")

    new_case = {
        "id": case_id,
        "attack_type": attack_type.upper(),
        "prompt": prompt,
        "expected_behavior": "REFUSE",
        "expected_refusal_keyword": expected_refusal_keyword
    }

    dataset.append(new_case)
    save_dataset(config.ADVERSARIAL_DATASET_PATH, dataset)
    print(f"[SUCCESS] Successfully added safety regression test '{case_id}' to {config.ADVERSARIAL_DATASET_PATH}")
    return new_case

def convert_production_log_entry(log_entry: Dict[str, Any], case_id: str, expected_output: str) -> Dict[str, Any]:
    """Converts a SQLite audit log entry from app/db.py into a permanent regression test."""
    context_sources = log_entry.get("rag_sources", "").split(",")
    return add_golden_regression_case(
        case_id=case_id,
        category="PROD_REGRESSION",
        input_text=log_entry.get("incoming_message", ""),
        expected_output=expected_output,
        context=[f"Authoritative policy source: {s.strip()}" for s in context_sources if s.strip()],
        intent=log_entry.get("intent", "INQUIRY"),
        urgency="HIGH" if "error" in log_entry.get("incoming_message", "").lower() else "MEDIUM",
        ticket_expected=("Ticket: NONE" not in log_entry.get("action_taken", ""))
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert production failure to regression test")
    parser.add_argument("--id", required=True, help="Test case ID (e.g. REG-2026-001)")
    parser.add_argument("--input", required=True, help="Customer input query")
    parser.add_argument("--expected", required=True, help="Expected ground truth response")
    parser.add_argument("--category", default="PROD_REGRESSION", help="Category tag")
    parser.add_argument("--context", nargs="+", default=["Company Knowledge Base"], help="Context snippets")
    parser.add_argument("--intent", default="INQUIRY", help="Expected intent")
    parser.add_argument("--urgency", default="LOW", help="Expected urgency")
    parser.add_argument("--ticket", action="store_true", help="Whether ticket is expected")

    args = parser.parse_args()
    add_golden_regression_case(
        case_id=args.id,
        category=args.category,
        input_text=args.input,
        expected_output=args.expected,
        context=args.context,
        intent=args.intent,
        urgency=args.urgency,
        ticket_expected=args.ticket
    )
