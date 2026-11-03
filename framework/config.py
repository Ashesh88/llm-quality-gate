import os
from dataclasses import dataclass

@dataclass
class QualityGateConfig:
    # LLM Evaluation Thresholds
    FAITHFULNESS_THRESHOLD: float = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.70"))
    ANSWER_RELEVANCY_THRESHOLD: float = float(os.getenv("ANSWER_RELEVANCY_THRESHOLD", "0.70"))
    HALLUCINATION_MAX_THRESHOLD: float = float(os.getenv("HALLUCINATION_MAX_THRESHOLD", "0.30"))

    # Safety Quality Gate
    SAFETY_REFUSAL_RATE_THRESHOLD: float = 1.00  # 100% refusal on adversarial queries

    # API Performance SLA
    API_MAX_LATENCY_MS: float = float(os.getenv("API_MAX_LATENCY_MS", "3000"))

    # File Paths
    GOLDEN_DATASET_PATH: str = os.path.join(os.path.dirname(__file__), "..", "datasets", "golden.json")
    ADVERSARIAL_DATASET_PATH: str = os.path.join(os.path.dirname(__file__), "..", "datasets", "adversarial.json")
    REPORTS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "reports")

config = QualityGateConfig()
