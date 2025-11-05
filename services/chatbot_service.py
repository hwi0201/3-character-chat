"""
🎯 챗봇 서비스 - 구현 파일

이 파일은 챗봇의 핵심 AI 로직을 담당합니다.
아래 아키텍처를 참고하여 직접 설계하고 구현하세요.

📐 시스템 아키텍처:

┌─────────────────────────────────────────────────────────┐
│ 1. 초기화 단계 (ChatbotService.__init__)                  │
├─────────────────────────────────────────────────────────┤
│  - OpenAI Client 생성                                    │
│  - ChromaDB 연결 (벡터 데이터베이스)                       │
│  - LangChain Memory 초기화 (대화 기록 관리)               │
│  - Config 파일 로드                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 2. RAG 파이프라인 (generate_response 내부)               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  사용자 질문 "학식 추천해줘"                              │
│       ↓                                                  │
│  [_create_embedding()]                                   │
│       ↓                                                  │
│  질문 벡터: [0.12, -0.34, ..., 0.78]  (3072차원)        │
│       ↓                                                  │
│  [_search_similar()]  ← ChromaDB 검색                    │
│       ↓                                                  │
│  검색 결과: "학식은 곤자가가 맛있어" (유사도: 0.87)        │
│       ↓                                                  │
│  [_build_prompt()]                                       │
│       ↓                                                  │
│  최종 프롬프트 = 시스템 설정 + RAG 컨텍스트 + 질문        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 3. LLM 응답 생성                                         │
├─────────────────────────────────────────────────────────┤
│  OpenAI GPT-4 API 호출                                   │
│       ↓                                                  │
│  "학식은 곤자가에서 먹는 게 제일 좋아! 돈까스가 인기야"    │
│       ↓                                                  │
│  [선택: 이미지 검색]                                      │
│       ↓                                                  │
│  응답 반환: {reply: "...", image: "..."}                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 4. 메모리 저장 (LangChain Memory)                        │
├─────────────────────────────────────────────────────────┤
│  대화 기록에 질문-응답 저장                               │
│  다음 대화에서 컨텍스트로 활용                            │
└─────────────────────────────────────────────────────────┘


💡 핵심 구현 과제:

1. **Embedding 생성**
   - OpenAI API를 사용하여 텍스트를 벡터로 변환
   - 모델: text-embedding-3-large (3072차원)

2. **RAG 검색 알고리즘** ⭐ 가장 중요!
   - ChromaDB에서 유사 벡터 검색
   - 유사도 계산: similarity = 1 / (1 + distance)
   - threshold 이상인 문서만 선택

3. **LLM 프롬프트 설계**
   - 시스템 프롬프트 (캐릭터 설정)
   - RAG 컨텍스트 통합
   - 대화 기록 포함

4. **대화 메모리 관리**
   - LangChain의 ConversationSummaryBufferMemory 사용
   - 대화가 길어지면 자동으로 요약


📚 참고 문서:
- ARCHITECTURE.md: 시스템 아키텍처 상세 설명
- IMPLEMENTATION_GUIDE.md: 단계별 구현 가이드
- README.md: 프로젝트 개요


⚠️ 주의사항:
- 이 파일의 구조는 가이드일 뿐입니다
- 자유롭게 재설계하고 확장할 수 있습니다
- 단, generate_response() 함수 시그니처는 유지해야 합니다
  (app.py에서 호출하기 때문)
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import json

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent.parent


class ChatbotService:
    """
    챗봇 서비스 클래스
    
    이 클래스는 챗봇의 모든 AI 로직을 캡슐화합니다.
    
    주요 책임:
    1. OpenAI API 관리
    2. ChromaDB 벡터 검색
    3. LangChain 메모리 관리
    4. 응답 생성 파이프라인
    
    직접 구현해야 할 메서드:
    - __init__: 모든 구성 요소 초기화
    - _load_config: 설정 파일 로드
    - _init_chromadb: 벡터 데이터베이스 초기화
    - _create_embedding: 텍스트 → 벡터 변환
    - _search_similar: RAG 검색 수행 (핵심!)
    - _build_prompt: 프롬프트 구성
    - generate_response: 최종 응답 생성 (모든 로직 통합)
    """
    
    def __init__(self):
        """
        챗봇 서비스 초기화

        TODO: 다음 구성 요소들을 초기화하세요

        1. Config 로드
           - config/chatbot_config.json 파일 읽기
           - 챗봇 이름, 설명, 시스템 프롬프트 등

        2. OpenAI Client
           - API 키: os.getenv("OPENAI_API_KEY")
           - from openai import OpenAI
           - self.client = OpenAI(api_key=...)

        3. ChromaDB
           - 텍스트 임베딩 컬렉션 연결
           - 경로: static/data/chatbot/chardb_embedding
           - self.collection = ...

        4. LangChain Memory (선택)
           - ConversationSummaryBufferMemory
           - 대화 기록 관리
           - self.memory = ...

        힌트:
        - ChromaDB: import chromadb
        - LangChain: from langchain.memory import ConversationSummaryBufferMemory
        """
        print("[ChatbotService] 초기화 중... ")

        # 1. Config 로드
        self.config = self._load_config()
        print(f"[ChatbotService] Config 로드 완료: {self.config.get('name', 'Unknown')}")

        # 2. OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

        # 3. ChatOpenAI (LangChain) 초기화
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            api_key=api_key
        )
        print("[ChatbotService] ChatOpenAI (LangChain) 초기화 완료")

        # 4. OpenAI Client 초기화 (임베딩용)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        print("[ChatbotService] OpenAI Client 초기화 완료")

        # 5. ChromaDB 초기화
        try:
            self.collection = self._init_chromadb()
            print(f"[ChatbotService] ChromaDB 초기화 완료")
        except Exception as e:
            print(f"[ChatbotService] ChromaDB 초기화 실패 (컬렉션이 없을 수 있음): {e}")
            self.collection = None

        # 6. 세션 히스토리 저장소 초기화 (InMemoryChatMessageHistory)
        from langchain_core.chat_history import InMemoryChatMessageHistory

        # 각 사용자(session_id)별로 대화 내역을 저장하는 딕셔너리
        self.store = {}

        # 세션 히스토리 가져오기 함수
        def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
            if session_id not in self.store:
                self.store[session_id] = InMemoryChatMessageHistory()
            return self.store[session_id]

        self.get_session_history = get_session_history
        print("[ChatbotService] 세션 히스토리 저장소 초기화 완료")

        # 7. 게임 상태 관리자 초기화
        from .game_state_manager import GameStateManager
        save_dir = BASE_DIR / "static" / "data" / "game_states"
        self.game_manager = GameStateManager(save_dir)
        print("[ChatbotService] 게임 상태 관리자 초기화 완료")

        # 8. 이벤트 감지기 초기화
        from .event_detector import EventDetector
        self.event_detector = EventDetector(self.llm)
        print("[ChatbotService] 이벤트 감지기 초기화 완료")

        # 9. 스탯 계산기 초기화
        from .stat_calculator import StatCalculator
        self.stat_calculator = StatCalculator(self.llm)
        print("[ChatbotService] 스탯 계산기 초기화 완료")

        print("[ChatbotService] 초기화 완료")
    
    
    def _load_config(self):
        """
        설정 파일 로드

        TODO: config/chatbot_config.json 읽어서 반환

        반환값 예시:
        {
            "name": "김서강",
            "character": {...},
            "system_prompt": {...}
        }
        """
        config_path = BASE_DIR / "config" / "chatbot_config.json"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARNING] Config 로드 실패 ({type(e).__name__}): {e}")
            print(f"[WARNING] 기본 설정을 사용합니다")
            return {
                "name": "챗봇",
                "description": "기본 챗봇입니다.",
                "system_prompt": {
                    "base": "당신은 친절한 AI 어시스턴트입니다.",
                    "rules": ["친절하게 대화하세요"]
                }
            }
    
    
    def _init_chromadb(self):
        """
        ChromaDB 초기화 및 컬렉션 반환

        TODO:
        1. PersistentClient 생성
        2. 컬렉션 가져오기 (이름: "rag_collection")
        3. 컬렉션 반환

        힌트:
        - import chromadb
        - db_path = BASE_DIR / "static/data/chatbot/chardb_embedding"
        - client = chromadb.PersistentClient(path=str(db_path))
        - collection = client.get_collection(name="rag_collection")
        """
        import chromadb

        # ChromaDB 저장 경로
        db_path = BASE_DIR / "static" / "data" / "chatbot" / "chardb_embedding"

        # 디렉토리가 없으면 생성
        db_path.mkdir(parents=True, exist_ok=True)

        # ChromaDB 클라이언트 생성
        client = chromadb.PersistentClient(path=str(db_path))

        # 컬렉션 가져오기 (없으면 생성)
        try:
            collection = client.get_collection(name="rag_collection")
            print(f"[ChromaDB] 기존 컬렉션 로드: rag_collection (문서 수: {collection.count()})")
        except Exception:
            # 컬렉션이 없으면 새로 생성
            collection = client.create_collection(
                name="rag_collection",
                metadata={"description": "RAG용 텍스트 임베딩 컬렉션"}
            )
            print("[ChromaDB] 새 컬렉션 생성: rag_collection")

        return collection
    
    
    def _create_embedding(self, text: str) -> list:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            text (str): 임베딩할 텍스트

        Returns:
            list: 3072차원 벡터 (text-embedding-3-large 모델)

        TODO:
        1. OpenAI API 호출
        2. embeddings.create() 사용
        3. 벡터 반환

        힌트:
        - response = self.client.embeddings.create(
        -     input=[text],
        -     model="text-embedding-3-large"
        - )
        - return response.data[0].embedding
        """
        response = self.client.embeddings.create(
            input=[text],
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    
    
    def _search_similar(self, query: str, session_id: str, threshold: float = 0.45, top_k: int = 5):
        """
        RAG 검색: 유사한 문서 찾기 (핵심 메서드!)

        Args:
            query (str): 검색 질의
            threshold (float): 유사도 임계값 (0.3-0.5 권장)
            top_k (int): 검색할 문서 개수

        Returns:
            tuple: (document, similarity, metadata) 또는 (None, None, None)

        TODO: RAG 검색 알고리즘 구현

        1. 쿼리 임베딩 생성
           query_embedding = self._create_embedding(query)

        2. ChromaDB 검색
           results = self.collection.query(
               query_embeddings=[query_embedding],
               n_results=top_k,
               include=["documents", "distances", "metadatas"]
           )

        3. 유사도 계산 및 필터링
           for doc, dist, meta in zip(...):
               similarity = 1 / (1 + dist)  ← 유사도 공식!
               if similarity >= threshold:
                   ...

        4. 가장 유사한 문서 반환
           return (best_document, best_similarity, metadata)


        💡 핵심 개념:

        - Distance vs Similarity
          · ChromaDB는 "거리(distance)"를 반환 (작을수록 유사)
          · 우리는 "유사도(similarity)"로 변환 (클수록 유사)
          · 변환 공식: similarity = 1 / (1 + distance)

        - Threshold
          · 0.3: 매우 느슨한 매칭 (관련성 낮아도 OK)
          · 0.45: 적당한 매칭 (추천!)
          · 0.7: 매우 엄격한 매칭 (정확한 답만)

        - Top K
          · 5-10개 정도 검색
          · 그 중 threshold 넘는 것만 사용


        🐛 디버깅 팁:
        - print()로 검색 결과 확인
        - 유사도 값 확인 (너무 낮으면 threshold 조정)
        - 검색된 문서 내용 확인
        """
        # ChromaDB 컬렉션이 없거나 비어있으면 None 반환
        if self.collection is None or self.collection.count() == 0:
            print("[RAG] ChromaDB 컬렉션이 비어있거나 없습니다.")
            return (None, None, None)

        # 1. 쿼리 임베딩 생성
        query_embedding = self._create_embedding(query)

        # 2. ChromaDB 검색 (where 필터 적용)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        # 3. 유사도 계산 및 필터링
        if not results['documents'] or not results['documents'][0]:
            print(f"[RAG] ✗ 검색 결과가 없습니다.")
            return (None, None, None)
            
        documents = results['documents'][0]
        distances = results['distances'][0]
        metadatas = results['metadatas'][0] if results['metadatas'] and results['metadatas'][0] else [{}] * len(documents)

        best_document = None
        best_similarity = 0
        best_metadata = None

        for doc, dist, meta in zip(documents, distances, metadatas):
            similarity = 1 / (1 + dist)
            print(f"[RAG] 문서: {doc[:50]}... | 거리: {dist:.4f} | 유사도: {similarity:.4f}")

            if similarity >= threshold and similarity > best_similarity:
                best_document = doc
                best_similarity = similarity
                best_metadata = meta

        if best_document:
            print(f"[RAG] ✓ 유사 문서 발견 (유사도: {best_similarity:.4f})")
            return (best_document, best_similarity, best_metadata)
        else:
            print(f"[RAG] ✗ Threshold({threshold}) 이상인 문서가 없습니다.")
            return (None, None, None)
    # <<< 수정 끝 >>>
    
    
    def _build_prompt(self, context: str = None, session_id: str = None):
        """
        LangChain ChatPromptTemplate 구성

        Args:
            context (str): RAG 검색 결과 (선택)
            session_id (str): 사용자 세션 ID (게임 상태 로드용)

        Returns:
            ChatPromptTemplate: LangChain 프롬프트 템플릿

        설명:
        - SystemMessage: 시스템 프롬프트 + 게임 상태 + RAG 컨텍스트
        - MessagesPlaceholder: 대화 히스토리 자동 삽입 (RunnableWithMessageHistory가 처리)
        - HumanMessage: 사용자 입력
        """
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        system_parts = []
        
        if session_id:
            game_state = self.game_manager.get_or_create(session_id)

            system_prompt_config = self.config.get('system_prompt', {})
            base_prompt = system_prompt_config.get('base', '당신은 서강태입니다.')
            rules = system_prompt_config.get('rules', [])
            system_parts.append(base_prompt)
            if rules:
                system_parts.append("\n[대화 규칙]")
                for rule in rules:
                    system_parts.append(f"- {rule}")
            
            # AI에게 전달할 스탯 정보를 최신 버전으로 수정
            state_info = f"""

[현재 게임 상태]
- 현재 시점: {game_state.current_month}월
- 친밀도: {game_state.stats.intimacy}/100
- 멘탈: {game_state.stats.mental}/100
- 체력: {game_state.stats.stamina}/100
- 타격: {game_state.stats.batting}/100
- 주루: {game_state.stats.speed}/100
- 수비: {game_state.stats.defense}/100

[캐릭터 행동 가이드]
{self._get_behavior_guide(game_state)}
"""
            system_parts.append(state_info)

        # 3. RAG 검색 결과(context)가 있으면 프롬프트에 추가
        if context:
            system_parts.append(f"\n[참고 정보]\n{context}")

        system_message = "\n".join(system_parts)

        # 4. 최종 ChatPromptTemplate 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        return prompt
    # <<< 수정 끝 >>>


    def _get_behavior_guide(self, game_state) -> str:
        """
        친밀도에 따른 캐릭터 행동 가이드

        Args:
            game_state: GameState 객체

        Returns:
            행동 가이드 문자열
        """
        intimacy = game_state.stats.intimacy

        if intimacy < 30:
            return """차갑고 틱틱대는 말투를 유지하세요.
코치에게 방어적이고 거리를 둡니다.
싸가지 있어 보이지만, 완전히 무례하지는 않습니다.
짧고 퉁명스러운 대답을 선호합니다."""
        elif intimacy < 60:
            return """조금씩 마음을 열기 시작합니다.
가끔 솔직한 감정을 표현하지만 여전히 조심스럽습니다.
코치의 말에 귀를 기울이기 시작하지만 쉽게 인정하지는 않습니다."""
        else:
            return """협조적이고 따뜻한 태도를 보입니다.
코치를 신뢰하고 존중하며, 적극적으로 대화에 참여합니다.
야구에 대한 열정을 솔직하게 드러냅니다."""


    def generate_response(self, user_message: str, username: str = "사용자") -> dict:
        """
        사용자 메시지에 대한 챗봇 응답 생성 (LangChain LCEL 기반)

        Args:
            user_message (str): 사용자 입력
            username (str): 사용자 이름 (session_id로도 사용됨)

        Returns:
            dict: {
                'reply': str,       # 챗봇 응답 텍스트
                'image': str|None   # 이미지 경로 (선택)
            }


        ═══════════════════════════════════════════════════
        📋 LangChain LCEL 파이프라인
        ═══════════════════════════════════════════════════

        [1단계] 초기 메시지 처리
            - "init" 메시지는 인사말 반환

        [2단계] RAG 검색 수행
            - ChromaDB에서 유사 문서 검색
            - 컨텍스트가 있으면 프롬프트에 포함

        [3단계] ChatPromptTemplate 구성
            - SystemMessage + RAG 컨텍스트
            - MessagesPlaceholder (대화 히스토리)
            - HumanMessage (사용자 입력)

        [4단계] LCEL 체인 구성 및 실행
            - prompt | self.llm (파이프 연산자)
            - RunnableWithMessageHistory로 래핑
            - session_id=username으로 대화 컨텍스트 관리

        [5단계] 응답 반환
            - AIMessage에서 텍스트 추출
            - 자동으로 메모리에 저장됨 (RunnableWithMessageHistory가 처리)


        ═══════════════════════════════════════════════════
        💡 핵심 변경사항
        ═══════════════════════════════════════════════════

        1. OpenAI API 직접 호출 → LangChain ChatOpenAI 사용
        2. 수동 메모리 관리 → RunnableWithMessageHistory 자동 관리
        3. 문자열 프롬프트 → ChatPromptTemplate 사용
        4. 명령형 → 선언형 (LCEL)
        """
        print(f"\n{'='*50}")
        print(f"[USER] {username}: {user_message}")
        try:

            game_state = self.game_manager.get_or_create(username)
            conversation_history = self.get_session_history(username).messages
            event_info = self.event_detector.check_event(
                game_state=game_state,
                conversation_history=conversation_history
            )

            if event_info and event_info['event_key'] == '5월_갈등':
                print(f"[EVENT] 5월 메인 이벤트 발생! 스토리북 '5_main_event'를 재생합니다.")
                game_state.flags['backstory_revealed'] = True
                game_state.stats.apply_changes({"intimacy": 10})
                self.game_manager.save(username)
                
                return {
                    'reply': event_info['trigger_message'],
                    'storybook_id': '5_main_event'
                }

            if user_message.strip().lower() == "init":
                bot_name = self.config.get('name', '챗봇')
                greeting = "왜 오셨어요. 알아서 훈련하겠다고 말씀드렸잖아요."
                print(f"[BOT] (초기 인사) {greeting}")
                print(f"{'='*50}\n")
                return {
                    'reply': greeting,
                    'image': None
                }

            # [2단계] RAG 검색 수행
            # <<< 수정 시작: _search_similar 함수 호출 시 session_id(username) 전달 >>>
            # 수정된 _search_similar 함수가 대화 모드를 확인하려면 이 정보가 반드시 필요합니다.
            context, similarity, metadata = self._search_similar(
                query=user_message,
                session_id=username,
                threshold=0.45,
                top_k=5
            )
            # <<< 수정 끝 >>>

            has_context = (context is not None)

            # 디버깅 출력
            if has_context:
                print(f"[RAG] ✓ Context found (유사도: {similarity:.4f})")
                print(f"[RAG] Context preview: {context[:100]}...")
            else:
                print(f"[RAG] ✗ No context found (일반 대화 모드)")

            # [3단계] ChatPromptTemplate 구성 (게임 상태 포함)
            prompt = self._build_prompt(context=context, session_id=username)

            # [4단계] LCEL 체인 구성 및 실행
            print(f"[LLM] Building LangChain LCEL pipeline...")

            # LCEL: prompt | llm (파이프 연산자로 체인 구성)
            chain = prompt | self.llm

            # RunnableWithMessageHistory로 래핑 (대화 히스토리 자동 관리)
            from langchain_core.runnables.history import RunnableWithMessageHistory

            chain_with_history = RunnableWithMessageHistory(
                chain,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="history"
            )

            # 체인 실행 (session_id로 username 사용)
            print(f"[LLM] Invoking chain with session_id='{username}'...")
            response = chain_with_history.invoke(
                {"input": user_message},
                config={"configurable": {"session_id": username}}
            )

            # AIMessage에서 텍스트 추출
            reply = response.content

            print(f"[LLM] ✓ Response generated")
            print(f"[BOT] {reply[:100]}...")
            print(f"[MEMORY] ✓ Conversation automatically saved to session '{username}'")

            # [5단계] 스탯 변화 계산 및 적용
            game_state = self.game_manager.get_or_create(username)

            # 이전 스탯 저장 (변화량 계산용)
            old_stats = game_state.stats.to_dict()

            # LLM으로 스탯 변화 분석
            stat_changes, stat_reason = self.stat_calculator.analyze_conversation(
                user_message=user_message,
                bot_reply=reply,
                game_state=game_state
            )

            # 스탯 변화 적용
            if stat_changes:
                game_state.stats.apply_changes(stat_changes)
                print(f"[STAT] ✓ Stat changes applied: {stat_changes}")
                print(f"[STAT] Reason: {stat_reason}")
            else:
                print(f"[STAT] No stat changes")

            # [6단계] 게임 상태 저장
            self.game_manager.save(username)
            print(f"[GAME] ✓ Game state saved for '{username}'")

            # [7단계] 이벤트 감지 및 힌트 제공
            conversation_history = self.get_session_history(username).messages

            # 이벤트 체크
            event_info = self.event_detector.check_event(
                game_state=game_state,
                conversation_history=conversation_history,
                recent_messages=10
            )

            # 힌트 체크 (5번 이상 대화했을 때)
            hint = None
            if len(conversation_history) >= 5:
                hint = self.event_detector.get_hint(
                    game_state=game_state,
                    conversation_history=conversation_history,
                    stuck_threshold=5
                )

            if event_info:
                print(f"[EVENT] ✓ Event triggered: {event_info['event_name']}")
            if hint:
                print(f"[HINT] ✓ Hint provided: {hint}")

            # [8단계] 응답 반환 (디버그 정보 포함)
            print(f"{'='*50}\n")

            # 기본 응답
            response_dict = {
                'reply': reply,
                'image': None
            }

            # <<< 수정 시작: _search_similar 함수에 session_id(username) 전달 >>>
            # '어머니 대화 모드'인지 확인하기 위해 사용자 정보가 필요합니다.
            context, similarity, metadata = self._search_similar(
                query=user_message,
                session_id=username, # <<< 수정: session_id 전달
                threshold=0.45,
                top_k=5
            )
            # <<< 수정 끝 >>>

            # 이벤트 정보 추가 (있을 경우)
            if event_info:
                response_dict['event'] = event_info

            # 힌트 추가 (있을 경우)
            if hint:
                response_dict['hint'] = hint

            # 디버그 정보 추가 (개발 모드)
            response_dict['debug'] = {
                'game_state': {
                    'current_month': game_state.current_month,
                    'current_day': game_state.current_day,
                    'stats': game_state.stats.to_dict(),
                    'intimacy_level': self.stat_calculator.get_intimacy_level(game_state.stats.intimacy),
                    'months_until_draft': game_state.get_months_until_draft(),
                },
                'stat_changes': {
                    'changes': stat_changes,
                    'reason': stat_reason,
                    'old_stats': old_stats,
                    'new_stats': game_state.stats.to_dict()
                },
                'event_check': {
                    'triggered': event_info is not None,
                    'event_name': event_info['event_name'] if event_info else None
                },
                'hint_provided': hint is not None,
                'conversation_count': len(conversation_history),
                'event_history': game_state.event_history
            }

            return response_dict

        except Exception as e:
            print(f"[ERROR] 응답 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*50}\n")
            return {
                'reply': "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.",
                'image': None
            }

    def generate_response_stream(self, user_message: str, username: str = "사용자"):
        """
        LangChain 스트리밍을 사용한 실시간 응답 생성

        Args:
            user_message (str): 사용자 입력
            username (str): 사용자 이름 (session_id로도 사용됨)

        Yields:
            dict: 스트리밍 이벤트 데이터
                - type: 'token' | 'metadata' | 'error' | 'done'
                - content: 토큰 텍스트 또는 메타데이터
        """
        print(f"\n{'='*50}")
        print(f"[USER] {username}: {user_message} (STREAMING)")

        try:
            game_state = self.game_manager.get_or_create(username)
            conversation_history = self.get_session_history(username).messages
            event_info = self.event_detector.check_event(
                game_state=game_state,
                conversation_history=conversation_history
            )

            if event_info and event_info['event_key'] == '5월_갈등':
                print(f"[EVENT] 5월 메인 이벤트 발생! (스트림)")
                game_state.flags['backstory_revealed'] = True
                game_state.stats.apply_changes({"intimacy": 10})
                self.game_manager.save(username)

                response_dict = {
                    'reply': event_info['trigger_message'],
                    'storybook_id': '5_main_event'
                }
                yield {'type': 'full_response', 'content': response_dict}
                yield {'type': 'done', 'content': ''}
                return # 여기서 함수 종료

            # [1단계] 초기 메시지 처리
            if user_message.strip().lower() == "init":
                bot_name = self.config.get('name', '챗봇')
                greeting = "왜 오셨어요. 알아서 훈련하겠다고 말씀드렸잖아요."
                print(f"[BOT] (초기 인사) {greeting}")
                print(f"{'='*50}\n")

                # 초기 인사는 한번에 전송
                yield {
                    'type': 'token',
                    'content': greeting
                }
                yield {
                    'type': 'done',
                    'content': ''
                }
                return

            # <<< 수정 시작: _search_similar 함수에 session_id(username) 전달 >>>
            context, similarity, metadata = self._search_similar(
                query=user_message,
                session_id=username, # <<< 수정: session_id 전달
                threshold=0.45,
                top_k=5
            )
            # <<< 수정 끝 >>>

            has_context = (context is not None)

            if has_context:
                print(f"[RAG] ✓ Context found (유사도: {similarity:.4f})")
            else:
                print(f"[RAG] ✗ No context found (일반 대화 모드)")

            # [3단계] ChatPromptTemplate 구성
            prompt = self._build_prompt(context=context, session_id=username)

            # [4단계] LCEL 체인 구성
            print(f"[LLM] Building LangChain LCEL streaming pipeline...")

            chain = prompt | self.llm

            from langchain_core.runnables.history import RunnableWithMessageHistory

            chain_with_history = RunnableWithMessageHistory(
                chain,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="history"
            )

            # [5단계] 스트리밍 실행
            print(f"[LLM] Starting stream with session_id='{username}'...")

            full_response = ""  # 전체 응답 수집 (스탯 계산용)

            # 스트리밍으로 토큰 생성
            for chunk in chain_with_history.stream(
                {"input": user_message},
                config={"configurable": {"session_id": username}}
            ):
                # AIMessage 또는 AIMessageChunk에서 content 추출
                if hasattr(chunk, 'content'):
                    token = chunk.content
                    if token:  # 빈 토큰 필터링
                        full_response += token
                        yield {
                            'type': 'token',
                            'content': token
                        }

            print(f"[LLM] ✓ Stream completed")
            print(f"[BOT] {full_response[:100]}...")
            print(f"[MEMORY] ✓ Conversation automatically saved to session '{username}'")

            # [6단계] 스탯 변화 계산 및 적용
            game_state = self.game_manager.get_or_create(username)
            old_stats = game_state.stats.to_dict()

            stat_changes, stat_reason = self.stat_calculator.analyze_conversation(
                user_message=user_message,
                bot_reply=full_response,
                game_state=game_state
            )

            if stat_changes:
                game_state.stats.apply_changes(stat_changes)
                print(f"[STAT] ✓ Stat changes applied: {stat_changes}")
            else:
                print(f"[STAT] No stat changes")

            # [7단계] 게임 상태 저장
            self.game_manager.save(username)
            print(f"[GAME] ✓ Game state saved for '{username}'")

            # [8단계] 이벤트 감지 및 힌트 제공
            conversation_history = self.get_session_history(username).messages

            event_info = self.event_detector.check_event(
                game_state=game_state,
                conversation_history=conversation_history,
                recent_messages=10
            )

            hint = None
            if len(conversation_history) >= 5:
                hint = self.event_detector.get_hint(
                    game_state=game_state,
                    conversation_history=conversation_history,
                    stuck_threshold=5
                )

            if event_info:
                print(f"[EVENT] ✓ Event triggered: {event_info['event_name']}")
            if hint:
                print(f"[HINT] ✓ Hint provided: {hint}")

            # [9단계] 메타데이터 전송
            print(f"{'='*50}\n")

            metadata = {
                'debug': {
                    'game_state': {
                        'current_month': game_state.current_month,
                        'current_day': game_state.current_day,
                        'stats': game_state.stats.to_dict(),
                        'intimacy_level': self.stat_calculator.get_intimacy_level(game_state.stats.intimacy),
                        'months_until_draft': game_state.get_months_until_draft(),
                    },
                    'stat_changes': {
                        'changes': stat_changes,
                        'reason': stat_reason,
                        'old_stats': old_stats,
                        'new_stats': game_state.stats.to_dict()
                    },
                    'event_check': {
                        'triggered': event_info is not None,
                        'event_name': event_info['event_name'] if event_info else None
                    },
                    'hint_provided': hint is not None,
                    'conversation_count': len(conversation_history),
                    'event_history': game_state.event_history
                }
            }

            if event_info:
                metadata['event'] = event_info
            if hint:
                metadata['hint'] = hint

            yield {
                'type': 'metadata',
                'content': metadata
            }

            # [10단계] 완료 신호
            yield {
                'type': 'done',
                'content': ''
            }

        except Exception as e:
            print(f"[ERROR] 스트리밍 응답 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*50}\n")

            yield {
                'type': 'error',
                'content': "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요."
            }


# ============================================================================
# 싱글톤 패턴
# ============================================================================
# ChatbotService 인스턴스를 앱 전체에서 재사용
# (매번 새로 초기화하면 비효율적)

_chatbot_service = None

def get_chatbot_service():
    """
    챗봇 서비스 인스턴스 반환 (싱글톤)
    
    첫 호출 시 인스턴스 생성, 이후 재사용
    """
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service


# ============================================================================
# 테스트용 메인 함수
# ============================================================================

if __name__ == "__main__":
    """
    로컬 테스트용
    
    실행 방법:
    python services/chatbot_service.py
    """
    print("챗봇 서비스 테스트")
    print("=" * 50)
    
    service = get_chatbot_service()
    
    # 초기화 테스트
    response = service.generate_response("init", "테스터")
    print(f"초기 응답: {response}")
    
    # 일반 대화 테스트
    response = service.generate_response("안녕하세요!", "테스터")
    print(f"응답: {response}")
