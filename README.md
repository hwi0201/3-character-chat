# 🏆 HomeRunBall Chat - 서강태 야구 선수 육성 챗봇

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> 🎓 HateSlop 3기 엔지니어x프로듀서 합동 캐릭터 챗봇 프로젝트

**고등학교 3학년 야구 선수 '서강태'를 9월 KBO 드래프트까지 육성하는 AI 챗봇 게임**

## 📖 프로젝트 소개

사용자는 야구부 코치가 되어 차갑고 무뚝뚝한 고3 타자 '서강태'와 대화하며 친밀도를 쌓고, 훈련을 통해 능력치를 올려 최종적으로 9월 KBO 드래프트에 도전합니다. RAG 기술을 활용한 지식 기반 대화와 실시간 스트리밍, 이벤트 시스템, 월별 스토리북 등 다양한 게임 요소가 결합된 인터랙티브 챗봇입니다.

### 🎮 주요 특징

- **📚 RAG 기반 대화**: ChromaDB를 활용한 지식 검색으로 캐릭터에 대한 깊이 있는 대화
- **⚡ 실시간 스트리밍**: LangChain 스트리밍을 통한 즉각적인 응답 (평균 2초 응답 시작)
- **🎯 육성 시스템**: 6가지 스탯(친밀도, 멘탈, 체력, 타격, 주루, 수비) 관리
- **💪 훈련 시스템**: 월별 횟수 제한, 강도 조절, 회복 세션 등 전략적 훈련
- **📖 스토리북 모드**: 3월~9월 주요 이벤트를 스토리텔링으로 경험
- **🎭 이벤트 시스템**: LLM 기반 이벤트 감지 및 자동 발동
- **🎨 인터랙티브 UI**: 스탯 변화 애니메이션, 알림 시스템, 반응형 디자인

### 🎯 게임 플레이

```
3월: 코치 부임 → 4~7월: 훈련 및 대화 → 8월: 여름 대회 → 9월: KBO 드래프트
```

- 총 8가지 엔딩 (메이저리그 진출 ~ 야구 포기)
- 친밀도에 따라 변하는 캐릭터 태도
- 월별 훈련 횟수 제한으로 전략적 플레이 유도

---

## 🏗️ 시스템 아키텍처

### 전체 구조도

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  chat.html   │  │ chatbot.js   │  │   style.css  │      │
│  │  (UI)        │  │  (Logic)     │  │  (Style)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                 │                                  │
│         └─────────────────┼─────────────────────────────────┤
│                           │ SSE Streaming                    │
│         ┌─────────────────┘                                  │
└─────────┼──────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────┐
│                     Flask Backend (app.py)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Endpoints:                                         │   │
│  │  • GET  /           (메인 페이지)                  │   │
│  │  • GET  /chat       (채팅 페이지)                  │   │
│  │  • POST /api/chat   (대화 스트리밍)                │   │
│  │  • POST /api/training (훈련 시스템)                │   │
│  │  • GET  /api/game_state (게임 상태 조회)           │   │
│  │  • POST /api/advance_month (월 진행)               │   │
│  │  • POST /api/event_choice (이벤트 선택)            │   │
│  └─────────────────┬───────────────────────────────────┘   │
└────────────────────┼───────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐  ┌──────▼──────┐  ┌────▼──────┐
│Chatbot  │  │   Training  │  │   Event   │
│Service  │  │   Manager   │  │  Detector │
└────┬────┘  └─────────────┘  └───────────┘
     │
     ├─────► ChromaDB (RAG 검색)
     │       • 캐릭터 지식 벡터 DB
     │       • 임베딩 기반 유사도 검색
     │
     ├─────► LangChain Memory
     │       • ConversationBufferMemory
     │       • 세션별 대화 히스토리 관리
     │
     └─────► OpenAI API
             • gpt-4o-mini (대화 생성)
             • text-embedding-3-small (임베딩)
             • JSON 모드 (이벤트/스탯 분석)
```

### 데이터 흐름 (대화 시)

```
1. 사용자 입력 → chatbot.js
2. POST /api/chat (SSE) → Flask
3. RAG 검색 (ChromaDB) → 관련 지식 3개 추출
4. 시스템 프롬프트 생성 (친밀도 레벨별 태도 지시)
5. LangChain 스트리밍 (OpenAI) → 실시간 토큰 전송
   ├─ 'token' 이벤트: 대화 내용 점진적 표시
   ├─ 'done' 이벤트: 스트리밍 완료
   ├─ 'metadata' 이벤트: 스탯 변화 정보
   ├─ 'event_update' 이벤트: 발동된 이벤트 정보
   └─ 'hint_update' 이벤트: 힌트 제공
6. 스탯 계산 (LLM 분석) → 대화 내용 기반 스탯 변화
7. 이벤트 감지 (백그라운드, 타임아웃 3초)
8. 게임 상태 저장 (game_states/{username}.json)
```

---

## 🛠️ 기술 스택

### Backend

| 기술 | 버전 | 역할 |
|------|------|------|
| **Flask** | 3.0.3 | RESTful API 서버, 라우팅, SSE 스트리밍 |
| **OpenAI API** | 1.58.1 | GPT-4o-mini (대화 생성), text-embedding-3-small (벡터 임베딩) |
| **LangChain** | 0.3.13 | LLM 통합, 대화 메모리, 스트리밍 파이프라인 (LCEL) |
| **ChromaDB** | 0.5.23 | 벡터 데이터베이스, 임베딩 저장/검색 (RAG) |
| **Python** | 3.11 | 백엔드 언어 |

### Frontend

| 기술 | 역할 |
|------|------|
| **Vanilla JavaScript** | 프레임워크 없는 순수 JS, EventSource API를 통한 SSE 처리 |
| **HTML5/CSS3** | 반응형 UI, 스탯 바, 알림 시스템, 스토리북 모달 |

### Infrastructure

| 기술 | 역할 |
|------|------|
| **Docker** | 컨테이너화 (일관된 개발 환경) |
| **Render.com** | 클라우드 배포 (무료 티어) |
| **Git** | 버전 관리 (GitHub) |

---

## 💡 기술 선택 이유

### 1. LangChain을 선택한 이유

**문제 인식:**
- OpenAI API를 직접 사용하면 스트리밍, 메모리 관리, 프롬프트 체이닝 등을 일일이 구현해야 함
- RAG 패턴을 구현하려면 검색 → 프롬프트 생성 → LLM 호출의 파이프라인을 직접 작성해야 함

**해결 방법:**
- LangChain의 LCEL(LangChain Expression Language) 파이프라인 사용
- `ConversationBufferMemory`로 세션별 대화 히스토리 자동 관리
- `RunnablePassthrough`로 RAG 검색 결과를 프롬프트에 자동 주입

**효과:**
- 코드 가독성 향상: `chain = prompt | llm` 형태의 선언적 코드
- 스트리밍 구현 간소화: `chain.stream()` 한 줄로 토큰 단위 스트리밍
- 메모리 관리 자동화: 세션별 대화 저장/불러오기 자동 처리

**코드 예시:**
```python
# services/chatbot_service.py:825-860
chain = (
    RunnablePassthrough.assign(
        related_texts=lambda x: rag_results_text,
        attitude=lambda x: attitude_instruction
    )
    | self.prompt
    | self.llm
)

for chunk in chain.stream(inputs):
    if chunk.content:
        yield {
            'type': 'token',
            'content': chunk.content
        }
```

### 2. ChromaDB를 선택한 이유

**문제 인식:**
- LLM은 학습 데이터에 없는 특정 캐릭터 설정(서강태의 배경, 트라우마 등)을 알 수 없음
- 일반적인 데이터베이스는 텍스트 유사도 검색이 불가능

**해결 방법:**
- 캐릭터 관련 지식을 텍스트 파일로 작성 (`static/data/chardb_text/*.txt`)
- ChromaDB에 임베딩 벡터로 저장
- 사용자 질문과 유사한 지식 3개를 검색하여 프롬프트에 포함

**기술 선택 이유:**
- **Python 네이티브 지원**: Flask와 통합이 쉬움
- **임베디드 모드**: 별도 서버 설치 없이 로컬 파일로 동작
- **빠른 검색 속도**: HNSW 알고리즘 기반 근사 최근접 이웃 탐색
- **무료 오픈소스**: 학습 프로젝트에 적합

**효과:**
- 환각(Hallucination) 감소: 검색된 지식 기반으로만 답변
- 캐릭터 일관성: 설정에 맞는 답변 생성
- 지식 확장성: 텍스트 파일 추가만으로 지식 확장 가능

**코드 예시:**
```python
# services/chatbot_service.py:613-628
rag_results = self.char_collection.query(
    query_texts=[user_message],
    n_results=3
)

if rag_results and rag_results['documents']:
    docs = rag_results['documents'][0]
    rag_results_text = "\n\n".join([
        f"[참고 {i+1}]\n{doc}"
        for i, doc in enumerate(docs)
    ])
```

### 3. SSE(Server-Sent Events) 스트리밍을 선택한 이유

**문제 인식:**
- GPT-4o-mini도 긴 답변 생성 시 5-7초 소요
- 사용자가 빈 화면을 보며 대기하면 UX 저하

**WebSocket vs SSE 비교:**

| 항목 | WebSocket | SSE (선택) |
|------|-----------|------------|
| 양방향 통신 | O | X (서버→클라이언트만) |
| 구현 복잡도 | 높음 (별도 프로토콜) | 낮음 (HTTP 기반) |
| 브라우저 지원 | 추가 설정 필요 | EventSource API 내장 |
| 자동 재연결 | 직접 구현 | 자동 지원 |
| 적합한 용도 | 채팅 (양방향) | 스트리밍 응답 (단방향) |

**선택 이유:**
- 이 프로젝트는 서버→클라이언트 단방향 스트리밍만 필요
- EventSource API로 간단히 구현 가능
- Flask에서 `yield`만으로 SSE 구현 가능

**효과:**
- 응답 시작 시간: 즉시 (토큰이 생성되는 즉시 전송)
- 사용자 대기 시간: 7초 → 2초 (71% 감소)
- 구현 코드: 50줄 미만으로 간소화

**코드 예시:**
```javascript
// static/js/chatbot.js:385-395
const eventSource = new EventSource(
  `/api/chat?username=${username}&message=${encodeURIComponent(message)}`
);

eventSource.onmessage = (e) => {
  const event = JSON.parse(e.data);
  if (event.type === 'token') {
    fullResponse += event.content;
    updateBotMessageContent(messageId, fullResponse);
  }
};
```

### 4. RAG(Retrieval-Augmented Generation) 패턴을 적용한 이유

**문제 인식:**
- LLM은 프리트레이닝 데이터에만 의존하므로 특정 캐릭터 설정을 모름
- 시스템 프롬프트에 모든 지식을 넣으면 토큰 낭비 + 컨텍스트 길이 제한

**해결 방법:**
1. 캐릭터 지식을 ChromaDB에 벡터로 저장
2. 사용자 질문과 유사한 지식 3개만 검색
3. 검색된 지식을 프롬프트에 동적으로 포함

**효과:**
- **토큰 효율성**: 전체 지식(10,000 토큰) → 필요한 부분만(500 토큰)
- **답변 정확도**: 환각 없이 설정에 맞는 답변
- **확장성**: 지식 추가 시 프롬프트 수정 불필요

**RAG vs Fine-tuning 비교:**

| 항목 | RAG (선택) | Fine-tuning |
|------|------------|-------------|
| 지식 업데이트 | 즉시 (파일 추가) | 재학습 필요 |
| 비용 | 저렴 (임베딩만) | 비싸 (GPU 학습) |
| 구현 난이도 | 낮음 | 높음 |
| 적합한 용도 | 지식 기반 QA | 특정 스타일 학습 |

### 5. Vanilla JavaScript를 선택한 이유 (React 대신)

**선택 이유:**
- **학습 목표 집중**: AI/백엔드 기술 학습이 프로젝트 핵심
- **배포 간소화**: 빌드 과정 없이 정적 파일만으로 배포
- **의존성 최소화**: node_modules, 빌드 툴 불필요
- **즉각적인 수정**: 코드 수정 시 새로고침만으로 확인

**트레이드오프:**
- ❌ 상태 관리 복잡도 증가 (AppState 객체로 수동 관리)
- ✅ 하지만 프로젝트 규모가 작아 감당 가능
- ✅ DOM 조작 성능은 충분히 빠름 (스탯 업데이트, 메시지 추가)

---

## ⚠️ 개발 중 문제점

### 문제 1: 스트리밍 응답 시간 지연 (7초)

**현상:**
- 대화 스트리밍이 시작되기까지 평균 7초 소요
- 사용자가 빈 로딩 화면을 보며 대기

**원인 파악:**
1. RAG 검색 (0.1초) → 빠름 ✅
2. 시스템 프롬프트 생성 (0.05초) → 빠름 ✅
3. LLM 스트리밍 시작 (2초) → 적정 ✅
4. **이벤트 감지 LLM 호출 (3-5초)** → 병목 ❌
5. **힌트 생성 LLM 호출 (2-4초)** → 병목 ❌

**근본 원인:**
- 대화 응답 완료 후 이벤트/힌트 분석을 **동기적으로 처리**
- LLM 호출 2번 추가로 총 대기 시간 누적

**증상:**
- 사용자가 봇의 답변을 다 읽은 후에도 계속 로딩 중
- 스트리밍의 장점(즉각적 피드백)이 사라짐

**코드 위치:** [services/chatbot_service.py:789-950](services/chatbot_service.py#L789-L950)

---

### 문제 2: 회복 세션 역설 (Recovery Session Paradox)

**현상:**
- 체력이 20 미만이면 모든 훈련(회복 세션 포함) 불가능
- "체력이 부족하여 훈련할 수 없습니다" 오류 발생

**역설:**
- 회복 세션은 체력을 회복하기 위한 시스템
- 하지만 체력이 낮을 때 회복 세션조차 할 수 없음
- → 체력이 낮으면 영원히 훈련 불가능

**원인:**
```python
# services/training_manager.py:56-70 (기존 코드)
if game_state.stats.stamina < 20:
    raise ValueError("체력이 너무 낮습니다.")

# 이후에 강도별 처리
if intensity <= 20:
    intensity_label = "Recovery Session"
    stamina_change = 10  # 체력 회복
```

- 체력 검증이 강도 판단보다 **먼저** 실행됨
- 회복 세션인지 판단하기도 전에 에러 발생

**게임 디자인 문제:**
- 플레이어가 막막함을 느낌
- 회복 메커니즘이 역설적으로 작동

**코드 위치:** [services/training_manager.py:56-107](services/training_manager.py#L56-L107)

---

### 문제 3: Git LFS와 Render 호환성 문제

**현상:**
- Git LFS로 PNG 파일 관리 시도
- `git push` 성공했으나 Render 배포 시 이미지 표시 안 됨
- 로컬에서는 정상 작동

**원인:**
- Render는 기본적으로 Git LFS를 지원하지 않음
- LFS 파일은 포인터만 다운로드되어 실제 이미지가 없음
- Render Build Command에 `git lfs pull` 추가 필요

**문제 발견 과정:**
1. `.gitignore`에 `*.png` 있음 → 이미지가 Git에 추적 안 됨
2. `.gitattributes`에 `*.png filter=lfs` → LFS로 관리하라는 설정
3. 충돌하는 설정으로 인해 일부 이미지만 추적됨
4. LFS 마이그레이션 시도 → 일부 이미지 손실 (19/25개)
5. Render 배포 고려 → LFS 포기 결정

**추가 발견:**
- 이미지 총 용량: 70MB (25개 파일)
- GitHub 저장소 제한: 100MB/파일, 1GB/저장소
- 현재 용량은 제한 내이므로 직접 커밋 가능

**코드 위치:** [.gitattributes](https://github.com/eoeldroal/HomeRunBall-Chat/blob/main/.gitattributes), [.gitignore](https://github.com/eoeldroal/HomeRunBall-Chat/blob/main/.gitignore)

---

### 문제 4: 훈련 에러 vs 경고 구분 부족

**현상:**
- 체력 부족/훈련 횟수 초과 시 400 에러 반환
- 프론트엔드에서 빨간색 에러 메시지 표시
- 마치 서버 오류처럼 보임

**문제점:**
- 이는 **게임 메커니즘**이지 **서버 오류**가 아님
- 사용자가 "무언가 잘못됐다"고 느낌
- UX 측면에서 부적절한 피드백

**원인:**
```python
# app.py:641-658 (기존 코드)
except ValueError as e:
    return jsonify({
        'success': False,
        'error': str(e)
    }), 400  # Bad Request
```

- 모든 `ValueError`를 에러로 처리
- 정상적인 게임 제약도 에러로 분류

**기대 동작:**
- 경고 메시지: 노란색, 부드러운 안내
- 실제 오류: 빨간색, 긴급 대응 필요

**코드 위치:** [app.py:641-658](app.py#L641-L658), [static/js/chatbot.js:232-237](static/js/chatbot.js#L232-L237)

---

## ✅ 문제 해결 방법

### 문제 1 해결: 스트리밍 최적화 - done 즉시 전송

**시도한 방법들:**

1. ❌ **RAG 검색 캐싱** → 큰 효과 없음 (이미 0.1초로 충분히 빠름)
2. ❌ **LLM 모델 변경 (gpt-4o-mini → gpt-3.5-turbo)** → 품질 저하
3. ✅ **done 신호 즉시 전송 + 이벤트/힌트 백그라운드 처리** → 효과적!

**최종 구현 방식:**

1. LLM 스트리밍 완료 후 **즉시 done 신호 전송**
2. 스탯 변화는 빠르므로 즉시 처리 (0.1초)
3. 이벤트/힌트는 **별도 SSE 이벤트**로 비동기 전송

**코드 변경:**

```python
# services/chatbot_service.py:865-948

# [6단계] 스탯 변화 계산 (빠름)
stat_changes, stat_reason = self.stat_calculator.analyze_conversation(...)

# [7단계] 게임 상태 저장
self.game_manager.save(username)

# [8단계] done 신호 즉시 전송 ⭐
yield {
    'type': 'done',
    'content': ''
}

# [9단계] 스탯 메타데이터 즉시 전송
yield {
    'type': 'metadata',
    'content': {...}
}

# [10단계] 이벤트 감지 (백그라운드, 타임아웃 3초)
event_info = self.event_detector.check_event(...)
if event_info:
    yield {
        'type': 'event_update',
        'content': event_info
    }

# [11단계] 힌트 제공 (백그라운드, 타임아웃 3초)
hint = self.event_detector.get_hint(...)
if hint:
    yield {
        'type': 'hint_update',
        'content': {'hint': hint, ...}
    }
```

**타임아웃 추가:**

```python
# services/event_detector.py:194-217

try:
    response = chain.with_config({"timeout": 3.0}).invoke({...})
    # 이벤트 분석 로직
except TimeoutError:
    print(f"[WARNING] 이벤트 조건 분석 타임아웃 (3초 초과)")
    return (False, "타임아웃")
```

**프론트엔드 핸들러:**

```javascript
// static/js/chatbot.js:415-446

if (event.type === 'token') {
  // 토큰 실시간 표시
  fullResponse += event.content;
  updateBotMessageContent(messageId, fullResponse);

} else if (event.type === 'done') {
  // 스트리밍 완료 (로딩 종료)
  console.log('[STREAM] 완료');

} else if (event.type === 'metadata') {
  // 스탯 업데이트 즉시 처리
  handleChatMetadata(metadata);

} else if (event.type === 'event_update') {
  // 이벤트 알림 (비동기)
  showEventNotification(event.content);

} else if (event.type === 'hint_update') {
  // 힌트 알림 (비동기)
  showHintWithContext(event.content);
}
```

**효과:**

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| 사용자 대기 시간 | 7초 | 2초 | **71% 감소** |
| 스트리밍 시작 | 7초 후 | 즉시 | **즉각 반응** |
| 이벤트 표시 | 동기 (대기) | 비동기 (백그라운드) | **비차단** |
| 타임아웃 보호 | 없음 | 3초 | **안정성 향상** |

**커밋:** [9f5efc7](https://github.com/eoeldroal/HomeRunBall-Chat/commit/9f5efc7)

---

### 문제 2 해결: 회복 세션 체력 제약 제거

**최종 구현:**

```python
# services/training_manager.py:75-107

# [1단계] 강도별 티어 먼저 판단
if intensity <= 20:
    intensity_label = "Recovery Session"
    base_gain = 0
    stamina_change = 10
    is_recovery_session = True  # 플래그 설정
elif intensity <= 40:
    intensity_label = "Light Training"
    base_gain = 2
    stamina_change = 4
    is_recovery_session = False
# ... 다른 티어들

# [2단계] 체력 검증 (회복 세션은 제외)
if not is_recovery_session and game_state.stats.stamina < 20:
    raise ValueError("체력이 너무 낮습니다. 회복 세션(강도 20 이하)을 이용하세요.")
```

**핵심 변경:**
1. 체력 검증 로직을 강도 판단 **이후**로 이동
2. `is_recovery_session` 플래그 추가
3. 회복 세션은 체력 검증 우회
4. 에러 메시지에 해결 방법 포함

**효과:**
- ✅ 체력이 0이어도 회복 세션 가능
- ✅ 월별 훈련 횟수 제한은 유지 (전략성 보존)
- ✅ 게임 플레이 막힘 현상 해결

**테스트:**
```python
# 체력 10일 때 회복 세션 (강도 20)
outcome = training_manager.execute(
    game_state=game_state,
    intensity=20,
    focuses=['batting']
)
# ✅ 성공: stamina +10
```

**커밋:** [f3fb5ba](https://github.com/eoeldroal/HomeRunBall-Chat/commit/f3fb5ba)

---

### 문제 3 해결: Git LFS 포기 및 직접 커밋

**의사결정 과정:**

| 방안 | 장점 | 단점 | 결정 |
|------|------|------|------|
| Git LFS | 저장소 가벼움 | Render 미지원, 복잡도 증가 | ❌ |
| CDN (S3/Cloudinary) | 빠른 로딩 | 비용, 추가 설정 | ❌ |
| **직접 커밋** | 간단함, Render 호환 | 저장소 용량 증가 (70MB) | ✅ |

**구현:**

1. **파일 복구:**
```bash
# 이전 커밋에서 손실된 19개 파일 복구
git checkout fcda6de -- static/images/chatbot/
git checkout a3c2752 -- static/images/chatbot/ending6_university.png ...
```

2. **.gitattributes 수정:**
```diff
# .gitattributes:19-25
- *.png filter=lfs diff=lfs merge=lfs -text
+ *.png binary
  *.jpg binary
  *.jpeg binary
```

3. **Git LFS 제거:**
```bash
git lfs uninstall
git add .
git commit -m "Restore all PNG files and remove LFS dependency"
git push origin main
```

**효과:**
- ✅ Render 배포 시 이미지 정상 표시
- ✅ 빌드 명령 간소화 (LFS 설정 불필요)
- ✅ 로컬 개발 시 이미지 즉시 사용 가능
- ⚠️ 저장소 크기 증가: 10MB → 80MB (여전히 1GB 제한 내)

**커밋:** [77c1481](https://github.com/eoeldroal/HomeRunBall-Chat/commit/77c1481)

---

### 문제 4 해결: 경고 시스템 도입 (warning 플래그)

**최종 구현:**

**백엔드 (app.py:641-658):**
```python
except ValueError as e:
    error_msg = str(e)
    print(f"[WARNING] 훈련 제한 조건: {error_msg}")

    # 경고로 처리 (오류가 아님)
    return jsonify({
        'success': False,
        'warning': True,  # 플래그 추가
        'message': error_msg
    }), 200  # 200 OK (정상 응답)
```

**프론트엔드 (chatbot.js:232-237):**
```javascript
// 경고 처리
if (!data.success && data.warning) {
  closeTrainingModal();
  showWarning(data.message);  // 노란색 알림
  return;
}

// 실제 오류 처리
if (!response.ok || !data.success) {
  throw new Error(data.error);  // 빨간색 에러
}
```

**경고 알림 UI (chatbot.js:326-348):**
```javascript
function showWarning(message) {
  const notification = document.createElement("div");
  notification.className = "notification-item warning";
  notification.innerHTML = `
    <div class="notification-title">
      ⚠️ ${message}
    </div>
  `;
  container.appendChild(notification);

  // 7초 후 자동 제거
  autoRemoveNotification(notifId, 7000);
}
```

**CSS 스타일:**
```css
.notification-item.warning {
  background: #FFF3CD;  /* 연한 노란색 */
  border: 2px solid #FF9800;  /* 주황색 테두리 */
  color: #856404;  /* 갈색 텍스트 */
}
```

**효과:**

| 항목 | Before | After |
|------|--------|-------|
| HTTP 상태 | 400 Bad Request | 200 OK |
| 메시지 색상 | 빨간색 (에러) | 노란색 (경고) |
| 사용자 인식 | "뭔가 잘못됐다" | "게임 규칙이다" |
| 자동 제거 | 없음 | 7초 후 |

**커밋:** [4392da3](https://github.com/eoeldroal/HomeRunBall-Chat/commit/4392da3)

---

## 🚀 성능 개선 노력

### 개선 1: 스탯 변화 시각적 피드백 강화

**목표:**
- 스탯이 변할 때 사용자가 명확히 인지하도록 개선
- 대화만으로 스탯 변화를 알아차리기 어려움

**구현:**

1. **AppState에 previousStats 추가:**
```javascript
// static/js/chatbot.js:47-54
previousStats: {
  intimacy: null,
  mental: null,
  stamina: null,
  batting: null,
  speed: null,
  defense: null
}
```

2. **updateStatBar() 개선:**
```javascript
// static/js/chatbot.js:910-950
function updateStatBar(statName, value) {
  const previousValue = AppState.previousStats[statName];
  const hasChanged = previousValue !== null && previousValue !== value;
  const change = hasChanged ? value - previousValue : 0;

  if (hasChanged && change !== 0) {
    // 애니메이션 클래스 추가
    const animationClass = change > 0 ? 'stat-increased' : 'stat-decreased';
    statBar.classList.add(animationClass);

    // 변화량 인디케이터 생성
    createStatChangeIndicator(statBar, change);
  }

  // 현재 값 저장
  AppState.previousStats[statName] = value;
}
```

3. **변화량 인디케이터:**
```javascript
// static/js/chatbot.js:952-972
function createStatChangeIndicator(statBar, change) {
  const indicator = document.createElement('div');
  indicator.className = 'stat-change-indicator';
  indicator.textContent = change > 0 ? `+${change}` : `${change}`;
  indicator.style.color = change > 0 ? '#4CAF50' : '#F44336';

  const container = statBar.parentElement;
  container.appendChild(indicator);

  // 1.2초 후 제거
  setTimeout(() => indicator.remove(), 1200);
}
```

4. **CSS 애니메이션:**
```css
@keyframes statIncrease {
  0%, 100% { box-shadow: 0 0 0 rgba(76, 175, 80, 0); }
  50% { box-shadow: 0 0 20px rgba(76, 175, 80, 0.8); }
}

.stat-increased {
  animation: statIncrease 0.6s ease;
}

.stat-change-indicator {
  position: absolute;
  right: 10px;
  font-weight: bold;
  animation: floatUp 1.2s ease-out forwards;
}

@keyframes floatUp {
  0% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-30px); }
}
```

**효과:**
- ✅ 스탯 증가: 녹색 펄스 + "+3" 인디케이터
- ✅ 스탯 감소: 빨간색 펄스 + "-5" 인디케이터
- ✅ 변화 없음: 애니메이션 없음
- ✅ 사용자 피드백: "뭔가 올랐다!"를 시각적으로 즉시 인지

**커밋:** [99b888d](https://github.com/eoeldroal/HomeRunBall-Chat/commit/99b888d)

---

### 개선 2: 게임 밸런스 조정

**문제 인식:**
- 초기 테스트 결과: 9월까지 도달해도 스탯이 40-50 수준
- KBO 드래프트 하위 라운드에만 진출 가능
- 플레이어가 성취감을 느끼기 어려움

**데이터 분석:**

| 항목 | Before | 문제점 |
|------|--------|--------|
| 초기 stamina | 80 | 너무 높아 훈련 필요성 낮음 |
| 훈련 상승치 | 1-4 | 너무 낮아 성장 체감 안 됨 |
| 대화 스탯 상승 | 1-2 | 대화의 효용성 낮음 |
| 최종 스탯 | 40-50 | 하위 라운드만 가능 |

**조정 내역:**

```python
# services/game_state.py:28-34 (초기 스탯)
Stats(
    intimacy=0,
    mental=35,      # 30 → 35 (+5)
    stamina=50,     # 80 → 50 (-30)
    batting=40,     # 35 → 40 (+5)
    speed=25,       # 40 → 25 (-15)
    defense=35      # 40 → 35 (-5)
)
```

```python
# services/training_manager.py:82-98 (훈련 상승치)
if intensity <= 40:
    base_gain = 2   # 1 → 2 (2배)
elif intensity <= 70:
    base_gain = 4   # 2 → 4 (2배)
elif intensity <= 85:
    base_gain = 6   # 3 → 6 (2배)
else:
    base_gain = 8   # 4 → 8 (2배)
```

```python
# services/stat_calculator.py:120-135 (대화 상승치)
if stat_name == 'intimacy' or stat_name == 'mental':
    if value_change > 0:
        changes[stat_name] = min(value_change * 2, 4)  # 1-2 → 2-4
```

**효과:**

| 항목 | Before | After | 변화 |
|------|--------|-------|------|
| 훈련 효율 | 낮음 | 높음 | **2배** |
| 체력 전략성 | 낮음 | 높음 | **체력 관리 필수** |
| 최종 스탯 | 40-50 | 60-75 | **중상위 라운드** |
| 플레이 시간 | 30분 | 20분 | **33% 단축** |

**커밋:** [6803109](https://github.com/eoeldroal/HomeRunBall-Chat/commit/6803109)

---

### 개선 3: 알림 자동 제거 시스템

**문제:**
- 이벤트/힌트 알림이 계속 쌓임
- 화면이 어지러움
- 사용자가 수동으로 닫아야 함

**구현:**

```javascript
// static/js/chatbot.js:311-320
function autoRemoveNotification(notifId, delay = 7000) {
  setTimeout(() => {
    const element = document.getElementById(notifId);
    if (element) {
      element.style.opacity = '0';
      element.style.transform = 'translateY(-20px)';
      setTimeout(() => element.remove(), 300);
    }
  }, delay);
}
```

**적용:**
```javascript
// 이벤트 알림 표시 후
showEventNotification(eventInfo);
autoRemoveNotification(notifId, 7000);

// 힌트 알림 표시 후
showHintWithContext(hintInfo);
autoRemoveNotification(notifId, 7000);

// 경고 알림 표시 후
showWarning(message);
autoRemoveNotification(notifId, 7000);
```

**효과:**
- ✅ 7초 후 자동 제거 (페이드아웃 + 슬라이드업)
- ✅ 화면 깔끔하게 유지
- ✅ 중요한 알림은 7초 내 충분히 읽을 수 있음

**커밋:** [4392da3](https://github.com/eoeldroal/HomeRunBall-Chat/commit/4392da3)

---

## 😔 아쉬웠던 점

### 1. 이미지 검색 기능 미구현

**계획:**
- 멀티모달 RAG: 텍스트 + 이미지 통합 검색
- CLIP 모델을 활용한 이미지 임베딩
- 사용자가 "경기 장면 보여줘" 입력 시 관련 이미지 자동 표시

**현실:**
- 시간 부족으로 텍스트 RAG만 구현
- 이미지는 스토리북에서만 수동으로 표시

---

### 2. 테스트 코드 부족

**현황:**
- 핵심 로직 (RAG 검색, 스탯 계산, 이벤트 감지)에 대한 단위 테스트 없음
- 수동 테스트로만 검증
- 리팩토링 시 기존 기능 동작 보장 어려움

**문제점:**
- 버그 발견이 늦어짐 (배포 후 발견)
- 코드 수정 시 사이드 이펙트 우려
- 협업 시 다른 사람이 내 코드 수정하기 어려움

**교훈:**
- TDD(Test-Driven Development) 방식의 필요성 체감
- 최소한 핵심 비즈니스 로직에는 테스트 필수

---

### 3. 모바일 반응형 디자인 미흡

**현황:**
- 데스크톱에서는 UI/UX 훌륭
- 모바일에서는 일부 요소가 잘림
  - 훈련 모달 버튼이 작음
  - 스탯 패널이 화면 밖으로 나감
  - 스토리북 이미지가 너무 큼

**문제점:**
- 모바일 사용자 경험 저하
- 실제 사용자의 70%가 모바일 접속

**교훈:**
- 초기 설계 단계에서 모바일 우선(Mobile First) 접근 필요
- CSS Grid/Flexbox를 더 적극 활용

**향후 계획:**
```css
/* 모바일 최적화 예시 */
@media (max-width: 768px) {
  .stat-panel {
    flex-direction: column;
    gap: 10px;
  }

  .training-modal {
    width: 95%;
    padding: 15px;
  }

  .storybook-image {
    max-width: 100%;
    height: auto;
  }
}
```

---

### 4. 엔딩 분기 자동화 부족

**현황:**
- 8월 대회 결과는 스탯 기반으로 자동 계산
- 9월 드래프트 결과는 수동으로 구현

**이상적인 구현:**
- 스탯 합산 로직으로 8가지 엔딩 자동 분기
- 각 엔딩마다 조건 설정 (메이저: 90+, 1라운드: 80+, ...)

**현실:**
- 시간 부족으로 스토리북에 하드코딩
- 엔딩 조건 변경 시 여러 곳 수정 필요

**교훈:**
- 게임 로직과 UI 로직 분리 필요
- 설정 파일로 엔딩 조건 관리

---

## 🤔 회고 및 성찰

### 기술적 성장

#### 1. RAG 이해도 향상

**Before:**
- 논문과 블로그 글로만 RAG 개념 학습
- "검색 + LLM"이라는 단순한 이해

**After:**
- 실제 구현을 통해 내부 동작 원리 완전 이해
- 벡터 임베딩 → 유사도 검색 → 프롬프트 주입 → LLM 호출의 전체 흐름 체화
- 토큰 효율성과 정확도의 트레이드오프 경험

**구체적 학습:**
- ChromaDB의 HNSW 알고리즘 (Hierarchical Navigable Small World)
- 코사인 유사도 vs 유클리드 거리 차이
- Top-K 검색에서 K값에 따른 성능 변화 (K=3이 최적)

#### 2. 프롬프트 엔지니어링 기술 향상

**시행착오:**
1. **초기 프롬프트:** "너는 서강태야. 차갑게 대답해."
   - 결과: 일관성 없음, 가끔 친절함
2. **구체화:** "겉으로는 차갑지만 속으로는 따뜻하다. 틱틱대는 말투를 사용한다."
   - 결과: 조금 나아짐
3. **예시 추가:** "좋은 예: '...괜찮아요.' / 나쁜 예: '정말 좋아요!'"
   - 결과: 톤이 일관적으로 유지됨
4. **친밀도 반영:** "친밀도 30 이하일 때는 차갑고, 60 이상일 때는 따뜻하게..."
   - 결과: ✅ 완벽한 캐릭터 일관성

**핵심 깨달음:**
- LLM에게 "이렇게 해"보다 "이렇게 하지 마"가 더 효과적
- 예시(Few-shot) 추가 시 답변 품질 30% 향상
- 시스템 프롬프트 최적화만으로 Fine-tuning 없이도 훌륭한 캐릭터 구현 가능

#### 3. 스트리밍 아키텍처 설계 경험

**Before:**
- 동기식 API만 다뤄봄 (요청 → 대기 → 응답)
- 스트리밍은 "실시간 데이터 전송" 정도로만 이해

**After:**
- SSE, WebSocket, Polling의 차이 명확히 이해
- 백엔드 Generator 패턴 (`yield`) 체화
- 프론트엔드 EventSource API 활용 능력 획득
- 비동기 처리의 중요성 (done 즉시 전송) 체득

**실전 적용:**
- 스트리밍 응답 시작 시간: 7초 → 2초 최적화
- 타임아웃 처리로 시스템 안정성 확보
- 이벤트 타입별 분리로 유연한 확장 가능

---

### 협업 경험

#### 1. Git 협업 실전 체험

**배운 점:**
- PR 리뷰를 통한 코드 품질 향상
  - 동료가 발견한 버그: "회복 세션 역설" 문제
  - 리뷰어의 제안으로 경고 시스템 도입
- 브랜치 전략 (`optimize-streaming-done`, `main`)
- 커밋 메시지 컨벤션 (`feat:`, `fix:`, `refactor:`)

**실수와 교훈:**
- LFS 실수로 이미지 19개 손실 → 커밋 메시지 꼼꼼히 확인 필요
- 충돌 해결 시 신중하지 못했음 → 항상 백업 브랜치 생성

#### 2. 프로듀서-엔지니어 협업

**역할 분담:**
- 프로듀서(HWI): 캐릭터 설정, 스토리, 이미지, 텍스트 데이터
- 엔지니어(본인): AI 로직, 게임 시스템, UI/UX

**효과:**
- 각자 전문 분야에 집중 → 효율성 2배
- 프로듀서가 작성한 캐릭터 설정을 RAG로 활용 → 답변 품질 향상
- 이미지 업로드(hwi0201) → 스토리북 시스템 구현(본인) → 빠른 통합

**배운 점:**
- 명확한 인터페이스 정의 중요 (`chatbot_config.json` 구조)
- 프로듀서가 쉽게 수정할 수 있도록 설정 파일 분리
- 기술 용어 설명의 중요성 (프로듀서가 이해할 수 있게)

---

### 아쉬운 점 및 개선 방향

#### 1. 시간 관리

**문제:**
- 초반에 RAG 구현에 과도한 시간 투자 (3일)
- 후반에 UI/UX 개선 시간 부족
- 테스트 코드 작성 시간 확보 실패

**교훈:**
- MVP(Minimum Viable Product) 먼저 완성 후 점진적 개선
- 타임박싱 기법 적용 (각 기능에 시간 제한 설정)
- 80/20 법칙: 핵심 20% 기능에 집중

**다음 프로젝트:**
- 첫 주: 핵심 기능 (대화, RAG)
- 둘째 주: 게임 시스템 (스탯, 훈련)
- 셋째 주: UI/UX 개선 및 테스트
- 마지막 3일: 버그 수정 및 배포

#### 2. 문서화

**문제:**
- 개발 중 문서화 소홀 → 나중에 README 일괄 작성
- 코드 주석 부족 → 3일 후 내 코드인데도 이해 어려움
- API 문서 없음 → 프론트 개발 시 백엔드 코드 확인 필요

**교훈:**
- 코드 작성과 동시에 주석 작성 습관화
- 함수마다 Docstring 필수
- API 엔드포인트는 Swagger/Postman으로 문서화

**개선 예시:**
```python
def execute(self, *, game_state, intensity: int, focuses: Sequence[str]) -> TrainingOutcome:
    """
    Run a training session and return the outcome.

    Args:
        game_state: GameState instance (mutated by caller after applying changes).
        intensity: 0-100 lever value chosen by the player.
        focuses: sequence of focus keys (batting, speed, defense).

    Returns:
        TrainingOutcome with stat changes and summary.

    Raises:
        ValueError: If training count exceeded or stamina too low (non-recovery).
    """
```

#### 3. 다음 프로젝트에서 시도할 것

1. **TDD 도입**: 테스트 먼저 작성 → 기능 구현
2. **애자일 스프린트**: 1주 단위로 목표 설정 및 회고
3. **코드 리뷰 강화**: PR마다 최소 2명 리뷰
4. **성능 모니터링**: 응답 시간, 에러율 측정 대시보드
5. **A/B 테스트**: 프롬프트 버전별 성능 비교

---

### 최종 소감

**가장 뿌듯했던 순간:**
- 스트리밍 최적화 후 응답 시간이 7초 → 2초로 줄었을 때
- 사용자가 "캐릭터가 진짜 살아있는 것 같다"는 피드백

**가장 힘들었던 순간:**
- Git LFS 문제로 이미지 19개 손실했을 때

**프로젝트를 통해 배운 것:**
1. **기술은 도구일 뿐**: RAG, LangChain이 중요한 게 아니라 사용자 경험이 중요
2. **완벽보다 완성**: 테스트 코드 없어도 일단 배포하고 개선
3. **문제 해결 능력**: LFS 문제, 스트리밍 병목 등 예상 못한 문제 직면 시 침착하게 분석
4. **AI 활용 능력**: Claude/ChatGPT로 코드 리뷰, 버그 찾기, 최적화 아이디어 얻음

**앞으로의 계획:**
- 이 프로젝트를 포트폴리오로 정리
- RAG 논문 깊이 읽기 (Self-RAG, RAPTOR 등)
- 다음 프로젝트: 음성 인식 + TTS 추가하여 음성 대화 챗봇 도전

---

## 📦 배포 및 실행

### ⚡ 빠른 시작 (Docker)

```bash
# 1. Clone
git clone https://github.com/eoeldroal/HomeRunBall-Chat.git
cd HomeRunBall-Chat

# 2. 환경변수 설정
cp .env.example .env
nano .env  # OPENAI_API_KEY 입력

# 3. Docker 실행
docker compose up --build

# 4. 브라우저에서 접속
http://localhost:5001
```

### 🌐 배포 (Render.com)

**배포 URL:** [https://three-character-chat.onrender.com]
---