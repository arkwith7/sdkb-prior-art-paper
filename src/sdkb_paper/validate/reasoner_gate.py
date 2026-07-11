"""OWL 일관성(consistency) 게이트 — owlready2 + HermiT.

주의: HermiT 리즈너는 Java 가 필요하다 (로컬/Colab: apt-get install default-jre).
CI 에서는 무겁기 때문에 기본적으로 로컬/주차 마일스톤 시점에만 실행.

CLI:  python -m sdkb_paper.validate.reasoner_gate <ontology.owl|ttl>
"""
from __future__ import annotations

import sys


def check_consistency(path: str) -> bool:
    from owlready2 import OwlReadyInconsistentOntologyError, get_ontology, sync_reasoner

    onto = get_ontology(f"file://{path}").load()
    try:
        with onto:
            sync_reasoner()  # HermiT
        return True
    except OwlReadyInconsistentOntologyError:
        return False


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m sdkb_paper.validate.reasoner_gate <ontology-file>")
        sys.exit(2)
    ok = check_consistency(sys.argv[1])
    print(f"[reasoner_gate] consistent = {ok}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
