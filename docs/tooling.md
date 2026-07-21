# 온톨로지 도구 (조회·편집·검증)

정본은 **[01.code_spec/TOOLING.md](../01.code_spec/TOOLING.md)** 에 있다.

요약: **Protégé 5.6.9 (WSL 네이티브, `~/opt/Protege-5.6.9/` · 실행 `protege`) + pySHACL(프로젝트
내장) + VS Code RDF/SPARQL 확장.** GUI 로 손댄 뒤에는 반드시 `make validate → make reason →
make cq`(또는 `make gate`)로 회귀를 확인한다. 편집 금지 구역·저장 규약은
[CLAUDE.md](../CLAUDE.md) §1·§5 를 따른다.
