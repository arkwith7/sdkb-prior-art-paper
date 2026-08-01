"""서지상세 원응답 → B층이 판정에 쓰는 네 값 (PLAN-032 §5.1 ④).

한 콜에서 **포함 2(심사관 인용 ≥1) · 포함 3(claim1) · 배제 3(NPL 전용) · 포함 1 확정
(`status_empty` 건의 행정상태)** 을 전부 읽는다. 콜을 나누면 예산이 배로 든다.

**NPL 판정 규칙(구현 동결 · PLAN-032 §7).** KIPRIS 는 특허문헌/비특허문헌을 구분하는 필드를
주지 않는다 — 인용 식별자 문자열만 준다. A층 실측 형식은 `KR1020190085654 A`·`US20190348292 A1`
(국가 2자 + 숫자 6자 이상 + 종별)이므로 **정규화 후 `^[A-Z]{2}\\d{6,}` 에 맞으면 특허문헌**,
아니면 비특허문헌으로 센다. 규칙을 나중에 느슨하게 고치면 배제 3의 분모가 바뀌므로 동결한다.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# 인용 식별자에서 공백·하이픈·점을 지운 뒤 판정한다(`KR 10-2019-0085654 A` → `KR1020190085654A`).
_SEP_RE = re.compile(r"[\s\-.,/()]+")
_PATENT_RE = re.compile(r"^[A-Z]{2}\d{6,}")
# 인용 번호 태그의 별칭 (엔드포인트 판올림 방어 — 이름이 바뀌면 조용히 0건이 되는 것이 최악이다).
_DOC_TAGS = ("documentsNumber", "documentNumber", "docNumber")
_FLAG_TAGS = ("examinerQuotationFlag", "examinerQuotationYn", "examinerQuotationYN")
_ART_TAGS = ("priorArtDocumentsInfo", "priorArtDocumentInfo", "priorArtDocuments", "priorArtDocument")
_STATUS_TAGS = ("finalDisposal", "examinationStatus", "examinationDocStatus")


@dataclass(frozen=True)
class Biblio:
    """판정에 필요한 것만 담는다 — **원문 청구항은 담지 않는다**(채택분만 별도 보관)."""

    application_number: str
    examiner_citations: tuple[str, ...]   # 심사관 인용(플래그 Y)만. 봉인 대상 = qrel 원천
    npl_only: bool                        # 인용이 전부 비특허문헌인가 (배제 3)
    claim1: str                           # 독립항 1 전문 (포함 3)
    examination_status: str               # 행정상태 (포함 1 확정용)


def is_patent_document(cited: str) -> bool:
    """인용 식별자가 특허문헌인가. 규칙은 모듈 docstring 에 동결."""
    return bool(_PATENT_RE.match(_SEP_RE.sub("", cited).upper()))


def _tag(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _first_text(root: ET.Element, names: tuple[str, ...]) -> str:
    """이름 후보 중 **먼저 나오는 비어있지 않은** 값. 문서 순서를 따르므로 결정적."""
    for el in root.iter():
        if _tag(el) in names and (el.text or "").strip():
            return el.text.strip()
    return ""


def _claim1(root: ET.Element) -> str:
    """`claimInfo` 의 첫 청구항. `1.`/`1 ` 로 시작하는 것을 우선하고, 없으면 첫 항."""
    claims = [
        (el.text or "").strip()
        for el in root.iter()
        if _tag(el) in ("claim", "claimText") and (el.text or "").strip()
    ]
    for text in claims:
        if text.startswith(("1.", "1 ")):
            return text
    return claims[0] if claims else ""


def parse_biblio(body: str, application_number: str) -> Biblio:
    root = ET.fromstring(body)

    examiner: list[str] = []
    non_examiner_seen = False
    for art in root.iter():
        if _tag(art) not in _ART_TAGS:
            continue
        cited = ""
        flag = ""
        for child in art.iter():
            name = _tag(child)
            text = (child.text or "").strip()
            if not text:
                continue
            if name in _DOC_TAGS and not cited:
                cited = text
            elif name in _FLAG_TAGS and not flag:
                flag = text.upper()
        if not cited:
            continue
        if flag == "Y":
            examiner.append(cited)
        else:
            non_examiner_seen = True
    _ = non_examiner_seen  # 심사관 인용만이 §3 포함 2의 대상이다 — 출원인 인용은 세지 않는다.

    # 배제 3: **심사관 인용이 있는데 전부 비특허문헌**인 경우. 인용 0건은 포함 2가 먼저 잡는다.
    npl_only = bool(examiner) and not any(is_patent_document(c) for c in examiner)

    return Biblio(
        application_number=application_number,
        examiner_citations=tuple(examiner),
        npl_only=npl_only,
        claim1=_claim1(root),
        examination_status=_first_text(root, _STATUS_TAGS),
    )
