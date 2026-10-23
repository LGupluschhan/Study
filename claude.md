# 공부 폴더 작업 지침

## 로컬 스킬

이 폴더의 스킬은 `Claude/Skills/` 아래에 있다. 요청이 스킬 설명에 해당하면 먼저 그 스킬의 `SKILL.md`를 읽고 그 절차를 따른다.

### page-to-visual-notes

- 위치: `Claude/Skills/page-to-visual-notes/SKILL.md`
- 언제: 웹 페이지(강의·코스·문서)의 특정 섹션(#anchor) 내용만 정리하고, 개념마다 도식을 붙인 HTML 아티팩트로 만들어 달라는 요청. 예) "이 페이지 내용만 아티팩트로 정리해줘", "page-d2도 같은 형식으로", "이 섹션 시각화해줘"
- 핵심 순서: `scripts/extract_section.py`로 섹션 추출 → `templates/content_skeleton.json`을 복사해 내용 작성 → `scripts/build_page.py`로 HTML 생성 → Artifact 게시
- 참고 자료: 스키마는 `references/blocks.md`, 완성 예시는 `examples/ccarp_page-d1.json`
- 결과 HTML은 이 폴더(`/Users/chhan/Desktop/Project/공부/`)에 저장한다. 파일명은 사용자가 지정한 이름을 쓰고, 지정하지 않았으면 `<코스>_<anchor>.html`로 한다(예: `ccarp_page-d1.html`).
