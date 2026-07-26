# TOOLING — 온톨로지 조회·편집·검증 도구 (정본)

> **이 문서가 지지하는 것.** RQ/H 를 직접 지지하지는 않는다 — 이것은 **연구자가 T-Box/A-Box 를
> 눈으로 조회하고 손으로 수정·보완할 때 쓰는 도구의 설치·운영 정본**이다. 도구로 손댄 뒤에는
> 반드시 §5 게이트로 회귀를 확인해야 논문의 수치(G₀ 서명·H1·CQ)가 흔들리지 않는다.
> **[v0.9: 이 문서의 "H1(커버리지)·RQ3" 라벨은 구 패러다임 → S1/S3. v0.9 확증가설 H1–H5는 별개 — [RECONCILIATION-v09.md](RECONCILIATION-v09.md) §1]**
> 편집 대상·금지 구역은 [CLAUDE.md](../CLAUDE.md) §1·§5 를 그대로 따른다.

## 0. 결론 — 무엇을 설치했나 (2026-07-21, 실측)

| 도구 | 용도 | 설치 위치 / 방법 | 상태 |
|---|---|---|---|
| **Protégé 5.6.9** (WSL 네이티브) | T-Box 클래스·속성 설계, A-Box 개체 편집, SPARQL 조회, HermiT 추론 | `~/opt/Protege-5.6.9/` · 자체 JRE 11 번들 | ✅ WSLg 로 GUI 기동 확인 |
| **pySHACL / rdflib / owlready2** | SHACL 구조 검증 (게이트 L1 엔진) | `pyproject.toml` 의존성 → `make setup` | ✅ 프로젝트 내장 |
| **VS Code 확장 3종** | TTL/SPARQL/SHACL 문법 하이라이팅, SPARQL 실행 | `code --install-extension` (아래 §3) | ✅ 설치됨 |

**설치 난이도 최소 조합 = Protégé + pySHACL.** pySHACL 은 이미 프로젝트 의존성이라 `make setup`
한 번이면 끝나고, Fuseki/RDF4J 같은 서버형 트리플스토어는 조회에 필요하지 않다 — 조회는 Protégé 의
**SPARQL Query 탭**이 흡수한다. 서버형 조회를 체계화할 필요가 생기면 그때 Fuseki 를 얹는다.

---

## 1. Protégé — WSL 네이티브 설치 (완료된 절차)

WSLg(`DISPLAY=:0`)가 있어 **WSL 안에 설치한 Linux 빌드가 Windows 데스크톱에 그대로 뜬다.**
Windows 쪽에 따로 설치할 필요 없다. 배포판에 **자체 JRE(Java 11)** 가 번들되어 시스템 Java 21 과
충돌하지 않는다.

```bash
# 1) 다운로드·해제 (5.6.9 linux — 자체 JRE 포함)
mkdir -p ~/opt && cd ~/opt
curl -fL -o Protege-5.6.9-linux.tar.gz \
  https://github.com/protegeproject/protege-distribution/releases/download/protege-5.6.9/Protege-5.6.9-linux.tar.gz
tar xzf Protege-5.6.9-linux.tar.gz
chmod +x ~/opt/Protege-5.6.9/run.sh

# 2) PATH 런처
ln -sf ~/opt/Protege-5.6.9/run.sh ~/.local/bin/protege   # ~/.local/bin 이 PATH 에 있음

# 3) 앱 메뉴 등록 (WSLg 가 Windows 시작 메뉴로 노출)
#    ~/.local/share/applications/protege.desktop 생성 (Exec=~/opt/Protege-5.6.9/run.sh)
```

**실행:** 터미널에서 `protege` (또는 Windows 시작 메뉴의 "Protégé").
첫 기동은 플러그인 업데이트 확인 때문에 20~40초 걸릴 수 있다 — 정상이다.

> 힙이 부족하면 `~/opt/Protege-5.6.9/conf/jvm.conf` 의 `max_heap_size` 를 올린다. G₁/G₂ 는
> 40만 트리플대라 기본값으로도 열리지만, 여러 그래프를 동시에 얹으면 `max_heap_size=4G` 권장.

---

## 2. Protégé 로 이 저장소 열기 (조회·편집)

T-Box 와 A-Box 가 여러 TTL 로 나뉘어 있으므로 **조립된 그래프 하나를 여는 것**이 가장 단순하다.

| 열 것 | Protégé 로 열 파일 (조회 사본) | 보는 것 |
|---|---|---|
| **G₀ 전체 (T-Box+A-Box)** | `data/processed/graph_v0_protege.ttl` | baseline 49,201 트리플 — H1 의 before |
| **G₁ 보강 후** | `data/processed/graph_v1_protege.ttl` | 삼성·SK하이닉스 델타 (26M) |
| **G₂ 소부장 (RQ3 → S3)** | `data/processed/graph_v2_protege.ttl` | KSIA 188사 (94M ⚠ 힙 6G 권장) |
| **순수 T-Box 만** | `data/external/sdkb/sdkb-core.ttl` | 스키마만 (헤더 1개라 원본 그대로 열림 · ⚠ §4 직접 저장 금지) |

> `*_protege.ttl` 은 아래 함정 스니펫으로 만든 **조회 전용 사본**이다(gitignore). 원본 `graph_v*.ttl`
> 은 헤더가 5개라 Protégé 에서 바로 열리지 않는다. **게이트(§5)는 항상 원본에 돌린다.**
> **G₂(94M)는 로딩·추론 전에** `~/opt/Protege-5.6.9/conf/jvm.conf` 의 `max_heap_size=6G` 로 올린다.

> ⚠ **함정: `OWLOntologyAlreadyExistsException` (조립 그래프 로딩 실패).** `graph_v0.ttl` 은 SDKB
> 원천 파일들을 합친 것이라 **`owl:Ontology` 헤더가 5개**(gov:kr·ont:fore·ont:patent·gov·ont) 들어
> 있다. rdflib/pySHACL(게이트)은 트리플 뭉치로 읽어 무관하지만, **Protégé/OWLAPI 는 "1 문서 = 1
> 온톨로지" 라 두 번째 헤더에서 예외를 던진다.** 파일 결함이 아니라 로딩 규칙 차이다.
> **해결 — 헤더를 하나로 정리한 조회 전용 사본을 만든다** (정본 `graph_v0.ttl` 은 파이프라인 생성물이라
> 손대지 않는다. 사본은 `data/processed/` 에 두면 gitignore 되어 커밋에 섞이지 않는다):
> ```bash
> uv run python - <<'PY'
> from rdflib import Graph, RDF, OWL, URIRef
> g = Graph(); g.parse("data/processed/graph_v0.ttl", format="turtle")
> for s in list(g.subjects(RDF.type, OWL.Ontology)):     # 다중 헤더 제거
>     g.remove((s, RDF.type, OWL.Ontology))
> for t in list(g.triples((None, OWL.imports, None))):   # imports 제거(원천 추적 방지)
>     g.remove(t)
> g.add((URIRef("https://w3id.org/sdkb/merged/g0-view"), RDF.type, OWL.Ontology))  # 단일 헤더
> g.serialize("data/processed/graph_v0_protege.ttl", format="turtle")
> PY
> ```
> 그 뒤 Protégé 에서 **`data/processed/graph_v0_protege.ttl`** 을 연다(내용 전량 보존 · 헤더만 1개).
> G₁/G₂ 도 같은 증상이면 파일명만 바꿔 동일 처리한다. **이 사본은 조회 전용이다 — 편집·검증의 정본이
> 아니며, 게이트(§5)는 원본 `graph_v*.ttl` 에 돌린다.** 순수 T-Box 만 볼 때는 헤더가 하나인
> `data/external/sdkb/sdkb-core.ttl` 을 바로 열어도 된다.

`File ▸ Open` → 위 파일 선택 (조립 그래프는 위 함정 참고 후 `*_protege.ttl` 사본을 연다). 탐색:
- **Classes / Object Properties / Data Properties 탭** → T-Box
- **Individuals (by class) 탭** → A-Box 개체
- **SPARQL Query 탭** → `queries/cq/*.rq` 를 붙여넣어 조회
- **Reasoner ▸ HermiT ▸ Start reasoner** → 일관성·추론 확인 (게이트 L2 와 같은 엔진 계열)

> ⚠ **함정: HermiT 가 `xsd:date` 에서 막힌다.** 그래프에 `xsd:date` 리터럴이 다수(G₀ 2,119개)
> 있는데 HermiT 는 이 타입을 데이터레인지로 못 먹어 Start reasoner 시 오류가 날 수 있다. 이건 도구
> 한계이지 그래프 결함이 아니다 — **일관성의 정본 판정은 `make reason`** 이다(게이트가 date→dateTime
> 추론 전용 뷰를 만들어 넘긴다, CLAUDE.md §5 L2). Protégé 에서 추론이 필요하면 클래스 계층·추론된
> 타입 확인 정도로 쓰고, **일관성 결론은 게이트에 맡긴다.**

> ⚠ **함정: Protégé 가 `catalog-v001.xml` 을 만든다.** 온톨로지를 열면 그 폴더에 카탈로그 파일을
> 자동 생성한다. `data/external/sdkb/`(얼린 스냅샷·PROVENANCE 대상)에서 열면 스냅샷이 오염된다.
> `.gitignore` 에 `catalog-v*.xml` 를 넣어 자동 무시되게 해두었다 — 커밋 전 `git status` 로 재확인만.

---

## 3. VS Code 확장 (설치 완료)

저장소 안에서 TTL 을 직접 편집·diff·검색할 때. Remote-WSL 세션에 설치되어 있다.

```bash
code --install-extension stardog-union.stardog-rdf-grammars   # Turtle/TriG/N-Triples/SPARQL/SHACL 하이라이팅
code --install-extension zazuko.sparql-notebook               # .sparqlbook 으로 SPARQL 실행 (+langserver, data-table 동반 설치)
```

설치된 것 (`code --list-extensions`):
- `stardog-union.stardog-rdf-grammars` — RDF 계열 문법 하이라이팅
- `stardog-union.vscode-langserver-sparql` — SPARQL 자동완성·진단
- `zazuko.sparql-notebook` — SPARQL 노트북 (엔드포인트 또는 로컬 파일 질의)

용도 분담: **소규모 수정·리팩터링·커밋 전 diff 검토는 VS Code, 구조적 편집·개체 추가·추론은 Protégé.**

---

## 4. 편집 후 저장 규약 (중요 — CLAUDE.md §1 강제)

- 저장은 **반드시 Turtle 포맷**. 포맷을 바꾸면 git diff·게이트가 흔들린다.
- **`data/external/sdkb/` 직접 편집 금지** (§1-7: baseline 스냅샷). 여기 결함이면 상류 `~/Dev/sdkb`
  에서 고치고 `make vendor`. 저장소 안에서 우회 패치하면 스냅샷 출처가 거짓이 된다.
- **`data/processed/*.ttl` 손편집은 정본이 아니다.** 재현성은 `make baseline`/`make merge` 가 만든다.
  Protégé/VS Code 편집은 **관찰·실험** 용도로 쓰고, 확정 변경은 상류 또는 파이프라인에 반영한다.
- **어휘를 발명하지 않는다** (§1-5): 새 클래스·속성이 필요하면 코드/편집 전에 사람에게 묻는다.

---

## 5. 수정 → 재검증 → 게이트 (고정 순서)

GUI 로 손댄 뒤에는 **예외 없이** 프로젝트 게이트로 회귀를 확인한다. 개별 pySHACL CLI 로 끝내지 않는다
— delta shape·추론 뷰 변환이 게이트에만 걸려 있다.

```bash
make validate   # L1 SHACL (queries/shapes/graph + delta)
make reason     # L2 HermiT 일관성
make cq          # L3 CQ 27개 응답
make gate       # L0~L3 전체 — 그래프 자체를 바꿨으면 반드시 이것
```

> T-Box 용어 변경은 A-Box·SHACL·CQ 로 연쇄 영향이 크다. **"수정 → 쿼리 재검증 → 게이트"** 순서를
> 고정하고, shape/CQ 가 하나라도 빨간불이면 커밋 전에 멈춰 원인을 확인한다.
> 그래프를 바꿨다면 `make baseline` 을 두 번 돌려 **동일 graph_v0** 인지(재현성)도 확인한다.

---

## 6. 왜 이 조합인가 (기각한 대안)

- **Fuseki / RDF4J Server** — 조회를 서버로 체계화할 때 좋지만, Java 서버 구동·리포지토리 생성·데이터
  적재가 추가돼 "설치 난이도 최소" 기준에서 탈락. 조회는 Protégé SPARQL 탭 + VS Code SPARQL 노트북으로
  충분하다. 대량·반복 질의를 서버로 돌릴 필요가 생기면 그때 도입한다.
- **Windows 네이티브 Protégé** — WSLg 가 있어 불필요. WSL 빌드가 Windows 데스크톱에 그대로 뜨고,
  저장소 파일을 `\\wsl$` 경유 없이 네이티브 경로로 연다.
- **owlready2 를 편집 도구로** — 프로그램적 조작용이지 GUI 조회·편집 도구가 아니다. 게이트 엔진으로만 쓴다.
