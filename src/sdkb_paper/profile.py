"""프로파일 — 게이트를 자원에서 떼어내는 값 묶음 (PLAN-064 A-1 · SPEC-009 §3.1).

**왜 필요한가.** 게이트 코드에는 SDKB 전제가 네 층으로 박혀 있었다 — 어휘(네임스페이스)·스위트
이름과 층 귀속·결함의 조작 술어와 결정성 규칙·승인식의 형태. 그 전제가 값으로 나와 있지 않으면
"게이트는 자원 비의존적"이라는 주장은 코드로 증명되지 않는다(C3·C4).

**왜 전역 스위치가 아닌가.** 환경변수 하나로 `config` 상수를 갈아 끼우면 호출부는 안 고쳐도
되지만, 한 프로세스 안에서 SDKB 경로와 Brick 경로가 섞일 때 조용히 틀린다 — `analysis/faults.py`
가 `config.GRAPH_V0` 를 읽는 동안 스위트만 Brick 인 상태가 만들어진다. 그래서 프로파일은 **함수
인자로 흐르고**, 기본값은 import 시점이 아니라 **호출 시점**에 `active()` 로 푼다.

**이중 정본을 만들지 않는 두 장치.** ① `profiles/sdkb.yaml` 의 값이 현행 `config` 리터럴과
동일함을 테스트가 단언한다(전사 검증). ② `prereg` 블록을 가진 프로파일은 로드 시점에 **디스크
실물의 sha256 과 대조**하고, 불일치면 `PreregMismatch` 로 죽는다 — 동결 밖 자원 위에서 판정이
돌기 시작하면 사전등록은 그 순간 무효다(CLAUDE.md §1-3).

이 모듈은 `config` 를 import 하지 않는다(순환 방지). 경로는 자체 ROOT 로 푼다.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = ROOT / "profiles"
DEFAULT_PROFILE = "sdkb"
ENV_VAR = "SDKB_PROFILE"


class ProfileError(RuntimeError):
    """프로파일 정의가 자기모순이거나 필수 항목이 없을 때."""


class PreregMismatch(RuntimeError):
    """동결된 사전등록 sha256 과 디스크 실물이 다를 때 — 판정을 시작하지 않는다."""


@dataclass(frozen=True)
class FaultProfile:
    """결함 하나의 조작 명세. 코드가 아니라 사전등록이 정하는 부분만 담는다."""

    key: str
    number: int                      # seed 규칙 linear 의 결함 번호
    kind: str                        # "rate"(비율) | "tier"(누적 단계)
    strengths: tuple                 # rate: (0.05,0.10,0.20) · tier: (1,2,3)
    reps: tuple[int, ...]
    predicates: tuple[str, ...] = ()
    prefix: str = ""                 # 조작 술어의 네임스페이스 접두어 이름
    options: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Profile:
    name: str
    namespaces: dict[str, str]
    bare_prefix: str
    cq_dir: Path
    shapes_graph: Path
    shapes_delta: Path
    cq_suites: tuple[str, ...]
    l3_suites: tuple[str, ...]
    t3_suites: tuple[str, ...]
    cq_targets: tuple[str, ...]
    cq_gate_target: str
    cq_extra_headers: tuple[str, ...]
    cq_monotone: tuple[str, ...]
    cq_tau: float
    cq_tau_grid: tuple[float, ...]
    generation_dir: Path
    graph_default: Path | None
    has_t1_t2: bool
    # L1 판정 형태 — "conforms"(SDKB 기본) | "relative"(기준 대비 신규 위반 · SPEC-010 §6.2).
    # 무결한 그래프도 conforms=False 인 자원에서는 이진 판정이 상수라 결함을 구분하지 못한다.
    l1_mode: str
    seed_rule: str
    seed_base: int | None
    strengths: tuple
    cross_fault_predicates: dict[str, tuple[str, ...]]
    faults: dict[str, FaultProfile]
    protected_config_attrs: tuple[str, ...]
    protected_paths: tuple[str, ...]
    prereg: dict | None

    # --- 술어 추출 ---------------------------------------------------------
    def predicate_pattern(self) -> re.Pattern:
        """`suite_predicates()` 가 쓰는 정규식 — **프로파일 접두어에서 생성한다**.

        구 구현은 `ont:`·`skos:` 를 정규식에 박아 두었고, 그래서 Brick CQ(전량 `brick:`)에서
        모든 스위트가 빈 집합이 되어 교집합 검사가 **실패가 아니라 공허한 통과**를 냈다.
        접두어를 값으로 빼면 그 실패 양식이 원리적으로 사라진다(SPEC-009 §2 ③).
        """
        alt = "|".join(re.escape(p) for p in sorted(self.namespaces))
        return re.compile(rf"\b({alt}):([a-z][A-Za-z0-9_]*)")

    def qname(self, prefix: str, local: str) -> str:
        """술어의 표기 — `bare_prefix` 의 것만 지역명, 나머지는 접두어를 붙인다.

        구 구현이 `ont:` 는 지역명으로, `skos:` 는 `skos:broader` 로 적었다. 그 표기가
        `CROSS_FAULT_PREDICATES`·테스트·사전등록 §4.1 표와 맞물려 있으므로 값으로 보존한다.
        """
        return local if prefix == self.bare_prefix else f"{prefix}:{local}"

    def iri(self, prefix: str, local: str) -> str:
        if prefix not in self.namespaces:
            raise ProfileError(f"프로파일 '{self.name}' 에 접두어 '{prefix}' 가 없다")
        return self.namespaces[prefix] + local

    # --- 결정성 -----------------------------------------------------------
    def seed_for(self, key: str, rate: float, rep: int) -> int:
        """(결함·강도·반복) → 고정 시드. 규칙 자체가 프로파일 값이다.

        `sha256` — SDKB 동결 규칙 `sha256(key|rate|rep)`.
        `linear` — EP5 사전등록 §4.2 의 `seed_base + 100·결함번호 + 반복번호`.
          **이 식에는 강도가 없다.** 따라서 같은 (결함·반복)의 세 강도는 같은 시드를 공유한다.
          결정성은 온전하며(같은 입력 → 같은 출력) 판정에도 관여하지 않는다. 식을 고쳐서 강도를
          넣지 않는다 — 동결 이후의 개선은 개선이 아니라 사후 조정이다(CLAUDE.md §1-3).
        """
        if self.seed_rule == "sha256":
            h = hashlib.sha256(f"{key}|{rate:.4f}|{rep}".encode()).digest()
            return int.from_bytes(h[:4], "big")
        if self.seed_rule == "linear":
            if self.seed_base is None:
                raise ProfileError(f"프로파일 '{self.name}': seed_rule=linear 인데 seed_base 가 없다")
            spec = self.faults.get(key)
            if spec is None:
                raise ProfileError(f"프로파일 '{self.name}' 에 결함 '{key}' 의 번호가 없다")
            return self.seed_base + 100 * spec.number + rep
        raise ProfileError(f"알 수 없는 seed 규칙: '{self.seed_rule}'")


def _tuple(v) -> tuple:
    return tuple(v) if v is not None else ()


def _path(root: Path, v) -> Path | None:
    return None if v is None else (root / v if not Path(v).is_absolute() else Path(v))


def _validate(p: Profile) -> Profile:
    """자기모순을 로드 시점에 죽인다 — 게이트가 돌기 시작한 뒤에 알면 늦다."""
    l3, t3, all_s = set(p.l3_suites), set(p.t3_suites), set(p.cq_suites)
    if l3 & t3:
        raise ProfileError(f"'{p.name}': L3 와 T3 가 겹친다 {sorted(l3 & t3)} — "
                           "겹치면 L3 ⊇ T3 가 되어 T3 단독검출이 원리적으로 0 이다(PLAN-022)")
    if l3 | t3 != all_s:
        raise ProfileError(f"'{p.name}': L3 ∪ T3 가 스위트 전량과 다르다 — 검출력이 줄어든다")
    if p.cq_gate_target not in p.cq_targets:
        raise ProfileError(f"'{p.name}': 게이트 대상 '{p.cq_gate_target}' 이 조회 대상 목록에 없다")
    if p.l1_mode not in ("conforms", "relative"):
        raise ProfileError(f"'{p.name}': 알 수 없는 L1 판정 형태 '{p.l1_mode}'")
    if p.cq_tau not in p.cq_tau_grid:
        raise ProfileError(f"'{p.name}': 주값 τ={p.cq_tau} 가 동결 격자 {p.cq_tau_grid} 밖이다")
    if not p.cq_dir.exists():
        raise ProfileError(f"'{p.name}': CQ 디렉터리가 없다 — {p.cq_dir}")
    return p


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while blk := fh.read(chunk):
            h.update(blk)
    return h.hexdigest()


def verify_prereg(p: Profile) -> dict:
    """동결 sha256 과 디스크 실물을 대조한다. 불일치는 예외다(경고가 아니다).

    사전등록이 붙잡는 것은 커밋이 아니라 **산출물의 sha256** 이다(CLAUDE.md §2.1). 그래서
    여기서 보는 것도 파일 실물이다. 없는 파일은 "통과"가 아니라 불일치로 센다 — 조용히 빠지면
    동결 목록이 장식이 된다.
    """
    if not p.prereg:
        return {"checked": 0, "ok": True, "missing": [], "mismatch": []}
    missing, mismatch, n = [], [], 0
    for rel, want in sorted(p.prereg.get("sha256", {}).items()):
        f = ROOT / rel
        n += 1
        if not f.exists():
            missing.append(rel)
            continue
        got = _sha256(f)
        if got != want:
            mismatch.append({"file": rel, "expected": want, "actual": got})
    if missing or mismatch:
        raise PreregMismatch(
            f"프로파일 '{p.name}': 동결 자원과 디스크가 다르다 — "
            f"없음 {len(missing)}건 {missing[:3]} · 불일치 {len(mismatch)}건 "
            f"{[m['file'] for m in mismatch][:3]}\n"
            "         사전등록은 파일 sha256 을 동결한다. 다른 자원 위에서 판정을 시작하지 않는다."
        )
    return {"checked": n, "ok": True, "missing": [], "mismatch": []}


_CACHE: dict[str, Profile] = {}


def load(name: str = DEFAULT_PROFILE, *, verify: bool = True) -> Profile:
    """`profiles/<name>.yaml` 을 읽어 Profile 을 만든다(결과는 캐시한다)."""
    key = f"{name}|{verify}"
    if key in _CACHE:
        return _CACHE[key]
    f = PROFILES_DIR / f"{name}.yaml"
    if not f.exists():
        have = sorted(q.stem for q in PROFILES_DIR.glob("*.yaml")) if PROFILES_DIR.exists() else []
        raise ProfileError(f"프로파일 '{name}' 이 없다: {f} (있는 것: {have})")
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    faults = {}
    for k, v in (d.get("faults") or {}).items():
        faults[k] = FaultProfile(
            key=k, number=int(v["number"]), kind=v["kind"],
            strengths=_tuple(v["strengths"]), reps=_tuple(v.get("reps", (1,))),
            predicates=_tuple(v.get("predicates")), prefix=v.get("prefix", ""),
            options=v.get("options") or {})
    p = Profile(
        name=d["name"],
        namespaces=dict(d["namespaces"]),
        bare_prefix=d["bare_prefix"],
        cq_dir=_path(ROOT, d["cq_dir"]),
        shapes_graph=_path(ROOT, d["shapes_graph"]),
        shapes_delta=_path(ROOT, d["shapes_delta"]),
        cq_suites=_tuple(d["cq_suites"]),
        l3_suites=_tuple(d["l3_suites"]),
        t3_suites=_tuple(d["t3_suites"]),
        cq_targets=_tuple(d["cq_targets"]),
        cq_gate_target=d["cq_gate_target"],
        cq_extra_headers=_tuple(d.get("cq_extra_headers")),
        cq_monotone=_tuple(d["cq_monotone"]),
        cq_tau=float(d["cq_tau"]),
        cq_tau_grid=tuple(float(x) for x in d["cq_tau_grid"]),
        generation_dir=_path(ROOT, d["generation_dir"]),
        graph_default=_path(ROOT, d.get("graph_default")),
        has_t1_t2=bool(d["has_t1_t2"]),
        l1_mode=d.get("l1_mode", "conforms"),
        seed_rule=d["seed_rule"],
        seed_base=d.get("seed_base"),
        strengths=_tuple(d.get("strengths")),
        cross_fault_predicates={k: _tuple(v)
                                for k, v in (d.get("cross_fault_predicates") or {}).items()},
        faults=faults,
        protected_config_attrs=_tuple(d.get("protected_config_attrs")),
        protected_paths=_tuple(d.get("protected_paths")),
        prereg=d.get("prereg"),
    )
    _validate(p)
    if verify:
        verify_prereg(p)
    _CACHE[key] = p
    return p


def active() -> Profile:
    """현재 프로파일. `SDKB_PROFILE` 이 없으면 sdkb 다 — 기본이 기존 동작이어야 한다."""
    return load(os.environ.get(ENV_VAR, DEFAULT_PROFILE))


def resolve(p: "Profile | str | None") -> Profile:
    """함수 인자용 — None 이면 **호출 시점에** active() 를 푼다(import 시점이 아니다)."""
    if p is None:
        return active()
    return load(p) if isinstance(p, str) else p
