"""서술문 → 온톨로지 개념 앵커링 → SPARQL 생성.

실무자는 키워드가 아니라 **문장**으로 문제를 말한다("에칭 균일도를 78%→93% 로 올려야 한다").
이 모듈은 그 문장에서 **그래프 자신의 어휘**(prefLabel·altLabel)만을 근거로 개념을 집어낸다.
사전을 그래프에서 만들기 때문에 어휘를 발명하지 않고, 앵커가 IRI 이므로 생성 쿼리에
사용자 문자열이 보간되지 않는다(리터럴 인젝션 경로 소멸).

결정적이다 — 같은 문장·같은 그래프면 같은 앵커·같은 쿼리가 나온다. LLM 을 부르지 않는다.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, replace

from sdkb_paper.explore.store import run_query

ONT = "https://w3id.org/sdkb/ont/"

# 앵커 사전에 넣을 클래스. 특허·거절특허·조직 제목은 **제외**한다 —
# G₀ prefLabel 3,334 중 2,000 이 특허 제목이고 그 토큰(및·방법·장치)은 순수 노이즈다.
ANCHOR_CLASSES = (
    "Process",
    "SubProcess",
    "Device",
    "Skill",
    "FailureMode",
    "Material",
    "Equipment",
    "EquipmentClass",
    "Problem",
    "RootCause",
    "Mitigation",
    "Concept",
)

# 질의 경로를 가진 축만 쿼리 생성에 쓴다. 나머지는 표시만 한다.
QUERYABLE = ("Process", "SubProcess", "Device", "Skill", "FailureMode", "Problem")

_WORD = re.compile(r"[A-Za-z0-9가-힣]+(?:-[A-Za-z0-9가-힣]+)*")

# 영문 기능어. 도메인 무관하게 항상 무의미하다(코퍼스 빈도로는 걸러지지 않는다 —
# 사전이 영문 명사구 위주라 'to'·'we' 는 사전 빈도가 0 이다).
_FUNCTION_WORDS = frozenset(
    # 'doe' 는 넣지 않는다 — does 의 어간이지만 동시에 실험계획법(DOE Analysis)이다.
    """a an and are as at be been better by can could current do does for from
    had has have how in is it its key more most need not of on or our out should so
    that the their there these this to us use used using was we were what when where
    which who will with would you your 및 그 이 를 을 은 는 의 에 와 과 하는 위한 이를""".split()
)

# 사전 문서빈도가 이 비율을 넘는 토큰은 변별력이 없다고 보고 자동 배제한다.
# (예: 사전이 특허 제목을 포함하게 되면 '방법'·'장치'가 여기서 걸린다)
# G₀ 사전 599항목 기준 상한 ≈ 18 — 머리명사 'process'(27) 는 걸러지고
# 개념 이름 'cmp'(45)·'deposition'(44) 은 아래 면제로 살아남는다.
_DF_MAX_RATIO = 0.03

# 서술형 라벨 클래스 — 주제어 불일치를 배제 근거로 삼는다(분류 축에는 적용하지 않는다).
_NARRATIVE = frozenset({"Problem", "RootCause", "Mitigation"})

# 앵커 채택 임계. 라벨 토큰의 절반 이상이 문장에 있어야 한다.
_MIN_SCORE = 0.5
# 클래스당 채택 상한 — 데모 화면이 칩으로 뒤덮이지 않게.
_TOP_PER_CLASS = 5

_lexicons: dict[str, list["Entry"]] = {}


@dataclass(frozen=True)
class Entry:
    iri: str
    cls: str
    label: str
    is_alt: bool
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class Anchor:
    iri: str
    cls: str
    label: str
    matched: tuple[str, ...]
    score: float
    via_alt: bool
    # 같은 라벨을 쓰는 형제 노드. 실무문제 226개 중 19개 라벨이 최대 28개 노드에 공유된다
    # (동일 라벨 = 동일 문제가 아니다). 화면엔 한 줄로 보이되 질의는 전부를 대상으로 해야 한다.
    siblings: tuple[str, ...] = ()

    @property
    def iris(self) -> tuple[str, ...]:
        return (self.iri, *self.siblings)


def normalize(word: str) -> str:
    """소문자화 + 영문 복수/진행형 접미사 절단. 문장과 라벨에 **동일하게** 적용한다.

    'Processes'→'proces', 'process'→'proces' 처럼 어간이 어법상 틀려도 무방하다 —
    양쪽이 같은 규칙을 지나므로 매칭만 맞으면 된다.
    """
    w = word.lower()
    if len(w) <= 4:
        return w
    if w.endswith("ing"):
        return w[:-3]
    if w.endswith("ed"):
        return w[:-2]
    # 'es' 는 치찰음 뒤에서만 복수 어미다 — 그래야 'processes'→'process' 가 되고
    # 'process' 는 아래 'ss' 예외로 그대로 남아 **양쪽이 같은 어간에 모인다.**
    if w.endswith("es") and w[:-2].endswith(("s", "x", "z", "ch", "sh")):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def tokenize(text: str) -> list[str]:
    return [normalize(m.group()) for m in _WORD.finditer(text)]


# 한국어 조사. 긴 것부터 시도한다("에서" 를 "서" 로 자르면 안 된다).
_JOSA = (
    "에서는", "으로서", "으로써", "에게서", "이라는", "에서", "으로", "에는", "이나", "에게",
    "까지", "부터", "이라", "라는", "와의", "과의", "의", "를", "을", "이", "가", "은", "는",
    "에", "와", "과", "나", "로", "도", "만", "랑", "며",
)


def strip_josa(token: str, known: frozenset[str]) -> str | None:
    """조사를 뗀 어간을 돌려준다 — **그 어간이 사전에 실재할 때만.**

    사전 대조를 조건으로 두는 것이 핵심이다. 무조건 자르면 '현상이'→'현상' 처럼
    사전에 없는 말을 만들어 놓고 매칭을 시도하게 되고, 그건 형태소 분석이 아니라 추측이다.
    실측: '식각을 개선하고 증착이 불안정합니다' 가 조사 때문에 앵커 0개였다.
    """
    if not any("가" <= c <= "힣" for c in token) or token in known:
        return None
    for josa in _JOSA:
        if token.endswith(josa):
            stem = token[: -len(josa)]
            if len(stem) >= 2 and stem in known:
                return stem
    return None


def korean_tokens(entries: list[Entry]) -> frozenset[str]:
    """사전에 실재하는 한국어 토큰 — 조사 절단의 유일한 판정 근거."""
    return frozenset(
        t for e in entries for t in e.tokens if any("가" <= c <= "힣" for c in t)
    )


# 클래스를 **질의에서** 걸러야 한다. 전체 라벨을 받아 파이썬에서 거르면 G₂(라벨 수만)에서
# store.MAX_ROWS 상한에 걸려 사전이 조용히 잘린다 — 실제로 G₂ 의 Device 34개 중
# 21개만 실려 HBM 이 사라졌었다. 잘린 사전은 "그 개념이 없다"와 구별되지 않는다.
_LEX_QUERY = (
    """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX ont: <https://w3id.org/sdkb/ont/>
SELECT ?s ?t ?pref ?alt WHERE {
  VALUES ?t { """
    + " ".join(f"ont:{c}" for c in ANCHOR_CLASSES)
    + """ }
  ?s a ?t ; skos:prefLabel ?pref .
  OPTIONAL { ?s skos:altLabel ?alt }
}
"""
)


def build_lexicon(graph_key: str) -> list[Entry]:
    """그래프의 prefLabel·altLabel 로 앵커 사전을 만든다(그래프당 1회, 캐시).

    altLabel 을 쓰는 것이 핵심이다 — 동의어를 이 모듈이 발명하지 않고 온톨로지가 공급한다.
    """
    if graph_key in _lexicons:
        return _lexicons[graph_key]
    res = run_query(graph_key, _LEX_QUERY)
    if res.truncated:
        # 잘린 사전은 오답을 낸다("그 개념이 그래프에 없다"와 구별되지 않는다). 조용히 넘기지 않는다.
        raise RuntimeError(
            f"{graph_key} 어휘 사전이 {len(res.rows)}행에서 잘렸다 — store.MAX_ROWS 를 올려라"
        )
    seen: set[tuple[str, str]] = set()
    entries: list[Entry] = []
    for s, t, pref, alt in res.rows:
        cls = t["value"].removeprefix(ONT)
        for label, is_alt in ((pref, False), (alt, True)):
            if not label:
                continue
            text = label["value"]
            if (s["value"], text) in seen:
                continue
            seen.add((s["value"], text))
            entries.append(
                Entry(s["value"], cls, text, is_alt, tuple(dict.fromkeys(tokenize(text))))
            )
    _lexicons[graph_key] = entries
    return entries


def topic_tokens(entries: list[Entry]) -> frozenset[str]:
    """분류 축(공정·소자·스킬·불량모드) 라벨을 이루는 토큰 = 온톨로지가 인정한 주제어.

    'cmp'·'etch'·'deposition' 이 여기 든다. 이들은 아무리 흔해도 불용어가 아니다 —
    실무문제 라벨 226개가 템플릿(``… process for uniformity``)이라 흔할 뿐이고,
    바로 그 토큰이 문제를 구별하기 때문이다.
    """
    axis = ("Process", "SubProcess", "Device", "Skill", "FailureMode", "Material")
    return frozenset(t for e in entries if e.cls in axis for t in e.tokens)


def stopwords(entries: list[Entry]) -> frozenset[str]:
    """기능어 + 사전 안에서 너무 흔해 변별력이 없는 토큰(주제어는 제외).

    목록을 코드에 박지 않고 사전에서 산출한다 — 코퍼스가 바뀌면 따라간다.
    """
    df = Counter(tok for e in entries for tok in set(e.tokens))
    ceiling = max(2, int(len(entries) * _DF_MAX_RATIO))
    # 면제는 **한 단어가 통째로 개념 이름인 것**(CMP·Etch·PVD·DOE)에 한한다.
    # 'process' 같은 머리명사는 축 라벨에 들어 있어도 변별력이 없다 —
    # 이걸 면제하면 'Back-End Processes' 가 'process' 한 토큰으로 잡힌다.
    axis = ("Process", "SubProcess", "Device", "Skill", "FailureMode", "Material")
    names = {e.tokens[0] for e in entries if e.cls in axis and len(e.tokens) == 1}
    common = {t for t, n in df.items() if n > ceiling} - names
    return frozenset(_FUNCTION_WORDS) | common


def _score(label_tokens: tuple[str, ...], sentence: set[str], stop: frozenset[str]) -> tuple:
    """(점수, 일치 토큰). 불용어만으로는 앵커가 되지 않는다."""
    useful = [t for t in label_tokens if t not in stop]
    if not useful:
        return 0.0, ()
    hit = [t for t in useful if t in sentence]
    if not hit:
        return 0.0, ()
    # 1토큰 라벨(C4·Seam·CDU)은 완전일치일 때만 인정 — 짧을수록 오폭이 크다.
    if len(useful) == 1 and len(label_tokens) == 1:
        return (1.0, tuple(hit)) if hit else (0.0, ())
    return len(hit) / len(useful), tuple(hit)


def anchor(text: str, graph_key: str) -> list[Anchor]:
    """서술문에서 개념 앵커를 뽑는다. 점수 내림차순, 클래스당 상위 N."""
    entries = build_lexicon(graph_key)
    stop = stopwords(entries)
    sentence = set(tokenize(text))
    if not sentence:
        return []
    # 조사가 붙은 형태를 어간으로도 볼 수 있게 넓힌다(원형은 그대로 둔다).
    known_ko = korean_tokens(entries)
    sentence |= {s for t in list(sentence) if (s := strip_josa(t, known_ko))}

    topics = topic_tokens(entries)
    best: dict[str, Anchor] = {}  # IRI 당 최고점 하나 (pref/alt 중복 방지)
    for e in entries:
        score, hit = _score(e.tokens, sentence, stop)
        if score < _MIN_SCORE:
            continue
        # 서술형 라벨(실무문제·원인·완화책)은 템플릿을 공유하므로 주제어 하나가 전부를 가른다.
        # 문장에 없는 주제어를 담고 있으면 **다른 문제**다 — 'CMP … uniformity' 를 배제한다.
        if e.cls in _NARRATIVE and any(t in topics and t not in sentence for t in e.tokens):
            continue
        # 동점이면 긴 라벨이 이긴다 — 'Plasma Etch' 가 'Etch' 보다 구체적이다.
        cand = Anchor(e.iri, e.cls, e.label, hit, round(score, 3), e.is_alt)
        prev = best.get(e.iri)
        if prev is None or (cand.score, len(cand.matched)) > (prev.score, len(prev.matched)):
            best[e.iri] = cand

    # 같은 (클래스, 라벨)을 쓰는 노드는 한 앵커로 접는다 — 접지 않으면 상한 5개가
    # 동일 라벨 하나로 다 차서 다른 개념이 밀려난다.
    folded: dict[tuple[str, str], Anchor] = {}
    for a in sorted(best.values(), key=lambda x: (-x.score, x.iri)):
        key = (a.cls, a.label)
        head = folded.get(key)
        if head is None:
            folded[key] = a
        else:
            folded[key] = replace(head, siblings=(*head.siblings, a.iri))

    ranked = sorted(folded.values(), key=lambda a: (-a.score, -len(a.matched), a.label))
    out: list[Anchor] = []
    per_class: Counter = Counter()
    for a in ranked:
        if per_class[a.cls] >= _TOP_PER_CLASS:
            continue
        per_class[a.cls] += 1
        out.append(a)
    return out


def unused_spans(text: str, anchors: list[Anchor], graph_key: str) -> list[str]:
    """질의에 쓰이지 않은 내용어. 성능 수치·제약조건은 대응 술어가 없다 —
    없는 것을 있는 척하지 않고 화면에 그대로 남긴다."""
    entries = build_lexicon(graph_key)
    stop = stopwords(entries)
    known_ko = korean_tokens(entries)
    used = {t for a in anchors for t in a.matched}
    out: list[str] = []
    for m in _WORD.finditer(text):
        tok = normalize(m.group())
        # 조사가 붙은 채로도 '쓰임'을 판정해야 한다 — '식각을' 이 앵커가 됐는데
        # 미사용 목록에 남으면 화면이 스스로와 모순된다.
        if tok in used or strip_josa(tok, known_ko) in used or tok in stop:
            continue
        if tok in _FUNCTION_WORDS:
            continue
        if m.group() not in out:
            out.append(m.group())
    return out


# --- SPARQL 생성 -------------------------------------------------------
# 앵커는 IRI 이므로 <...> 로 직접 바인딩한다. 사용자 문자열은 어떤 쿼리에도 들어가지 않는다.

_PREFIX = """PREFIX ont: <https://w3id.org/sdkb/ont/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def _values(var: str, iris: list[str]) -> str:
    return f"VALUES {var} {{ " + " ".join(f"<{i}>" for i in iris) + " }"


def _by_class(anchors: list[Anchor], *classes: str) -> list[str]:
    """형제 IRI 까지 전부 — 화면은 한 줄이어도 질의는 같은 라벨의 모든 노드를 봐야 한다."""
    return [i for a in anchors if a.cls in classes for i in a.iris]


def build_queries(anchors: list[Anchor], *, before: str = "2015-01-01") -> dict[str, str]:
    """앵커 → 실무 질의 3종. 앵커가 없는 시나리오는 키를 만들지 않는다(빈 쿼리 금지)."""
    steps = _by_class(anchors, "Process", "SubProcess")
    devices = _by_class(anchors, "Device")
    skills = _by_class(anchors, "Skill")
    problems = _by_class(anchors, "Problem")
    modes = _by_class(anchors, "FailureMode")
    concepts = steps + devices
    queries: dict[str, str] = {}

    # ① 전문가 — 공정/스킬/실무문제/불량모드 어느 축으로 들어와도 Skill 로 수렴시킨 뒤 Expert 로 간다.
    seeds = []
    if skills:
        seeds.append(_values("?skill", skills))
    if steps:
        seeds.append(f"{{ {_values('?step', steps)} ?step ont:requiresSkill ?skill }}")
    if problems:
        seeds.append(f"{{ {_values('?prob', problems)} ?prob ont:requiresSkill ?skill }}")
    if modes:
        seeds.append(
            f"{{ {_values('?mode', modes)} ?p2 ont:exhibitsFailureMode ?mode ; "
            "ont:requiresSkill ?skill }"
        )
    if seeds:
        body = "\n  UNION ".join(s if s.startswith("{") else f"{{ {s} }}" for s in seeds)
        queries["expert"] = (
            _PREFIX
            + f"""SELECT DISTINCT ?expertLabel ?skillLabel ?affiliation WHERE {{
  {body}
  ?skill skos:prefLabel ?skillLabel .
  ?expert a ont:Expert ; ont:hasSkill ?skill ; skos:prefLabel ?expertLabel .
  OPTIONAL {{ ?expert ont:affiliatedWith ?org . ?org skos:prefLabel ?affiliation }}
}} ORDER BY ?skillLabel ?expertLabel LIMIT 200"""
        )

    # ② 선행기술 — 개념(공정 ∪ 디바이스)을 실현하며 착상일보다 앞선 특허.
    if concepts:
        queries["priorart"] = (
            _PREFIX
            + f"""SELECT DISTINCT ?conceptLabel ?patent ?title ?filed WHERE {{
  {_values("?concept", concepts)}
  ?concept skos:prefLabel ?conceptLabel .
  ?patent a ont:Patent ; ont:filingDate ?filed .
  {{ ?patent ont:realizesProcess ?concept }} UNION {{ ?patent ont:concernsDevice ?concept }}
  OPTIONAL {{ ?patent skos:prefLabel ?title }}
  FILTER(?filed < "{before}"^^xsd:date)
}} ORDER BY DESC(?filed) LIMIT 200"""
        )

    # ③ FTO — 위 개념을 실현하는 특허 중 청구항 전문을 갖춘 것을 출원인별로.
    if concepts:
        queries["fto"] = (
            _PREFIX
            + f"""SELECT ?orgLabel (COUNT(DISTINCT ?patent) AS ?ftoReady) WHERE {{
  {_values("?concept", concepts)}
  ?patent a ont:Patent ; ont:claimText ?claim ; ont:assignedTo ?org .
  {{ ?patent ont:realizesProcess ?concept }} UNION {{ ?patent ont:concernsDevice ?concept }}
  ?org skos:prefLabel ?orgLabel .
}} GROUP BY ?orgLabel ORDER BY DESC(?ftoReady) LIMIT 200"""
        )

    return queries


def interpret(text: str, graph_key: str, *, before: str = "2015-01-01") -> dict:
    """엔드포인트 진입점 — 앵커·미사용 구절·생성 쿼리를 함께 돌려준다(글래스박스)."""
    anchors = anchor(text, graph_key)
    return {
        "anchors": [
            {
                "iri": a.iri,
                "cls": a.cls,
                "label": a.label,
                "matched": list(a.matched),
                "score": a.score,
                "via_alt": a.via_alt,
                "queryable": a.cls in QUERYABLE,
                "nodes": len(a.iris),
            }
            for a in anchors
        ],
        "unused": unused_spans(text, anchors, graph_key),
        "queries": build_queries(anchors, before=before),
    }
