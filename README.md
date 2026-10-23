# Study

공부한 내용을 정리하는 저장소입니다. 웹 강의·문서의 특정 섹션을 한국어로 요약하고, 개념마다 도식을 붙인 HTML 학습 노트로 만들어 보관합니다.

## 구조

```
Study/
├─ CCAR-P/   # CCA-R P 코스 시각화 노트 (Domain 1~7, 시험 블루프린트)
├─ CCAR-F/   # CCA-R F 코스 노트 (준비 중)
├─ Claude/
│  ├─ Skills/   # 노트 생성용 로컬 스킬
│  └─ Agents/
└─ claude.md    # Claude Code 작업 지침
```

## 학습 노트 (CCAR-P)

| 파일 | 내용 |
| --- | --- |
| `ccarp_page-d1.html` ~ `ccarp_page-d7.html` | Domain 1~7 정리 |
| `ccarp_page-blueprint.html` | 시험 블루프린트 |

HTML 파일은 브라우저에서 바로 열어 볼 수 있습니다(라이트/다크, 모바일 대응).

## 노트 만드는 방법

`Claude/Skills/page-to-visual-notes`  스킬을 사용합니다.

1. `scripts/extract_section.py`로 페이지의 `#anchor` 섹션만 추출
2. `templates/content_skeleton.json`을 복사해 내용 작성
3. `scripts/build_page.py`로 HTML 생성

블록·도식 스키마는 `references/blocks.md`, 완성 예시는 `examples/ccarp_page-d1.json`을 참고하세요. 자세한 절차는 [SKILL.md](Claude/Skills/page-to-visual-notes/SKILL.md)에 있습니다.

## 파일명 규칙

`<코스>_<anchor>.html` (예: `ccarp_page-d1.html`)
