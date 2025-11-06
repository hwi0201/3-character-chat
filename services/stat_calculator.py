"""
스탯 계산 시스템

LLM을 활용하여 사용자의 대화 내용을 분석하고,
선수 스탯에 미치는 영향을 자동으로 계산합니다.
"""

from typing import Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json


class StatCalculator:
    """
    대화 기반 스탯 변화 계산기

    사용자와 챗봇의 대화를 분석하여:
    1. 각 스탯에 미치는 영향 평가
    2. 변화량 계산
    3. 변화 이유 설명
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: ChatOpenAI 인스턴스
        """
        self.llm = llm

    def analyze_conversation(
        self,
        user_message: str,
        bot_reply: str,
        game_state,
        conversation_context: str = None
    ) -> Tuple[Dict[str, int], str]:
        """
        대화 내용을 분석하여 스탯 변화 계산

        Args:
            user_message: 사용자 메시지
            bot_reply: 봇 응답
            game_state: 현재 게임 상태
            conversation_context: 대화 맥락 (선택)

        Returns:
            (스탯 변화 딕셔너리, 설명 텍스트)
            예: ({"intimacy": +5, "mental": +3}, "긍정적인 격려로 자신감 상승")
        """

        # 현재 스탯 정보
        current_stats = {
            "intimacy": game_state.stats.intimacy,
            "mental": game_state.stats.mental,
            "stamina": game_state.stats.stamina,
            "batting": game_state.stats.batting,
            "speed": game_state.stats.speed,
            "defense": game_state.stats.defense
        }

        # LLM 프롬프트 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 야구 선수의 심리 상태를 분석하는 전문가입니다.

코치(사용자)와 선수(AI)의 대화를 분석하여, **친밀도(intimacy)와 멘탈(mental)**에 미치는 영향만 평가하세요.

**[중요]**
- 물리적 스탯(타격, 주루, 수비, 체력)은 별도의 훈련 시스템에서 관리됩니다.
- 당신은 **대화를 통한 감정적/심리적 변화만** 분석합니다.

**[분석 지침]**
- 일반적인 대화는 스탯 변화가 거의 없습니다.
- 깊은 감정적 교류가 있을 때만 큰 변화를 적용하세요.
- 선수의 트라우마(도루 공포증)와 관련된 대화는 멘탈에 큰 영향을 줍니다.
- 현재 친밀도가 낮으면 긍정적 대화의 효과도 제한적일 수 있습니다.

**[스탯 변화 규칙]**

1.  **친밀도(intimacy):**
    *  `+4`: 코치가 선수의 상태를 묻거나 단순 격려. (예: '컨디션 어때?', '힘내자', '오늘 훈련 어땠어?')
    *  `+10`: 코치가 선수의 재능을 인정하거나 진심으로 걱정. (예: '너의 스윙은 최고야', '무슨 일 있었어?')
    *  `+20`: 코치가 선수의 트라우마를 공감하고 위로. (예: '네 잘못이 아니야', '천천히 극복하면 돼')
    *  `-16`: 친밀도가 30 미만인데 트라우마를 강제로 캐물거나 무시하는 태도를 보일 때.
    *  `-10`: 선수의 감정을 무시하거나 차갑게 대할 때.

2.  **멘탈(mental):**
    *  `+6`: 코치가 진심 어린 격려와 응원을 할 때.
    *  `+10`: 코치가 명상, 휴식, 스트레스 관리를 권유할 때.
    *  `+16`: 선수의 두려움이나 불안을 공감하고 위로할 때.
    *  `+30`: 도루 트라우마 극복을 돕는 대화에 성공했을 때. (현재 친밀도가 50 이상)
    *  `-6`: 선수가 불안감이나 스트레스를 호소할 때.
    *  `-10`: 선수의 실수나 약점을 직접적으로 비난할 때.
    *  `-16`: 트라우마와 관련된 무신경한 발언을 할 때.

**[주의사항]**
- 훈련에 대한 언급('타격 훈련', '달리기', '수비 연습' 등)은 물리적 스탯에 영향을 주지 않습니다.
- 훈련 후 피로나 긍정적 대화만 친밀도와 멘탈에 영향을 줍니다.

**응답 형식 (JSON):**
반드시 아래 JSON 형식으로만 응답하세요.
{{
    "stat_changes": {{
        "intimacy": 0,
        "mental": 0
    }},
    "reason": "규칙에 기반한 변화 이유를 한 문장으로 설명"
}}"""),
            ("human", """[현재 게임 상태]
- 현재 시점: {current_month}월
- 현재 스탯: {current_stats}

[이번 대화]
코치(사용자): {user_message}
강태(AI): {bot_reply}

{context_info}

이 대화가 강태의 스탯에 미치는 영향을 분석해주세요.""")
        ])

        chain = prompt | self.llm

        try:
            # 컨텍스트 정보 구성
            context_info = f"[대화 맥락]\n{conversation_context}" if conversation_context else ""

            response = chain.invoke({
                "current_month": game_state.current_month,
                "current_stats": json.dumps(current_stats, ensure_ascii=False),
                "user_message": user_message,
                "bot_reply": bot_reply,
                "context_info": context_info
            })

            # JSON 파싱
            result = json.loads(response.content)
            stat_changes = result.get('stat_changes', {})
            reason = result.get('reason', '대화 분석 완료')

            # 0인 값 제거 (깔끔한 출력을 위해)
            stat_changes = {k: v for k, v in stat_changes.items() if v != 0}

            return (stat_changes, reason)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WARNING] 스탯 분석 실패 ({type(e).__name__}): {e}")
            return ({}, "스탯 분석 실패")

    def get_intimacy_level(self, intimacy: int) -> str:
        """
        친밀도 레벨 텍스트 반환

        Args:
            intimacy: 친밀도 값 (0-100)

        Returns:
            레벨 설명 문자열
        """
        if intimacy < 20:
            return "매우 낮음 - 거의 대화하지 않으려 함"
        elif intimacy < 40:
            return "낮음 - 방어적이고 거리를 둠"
        elif intimacy < 60:
            return "보통 - 조금씩 마음을 열기 시작"
        elif intimacy < 80:
            return "높음 - 신뢰하고 협조적"
        else:
            return "매우 높음 - 진심으로 존경하고 따름"
