#!/usr/bin/env python3
"""scripts/submission_check.py — 투고 파생본의 데스크 리젝 요인 검사 (CLAUDE.md §2.3).

용법:  python scripts/submission_check.py [--root .] [--warn]
종료:  0 = 통과(또는 대상 부재/--warn) · 1 = 위반 · 2 = 설정 오류

무엇을 보는가 — PLAN-048 §0 완료 기준(DoD) D2–D6 을 기계로 옮긴 것이다.
  D2  플레이스홀더 0건            (`[서지 재확인 필요]` 류)
  D3  영문 제목·초록 존재
  D4  작업 정본 전용 블록 0건      (원고상태·정정 대장·개봉 원장·미수행 설계 전문)
  D5  본문 표 ≤ 13 · 그림 4–8
  D6  본문 분량 — 권고 목표 61 % 초과는 **경고** · 실패 상한 63 % 초과는 **차단** · **참고문헌 제외**
  D7  영문 초록 ≤ 250 단어          (AEI 투고 규정)
  D8  키워드 ≤ 7 개                 (AEI 투고 규정)
  D9  본문 §참조의 도달성           (축약·재배열로 사라진 절을 가리키지 않는가)
  ＋  내부 링크 도달성 (이관은 삭제가 아니다 — supplementary 링크가 끊기면 실패)

설계 메모
- **대상은 파생본뿐이다**(`paper/submission/**/*.md`). 작업 정본은 감사 기록이므로 이 검사의
  대상이 아니다 — 정본에 상한을 걸면 기록을 지우라는 요구가 된다.
- 파생본이 아직 없으면(PLAN-048 1단계 전) **대상 부재로 통과**시키고 그 사실을 출력한다.
  없는 것을 실패로 만들면 0단계 배선 자체가 CI 를 붉힌다.
- 분량 기준선은 **코드에 동결**한다. 정본을 실시간으로 읽어 비교하면 정본이 자라는 만큼
  목표가 헐거워진다(움직이는 골대).
- **D7·D8 은 투고처 규정이므로 협상 대상이 아니다**(D6 의 축약 목표는 우리가 정한 페이지 목표라
  성격이 다르다). 규정이 바뀌면 상수를 고치고 출처를 주석에 남긴다.
- **2026-08-26 · 투고처가 바뀌었고 새 규정을 확인했다**(PLAN-081 §5-② 종결). 1지망은
  `Results in Engineering` 이며 Guide for Authors 실측 결과 **D7·D8 의 값은 바뀌지 않는다** —
  초록 *"does not exceed 250 words"* · 키워드 *"1 to 7 keywords"*. 우연이 아니라 두 저널이
  같은 Elsevier 표준을 쓴다. **두 상수는 이제 잠정값이 아니라 확정값이며 출처만 바뀌었다.**
- **같은 규정이 D5·D6 의 성격을 바꾼다.** 이 저널은 *"no strict formatting requirements
  (on length restrictions or reference formatting, for example)"* 를 명시한다. 곧 분량·표·그림
  상한은 **투고처 규정이 아니라 전부 우리가 정한 편집 목표**다(D7·D8 과 성격이 다르다).
- **D9 는 §2.3 의 "이관은 삭제가 아니다"를 절 참조로 확장한 것**이다. 파생본은 장 구성을 접으며
  만들어지므로(PLAN-048 2단계: 11장 → 8장) 산문에 남은 옛 절 번호가 조용히 죽은 링크가 된다.
  파일 링크만 검사하면 이것을 놓친다 — 실제로 놓쳤다(§4.8·§4.9·§4.9.1).
  CLAUDE.md 를 가리키는 하이픈 형식(`§1-2`)은 원고 밖 참조이므로 세지 않는다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 동결 기준선 — paper/논문_v0_9_SDKB_통합초안.md, 2026-08-10 (PLAN-048 승인 시점) 실측.
# 전체 124,354자 = 본문 114,472자 + 서지 9,882자 (커밋 9188e757 의 정본에서 재측정 · 2026-08-16).
BASELINE_CHARS = 124_354            # 참고 — D6 는 아래 본문 기준선으로 판정한다
BASELINE_BODY_CHARS = 114_472       # D6 분모: `# 참고문헌` 앞까지
# D6 목표 −40 % → −39 % (2026-08-17 · 사용자 승인). **투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다**(D7·D8 과 성격이 다르다 — 위 설계 메모). 완화한 이유는
# AEI 게재 문헌과의 포지셔닝을 §2.2·§2.3·§2.4·§3 에 보강했기 때문이다. AEI 심사표는 해당
# 저널 발표 연구의 반영을 명시적으로 평가하는데, 직전 판의 AEI 인용은 3편뿐이었다.
# **완화분은 서술이 아니라 문헌에만 쓴다** — 직전 판의 본문은 68,672자(−40.01 %)로 상한에
# 11자를 남기고 있었고, 문헌 보강의 순증은 807자다(신설 문단 둘 · §2.3 한 문단 · §3 한 문장 ·
# 표 1 을 10행에서 6행으로 압축한 감소분을 상계한 값). 판정·수치는 하나도 바뀌지 않았다.
# D6 를 한 줄 상한에서 **2단 규칙**으로 바꾼다 (2026-08-20 · 사용자 승인).
# 왜 바꾸는가: 직전 판의 본문은 상한에 **5자**를 남기고 있었다. 그 상태에서 D6 는 편집 품질을
# 관리하는 것이 아니라 **설명의 보강을 차단**한다 — 문장 하나를 더하면 검사가 실패하므로,
# 저자는 설명을 제대로 쓰는 대신 축약하도록 유도된다. 실제로 산출물 설계를 서술하는 §3.1 이
# 1,225자인 반면 결과·한계 서술은 1만 5천자를 넘었다. **D6 는 투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다**(D7·D8 과 성격이 다르다 — 위 설계 메모).
# 규칙은 둘이다. 권고 목표(soft) 를 넘으면 **경고만** 내고, 실패 상한(hard) 을 넘어야 차단한다.
# 경고 구간은 편집 중에만 쓰는 작업 여유이며, 최종 투고본은 권고 목표 아래로 되돌린다.
# D6 재설정 −39 %/−37 % → **−32 %/−30 %** (2026-08-22 · 사용자 승인 · PLAN-067 R-0).
# 왜 다시 바꾸는가: 2단 규칙을 도입한 2026-08-20 의 사유가 **그대로 재발했다**. 직전 판의 본문은
# 72,115자로 실패 상한 72,117 에 **2자**를 남기고 있었고, 그 상태에서 D6 는 편집 품질을 관리하는
# 것이 아니라 **문장 하나의 추가를 차단**한다. 이번에 차단된 것은 군더더기가 아니라 ① 용어 첫 등장
# 정의 21항(PLAN-066 B-3′ · 규율이 요구한 것) ② EP5 재프레이밍(PLAN-067 · 사전등록 §3 이 보고를
# 지시해 둔 홀드아웃 관찰면 7/15 포함)이다. **규율이 요구한 서술을 분량 목표가 막는 상태는 목표가
# 잘못 걸린 것이다.**
# 완화 폭의 근거: PLAN-066 정의 삽입 +1,760 · PLAN-067 재구성 +약 1,810 · D 단계 영문화 여유.
# **D6 는 투고처 규정이 아니라 우리가 정한 페이지 목표이므로 조정 대상이다**(D7 초록 250단어 ·
# D8 키워드 7 과 성격이 다르다 — 그 둘은 건드리지 않는다).
# **경고 구간은 여전히 편집 중에만 쓰는 작업 여유이며, 최종 투고본은 권고 목표 아래로 되돌린다.**
# 최종 분량의 실질 상한은 D 단계의 영문 본문 11,500단어가 진다(PLAN-064 §4.1).
# D6 원복 (2026-08-25 · PLAN-069 트랙 A ⑤ · O-4). 2026-08-22 에 0.68/0.70 으로 완화하였던 값을
# PLAN-068 A-6 이 목표한 **0.61/0.63** 으로 되돌린다. **되돌릴 수 있게 된 이유는 임계를 낮춘 것이
# 아니라 본문이 줄었기 때문이다** — PLAN-069 ④ 감량으로 본문이 74,023 → 69,814자가 되었고, 그
# 감량은 압축이 아니라 표·supplementary 와 중복되던 서술의 제거로 얻었다(§6 이동 대장).
# **완화 당시의 사유는 해소되었다** — 규율이 요구한 서술(용어 정의 · EP5 재프레이밍)은 전부 본문에
# 남아 있고 잘라낸 것은 같은 내용을 두 번 말하던 문단이다.
# D6 상향 (2026-08-26 · PLAN-081 §12.3 · 사용자 승인). **투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다**(D7 초록 250단어 · D8 키워드 7 과 성격이 다르다 — 그 둘은
# 건드리지 않는다). 1지망 `Results in Engineering` 은 *"no strict formatting requirements
# (on length restrictions or reference formatting, for example)"* 를 명시하므로, D6 의 외부
# 근거는 이제 없고 전부 우리 편집 목표다.
# **왜 올리는가:** PLAN-081 이 §3(산출물·절차)의 비중을 올리도록 지시했고 그 증량이 실제로
# 들어왔다 — §3.1 설계 결정과 그 대가 +539자 · §3.6 지속 통합 릴리스 절차 신설 +1,087자
# (파생본 실측 · 공백 포함 · 커밋 d330476 대비). 그 증량은 desk reject 방어의 본체이므로
# (§12.2 "A clear engineering problem, system, or process must be addressed") 되돌릴 대상이
# 아니다. 목표를 그대로 두면 D6 는 편집 품질을 관리하는 것이 아니라 **규율이 요구한 서술의
# 추가를 차단**한다 — 2026-08-20 과 2026-08-22 에 두 번 재발한 그 상태다.
# **상향 폭은 증량 실측치 그대로다** — 69,828 + 1,626 = 71,454 → 0.6242, 반올림하여 0.624.
# 실패 상한은 두 값의 폭(0.02)을 유지해 0.644 로 옮긴다.
# **경고 구간은 여전히 편집 중에만 쓰는 작업 여유이며, 최종 투고본은 권고 목표 아래로 되돌린다.**
LENGTH_TARGET_RATIO = 0.624         # D6 권고 목표(soft): −37.6 % 이상 축약 · 초과 시 경고
LENGTH_HARD_RATIO = 0.644           # D6 실패 상한(hard): −35.6 % · 초과 시 차단
BIB_HEAD = "# 참고문헌"             # 이 제목부터는 D6 분량에서 제외한다

MAX_TABLES = 14                     # D5
# D5 · 표 상한 13 → 14 (2026-08-22 · 사용자 승인 · PLAN-064 A-5). **투고처 규정이 아니라 우리가
# 정한 페이지 목표이므로 조정 대상이다**(D7·D8 과 성격이 다르다). 왜 올리는가: 이 검사는 캡션이
# 아니라 **표 분리행**을 세는데, 약어표(Nomenclature)가 그 한 칸을 쓰고 있어 상한 13 은 번호표
# 12개까지만 허용했다. EP5(제2 도메인 이식) 판정표를 표 13 으로 실으면 분리행은 14 가 된다.
# 즉 상향분 1 은 새 표 하나이며, 번호표는 13개다. 분량 기준 D6 은 글자 수 판정이므로 이 상향의
# 영향을 받지 않는다 — 신설 표의 글자 수는 그대로 D6 에 들어간다.
# D5 · 표 상한 12 → 13 (2026-08-19 · 사용자 승인 · PLAN-060). **투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다**(D7·D8 과 성격이 다르다 — 위 설계 메모). 상향한 이유는 외부
# 검토가 지적한 둘을 표로만 해소할 수 있기 때문이다: ① 설계과학연구의 단계와 본 연구의 실행을
# 잇는 절차 표가 없어 방법론이 결과 속에 흩어져 있었고, ② 중앙 판정 넷이 전부 임계와의 비교인데
# 그 판정이 전환점에서 얼마나 떨어져 있는지가 어디에도 없었다. 둘 다 산문으로 풀면 같은 값을
# 여러 문단에 반복하게 되어 오히려 분량이 는다. **상한에는 캡션 없는 약어표가 함께 세어진다** —
# 그래서 본문 캡션은 12개이고 분리행은 13개다. 분량 기준 D6 은 글자 수 판정이므로 이 상향의
# 영향을 받지 않으며, 신설 표의 글자 수는 그대로 D6 에 들어간다.
# D5 · 그림 상한 4–5 → 4–8 (2026-08-16 · 사용자 승인). **투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다**(D7·D8 과 성격이 다르다 — 위 설계 메모). 상향한 이유는
# 개념 도식 넷을 본문에 넣기 위해서다: 결과 장에만 데이터 차트가 몰려 있어 서론부터
# 평가설계까지가 시각 자료 없이 개념 구조를 산문으로만 전달하고 있었다.
# **그림이 넷 늘어난 만큼 표는 둘 줄었다** — 세 태스크 뷰 표와 승인식 각 항 표는 같은 내용을
# 더 잘 나르는 그림(그림 3·4)으로 대체했다. 분량 기준 D6 은 글자 수로 판정하므로 이 상향의
# 영향을 받지 않는다. 규격은 paper/FIGURE-SPEC.md.
FIGURE_RANGE = (4, 8)               # D5

# D7·D8 — **확정값**(2026-08-26 · PLAN-081 · Results in Engineering Guide for Authors 실측).
# 초록 "does not exceed 250 words" · 키워드 "1 to 7 keywords". 구 출처(AEI)와 값이 같다.
MAX_ABSTRACT_WORDS = 250            # D7 — Results in Engineering Guide for Authors (투고처 규정)
MAX_KEYWORDS = 7                    # D8 — 위와 같음

PLACEHOLDERS = [                    # D2 — verdicts.yaml PLACEHOLDERS 와 이중 방어
    "[서지 재확인 필요]",
    "[실험 후 기입]",
    "[최종 릴리스 후 기입]",
    "[미확정 서지]",
    "TODO",
]

# D4 — 작업 정본에만 있어야 하는 감사 블록의 표지. 파생본에서 발견되면 이관 누락이다.
WORKDOC_MARKERS = [
    "원고 상태",
    "정정 대장",
    "개봉 원장",
    "봉인 개봉 기록",
    "미수행 설계 전문",
]

TABLE_SEP = re.compile(r"^\|[\s:|-]+\|?\s*$")
IMAGE_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
INTERNAL_LINK = re.compile(r"(?<!!)\[[^\]]*\]\((?!https?:|mailto:)([^)#]+)(?:#[^)]*)?\)")

ABSTRACT_HEAD = re.compile(r"^#{1,3}\s*(Abstract|영문 초록)\s*$", re.I)
KEYWORDS_LINE = re.compile(r"^\**\s*(Keywords?|키워드)\s*\**\s*[::]\s*(.+)$", re.I)
HEADING_NUM = re.compile(r"^#+\s+(\d+(?:\.\d+)*)\.?\s")
# 원고 안의 절 참조. 뒤에 하이픈이 오면 CLAUDE.md 조항(§1-2)이므로 제외한다.
SECTION_REF = re.compile(r"§\s?(\d+(?:\.\d+)*)(?![.\d]*-)")
LATIN_WORD = re.compile(r"[A-Za-z]")
# D9 는 참고문헌 앞까지만 본다 — 서지의 §는 법령·심사기준 조항(MPEP § 904, 35 U.S.C. § 102)이지
# 이 원고의 절이 아니다. 같은 기호, 다른 이름공간.
REFS_HEAD = re.compile(r"^#+\s*(참고문헌|References)\b", re.I)


def strip_fenced(lines: list[str]) -> list[str]:
    out, in_fence = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return out


def check_file(path: Path, root: Path, warns: list[str] | None = None) -> list[str]:
    fails: list[str] = []
    # 경고 채널을 넘기지 않으면 경고는 버린다 — 단위 테스트가 차단 위반만 보기 위해서다.
    warns = [] if warns is None else warns
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = strip_fenced(text.splitlines())
    body = "\n".join(lines)

    # D2 · 플레이스홀더
    for i, line in enumerate(lines, 1):
        for ph in PLACEHOLDERS:
            if ph in line:
                fails.append(f"{path}:{i}: [D2] 플레이스홀더 잔존 — {ph}")

    # **원고 검사와 제출 부속물 검사를 가른다 (2026-08-21 · PLAN-063 트랙 4).**
    # D3(영문 제목·초록)·D5(표·그림 계수)·D6(분량)·D7(초록 단어)·D8(키워드)은 **원고의 성질**을
    # 재는 검사다. Highlights·cover letter·declarations 에 같은 자를 대면 "그림 0개"와 "초록 없음"이
    # 위반으로 잡히는데, 그 파일들은 그림도 초록도 가질 이유가 없다. 부속물은 D2(플레이스홀더) ·
    # D4(작업 정본 전용 블록) · D9(절 참조 도달성) · 내부 링크 검사를 그대로 받는다 — **면제가
    # 아니라 해당 없는 항목을 빼는 것이다.**
    is_manuscript = path.stem == "manuscript"

    # D3 · 영문 제목·초록 (ASCII 알파벳이 실질적으로 있는 제목/초록 절)
    has_en_title = bool(re.search(r"^#\s+.*[A-Za-z]{4,}", body, re.M))
    has_en_abstract = bool(re.search(r"^#{1,3}\s*(Abstract|영문 초록)", body, re.M))
    if is_manuscript and not has_en_title:
        fails.append(f"{path}: [D3] 영문 제목 없음")
    if is_manuscript and not has_en_abstract:
        fails.append(f"{path}: [D3] 영문 초록 절(Abstract) 없음")

    # D4 · 작업 정본 전용 블록
    for i, line in enumerate(lines, 1):
        for marker in WORKDOC_MARKERS:
            if marker in line and line.lstrip().startswith("#"):
                fails.append(f"{path}:{i}: [D4] 작업 정본 전용 블록 잔존 — {marker}")

    # D5 · 표·그림 계수
    n_tables = sum(1 for line in lines if TABLE_SEP.match(line))
    n_figures = len(IMAGE_REF.findall(body))
    if is_manuscript and n_tables > MAX_TABLES:
        fails.append(f"{path}: [D5] 본문 표 {n_tables}개 > 상한 {MAX_TABLES}")
    if is_manuscript and not (FIGURE_RANGE[0] <= n_figures <= FIGURE_RANGE[1]):
        fails.append(f"{path}: [D5] 그림 {n_figures}개 — 목표 {FIGURE_RANGE[0]}–{FIGURE_RANGE[1]}")

    # D6 · 분량
    # 참고문헌은 세지 않는다 — D6 는 "본문 분량"이고, 서지를 분량에 넣으면 **문헌을 보강할수록
    # 본문을 깎아야 하는** 역유인이 된다(2026-08-16 · 사용자 승인). 기준선도 같은 방식으로
    # 동결 시점 정본에서 다시 쟀으므로 비교는 그대로 같은 자다 — 목표는 −40 % 로 불변이다.
    #
    # **영문 산출물(`paper/submission/en/`)에는 D6 를 적용하지 않는다.** 기준선
    # `BASELINE_BODY_CHARS` 는 한국어 정본의 **글자 수**에서 동결한 값이고, 같은 내용을 영문으로
    # 옮기면 글자 수가 배 가까이 늘어난다 — 그 상태에서 이 자를 대면 재는 것은 분량이 아니라
    # 언어다. 영문 분량은 투고처의 페이지 규정으로 따로 관리하며, D2·D3·D7·D8·D9 와 링크
    # 검사는 영문 산출물에도 그대로 적용된다.
    is_english = (root / "paper" / "submission" / "en") in path.parents
    bib_at = text.find(BIB_HEAD)
    body_len = len(text if bib_at < 0 else text[:bib_at])
    soft = int(BASELINE_BODY_CHARS * LENGTH_TARGET_RATIO)
    hard = int(BASELINE_BODY_CHARS * LENGTH_HARD_RATIO)
    if not is_manuscript:
        pass                      # 부속물은 분량 목표의 대상이 아니다
    elif is_english:
        warns.append(f"{path}: [D6·비대상] 영문 원고 — 한국어 글자 수 목표를 적용하지 않는다 "
                     f"(본문 {body_len:,}자)")
    elif body_len > hard:
        pct = 100 * (1 - body_len / BASELINE_BODY_CHARS)
        fails.append(
            f"{path}: [D6] 본문 분량 {body_len:,}자 > 실패 상한 {hard:,}자 "
            f"(기준선 {BASELINE_BODY_CHARS:,}자 대비 −{pct:.1f} % · 권고 목표 {soft:,}자)"
        )
    elif body_len > soft:
        pct = 100 * (1 - body_len / BASELINE_BODY_CHARS)
        warns.append(
            f"{path}: [D6·경고] 본문 분량 {body_len:,}자 > 권고 목표 {soft:,}자 "
            f"(실패 상한 {hard:,}자 · 기준선 대비 −{pct:.1f} %) — 편집 중 여유 구간"
        )

    # D7 · 영문 초록 단어수 — Abstract 절 시작부터 다음 제목 또는 Keywords 행 직전까지.
    abs_start = next((i for i, ln in enumerate(lines) if ABSTRACT_HEAD.match(ln.strip())), None)
    if abs_start is not None:
        chunk: list[str] = []
        for ln in lines[abs_start + 1:]:
            if ln.lstrip().startswith("#") or KEYWORDS_LINE.match(ln.strip()):
                break
            chunk.append(ln)
        n_words = sum(1 for w in " ".join(chunk).split() if LATIN_WORD.search(w))
        if n_words > MAX_ABSTRACT_WORDS:
            fails.append(
                f"{path}:{abs_start + 1}: [D7] 영문 초록 {n_words}단어 > 상한 "
                f"{MAX_ABSTRACT_WORDS} (−{n_words - MAX_ABSTRACT_WORDS}단어 필요 · 투고처 규정)"
            )

    # D8 · 키워드 개수
    for i, line in enumerate(lines, 1):
        m = KEYWORDS_LINE.match(line.strip())
        if not m:
            continue
        raw = m.group(2)
        parts = [p.strip(" *") for p in re.split(r"[;；]" if ";" in raw or "；" in raw else "[,，]", raw)]
        parts = [p for p in parts if p]
        if len(parts) > MAX_KEYWORDS:
            fails.append(
                f"{path}:{i}: [D8] 키워드 {len(parts)}개 > 상한 {MAX_KEYWORDS} (투고처 규정)"
            )

    # D9 · §참조 도달성 — 축약·재배열로 사라진 절을 가리키면 실패한다.
    defined = {m.group(1) for ln in lines if (m := HEADING_NUM.match(ln))}
    if defined:                      # 번호 제목이 없는 파일(부속물 등)은 대상 아님
        refs_at = next((i for i, ln in enumerate(lines) if REFS_HEAD.match(ln.strip())), len(lines))
        for i, line in enumerate(lines[:refs_at], 1):
            for ref in SECTION_REF.findall(line):
                if ref not in defined:
                    fails.append(f"{path}:{i}: [D9] 없는 절 참조 — §{ref}")

    # 내부 링크 도달성
    for i, line in enumerate(lines, 1):
        for target in INTERNAL_LINK.findall(line):
            target = target.strip()
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists() and not (root / target).resolve().exists():
                fails.append(f"{path}:{i}: [LINK] 내부 링크 단절 — {target}")

    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0 (§2.3 경고 모드)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    targets = sorted((root / "paper" / "submission").rglob("*.md"))
    if not targets:
        print("대상 부재: paper/submission/**/*.md — 투고 파생본이 아직 없다 (PLAN-048 1단계 전). 통과.")
        return 0

    fails: list[str] = []
    warns: list[str] = []
    for f in targets:
        fails += check_file(f, root, warns)

    for line in warns:
        print(line)
    for line in fails:
        print(line)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 투고 준비 위반 {len(fails)}건 (PLAN-048 DoD D2–D9)")
        if args.warn:
            print("(경고 모드 — CLAUDE.md §2.3: PLAN-048 3단계 종료 시 차단으로 승격)")
            return 0
        return 1
    tail = f" · 경고 {len(warns)}건" if warns else ""
    print(f"통과: {len(targets)}개 파일 · 투고 준비 검사 (D2–D9 · 내부 링크){tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
