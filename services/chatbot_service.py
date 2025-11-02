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

        # 2. OpenAI Client 초기화
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)
        print("[ChatbotService] OpenAI Client 초기화 완료")

        # 3. ChromaDB 초기화
        try:
            self.collection = self._init_chromadb()
            print(f"[ChatbotService] ChromaDB 초기화 완료")
        except Exception as e:
            print(f"[ChatbotService] ChromaDB 초기화 실패 (컬렉션이 없을 수 있음): {e}")
            self.collection = None

        # 4. LangChain Memory 초기화 (선택)
        try:
            from langchain.memory import ConversationBufferMemory
            from langchain_openai import ChatOpenAI

            # 메모리 초기화 (간단한 버퍼 메모리 사용)
            self.memory = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
            print("[ChatbotService] LangChain Memory 초기화 완료")
        except Exception as e:
            print(f"[ChatbotService] LangChain Memory 초기화 실패 (선택 사항): {e}")
            self.memory = None

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
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"[ERROR] 설정 파일을 찾을 수 없습니다: {config_path}")
            # 기본 설정 반환
            return {
                "name": "챗봇",
                "description": "기본 챗봇입니다.",
                "system_prompt": {
                    "base": "당신은 친절한 AI 어시스턴트입니다.",
                    "rules": ["친절하게 대화하세요"]
                }
            }
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 오류: {e}")
            return {
                "name": "챗봇",
                "system_prompt": {"base": "당신은 친절한 AI 어시스턴트입니다."}
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
        try:
            response = self.client.embeddings.create(
                input=[text],
                model="text-embedding-3-large"
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            print(f"[ERROR] 임베딩 생성 실패: {e}")
            raise
    
    
    def _search_similar(self, query: str, threshold: float = 0.45, top_k: int = 5):
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
        # ChromaDB 컬렉션이 없으면 None 반환
        if self.collection is None:
            print("[RAG] ChromaDB 컬렉션이 없습니다.")
            return (None, None, None)

        # 컬렉션이 비어있으면 None 반환
        if self.collection.count() == 0:
            print("[RAG] ChromaDB 컬렉션이 비어있습니다. 문서를 추가해주세요.")
            return (None, None, None)

        try:
            # 1. 쿼리 임베딩 생성
            query_embedding = self._create_embedding(query)

            # 2. ChromaDB 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )

            # 3. 유사도 계산 및 필터링
            documents = results['documents'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)

            # 가장 유사한 문서 찾기
            best_document = None
            best_similarity = 0
            best_metadata = None

            for doc, dist, meta in zip(documents, distances, metadatas):
                # 유사도 계산 (거리 → 유사도 변환)
                similarity = 1 / (1 + dist)

                print(f"[RAG] 문서: {doc[:50]}... | 거리: {dist:.4f} | 유사도: {similarity:.4f}")

                # Threshold 이상인 것만 선택
                if similarity >= threshold and similarity > best_similarity:
                    best_document = doc
                    best_similarity = similarity
                    best_metadata = meta

            # 4. 결과 반환
            if best_document:
                print(f"[RAG] ✓ 유사 문서 발견 (유사도: {best_similarity:.4f})")
                print(f"[RAG] 문서 내용: {best_document[:100]}...")
                return (best_document, best_similarity, best_metadata)
            else:
                print(f"[RAG] ✗ Threshold({threshold}) 이상인 문서가 없습니다.")
                return (None, None, None)

        except Exception as e:
            print(f"[ERROR] RAG 검색 실패: {e}")
            return (None, None, None)
    
    
    def _build_prompt(self, user_message: str, context: str = None, username: str = "사용자"):
        """
        LLM 프롬프트 구성

        Args:
            user_message (str): 사용자 메시지
            context (str): RAG 검색 결과 (선택)
            username (str): 사용자 이름

        Returns:
            str: 최종 프롬프트

        TODO:
        1. 시스템 프롬프트 가져오기 (config에서)
        2. RAG 컨텍스트 포함 여부 결정
        3. 대화 기록 포함 (선택)
        4. 최종 프롬프트 문자열 반환

        프롬프트 예시:
        ```
        당신은 서강대학교 선배 김서강입니다.
        신입생들에게 학교 생활을 알려주는 역할을 합니다.

        [참고 정보]  ← RAG 컨텍스트가 있을 때만
        학식은 곤자가가 맛있어. 돈까스가 인기야.

        사용자: 학식 추천해줘
        ```
        """
        # 1. 시스템 프롬프트 가져오기
        system_prompt = self.config.get('system_prompt', {})
        base_prompt = system_prompt.get('base', '당신은 친절한 AI 어시스턴트입니다.')
        rules = system_prompt.get('rules', [])

        # 시스템 프롬프트 구성
        prompt_parts = [base_prompt]

        # 규칙이 있으면 추가
        if rules:
            prompt_parts.append("\n[대화 규칙]")
            for rule in rules:
                prompt_parts.append(f"- {rule}")

        # 2. RAG 컨텍스트 포함
        if context:
            prompt_parts.append(f"\n[참고 정보]\n{context}")

        # 3. 대화 기록 포함 (선택)
        if self.memory:
            try:
                chat_history = self.memory.load_memory_variables({})
                if chat_history and 'chat_history' in chat_history:
                    history = chat_history['chat_history']
                    if history:
                        prompt_parts.append("\n[최근 대화]")
                        # 최근 3개 메시지만 포함
                        recent_messages = history[-6:] if len(history) > 6 else history
                        for msg in recent_messages:
                            role = "사용자" if msg.type == "human" else "챗봇"
                            prompt_parts.append(f"{role}: {msg.content}")
            except Exception as e:
                print(f"[WARN] 대화 기록 로드 실패: {e}")

        # 4. 사용자 메시지 추가
        prompt_parts.append(f"\n{username}: {user_message}")

        # 최종 프롬프트 반환
        final_prompt = "\n".join(prompt_parts)
        return final_prompt
    
    
    def generate_response(self, user_message: str, username: str = "사용자") -> dict:
        """
        사용자 메시지에 대한 챗봇 응답 생성
        
        Args:
            user_message (str): 사용자 입력
            username (str): 사용자 이름
        
        Returns:
            dict: {
                'reply': str,       # 챗봇 응답 텍스트
                'image': str|None   # 이미지 경로 (선택)
            }
        
        
        TODO: 전체 응답 생성 파이프라인 구현
        
        
        ═══════════════════════════════════════════════════
        📋 구현 단계
        ═══════════════════════════════════════════════════
        
        [1단계] 초기 메시지 처리
        
            if user_message.strip().lower() == "init":
                # 첫 인사말 반환
                bot_name = self.config.get('name', '챗봇')
                return {
                    'reply': f"안녕! 나는 {bot_name}이야.",
                    'image': None
                }
        
        
        [2단계] RAG 검색 수행
        
            context, similarity, metadata = self._search_similar(
                query=user_message,
                threshold=0.45,
                top_k=5
            )
            
            has_context = (context is not None)
        
        
        [3단계] 프롬프트 구성
        
            prompt = self._build_prompt(
                user_message=user_message,
                context=context,
                username=username
            )
        
        
        [4단계] LLM API 호출
        
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 gpt-4
                messages=[
                    {"role": "system", "content": "시스템 프롬프트"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            reply = response.choices[0].message.content
        
        
        [5단계] 메모리 저장 (선택)
        
            if self.memory:
                self.memory.save_context(
                    {"input": user_message},
                    {"output": reply}
                )
        
        
        [6단계] 응답 반환
        
            return {
                'reply': reply,
                'image': None  # 이미지 검색 로직 추가 가능
            }
        
        
        ═══════════════════════════════════════════════════
        💡 핵심 포인트
        ═══════════════════════════════════════════════════
        
        1. RAG 활용
           - 검색 결과가 있으면 프롬프트에 포함
           - 없으면 일반 대화 모드
        
        2. 에러 처리
           - try-except로 API 오류 처리
           - 실패 시 기본 응답 반환
        
        3. 로깅
           - 각 단계마다 print()로 상태 출력
           - 디버깅에 매우 유용!
        
        4. 확장성
           - 이미지 검색 로직 추가 가능
           - 감정 분석 추가 가능
           - 다중 언어 지원 가능
        
        
        ═══════════════════════════════════════════════════
        🐛 디버깅 예시
        ═══════════════════════════════════════════════════

        print(f"\n{'='*50}")
        print(f"[USER] {username}: {user_message}")
        print(f"[RAG] Context found: {has_context}")
        if has_context:
            print(f"[RAG] Similarity: {similarity:.4f}")
            print(f"[RAG] Context: {context[:100]}...")
        print(f"[LLM] Calling API...")
        print(f"[BOT] {reply}")
        print(f"{'='*50}\n")
        """

        print(f"\n{'='*50}")
        print(f"[USER] {username}: {user_message}")

        try:
            # [1단계] 초기 메시지 처리
            if user_message.strip().lower() == "init":
                bot_name = self.config.get('name', '챗봇')
                greeting = f"안녕! 나는 {bot_name}이야. 무엇이든 물어봐!"
                print(f"[BOT] (초기 인사) {greeting}")
                print(f"{'='*50}\n")
                return {
                    'reply': greeting,
                    'image': None
                }

            # [2단계] RAG 검색 수행
            context, similarity, metadata = self._search_similar(
                query=user_message,
                threshold=0.45,
                top_k=5
            )

            has_context = (context is not None)

            # [3단계] 프롬프트 구성
            prompt = self._build_prompt(
                user_message=user_message,
                context=context,
                username=username
            )

            # 디버깅 출력
            if has_context:
                print(f"[RAG] ✓ Context found (유사도: {similarity:.4f})")
                print(f"[RAG] Context preview: {context[:100]}...")
            else:
                print(f"[RAG] ✗ No context found (일반 대화 모드)")

            # [4단계] LLM API 호출
            print(f"[LLM] Calling OpenAI API...")

            # 시스템 프롬프트 추출
            system_prompt_config = self.config.get('system_prompt', {})
            system_message = system_prompt_config.get('base', '당신은 친절한 AI 어시스턴트입니다.')

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            reply = response.choices[0].message.content

            print(f"[LLM] ✓ Response generated")
            print(f"[BOT] {reply[:100]}...")

            # [5단계] 메모리 저장 (선택)
            if self.memory:
                try:
                    self.memory.save_context(
                        {"input": user_message},
                        {"output": reply}
                    )
                    print(f"[MEMORY] ✓ Conversation saved")
                except Exception as e:
                    print(f"[WARN] 메모리 저장 실패: {e}")

            # [6단계] 응답 반환
            print(f"{'='*50}\n")
            return {
                'reply': reply,
                'image': None  # 이미지 검색 로직은 추후 추가 가능
            }

        except Exception as e:
            print(f"[ERROR] 응답 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*50}\n")
            return {
                'reply': "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.",
                'image': None
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
