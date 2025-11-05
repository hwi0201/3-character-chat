"""
이벤트 감지 시스템

LLM을 활용하여 대화 내용을 분석하고,
이벤트 발생 조건을 자동으로 판단합니다.
"""

from typing import Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json


class EventDetector:
    """
    대화 기반 이벤트 감지기

    매 대화마다 현재 상황을 분석하여:
    1. 이벤트 발생 조건 체크
    2. 사용자 행동 패턴 분석
    3. 필요시 힌트 제공
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: ChatOpenAI 인스턴스
        """
        self.llm = llm
        self.event_definitions = self._load_event_definitions()

    def _load_event_definitions(self) -> Dict:
        """
        이벤트 정의 로드

        각 월별로 발생 가능한 이벤트와 조건을 정의합니다.
        """
        return {
            "3월_종료": {
                "name": "3월 종료 - 4월 훈련 시작",
                "conditions": [
                    "3월에 최소 5번 이상 대화했다",
                    "강태와 기본적인 소개는 끝났다",
                    "친밀도가 일정 수준 이상이거나, 대화가 반복되고 있다"
                ],
                "trigger_message": "강태와 충분히 대화를 나눴습니다. 이제 본격적인 4월 훈련을 시작할까요?",
                "hints": [
                    "강태의 야구 실력에 대해 물어보세요",
                    "앞으로의 목표에 대해 이야기해보세요",
                    "간단한 격려의 말을 건네보세요"
                ]
            },
            "5월_갈등": {
                "name": "5월 갈등 이벤트",
                "conditions": [
                    "5월이다",
                    "최소 3번 이상 훈련 관련 대화를 나눴다",
                    "강태가 코치를 어느 정도 신뢰하기 시작했다"
                ],
                "trigger_message": "강태에게 무슨 일이 생긴 것 같습니다...",
                "hints": [
                    "강태의 과거에 대해 물어보세요",
                    "강태의 가족 이야기를 들어보세요",
                    "훈련 중 강태의 태도 변화를 관찰해보세요"
                ]
            }
        }

    def check_event(
        self,
        game_state,
        conversation_history: list,
        recent_messages: int = 10
    ) -> Optional[Dict]:
        """
        이벤트 발생 조건 체크

        Args:
            game_state: GameState 객체
            conversation_history: 전체 대화 히스토리
            recent_messages: 최근 N개 메시지 분석

        Returns:
            이벤트 정보 딕셔너리 또는 None
        """
        # 현재 월에 해당하는 이벤트 찾기
        current_month = game_state.current_month
        event_key = None

        # 3월이고 아직 4월로 안 넘어갔으면
        if current_month == 3 and "march_completed" not in game_state.event_history:
            event_key = "3월_종료"
        # 5월이고 갈등 이벤트를 안 봤으면
        elif current_month == 5 and "conflict_event" not in game_state.event_history:
            event_key = "5월_갈등"

        if not event_key:
            return None

        event_def = self.event_definitions.get(event_key)
        if not event_def:
            return None

        # LLM에게 조건 충족 여부 판단 요청
        is_triggered, reason = self._analyze_conditions(
            event_def,
            game_state,
            conversation_history[-recent_messages:] if len(conversation_history) > recent_messages else conversation_history
        )

        if is_triggered:
            return {
                'event_key': event_key,
                'event_name': event_def['name'],
                'trigger_message': event_def['trigger_message'],
                'reason': reason
            }

        return None

    def _analyze_conditions(
        self,
        event_def: Dict,
        game_state,
        recent_messages: list
    ) -> Tuple[bool, str]:
        """
        LLM을 사용하여 이벤트 조건 충족 여부 분석

        Args:
            event_def: 이벤트 정의
            game_state: 게임 상태
            recent_messages: 최근 대화 내역

        Returns:
            (조건 충족 여부, 이유)
        """

        # 대화 히스토리 요약 (이미 recent_messages로 제한되어 넘어옴)
        conversation_summary = "\n".join([
            f"{msg.type}: {msg.content[:100]}"
            for msg in recent_messages
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 게임 이벤트 발생 조건을 판단하는 전문가입니다.

주어진 게임 상태와 대화 내용을 분석하여, 이벤트 발생 조건이 충족되었는지 판단하세요.

응답 형식 (JSON):
{{
    "triggered": true 또는 false,
    "reason": "판단 이유를 한 문장으로",
    "confidence": 0.0~1.0 (확신도)
}}

조건이 대부분(70% 이상) 충족되었다고 판단되면 triggered를 true로 설정하세요."""),
            ("human", """[이벤트]: {event_name}

[발생 조건]
{conditions}

[현재 게임 상태]
- 현재 월: {current_month}월
- 친밀도: {intimacy}/100
- 총 대화 횟수: {conversation_count}회
- 이벤트 히스토리: {event_history}

[최근 대화 내용]
{conversation_summary}

이벤트를 발동시켜야 할까요?""")
        ])

        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "event_name": event_def['name'],
                "conditions": "\n".join([f"- {cond}" for cond in event_def['conditions']]),
                "current_month": game_state.current_month,
                "intimacy": game_state.stats.intimacy,
                "conversation_count": len(recent_messages),
                "event_history": ", ".join(game_state.event_history) if game_state.event_history else "없음",
                "conversation_summary": conversation_summary if conversation_summary else "대화 없음"
            })

            # JSON 파싱
            result = json.loads(response.content)
            triggered = result.get('triggered', False)
            reason = result.get('reason', '')
            confidence = result.get('confidence', 0.0)

            # 확신도가 0.7 이상일 때만 발동
            return (triggered and confidence >= 0.7, reason)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WARNING] 이벤트 조건 분석 실패 ({type(e).__name__}): {e}")
            return (False, "분석 실패")

    def get_hint(
        self,
        game_state,
        conversation_history: list,
        stuck_threshold: int = 5
    ) -> Optional[str]:
        """
        사용자가 진행을 못 하고 있으면 힌트 제공

        Args:
            game_state: 게임 상태
            conversation_history: 대화 히스토리
            stuck_threshold: N번 이상 비슷한 대화 반복 시 힌트

        Returns:
            힌트 메시지 또는 None
        """

        # 최근 대화가 충분하지 않으면 힌트 제공 안 함
        if len(conversation_history) < stuck_threshold:
            return None

        # 현재 월에 해당하는 이벤트 찾기
        current_month = game_state.current_month
        event_key = None

        if current_month == 3 and "march_completed" not in game_state.event_history:
            event_key = "3월_종료"
        elif current_month == 5 and "conflict_event" not in game_state.event_history:
            event_key = "5월_갈등"

        if not event_key:
            return None

        event_def = self.event_definitions.get(event_key)
        if not event_def:
            return None

        # LLM에게 사용자가 막혔는지 판단 요청
        recent = conversation_history[-stuck_threshold:]
        conversation_summary = "\n".join([
            f"{msg.type}: {msg.content[:100]}"
            for msg in recent
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 사용자의 행동 패턴을 분석하는 전문가입니다.

최근 대화 내용을 보고, 사용자가:
1. 같은 주제로만 반복해서 대화하고 있는가?
2. 진행 방향을 못 찾고 있는가?
3. 이벤트 발동을 위한 조건을 충족시키지 못하고 있는가?

판단하여 JSON으로 응답하세요:
{{
    "is_stuck": true 또는 false,
    "reason": "판단 이유"
}}"""),
            ("human", """[목표 이벤트]: {event_name}

[발생 조건]
{conditions}

[최근 대화 내용]
{conversation_summary}

사용자가 막혀있나요?""")
        ])

        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "event_name": event_def['name'],
                "conditions": "\n".join([f"- {cond}" for cond in event_def['conditions']]),
                "conversation_summary": conversation_summary
            })

            result = json.loads(response.content)
            is_stuck = result.get('is_stuck', False)

            if is_stuck:
                # 힌트 중 하나를 랜덤으로 선택
                import random
                hints = event_def.get('hints', [])
                if hints:
                    return f"💡 힌트: {random.choice(hints)}"

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WARNING] 힌트 생성 실패 ({type(e).__name__}): {e}")

        return None
