# TRD - Todo List 웹사이트

## 1. 기술 목표
HTML5, CSS3, Vanilla JavaScript를 사용해 별도 서버나 프레임워크 없이 동작하는 클라이언트 중심 Todo List를 구성한다. 본 문서는 구현 전에 기술 구조와 데이터 계약을 정의한다.

## 2. 기술 스택
- **문서 구조**: HTML5
- **스타일**: Tailwind CSS 유틸리티 + `tailwind.css` 커스텀 스타일
- **동작**: JavaScript (ES6 이상)
- **데이터 저장**: Web Storage API의 `localStorage`
- **외부 의존성**: Tailwind Play CDN, Google Fonts CDN (프로토타입 단계)
- **실행 환경**: 최신 Chrome, Edge, Firefox, Safari

## 3. 제안 파일 구조
```text
todolist/
├── index.html
├── tailwind.css
└── script.js
```

`index.html`에서 Tailwind Play CDN을 로드하고, `tailwind.css`에서 색상 토큰과 뉴욕 신문 지면 스타일을 정의한다.

## 4. 화면 구조
```text
body
└── main.todo-app
    ├── header
    │   ├── h1: Todo List
    │   └── p: 목록 요약
    ├── form#todo-form
    │   ├── label 또는 시각적으로 숨겨진 label
    │   ├── input#todo-input
    │   └── button[type="submit"]
    ├── nav.filter-tabs
    │   ├── button[data-filter="all"]
    │   ├── button[data-filter="active"]
    │   └── button[data-filter="completed"]
    ├── ul#todo-list
    └── footer.todo-summary
```

## 5. 데이터 모델
각 Todo 항목은 다음 형태를 사용한다.

```js
{
  id: "고유 문자열",
  text: "할 일 내용",
  completed: false,
  createdAt: "ISO 8601 날짜 문자열"
}
```

- `id`: 항목 식별자. 삭제 및 상태 변경에 사용한다.
- `text`: 사용자가 입력한 할 일 내용이다.
- `completed`: 완료 여부를 나타낸다.
- `createdAt`: 생성 순서와 향후 정렬에 사용할 수 있는 생성 시각이다.

## 6. 저장 규칙
- 저장 키: `todo-list-items`
- 저장 값: Todo 객체 배열의 JSON 문자열
- 앱 시작 시 `localStorage`에서 값을 읽고 배열로 변환한다.
- 값이 없거나 JSON 변환에 실패하거나 배열이 아니면 빈 배열을 사용한다.
- 추가, 완료 상태 변경, 삭제가 끝날 때마다 저장한다.

## 7. 상태 관리
- `todos`: 전체 Todo 배열
- `currentFilter`: 현재 필터 (`all`, `active`, `completed`)
- 파생 상태는 렌더링 시 계산한다.
  - 표시 대상 목록
  - 전체 항목 수
  - 미완료 항목 수
  - 완료 항목 수

## 8. 이벤트 및 함수 책임
- `init()`: DOM 참조, 저장 데이터 로드, 이벤트 등록, 첫 렌더링
- `handleAddTodo(event)`: 입력 검증 및 새 Todo 생성
- `handleToggleTodo(id)`: 완료 상태 전환
- `handleDeleteTodo(id)`: Todo 삭제
- `handleFilterChange(filter)`: 현재 필터 변경
- `render()`: 목록, 필터 상태, 요약 정보 갱신
- `saveTodos()`: 현재 배열을 로컬 저장소에 저장
- `loadTodos()`: 저장 데이터 복원
- `createTodoElement(todo)`: Todo 항목 DOM 생성

## 9. 이벤트 처리 원칙
- 추가 폼은 `submit` 이벤트를 사용해 Enter 키와 버튼 동작을 통합한다.
- 목록은 이벤트 위임을 사용해 동적으로 생성되는 항목을 처리한다.
- 삭제와 상태 변경 시 항목의 `data-todo-id`를 사용한다.
- 화면에 사용자 입력을 삽입할 때 `innerHTML` 대신 텍스트 기반 DOM API를 우선 사용한다.

## 10. 반응형 및 접근성 기준
- 모바일 우선 레이아웃을 기본으로 한다.
- 입력창과 추가 버튼은 좁은 화면에서 충분한 너비와 높이를 확보한다.
- 포커스 상태를 CSS로 명확히 표시한다.
- 필터 버튼의 현재 상태를 `aria-pressed` 등으로 표현한다.
- 체크박스와 삭제 버튼은 키보드로 접근할 수 있어야 한다.
- 색상만으로 완료 여부를 전달하지 않는다.
- `prefers-reduced-motion` 설정을 존중한다.

## 11. 오류 및 예외 처리
- 빈 입력은 추가하지 않는다.
- 로컬 저장소 접근이 불가능한 경우 화면 기능은 계속 동작하도록 하고, 저장 실패는 사용자에게 안내할 수 있도록 한다.
- 저장 데이터 파싱 실패 시 앱을 중단하지 않고 빈 목록으로 초기화한다.

## 12. 검증 계획
- HTML 문법 및 시맨틱 구조 확인
- 데스크톱과 모바일 뷰포트 확인
- 추가, 완료 전환, 삭제, 필터, 새로 고침 후 복원 확인
- 빈 입력 및 잘못된 저장 데이터 확인
- 키보드 포커스 이동과 기본 접근성 확인
