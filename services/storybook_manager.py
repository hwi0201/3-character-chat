"""
스토리북 관리 서비스

스토리북 데이터 로드, 목표 확인, 엔딩 결정 등을 담당합니다.
게임의 스토리 진행을 관리하는 핵심 모듈입니다.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


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
        except FileNotFoundError:
            error_msg = f"스토리북 설정 파일을 찾을 수 없습니다: {self.config_path}"
            print(f"[ERROR] {error_msg}")
            raise FileNotFoundError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"JSON 파싱 오류: {e}"
            print(f"[ERROR] {error_msg}")
            raise json.JSONDecodeError(error_msg, e.doc, e.pos)

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

        # 스탯 이름 매핑 (config와 GameState 간 불일치 해결)
        # config: "running" <-> GameState: "speed"
        stat_mapping = {
            'running': 'speed'  # config의 running을 GameState의 speed로 매핑
        }

        # 각 목표 달성 여부 확인
        achieved = {}
        required = {}
        current = {}

        for stat_name, goal_value in goals.items():
            # description 필드는 스킵
            if stat_name == "description":
                continue

            # 스탯 이름 매핑 적용
            actual_stat_name = stat_mapping.get(stat_name, stat_name)
            current_value = current_stats.get(actual_stat_name, 0)
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

        # 9월이면 엔딩
        if current_month == 9:
            print("[StorybookManager] 9월 - 엔딩 스토리북으로 이동")
            return "9_ending"

        # 9월 이상이면 None (게임 종료)
        if current_month >= 9:
            print("[StorybookManager] 9월 이후 - 게임 종료")
            return None

        # 목표 달성 여부 확인
        all_achieved, goal_info = self.check_goals_achieved(game_state)

        if all_achieved:
            # 다음 월로 전환하는 스토리북
            next_month = current_month + 1
            transition_id = f"{current_month}_to_{next_month}_transition"
            print(f"[StorybookManager] 목표 달성! 전환 스토리북: {transition_id}")
            return transition_id
        else:
            # 목표 미달성 - 계속 채팅 모드
            print(f"[StorybookManager] 목표 미달성. 계속 채팅 모드.")
            return None

    def determine_ending(self, game_state) -> dict:
        """
        최종 엔딩 결정 (9월)

        Logic:
        1. 모든 스탯 80 이상 -> A 엔딩
        2. 평균 스탯 60 이상 -> B 엔딩
        3. 그 외 -> C 엔딩

        Args:
            game_state: GameState 객체

        Returns:
            dict: {
                "ending_type": "A",
                "name": "완벽한 성공",
                "content": "...",
                "image": "...",
                "pages": [...]
            }
        """
        stats = game_state.stats.to_dict()

        # 엔딩 판정에 사용할 스탯 (친밀도 제외)
        # 설정 파일의 엔딩 조건에 맞춰 스탯 선택
        ending_stats = {
            'stamina': stats.get('stamina', 0),
            'power': stats.get('power', 0),
            'speed': stats.get('speed', 0),  # running -> speed (GameState 기준)
            'mental': stats.get('mental', 0)
        }

        # A 엔딩: 모든 스탯 80 이상
        if all(value >= 80 for value in ending_stats.values()):
            ending_type = "A"
            print(f"[StorybookManager] 엔딩 결정: A (모든 스탯 80 이상)")
        # B 엔딩: 평균 스탯 60 이상
        elif sum(ending_stats.values()) / len(ending_stats) >= 60:
            ending_type = "B"
            print(f"[StorybookManager] 엔딩 결정: B (평균 스탯 60 이상)")
        # C 엔딩: 그 외
        else:
            ending_type = "C"
            print(f"[StorybookManager] 엔딩 결정: C (기타)")

        # 엔딩 데이터 가져오기
        endings = self.config.get('endings', {})
        ending_data = endings.get(ending_type, endings.get('C'))  # 없으면 C 엔딩

        if not ending_data:
            print("[ERROR] 엔딩 데이터가 없습니다!")
            return {
                "ending_type": "C",
                "title": "알 수 없는 엔딩",
                "subtitle": "",
                "pages": [],
                "achievements": []
            }

        # 엔딩 정보 반환
        result = {
            "ending_type": ending_type,
            "title": ending_data.get('title', 'Unknown'),
            "subtitle": ending_data.get('subtitle', ''),
            "pages": ending_data.get('pages', []),
            "achievements": ending_data.get('achievements', []),
            "completion_action": ending_data.get('completion_action', 'game_end')
        }

        print(f"[StorybookManager] 엔딩: {ending_type} - {result['title']}")
        print(f"[StorybookManager] 최종 스탯: {ending_stats}")

        return result

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
    print("=" * 60)
    print("스토리북 관리자 테스트")
    print("=" * 60)

    # 매니저 초기화
    manager = StorybookManager()
    print()

    # 테스트 1: 3월 오프닝 가져오기
    print("\n[TEST 1] 3월 오프닝 스토리북 가져오기")
    print("-" * 60)
    storybook = manager.get_storybook("3_opening")
    print(f"[OK] 스토리북 ID: {storybook['id']}")
    print(f"[OK] 제목: {storybook['title']}")
    print(f"[OK] 페이지 수: {len(storybook['pages'])}개")

    # 테스트 2: 목표 가져오기
    print("\n[TEST 2] 3월 목표 가져오기")
    print("-" * 60)
    goals = manager.get_month_goals(3)
    print(f"[OK] 목표 설명: {goals.get('description', 'N/A')}")
    print(f"[OK] 친밀도 목표: {goals.get('intimacy', 0)}")
    print(f"[OK] 체력 목표: {goals.get('stamina', 0)}")
    print(f"[OK] 힘 목표: {goals.get('power', 0)}")
    print(f"[OK] 주루 목표: {goals.get('running', 0)}")
    print(f"[OK] 멘탈 목표: {goals.get('mental', 0)}")

    # 테스트 3: 목표 달성 확인 (가상 게임 스테이트)
    print("\n[TEST 3] 목표 달성 확인 (Mock GameState)")
    print("-" * 60)

    # GameState 임포트 및 생성
    from game_state_manager import GameState

    test_state = GameState(session_id="test_user")
    test_state.current_month = 3
    test_state.stats.intimacy = 25
    test_state.stats.stamina = 65
    test_state.stats.power = 55
    test_state.stats.speed = 50
    test_state.stats.mental = 45

    all_achieved, goal_info = manager.check_goals_achieved(test_state)
    print(f"[OK] 모든 목표 달성: {all_achieved}")
    print(f"[OK] 세부 정보:")
    for stat_name in goal_info['achieved'].keys():
        achieved = "[OK]" if goal_info['achieved'][stat_name] else "[NO]"
        print(f"  {achieved} {stat_name}: {goal_info['current'][stat_name]}/{goal_info['required'][stat_name]}")

    # 테스트 4: 다음 스토리북 ID 결정
    print("\n[TEST 4] 다음 스토리북 ID 결정")
    print("-" * 60)

    # 목표 달성 케이스
    test_state.current_phase = "chat"
    test_state.stats.intimacy = 25
    test_state.stats.stamina = 65
    test_state.stats.power = 55
    test_state.stats.speed = 55
    test_state.stats.mental = 45

    next_id = manager.get_next_storybook_id(test_state)
    print(f"[OK] 다음 스토리북 ID (목표 달성 시): {next_id}")

    # 목표 미달성 케이스
    test_state.stats.intimacy = 10
    test_state.stats.stamina = 40

    next_id = manager.get_next_storybook_id(test_state)
    print(f"[OK] 다음 스토리북 ID (목표 미달성 시): {next_id}")

    # 테스트 5: 엔딩 결정
    print("\n[TEST 5] 엔딩 결정 테스트")
    print("-" * 60)

    # A 엔딩 (모든 스탯 80 이상)
    test_state.current_month = 9
    test_state.stats.intimacy = 95
    test_state.stats.stamina = 90
    test_state.stats.power = 85
    test_state.stats.speed = 80
    test_state.stats.mental = 85

    ending_a = manager.determine_ending(test_state)
    print(f"[OK] A 엔딩 테스트: {ending_a['ending_type']} - {ending_a['title']}")

    # B 엔딩 (평균 60 이상)
    test_state.stats.intimacy = 70
    test_state.stats.stamina = 70
    test_state.stats.power = 65
    test_state.stats.speed = 60
    test_state.stats.mental = 65

    ending_b = manager.determine_ending(test_state)
    print(f"[OK] B 엔딩 테스트: {ending_b['ending_type']} - {ending_b['title']}")

    # C 엔딩 (그 외)
    test_state.stats.intimacy = 40
    test_state.stats.stamina = 50
    test_state.stats.power = 45
    test_state.stats.speed = 40
    test_state.stats.mental = 40

    ending_c = manager.determine_ending(test_state)
    print(f"[OK] C 엔딩 테스트: {ending_c['ending_type']} - {ending_c['title']}")

    print("\n" + "=" * 60)
    print("[SUCCESS] 모든 테스트 완료!")
    print("=" * 60)
