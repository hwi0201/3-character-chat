# --- START OF FILE services/game_event_manager.py ---

from typing import Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import random

class GameEventManager:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def calculate_at_bat_result(self, advice: str, stamina: int) -> Tuple[str, Dict]:
        """
        사용자의 조언과 선수의 체력을 바탕으로 타석 결과를 확률적으로 계산합니다.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 프로야구 코칭 전문가입니다. 선수의 현재 상태와 코치의 조언을 분석하여, 조언의 질을 세 가지 항목으로 평가하고 JSON 형식으로만 응답해야 합니다.

1.  **정서적 톤 (1-3점):** 조언이 얼마나 따뜻하고 선수에게 자신감을 주는가? (격려, 믿음 표현 시 고득점)
2.  **실질적 조언 (1-3점):** 조언이 얼마나 구체적이고 실질적인 도움이 되는가? (뜬구름 잡는 소리는 저득점)
3.  **관계적 신뢰 (1-3점):** 조언이 선수를 지지하고 신뢰하는 마음을 보여주는가? (비난, 압박 시 저득점)

**응답 형식 (JSON ONLY):**
{{
  "tone_score": 점수,
  "advice_score": 점수,
  "trust_score": 점수
}}"""),
            ("human", "선수의 현재 체력은 {stamina}/100 입니다. 코치가 다음과 같이 조언했습니다:\n\n\"{advice}\"\n\n위 조언을 세 가지 항목으로 평가하여 점수를 매겨주세요.")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"advice": advice, "stamina": stamina})
            scores = json.loads(response.content)
            
            # 1. 조언 점수 계산
            total_score = scores.get('tone_score', 1) + scores.get('advice_score', 1) + scores.get('trust_score', 1)
            
            # 2. 멘탈 계수 (M) 계산
            if total_score <= 3: m_coeff = 0.6
            elif total_score <= 6: m_coeff = 1.0
            else: m_coeff = 1.4
            
            # 3. 피지컬 계수 (P) 계산
            if stamina <= 40: p_coeff = 0.7
            elif stamina <= 70: p_coeff = 1.0
            else: p_coeff = 1.3
            
            # 4. 최종 확률 계산
            homerun_prob = round(10 * m_coeff * p_coeff)
            hit_prob = round(30 * m_coeff * p_coeff)
            
            # 확률 정규화 (합이 100을 넘지 않도록)
            if homerun_prob + hit_prob >= 99:
                homerun_prob = min(homerun_prob, 40) # 홈런 최대 확률 40%로 제한
                hit_prob = 99 - homerun_prob
            
            strikeout_prob = 100 - (homerun_prob + hit_prob)
            
            # 5. 확률에 따라 최종 결과 결정
            outcomes = ["homerun", "hit", "strikeout"]
            weights = [homerun_prob, hit_prob, strikeout_prob]
            final_result = random.choices(outcomes, weights=weights, k=1)[0]
            
            # 디버깅 및 결과 확인을 위한 상세 정보
            details = {
                "scores": scores,
                "total_score": total_score,
                "m_coeff": m_coeff,
                "p_coeff": p_coeff,
                "probabilities": {"homerun": homerun_prob, "hit": hit_prob, "strikeout": strikeout_prob}
            }
            
            print(f"[8월 이벤트] 조언 분석 결과: {details}")
            print(f"[8월 이벤트] 최종 결과: {final_result.upper()}")

            return final_result, details

        except Exception as e:
            print(f"[ERROR] 8월 이벤트 결과 계산 실패: {e}")
            return "strikeout", {} # 오류 발생 시 최악의 결과 반환

    # <<< 수정 시작: '안타' 이후 '도루' 결과를 계산하는 새로운 함수 추가 >>>
    # 이유: 8월 이벤트의 2단계 분기("안타 -> 도루 시도")를 처리하기 위한 핵심 로직입니다.
    def calculate_steal_result(self, game_state) -> Tuple[str, Dict]:
        """
        선수의 스탯을 바탕으로 도루 성공 여부를 확률적으로 계산합니다.
        (기획: "겁에 질려 도루 시도 안 함" vs "도루 성공")
        """
        stats = game_state.stats
        
        # 도루 성공률 계산: (주루 능력 + 멘탈 + 친밀도/5) / 3 이 베이스 확률
        # 주루 능력이 가장 중요 (가중치 1.5), 멘탈은 극복 의지, 친밀도는 코치에 대한 믿음
        base_prob = (stats.speed * 1.5 + stats.mental + (stats.intimacy / 5)) / 3
        
        # 도루 공포증 극복 여부에 따라 큰 보너스/페널티 적용
        if game_state.flags.get('steal_phobia_overcome', False):
            success_prob = min(base_prob + 20, 95) # 극복 시 확률 대폭 상승 (최대 95%)
        else:
            success_prob = max(base_prob - 15, 5)  # 미극복 시 확률 대폭 하락 (최소 5%)

        success_prob = round(success_prob)
        fail_prob = 100 - success_prob
        
        # 확률에 따라 최종 결과 결정
        outcomes = ["steal_success", "steal_fail"]
        weights = [success_prob, fail_prob]
        final_result = random.choices(outcomes, weights=weights, k=1)[0]
        
        details = {
            "base_prob": base_prob,
            "final_prob": success_prob,
            "overcome_phobia": game_state.flags.get('steal_phobia_overcome', False)
        }
        
        print(f"[도루 이벤트] 계산 결과: {details}")
        print(f"[도루 이벤트] 최종 결과: {final_result.upper()}")
        
        return final_result, details
    # <<< 수정 끝 >>>

# 싱글톤 패턴으로 관리 (선택 사항이지만 권장)
_game_event_manager = None

def get_game_event_manager() -> GameEventManager:
    global _game_event_manager
    if _game_event_manager is None:
        from langchain_openai import ChatOpenAI
        import os
        # <<< 수정 시작: 싱글톤 생성 시에도 GameEventManager를 올바르게 호출하도록 수정 >>>
        # 이유: 이전에 llm 인스턴스를 직접 넘겨주지 않아 발생할 수 있는 오류를 방지합니다.
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=os.getenv("OPENAI_API_KEY"))
        _game_event_manager = GameEventManager(llm=llm)
        # <<< 수정 끝 >>>
    return _game_event_manager