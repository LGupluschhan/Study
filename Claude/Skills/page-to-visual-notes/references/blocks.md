# content.json 스키마

HTML 필드(`html`, `lead`, `left` 등)에는 `<strong>`, `<br>`, `<span class="c-accent|c-warm|c-ok">` 같은 인라인 HTML을 그대로 쓸 수 있다. `&`는 `&amp;`로 쓴다.
도식 라벨(`label`, `sub`, `lines`, `note` 등)은 일반 텍스트이며 빌더가 이스케이프한다.

## 페이지

```json
{
  "title": "탭/갤러리 이름 (2~4단어)",
  "eyebrow": "코스 · Part · Domain",
  "h1": "한국어 제목", "h1_en": "원문 제목",
  "lead": "한두 문장 요약 (HTML)",
  "weight": {"pct": 17, "label": "시험 비중 17%"},
  "sections": [ {"no": "1.1", "title": "...", "en": "...", "blocks": [ ... ]} ],
  "source": {"url": "원문 URL", "label": "링크 텍스트", "tail": "(선택) 뒤 문구"}
}
```
`weight`, `no`, `en`, `source`는 생략할 수 있다.

## 블록 (`"t"` 값)

| t | 필드 | 용도 |
|---|---|---|
| `p` | html | 본문 문단 (최대 폭 680px) |
| `note` | html | 작은 회색 보충 설명 |
| `h3` | text, en | 소제목 |
| `tasks` | items: [[번호, 텍스트], …] | 출제 항목·목차 카드 |
| `quote` | html, small | 인용 + 출처/해설 |
| `fig` | cap, items: [블록…] | 모눈 도면 패널. 도식은 보통 이 안에 넣는다 |
| `diagram` | kind + 도식 필드 | 도식 하나 (아래 참고) |
| `cards` | items: [{title, en, diagram?, html?, fit?: {label, html}}] | 패턴별 카드 그리드 + 작은 도식 |
| `backward` | left, right, steps: [{k, html, role?: goal/pick}] | 단계 흐름 카드 (goal=초록, pick=파랑) |
| `spectra` | items: [{title, left, right}] | 양 끝 비교 그라데이션 막대 |
| `callout` | tone?: warm, eyebrow, items: [블록…] | 강조 상자 (기본 파랑, warm=주황) |
| `vs` | items: [{tone: ok/warm/accent, tag, html}] | 판단 기준 비교 |
| `chips` | items: [텍스트…] | 비용·위험 태그 |
| `pillars` | items: [{title, en, html, ev}] | 기준·축 카드 (ev=근거/지표) |
| `split` | main{label, flex?}, rest{label, flex?}, aria, legend: [html…] | 비율 막대 |
| `takeaways` | items: [html…] | 체크 표시 핵심 정리 |
| `html` | html | 그대로 삽입 (최후의 수단) |

## 도식 (`"kind"`)

모든 도식에 `aria`(화면낭독기용 한 문장)를 넣는다. 노드의 `kind`는 색이다: `n` 기본, `a` 파랑(LLM·처리), `w` 주황(오케스트레이터·에이전트·피드백), `o` 초록(검증·집계·완료), `dash` 점선(동적/미정), `gate` 마름모(판정).
노드는 문자열 하나로 줄여 쓸 수 있다: `"입력"` = `{"label": "입력"}`.

### chain — 직렬 단계
```json
{"kind": "chain", "aria": "...", "caption": "(선택) 위쪽 캡션",
 "nodes": ["입력", {"label": "LLM 1", "kind": "a"},
           {"label": "GATE", "kind": "gate", "note": "점검 실패 → 중단", "fail": true}, "출력"]}
```
`note`는 노드 아래 작은 글씨다. `fail: true`이면 아래로 빠지는 주황 화살표를 함께 그린다. 노드에 `sub`를 주면 두 줄이 된다. 노드에 `edge: "w"|"a"`, `dash: true`를 주면 그 노드로 들어오는 화살표 스타일이 바뀐다.

### fanout — 분기/병렬/분할
```json
{"kind": "fanout", "aria": "...",
 "head": ["입력", {"label": "분류", "kind": "o"}],
 "branches": [{"label": "경로 A", "kind": "a"}, {"label": "경로 B", "kind": "w", "edge": "w", "dash": true}],
 "tail": [{"label": "집계", "kind": "o", "note": "다수결"}, "출력"]}
```
`tail`이 없으면 라우팅(갈라지기만 함)이 되고, 있으면 병렬 후 합치기가 된다. head·tail 안에 `gate`를 쓸 수 있다.

### cycle — 생성 ⇄ 평가 반복
`{"kind": "cycle", "a": {...}, "b": {...}, "forward": "결과물", "back": "비평 · 재시도", "exit": "기준 충족 → 출력"}`

### stages — 입력→처리→출력 + 피드백 (넓은 도식)
```json
{"kind": "stages", "stages": [{"title": "입력 Input", "lines": ["줄1", "줄2"], "kind": "n"}, ...],
 "feedback": {"title": "피드백 루프", "to": 1, "label": "되돌아가는 화살표 라벨", "note": "상자 아래 설명"}}
```
3~4단계를 권장한다(단계당 폭 200). `to`는 피드백이 돌아갈 단계 번호(0부터)이며 마지막 단계보다 앞이어야 한다. `lines`는 최대 2줄이다.

### ladder — 복잡도 계단 (넓은 도식)
`{"kind": "ladder", "axis": "복잡도 ↑", "climb": "부족할 때만", "steps": [{"title", "lines"(≤2), "kind"}, ...]}`

### agent — 에이전트 루프 (넓은 도식, 고정 배치)
`{"kind": "agent", "actor", "ask", "agent": {"label", "sub"}, "env": {"label", "sub"}, "act", "feedback", "repeat", "stop"}`

### hub — 중앙 분배
`{"kind": "hub", "lead": {"title", "sub", "kind"?}, "edge_label", "children": [{"title", "lines"(≤2), "kind"?, "dash"?}, ...]}`
자식은 2~4개를 권장한다. 자식 제목은 한글 7자 정도까지가 상자(폭 100)에 맞는다.

### peers — 경계를 넘는 대등한 통신 (2그룹)
`{"kind": "peers", "groups": [{"boundary": "조직 A", "agent": "에이전트 A"}, {...}], "label": ["정의된", "프로토콜"]}`

### raw — 직접 그린 SVG
`{"kind": "raw", "svg": "<svg class=\"m\" viewBox=\"0 0 300 130\" role=\"img\" aria-label=\"...\">...</svg>"}`
쓸 수 있는 클래스: 상자 `n n-a n-w n-o n-dash bound`, 선 `e e-a e-w` (+`e-dash`), 글자 `t tb ts tm ta tw`. 화살표 마커는 `url(#ar)`, `url(#ar-a)`, `url(#ar-w)`이다. 넓은 도식은 `class="d"`로 하고 `<div class="scroll">`로 감싼다.

## 폭 감각
작은 도식(`m`)은 카드 폭에 맞게 줄어든다. 한 줄에 노드 5개, 노드당 한글 6자 정도가 읽기 좋은 한계다. 길면 `sub`로 두 줄로 나눈다.
