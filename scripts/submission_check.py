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
  D7  영문 초록 ≤ 250 단어          (보수적 편집 상한 — 투고처 미정)
  D8  키워드 ≤ 7 개                 (보수적 편집 상한 — 투고처 미정)
  D9  본문 §참조의 도달성           (축약·재배열로 사라진 절을 가리키지 않는가)
  D10 보충자료 → 본문 §참조의 도달성 (보충자료가 "본문 §X"라 밝힌 참조만)
  ＋  내부 링크 도달성 (이관은 삭제가 아니다 — 링크가 끊기면 실패)

설계 메모
- **대상은 셋이다 — 파생본 · 산문 소스 · 보충자료.** 보충자료(`paper/supplementary/**/*.md`)는
  **내부 링크만** 받는다(2026-08-29). 보충자료는 심사자에게 나가는 자료인데 검사기 다섯이 전부
  대상에서 제외하고 있었고, 그 사각지대에서 죽은 링크와 낡은 판정 서술이 살아남았다. 다만 D9 는
  걸지 않는다 — 보충자료의 `§` 는 자기 문서가 아니라 다른 판의 원고를 가리킨다. **그 대신
  D10 이 "본문 §X" 라 스스로 밝힌 참조만 본다**(2026-08-30 · 아래 D10 주석).
  **감사 기록(`paper/audit/`)은 대상이 아니다.**
- **대상은 파생본과 산문 소스 둘이다.** 파생본(`paper/submission/**/*.md`)은 전 항목을 받고,
  **산문 소스**(`paper/manuscript/*_source.md`)는 **D9(§참조 도달성)와 내부 링크만** 받는다
  (2026-08-29 · O-15 · 사용자 승인). 정본에 분량·표/그림 상한을 걸면 기록을 지우라는 요구가
  되므로 그 넷(D2·D4·D5·D6 및 D3·D7·D8)은 산문 소스에 적용하지 않는다 — **면제가 아니라
  해당 없는 항목을 빼는 것이다**(부속물 처리와 같은 규칙).
- **왜 넓히는가 (O-15).** D9 와 링크 검사는 이 검사기에만 있고, 이 검사기는 파생본만 보았다.
  그래서 **조립을 동결한 기간에는 정본에서 절을 옮기거나 번호를 바꾸어 §참조가 죽어도 검사군
  다섯이 전부 초록이었다.** 실제로 PLAN-085 재구성이 그 상태에서 진행됐고 확인은 손으로 했다.
  전례는 `verdicts` 의 산문 소스 편입(PLAN-067 R-7)이며, 그때처럼 **대상만 넓히고 규칙은
  그대로 둔다.** 켜는 시점 실측은 **위반 0**(국문 소스 절 제목 38 · 고유 §참조 35 · 미도달 0 ·
  깨진 링크 0 · 영문 소스 D9 0 · 링크 0)이므로 경고 단계 없이 차단으로 켠다.
- **산문 소스의 링크는 자기 위치가 아니라 조립 대상 위치를 기준으로 쓰여 있다.** 국문 소스는
  `paper/submission/`, 영문 소스는 `paper/submission/en/` 이 기준이다(깊이가 달라 영문은
  `../../`). 소스 디렉터리에서 그대로 풀면 영문 28건이 거짓 위반이 된다 — 그래서 대상마다
  **링크 기준 디렉터리**를 함께 등록한다.
- 파생본이 아직 없으면(PLAN-048 1단계 전) **대상 부재로 통과**시키고 그 사실을 출력한다.
  없는 것을 실패로 만들면 0단계 배선 자체가 CI 를 붉힌다.
- 분량 기준선은 **코드에 동결**한다. 정본을 실시간으로 읽어 비교하면 정본이 자라는 만큼
  목표가 헐거워진다(움직이는 골대).
- **투고처는 미정이다.** 그러므로 D5–D9 는 전부 **우리가 정한 편집 목표**이며, 어느 것도
  외부 규정을 근거로 삼지 않는다. D7·D8 의 값(초록 250단어 · 키워드 7)은 다수 저널이 요구하는
  범위 가운데 **가장 좁은 쪽**을 택한 보수적 상한이다 — 투고처가 정해지면 그 규정으로 대체하고
  출처를 이 주석에 남긴다. **투고처를 전제한 서술을 이 파일에 다시 넣지 않는다.**
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

# 동결 기준선 — paper/archive/논문_v0_9_SDKB_통합초안.md, 2026-08-10 (PLAN-048 승인 시점) 실측.
# 전체 124,354자 = 본문 114,472자 + 서지 9,882자 (커밋 9188e757 의 정본에서 재측정 · 2026-08-16).
BASELINE_CHARS = 124_354            # 참고 — D6 는 아래 본문 기준선으로 판정한다
BASELINE_BODY_CHARS = 114_472       # D6 분모: `# 참고문헌` 앞까지
# D6 목표 −40 % → −39 % (2026-08-17 · 사용자 승인). **투고처 규정이 아니라 우리가 정한
# 페이지 목표이므로 조정 대상이다.** 완화한 이유는 인접 문헌과의 포지셔닝을 §2.2·§2.3·§2.4·§3
# 에 보강했기 때문이며, 완화분은 서술이 아니라 문헌에만 썼다(순증 807자). 판정·수치는 하나도
# 바뀌지 않았다.
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
# D6 상향 (2026-08-26 · PLAN-081 §12.3 · 사용자 승인). **D6 에는 외부 근거가 없고 전부 우리
# 편집 목표다** — 투고처가 미정이므로 D7·D8 도 같은 성격이며, 다만 그 둘의 값은 보수적 상한이라
# 건드리지 않는다.
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

# D7·D8 — 투고처가 정해지기 전까지의 **보수적 편집 상한**이다. 값은 다수 저널이 요구하는 범위
# 가운데 가장 좁은 쪽을 택했다. 투고처가 정해지면 그 규정으로 대체하고 출처를 여기에 남긴다.
MAX_ABSTRACT_WORDS = 250            # D7 — 보수적 편집 상한 (투고처 미정)
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

# 산문 소스와 그 **링크 기준 디렉터리** (O-15). 값은 소스가 링크를 쓸 때 전제한 위치이며,
# 조립 산출물이 놓이는 자리다 — 소스 자신의 디렉터리가 아니다.
SOURCE_TARGETS: dict[str, str] = {
    "paper/manuscript/stage3_source.md": "paper/submission",
    "paper/manuscript/en_source.md": "paper/submission/en",
}

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



def _check_links(path: Path, root: Path, link_base: Path | None) -> list[str]:
    """내부 링크 도달성 — 이관은 삭제가 아니므로 끊긴 링크는 실패다."""
    fails: list[str] = []
    lines = strip_fenced(path.read_text(encoding="utf-8", errors="replace").splitlines())
    for i, line in enumerate(lines, 1):
        for target in INTERNAL_LINK.findall(line):
            target = target.strip()
            if not target:
                continue
            base = link_base or path.parent
            if not (base / target).resolve().exists() and not (root / target).resolve().exists():
                fails.append(f"{path}:{i}: [LINK] 내부 링크 단절 — {target}")

    return fails


# ── D10 · 보충자료가 **본문을 명시적으로 가리키는** §참조의 도달성 ────────────────
#
# **왜 D9 로는 못 잡는가.** D9 는 문서가 자기 절 번호로 재는 검사이고, 보충자료는 그 대상에서
# 빠져 있다 — 보충자료의 `§` 대부분이 자기 문서가 아니라 **다른 판의 원고**를 가리키기
# 때문이다(각 파일 서두가 그 판을 밝힌다). 그래서 보충자료는 §참조에 관해 **어느 검사도 받지
# 않았고**, 그 사각지대에서 실제로 죽은 포인터가 살아남았다.
#
# **실측(2026-08-30 · 이 규칙을 켜면서 고친 것).** 파생본의 §5 절 순서가 재배열됐는데 그 사상이
# 조립기에 반영되지 않아 표 3 의 다섯 행 중 넷이 죽은 절을 가리켰고, 같은 원인으로 보충자료가
# 본문을 잘못 가리켰다 — S6 대조표 4건(`투고본 §5.7` · `§6.2` · `§8.1` · `§6.4.3`) · S7 1건 ·
# S5 국문 1건 · S5 영문 8건. **S6 은 §0.9 규칙 4 가 요구하는 대조표이므로, 그것이 죽은 절을
# 가리키는 것은 링크 누락보다 나쁘다** — 심사자가 추적 가능성을 확인하러 오는 자리다.
#
# **무엇만 보는가.** `본문 §X` · `투고본 §X` · `§X of the manuscript` 처럼 **대상이 현행 본문임을
# 문장이 스스로 밝힌 참조**만 본다. 그 밖의 `§` 는 건드리지 않는다 — 다른 판을 가리키는 것이
# 정상이기 때문이다. 그러므로 이 규칙은 D9 의 확장이 아니라 **D9 가 원리적으로 볼 수 없는
# 부분집합**을 맡는다.
#
# **v0.9 고지가 있는 파일은 통째로 제외한다.** S1·S2·S3 는 서두에서 *"이 파일의 § 번호는 v0.9
# 판의 것"* 이라 선언하며, 그 선언이 파일 전체에 걸린다. 고지를 지우면 그때부터 검사 대상이
# 되므로, 고지는 면제 장치가 아니라 **범위 선언**이다.
#
# **한계를 밝힌다.** 실재하지만 **다른** 절을 가리키는 어긋남(§5.2 ↔ §5.4)은 이 규칙도 잡지
# 못한다. 그것은 절 순서를 바꿀 때 사람이 대조표를 함께 고쳐야 하는 자리이며, 조립기의
# `CHAPTER_REMAP` 주석이 그 의무를 적어 둔다.
SUPP_V09_NOTICE = re.compile(
    r"이 파일의 .?§.? 참조에 대하여|On the .?§.? references in this file"
)
# `본문 §5.3` · `투고본 §4.5` · `§5.3.1 of the manuscript` · `§4.4 and §5.3.2 of the manuscript`
SUPP_BODY_REF_KO = re.compile(r"(?:본문|투고본)\s*§\s?(\d+(?:\.\d+)*)")
SUPP_BODY_REF_EN = re.compile(
    r"§\s?(\d+(?:\.\d+)*)(?:[^.\n]{0,40}?§\s?\d+(?:\.\d+)*)?[^.\n]{0,40}?\bof the manuscript\b"
)


def _supp_body_sections(path: Path, root: Path) -> set[str] | None:
    """이 보충자료가 가리키는 **현행 본문**의 절 번호 집합. 본문이 없으면 None."""
    target = root / "paper" / "submission" / ("en/manuscript.md" if path.parent.name == "en" else "manuscript.md")
    if not target.exists():
        return None
    secs = {m.group(1) for ln in target.read_text(encoding="utf-8").splitlines()
            if (m := HEADING_NUM.match(ln))}
    return secs | {s.split(".")[0] for s in secs} if secs else None


def _check_supp_body_refs(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if SUPP_V09_NOTICE.search(text):
        return []                                  # 범위 선언 — 이 파일의 §는 v0.9 판이다
    valid = _supp_body_sections(path, root)
    if not valid:
        return []                                  # 조립 동결로 본문이 없으면 판정하지 않는다
    out: list[str] = []
    for i, line in enumerate(strip_fenced(text.splitlines()), 1):
        refs = set(SUPP_BODY_REF_KO.findall(line))
        for m in SUPP_BODY_REF_EN.finditer(line):
            refs |= set(re.findall(r"§\s?(\d+(?:\.\d+)*)", m.group(0)))
        for ref in sorted(refs - valid):
            out.append(f"{path}:{i}: [D10] 본문에 없는 절을 본문으로 가리킨다 — §{ref}")
    return out


def check_file(
    path: Path,
    root: Path,
    warns: list[str] | None = None,
    *,
    is_source: bool = False,
    links_only: bool = False,
    link_base: Path | None = None,
) -> list[str]:
    fails: list[str] = []
    # 경고 채널을 넘기지 않으면 경고는 버린다 — 단위 테스트가 차단 위반만 보기 위해서다.
    warns = [] if warns is None else warns
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = strip_fenced(text.splitlines())
    body = "\n".join(lines)

    # 보충자료는 **내부 링크만** 받는다 (2026-08-29 · 사용자 승인). 분량·표/그림·초록·키워드는
    # 투고 파생본의 규격이고, D9(§참조 도달성)도 대상이 아니다 — 보충자료의 `§` 는 자기 문서가
    # 아니라 **다른 판의 원고**를 가리키며(각 파일 서두가 그 판을 밝힌다), 자기 절 번호로 재면
    # 전량이 거짓 위반이 된다. 남는 것은 "이관은 삭제가 아니다"를 지키는 링크 도달성이다.
    if links_only:
        return _check_links(path, root, link_base) + _check_supp_body_refs(path, root)

    # D2 · 플레이스홀더 — 산문 소스는 대상이 아니다(O-15). 소스는 편집 중의 문서이고
    # 플레이스홀더의 정리는 조립·마감에서 판정한다.
    if not is_source:
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

    # D4 · 작업 정본 전용 블록 — 산문 소스는 대상이 아니다(O-15). 이 검사는 "정본에만 있어야
    # 하는 블록이 파생본으로 새어 나왔는가"를 묻는 것이므로, 소스에 대면 질문이 뒤집힌다.
    if not is_source:
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
                f"{MAX_ABSTRACT_WORDS} (−{n_words - MAX_ABSTRACT_WORDS}단어 필요 · 편집 상한)"
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
                f"{path}:{i}: [D8] 키워드 {len(parts)}개 > 상한 {MAX_KEYWORDS} (편집 상한)"
            )

    # D9 · §참조 도달성 — 축약·재배열로 사라진 절을 가리키면 실패한다.
    defined = {m.group(1) for ln in lines if (m := HEADING_NUM.match(ln))}
    if defined:                      # 번호 제목이 없는 파일(부속물 등)은 대상 아님
        refs_at = next((i for i, ln in enumerate(lines) if REFS_HEAD.match(ln.strip())), len(lines))
        for i, line in enumerate(lines[:refs_at], 1):
            for ref in SECTION_REF.findall(line):
                if ref not in defined:
                    fails.append(f"{path}:{i}: [D9] 없는 절 참조 — §{ref}")

    fails += _check_links(path, root, link_base)
    return fails


# ── D13 · 장별 분량 예산 (PLAN-086 · 2026-09-01) ────────────────────────────
#
# **왜 D6 로는 부족한가.** D6 는 문서 전체에 걸린 한 개의 수이고 영문에는 아무 검사가 없었다.
# 그래서 장 단위의 증가는 무신호로 지나갔고(PLAN-083 이후 +4,697자), 영문은 PLAN-080 이 정한
# 상한을 391 단어 넘긴 채 통과했다. 이 검사는 **경고**다 — 차단은 D6 가 계속 맡는다.

BUDGET_SPEC = Path("paper/word-budget.yaml")
_CHAP = re.compile(r"^#\s+(\d+)\.\s")
_EN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'’\-]*")


def _chapters(path: Path, bib_head: str) -> dict[str, list[str]]:
    """장 번호 → 그 장의 행. `0` 은 제목·초록·약어표를 담는 머리다."""
    out: dict[str, list[str]] = {}
    cur, buf = "0", []
    for line in strip_fenced(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        if re.match(rf"^#\s+{bib_head}\s*$", line):
            break
        if m := _CHAP.match(line):
            out[cur] = buf
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    out[cur] = buf
    return out


def check_budget(root: Path) -> list[str]:
    """장별 예산 대조 — 전량 경고다."""
    spec_path = root / BUDGET_SPEC
    if not spec_path.exists():
        return []
    try:
        import yaml
    except ImportError:                                  # pragma: no cover
        return [f"[D13] {BUDGET_SPEC} 를 읽을 수 없다 — pyyaml 미설치"]
    cfg = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    head = 1.0 + float(cfg["meta"].get("headroom", 0.0))
    warns: list[str] = []

    ko = root / cfg["meta"]["targets"]["ko"]
    en = root / cfg["meta"]["targets"]["en"]
    ko_ch = _chapters(ko, "참고문헌") if ko.exists() else {}
    en_ch = _chapters(en, "References") if en.exists() else {}

    def ko_n(lines: list[str]) -> int:
        return len(re.sub(r"\s", "", "\n".join(lines)))

    def en_n(lines: list[str]) -> int:
        # 표 행은 국문 파생본에서 문자 단위로 복사된 것이라 영문 산문의 분량이 아니다.
        prose = [ln for ln in lines if not ln.strip().startswith("|")]
        return len(_EN_WORD.findall("\n".join(prose)))

    tot = cfg.get("total") or {}
    if ko_ch and (n := sum(ko_n(v) for v in ko_ch.values())) > tot.get("ko_chars", 10**9):
        warns.append(f"[D13] 국문 총량 {n:,}자 > 목표 {tot['ko_chars']:,}자")
    if en_ch and (n := sum(en_n(v) for v in en_ch.values())) > tot.get("en_words", 10**9):
        warns.append(f"[D13] 영문 총량 {n:,}단어 > 목표 {tot['en_words']:,}단어")

    for key, budget in (cfg.get("chapters") or {}).items():
        name = budget.get("name", key)
        if key in ko_ch and (n := ko_n(ko_ch[key])) > budget["ko_chars"] * head:
            warns.append(f"[D13] {key}장({name}) 국문 {n:,}자 > 예산 {budget['ko_chars']:,}자")
        if key in en_ch and (n := en_n(en_ch[key])) > budget["en_words"] * head:
            warns.append(f"[D13] {key}장({name}) 영문 {n:,}단어 > 예산 {budget['en_words']:,}단어")
    return [f"{BUDGET_SPEC}: {w}" for w in warns]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0 (§2.3 경고 모드)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    derived = sorted((root / "paper" / "submission").rglob("*.md"))
    # 산문 소스는 조립 동결과 무관하게 항상 본다 — 이 편입의 이유가 바로 동결 기간의 공백이다(O-15).
    sources = [(root / rel, root / base) for rel, base in SOURCE_TARGETS.items() if (root / rel).exists()]
    # 보충자료 — 내부 링크만. 감사 기록(paper/audit/)은 대상이 아니다.
    supp = sorted((root / "paper" / "supplementary").rglob("*.md"))
    if not derived and not sources:
        print("대상 부재: paper/submission/**/*.md · paper/manuscript/*_source.md. 통과.")
        return 0
    if not derived:
        print("파생본 부재 — 산문 소스만 검사한다 (조립 동결 중이면 정상이다).")

    fails: list[str] = []
    warns: list[str] = []
    for f in derived:
        fails += check_file(f, root, warns)
    for f, base in sources:
        fails += check_file(f, root, warns, is_source=True, link_base=base)
    for f in supp:
        fails += check_file(f, root, warns, links_only=True)
    warns += check_budget(root)

    for line in warns:
        print(line)
    for line in fails:
        print(line)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 투고 준비 위반 {len(fails)}건 (PLAN-048 DoD D2–D10)")
        if args.warn:
            print("(경고 모드 — CLAUDE.md §2.3: PLAN-048 3단계 종료 시 차단으로 승격)")
            return 0
        return 1
    tail = f" · 경고 {len(warns)}건" if warns else ""
    print(
        f"통과: 파생본 {len(derived)}개 (D2–D9 · 내부 링크) + 산문 소스 {len(sources)}개 "
        f"(D9 · 내부 링크) + 보충자료 {len(supp)}개 (내부 링크 · D10){tail}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
