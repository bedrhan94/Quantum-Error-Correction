"""The paper's concrete examples, transcribed as *claims to be tested* (with page references).

Nothing here is used as a computed result; ``claimed`` values are only compared against
enumeration.  Page numbers refer to the published PDF (FFA 117 (2027) 102881).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaperExample:
    key: str
    q: int
    alpha1: tuple[int, int]  # C1 = <alpha1>
    alpha2: tuple[int, int]  # C2 = <alpha2>
    claimed: dict = field(default_factory=dict)
    eps_sets: dict = field(default_factory=dict)  # name -> list of (a, b) as printed
    source: str = ""


PAPER_EXAMPLES: dict[str, PaperExample] = {
    "Z25": PaperExample(
        key="Z25",
        q=25,
        alpha1=(3, 4),
        alpha2=(2, 1),
        claimed={
            "size_C1": 25,
            "size_C2": 125,
            "index": 5,
            "K": 5,
            "dual_generator": (10, 5),  # Example 7: C2^perpH = <10+5i>
            "size_dual": 5,  # Example 7 / Table 1
            "decode_example": {"y": (11, 8), "e": (8, 4), "c": (3, 4)},  # Example 8, p.16-17
            "decode_example_ex5": {"y": (2, 1), "e": (0, 15), "c": (2, 11)},  # Example 5, p.9-10
        },
        eps_sets={
            # Example 4 (p.8): {0, 10, 10i, 15i, -20i}
            "paper_example4": [(0, 0), (10, 0), (0, 10), (0, 15), (0, -20)],
            # Example 7/8 (p.15-16): {0, 2+i, 4+2i, 6+3i, 8+4i}
            "paper_example7": [(0, 0), (2, 1), (4, 2), (6, 3), (8, 4)],
        },
        source="Examples 4, 5, 7, 8; Tables 1-3",
    ),
    "Z85": PaperExample(
        key="Z85",
        q=85,
        alpha1=(7, 6),
        alpha2=(2, 1),
        claimed={"size_C1": 85, "size_C2": 1445, "index": 17, "K": 17, "size_dual": 5},
        eps_sets={},  # the paper prints no explicit eps for Z85
        source="Tables 1-3 (no worked example in the text)",
    ),
    "Z325": PaperExample(
        key="Z325",
        q=325,
        alpha1=(4, 7),
        alpha2=(3, 2),
        claimed={
            "size_C1": 1625,
            "size_C2": 8125,
            "index": 5,
            "K": 5,
            "dual_generator": (75, 50),  # Example 6: C2^perpH = <25 alpha2> = <75+50i>
            "size_dual": 13,
        },
        eps_sets={"paper_example6": [(0, 0), (3, 2), (6, 4), (9, 6), (12, 8)]},
        source="Example 6 (p.13-14); Tables 2-3",
    ),
}

# Table 1 / 2 / 3 row for Z_9 (not a Gaussian integer ring; checked separately)
Z9_CLAIMS = {"size_C1": 3, "size_C2": 9, "index": 3, "size_dual": 3, "K_table2": 1}

# Remark 8 (p.18-19): multi-qudit example over Z_5[i]^4, generators NOT given in the paper
Z5_N4_CLAIMS = {"q": 5, "n": 4, "size_C2": 5**6, "size_C1": 5**4, "size_dual": 25, "K": 25}
