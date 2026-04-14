from __future__ import annotations


def score_response(reply: str) -> float:
    if not reply.strip():
        return 0.0
    return 1.0
