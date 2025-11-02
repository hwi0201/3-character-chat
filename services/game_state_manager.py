"""
게임 상태 관리 시스템

야구 선수 육성 게임의 상태를 관리합니다.
- 선수 스탯 (친밀도, 멘탈, 체력, 힘, 주루능력)
- 게임 진행 상황 (현재 월, 이벤트 히스토리)
- 게임 플래그 (백스토리 공개 여부, 특별 엔딩 플래그 등)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class PlayerStats:
    """
    선수 스탯

    관계: 친밀도
    정신: 멘탈
    신체: 체력, 힘, 주루능력
    """

    # 관계
    intimacy: int = 0  # 친밀도 (0-100)

    # 정신
    mental: int = 50  # 멘탈 (0-100)

    # 신체
    stamina: int = 50  # 체력 (0-100)
    power: int = 30    # 힘 (0-100, 폐급 스타트)
    speed: int = 40    # 주루 능력 (0-100)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    def apply_changes(self, changes: Dict[str, int]):
        """
        스탯 변화 적용

        Args:
            changes: {"intimacy": +5, "mental": -10, ...}
        """
        for key, value in changes.items():
            if hasattr(self, key):
                current = getattr(self, key)
                # 0-100 범위로 클램핑
                new_value = max(0, min(100, current + value))
                setattr(self, key, new_value)

    def get_stat(self, stat_name: str) -> int:
        """특정 스탯 값 가져오기"""
        return getattr(self, stat_name, 0)


@dataclass
class GameState:
    """
    전체 게임 상태

    게임의 모든 상태를 저장하고 관리합니다.
    """

    session_id: str  # username (세션 식별자)

    # 시간 정보
    current_month: int = 3  # 3월부터 시작
    current_day: int = 1

    # 선수 스탯
    stats: PlayerStats = field(default_factory=PlayerStats)

    # 게임 플래그
    flags: Dict[str, bool] = field(default_factory=dict)

    # 이벤트 히스토리
    event_history: List[str] = field(default_factory=list)

    # 특별한 순간 (추후 구현)
    special_moments: List[dict] = field(default_factory=list)

    # 훈련 스케줄 (추후 구현)
    training_schedule: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """초기화 후 기본값 설정"""
        # stats가 None이면 새로 생성
        if self.stats is None or not isinstance(self.stats, PlayerStats):
            self.stats = PlayerStats()

        # flags 기본값 설정
        if not self.flags:
            self.flags = {
                'backstory_revealed': False,  # 5월 집 방문 여부
                'homerun_flag': False,  # 8월 홈런 달성
                'steal_phobia_overcome': False,  # 도루 공포증 극복
            }

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (저장용)"""
        return {
            'session_id': self.session_id,
            'current_month': self.current_month,
            'current_day': self.current_day,
            'stats': self.stats.to_dict(),
            'flags': self.flags,
            'event_history': self.event_history,
            'special_moments': self.special_moments,
            'training_schedule': self.training_schedule,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """딕셔너리에서 게임 상태 복원"""
        stats_data = data.pop('stats', {})
        instance = cls(**data)
        instance.stats = PlayerStats(**stats_data)
        return instance

    def get_months_until_draft(self) -> int:
        """드래프트까지 남은 개월 수"""
        return 9 - self.current_month


class GameStateManager:
    """
    게임 상태 저장/로드 관리

    각 사용자(세션)별로 게임 상태를 관리합니다.
    """

    def __init__(self, save_dir: Path):
        """
        Args:
            save_dir: 게임 상태 저장 디렉토리
        """
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # 메모리 캐시 (빠른 접근용)
        self._states: Dict[str, GameState] = {}

        print(f"[GameStateManager] 초기화 완료: {save_dir}")

    def get_or_create(self, session_id: str) -> GameState:
        """
        게임 상태 가져오기 또는 새로 생성

        Args:
            session_id: 사용자 식별자 (username)

        Returns:
            GameState 객체
        """
        # 메모리 캐시에 있으면 반환
        if session_id in self._states:
            return self._states[session_id]

        # 저장된 상태 로드 시도
        save_file = self.save_dir / f"{session_id}.json"
        if save_file.exists():
            try:
                with open(save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    state = GameState.from_dict(data)
                    self._states[session_id] = state
                    print(f"[GameStateManager] 게임 상태 로드: {session_id} ({state.current_month}월)")
                    return state
            except Exception as e:
                print(f"[GameStateManager] 게임 상태 로드 실패: {e}")

        # 새 게임 상태 생성
        state = GameState(session_id=session_id)
        self._states[session_id] = state
        print(f"[GameStateManager] 새 게임 시작: {session_id}")
        return state

    def save(self, session_id: str):
        """
        게임 상태 저장

        Args:
            session_id: 사용자 식별자
        """
        if session_id not in self._states:
            print(f"[GameStateManager] 저장할 상태가 없음: {session_id}")
            return

        state = self._states[session_id]
        save_file = self.save_dir / f"{session_id}.json"

        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"[GameStateManager] 게임 상태 저장 완료: {session_id}")
        except Exception as e:
            print(f"[GameStateManager] 저장 실패: {e}")

    def get_stat_summary(self, session_id: str) -> str:
        """
        현재 스탯 요약 텍스트 생성

        Args:
            session_id: 사용자 식별자

        Returns:
            포맷팅된 스탯 요약 문자열
        """
        state = self.get_or_create(session_id)
        stats = state.stats

        return f"""
📊 현재 스탯
━━━━━━━━━━━━━━━━━━
💖 친밀도: {stats.intimacy}/100
🧠 멘탈: {stats.mental}/100
💪 체력: {stats.stamina}/100
💥 힘: {stats.power}/100
🏃 주루: {stats.speed}/100
"""

    def get_game_info(self, session_id: str) -> str:
        """
        현재 게임 진행 상황 요약

        Args:
            session_id: 사용자 식별자

        Returns:
            게임 정보 문자열
        """
        state = self.get_or_create(session_id)
        months_left = state.get_months_until_draft()

        return f"""
📅 현재: {state.current_month}월 | 🎯 드래프트까지: {months_left}개월
"""

    def advance_month(self, session_id: str) -> bool:
        """
        다음 달로 진행

        Args:
            session_id: 사용자 식별자

        Returns:
            성공 여부 (9월 이후면 False)
        """
        state = self.get_or_create(session_id)

        if state.current_month >= 9:
            print(f"[GameStateManager] 이미 마지막 달(9월)입니다")
            return False

        state.current_month += 1
        state.current_day = 1
        state.event_history.append(f"{state.current_month}월 시작")

        self.save(session_id)
        print(f"[GameStateManager] {session_id}: {state.current_month}월로 진행")
        return True
