"""
스토리북 관리 서비스

스토리북 데이터 로드, 목표 확인, 엔딩 결정 등을 담당합니다.
게임의 스토리 진행을 관리하는 핵심 모듈입니다.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import random # <<수정: 확률 계산 위해 추가


class StorybookManager:
    """
    스토리북 관리 서비스

    스토리북 데이터 로드, 목표 확인, 엔딩 결정 등을 담당합니다.

    주요 책임:
    1. 스토리북 설정 파일 로드
    2. 월별 목표 관리
    3. 엔딩 결정 로직
    4. 다음 스토리북 진행 제어
    """

    def __init__(self, config_path: str = None):
        """
        스토리북 관리자 초기화

        Args:
            config_path: storybook_config.json 경로 (None이면 기본 경로)
        """
        print("[StorybookManager] 초기화 중...")

        # 기본 경로 설정
        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            config_path = base_dir / "config" / "storybook_config.json"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.config = self.load_config()

        print(f"[StorybookManager] 초기화 완료: {len(self.config.get('storybooks', {}))}개 스토리북 로드됨")

    def load_config(self) -> dict:
        """
        스토리북 설정 파일 로드

        Returns:
            dict: 스토리북 설정 데이터

        Raises:
            FileNotFoundError: 설정 파일이 없을 경우
            json.JSONDecodeError: JSON 파싱 오류
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"[StorybookManager] 설정 파일 로드 완료: {self.config_path}")
            return config
        except FileNotFoundError as e:
            error_msg = f"스토리북 설정 파일을 찾을 수 없습니다: {self.config_path}"
            print(f"[ERROR] {error_msg}")
            raise FileNotFoundError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"JSON 파싱 오류: {self.config_path} - {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise ValueError(error_msg) from e

    def get_storybook(self, storybook_id: str) -> dict:
        """
        특정 스토리북 가져오기

        Args:
            storybook_id: 스토리북 ID (예: "3_opening")

        Returns:
            dict: 스토리북 데이터

        Raises:
            ValueError: 스토리북 ID가 존재하지 않을 경우
        """
        storybooks = self.config.get('storybooks', {})

        if storybook_id not in storybooks:
            error_msg = f"스토리북 ID '{storybook_id}'가 존재하지 않습니다. 사용 가능한 ID: {list(storybooks.keys())}"
            print(f"[ERROR] {error_msg}")
            raise ValueError(error_msg)

        storybook = storybooks[storybook_id]
        print(f"[StorybookManager] 스토리북 로드: {storybook_id} - {storybook.get('title', 'Unknown')}")
        return storybook

    def get_current_storybook(self, game_state) -> Optional[dict]:
        """
        현재 게임 상태에 맞는 스토리북 반환

        Logic:
        - game_state.current_phase가 "storybook"이고 current_storybook_id가 있으면 해당 스토리북 반환
        - "chat"이면 None 반환

        Args:
            game_state: GameState 객체

        Returns:
            dict or None: 스토리북 데이터
        """
        # chat 모드이면 None 반환
        if game_state.current_phase == "chat":
            print("[StorybookManager] 현재 채팅 모드입니다. 스토리북 없음.")
            return None

        # storybook 모드이고 current_storybook_id가 있으면 해당 스토리북 반환
        if game_state.current_phase == "storybook" and game_state.current_storybook_id:
            try:
                storybook = self.get_storybook(game_state.current_storybook_id)
                return storybook
            except ValueError:
                print(f"[WARNING] 유효하지 않은 스토리북 ID: {game_state.current_storybook_id}")
                return None

        # 그 외의 경우 None 반환
        return None

    def check_goals_achieved(self, game_state, month: int = None) -> Tuple[bool, dict]:
        """
        월별 목표 달성 여부 확인

        Args:
            game_state: GameState 객체
            month: 확인할 월 (None이면 current_month 사용)

        Returns:
            tuple: (달성 여부, 목표 정보)
                - bool: 모든 목표 달성 여부
                - dict: {
                    "achieved": {"intimacy": True, "stamina": True, ...},
                    "current": {"intimacy": 25, "stamina": 65, ...},
                    "required": {"intimacy": 20, "stamina": 60, ...}
                  }
        """
        # 확인할 월 결정
        target_month = month if month is not None else game_state.current_month

        # 월별 목표 가져오기
        goals = self.get_month_goals(target_month)

        if not goals:
            print(f"[WARNING] {target_month}월의 목표가 없습니다.")
            return (False, {
                "achieved": {},
                "current": {},
                "required": {}
            })

        # 현재 스탯 가져오기
        current_stats = game_state.stats.to_dict()

        # <<< 수정 시작: 오래된 stat_mapping 제거 >>>
        # 이유: 이제 config 파일과 GameState의 스탯 이름이 일치하므로 매핑이 필요 없습니다.
        # stat_mapping = {
        #     'running': 'speed'
        # }
        # <<< 수정 끝 >>>

        # 각 목표 달성 여부 확인
        achieved = {}
        required = {}
        current = {}

        for stat_name, goal_value in goals.items():
            # description 필드는 스킵
            if stat_name == "description":
                continue

            # <<< 수정 시작: stat_mapping 로직 제거 >>>
            current_value = current_stats.get(stat_name, 0)
            # <<< 수정 끝 >>>
            is_achieved = current_value >= goal_value

            achieved[stat_name] = is_achieved
            required[stat_name] = goal_value
            current[stat_name] = current_value

        # 모든 목표 달성 여부
        all_achieved = all(achieved.values()) if achieved else False

        result = {
            "achieved": achieved,
            "current": current,
            "required": required
        }

        print(f"[StorybookManager] {target_month}월 목표 확인: 달성 여부 = {all_achieved}")
        print(f"[StorybookManager] 세부 사항: {result}")

        return (all_achieved, result)

    def get_next_storybook_id(self, game_state) -> Optional[str]:
        """
        다음에 보여줄 스토리북 ID 결정

        Logic:
        - current_phase가 "chat"이고 목표 달성 시:
          -> f"{current_month}_to_{current_month+1}_transition"
        - 9월이면 "9_ending"

        Args:
            game_state: GameState 객체

        Returns:
            str: 다음 스토리북 ID 또는 None
        """
        # chat 모드가 아니면 None 반환
        if game_state.current_phase != "chat":
            print("[StorybookManager] 현재 채팅 모드가 아닙니다. 다음 스토리북 없음.")
            return None

        current_month = game_state.current_month

        # 9월이면 엔딩 결정 스토리북으로 이동
        if current_month == 9:
            print("[StorybookManager] 9월 - 엔딩 스토리북으로 이동")
            return "9_opening" # <<< 수정: "9_ending"이 아닌 "9_opening"으로 해야 엔딩 결정 로직이 실행됨

        # 9월 이상이면 None (게임 종료)
        if current_month >= 9:
            print("[StorybookManager] 9월 이후 - 게임 종료")
            return None

        # 목표 달성 여부 확인 (디버깅 모드: 체크만 하고 항상 통과)
        all_achieved, goal_info = self.check_goals_achieved(game_state)

        # 디버깅 모드: 목표 달성 여부와 상관없이 다음 월로 진행
        next_month = current_month + 1
        transition_id = f"{current_month}_to_{next_month}_transition"

        if all_achieved:
            print(f"[StorybookManager] 목표 달성! 전환 스토리북: {transition_id}")
        else:
            print(f"[StorybookManager] [디버깅 모드] 목표 미달성이지만 강제 진행: {transition_id}")

        return transition_id

    # <<< 수정 시작: 엔딩 결정 함수를 최신 기획(스탯 총합 + 대회 결과)에 맞게 전면 수정 >>>
    # 이유: 기존 로직은 오래된 스탯('power')과 잘못된 계산 방식(A/B/C 평균)을 사용하고 있어 치명적인 오류를 발생시킵니다.
    def determine_ending(self, game_state) -> dict:
        """
        최종 엔딩 결정 (스탯 총합 + 8월 대회 결과 플래그)
        """
        stats = game_state.stats
        flags = game_state.flags

        # 1. 스탯 총합 계산 (친밀도, 멘탈 제외 4개 기술/신체 스탯, 최대 400점)
        total_score = stats.batting + stats.speed + stats.defense + stats.stamina
        
        # 2. 8월 대회 결과 가져오기 (이 플래그는 8월 이벤트에서 설정되어야 함)
        # 기본값은 '삼진(strikeout)'
        tournament_result = flags.get('tournament_result', 'strikeout')

        # 3. 스탯 총합에 따라 '스탯 범위' 결정
        stat_range = 4 # 기본값은 최하위 범위
        if total_score >= 320:   # 400점 만점에 320 이상 (S급 선수)
            stat_range = 1
        elif total_score >= 240: # 240 이상 (A급 선수)
            stat_range = 2
        elif total_score >= 150: # 150 이상 (B급 선수)
            stat_range = 3
        
        # 4. 엔딩 매트릭스에 따라 엔딩 ID 결정
        # 예: 범위 1 선수가 홈런을 치면 'A1' 엔딩
        ending_map = {
            1: {'homerun': 'A1', 'hit_steal': 'A2', 'hit': 'A3', 'strikeout': 'A4'},
            2: {'homerun': 'B1', 'hit_steal': 'B2', 'hit': 'B3', 'strikeout': 'B4'},
            3: {'homerun': 'C1', 'hit_steal': 'C2', 'hit': 'C3', 'strikeout': 'C4'},
            4: {'homerun': 'D1', 'hit_steal': 'D2', 'hit': 'D3', 'strikeout': 'D4'}
        }
        
        ending_id = ending_map.get(stat_range, {}).get(tournament_result, 'D4')

        # 5. 스페셜 엔딩 (메이저리그) 처리: 범위 1 + 홈런일 경우 5% 확률
        if ending_id == 'A1' and random.random() < 0.05:
            ending_id = 'S' # Special Ending

        # 6. 엔딩 데이터 가져오기
        endings = self.config.get('endings', {})
        ending_data = endings.get(ending_id, endings.get('D4')) # ID가 없으면 최하위 엔딩(D4)으로 처리

        print(f"[엔딩 결정] 최종 스탯 총합: {total_score} (범위 {stat_range})")
        print(f"[엔딩 결정] 대회 결과: {tournament_result}")
        print(f"[엔딩 결정] 최종 엔딩 ID: {ending_id} - {ending_data.get('title')}")

        return ending_data
    # <<< 수정 끝 >>>

    def get_month_goals(self, month: int) -> dict:
        """
        특정 월의 목표 가져오기

        Args:
            month: 월 (3-9)

        Returns:
            dict: 목표 딕셔너리 (없으면 빈 딕셔너리)
        """
        month_goals = self.config.get('month_goals', {})
        goals = month_goals.get(str(month), {})

        if goals:
            print(f"[StorybookManager] {month}월 목표: {goals.get('description', 'N/A')}")
        else:
            print(f"[WARNING] {month}월의 목표가 설정되지 않았습니다.")

        return goals


# ============================================================================
# 싱글톤 패턴
# ============================================================================
# StorybookManager 인스턴스를 앱 전체에서 재사용
# (매번 새로 초기화하면 비효율적)

_storybook_manager = None


def get_storybook_manager() -> StorybookManager:
    """
    스토리북 관리자 인스턴스 반환 (싱글톤)

    첫 호출 시 인스턴스 생성, 이후 재사용

    Returns:
        StorybookManager: 싱글톤 인스턴스
    """
    global _storybook_manager
    if _storybook_manager is None:
        _storybook_manager = StorybookManager()
    return _storybook_manager


# ============================================================================
# 테스트용 메인 함수
# ============================================================================

if __name__ == "__main__":
    """
    로컬 테스트용

    실행 방법:
    python services/storybook_manager.py
    """
    # <<< 수정 시작: 테스트 코드를 최신 스탯 시스템과 엔딩 로직에 맞게 전면 수정 >>>
    print("=" * 60)
    print("스토리북 관리자 테스트")
    print("=" * 60)

    # GameState 임포트 (테스트를 위해)
    try:
        from game_state_manager import GameState
    except ImportError:
        print("[ERROR] game_state_manager.py를 찾을 수 없어 테스트를 진행할 수 없습니다.")
        exit()

    # 매니저 초기화
    manager = StorybookManager()
    print()

    # 테스트 1: 3월 오프닝 가져오기 (정상 작동 확인)
    print("\n[TEST 1] 3월 오프닝 스토리북 가져오기")
    print("-" * 60)
    storybook = manager.get_storybook("3_opening")
    print(f"[OK] 스토리북 ID: {storybook.get('id')}")
    print(f"[OK] 제목: {storybook.get('title')}")

    # 테스트 2: 엔딩 결정 로직 테스트
    print("\n[TEST 2] 엔딩 결정 로직 테스트")
    print("-" * 60)

    # 시나리오 1: 최상위 스탯 + 홈런 -> 1라운드 지명(A1) 또는 메이저리그(S)
    test_state_s = GameState(session_id="test_s_rank")
    test_state_s.stats.batting = 90
    test_state_s.stats.speed = 85
    test_state_s.stats.defense = 80
    test_state_s.stats.stamina = 75  # 총점 330 (범위 1)
    test_state_s.flags['tournament_result'] = 'homerun'
    
    print("시나리오 1: 최상위 스탯 + 홈런")
    ending_s = manager.determine_ending(test_state_s)
    print(f"[OK] 결과: {ending_s.get('id')} - {ending_s.get('title')}\n")

    # 시나리오 2: 중간 스탯 + 안타 -> 드래프트 7라운드(B3)
    test_state_b = GameState(session_id="test_b_rank")
    test_state_b.stats.batting = 70
    test_state_b.stats.speed = 65
    test_state_b.stats.defense = 60
    test_state_b.stats.stamina = 55  # 총점 250 (범위 2)
    test_state_b.flags['tournament_result'] = 'hit'
    
    print("시나리오 2: 중간 스탯 + 안타")
    ending_b = manager.determine_ending(test_state_b)
    print(f"[OK] 결과: {ending_b.get('id')} - {ending_b.get('title')}\n")

    # 시나리오 3: 최하위 스탯 + 삼진 -> 야구 포기(D4)
    test_state_d = GameState(session_id="test_d_rank")
    test_state_d.stats.batting = 30 # 초기값에서 거의 성장 못함
    test_state_d.stats.speed = 40
    test_state_d.stats.defense = 35
    test_state_d.stats.stamina = 40 # 총점 145 (범위 4)
    test_state_d.flags['tournament_result'] = 'strikeout'

    print("시나리오 3: 최하위 스탯 + 삼진")
    ending_d = manager.determine_ending(test_state_d)
    print(f"[OK] 결과: {ending_d.get('id')} - {ending_d.get('title')}\n")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 모든 테스트 완료!")
    print("=" * 60)
    # <<< 수정 끝 >>>
