def calibrate(score: float, evidence_count: int) -> float:
    if evidence_count == 0:
        return round(min(score, 0.55), 3)
    return round(max(0.0, min(1.0, score)), 3)
