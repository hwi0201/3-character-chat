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
    선수 스탯 (모든 스탯 0~100 범위)

    관계: 친밀도
    정신: 멘탈
    신체: 체력
    기술: 타격, 주루, 수비
    """
    # 관계
    intimacy: int = 0      # 친밀도 (0-100)

    # 정신 (기본적인 멘탈은 있으나 약점이 명확함)
    mental: int = 30       # 멘탈

    # 신체 (고교 선수로서의 기본 피지컬)
    stamina: int = 80      # 체력

    # 기술 (재능은 있으나 아직 미숙한 상태)
    batting: int = 35      # 타격 능력
    speed: int = 40        # 주루 능력
    defense: int = 40      # 수비 능력

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    def apply_changes(self, changes: Dict[str, int]):
        """
        스탯 변화 적용 (모든 스탯 0-100 범위로 클램핑)
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
    # Training history for prompt context
    training_history: List[dict] = field(default_factory=list)

    # 스토리북 관련
    current_phase: str = "storybook"  # "storybook" | "chat"
    current_storybook_id: str = "3_opening"  # 현재 보고 있는 스토리북
    storybook_completed: Dict[str, bool] = field(default_factory=dict)  # 완료한 스토리북 목록

    # 이전 월 스탯 (전환 스토리북에서 변화량 표시용)
    previous_month_stats: Dict[str, int] = field(default_factory=dict)
    
    # <<< 수정 시작: '다음 행동'을 지정하는 플래그 추가 >>>
    # 이유: 8월 이벤트처럼 여러 단계로 진행되는 이벤트를 처리하기 위해, 현재 어떤 단계를 수행해야 하는지 저장해야 합니다.
    next_action: Optional[str] = None  # 예: "submit_advice", "decide_steal"
    # <<< 수정 끝 >>>

    def __post_init__(self):
        """초기화 후 기본값 설정"""
        # stats가 None이거나 PlayerStats 타입이 아니면 새로 생성
        if self.stats is None or not isinstance(self.stats, PlayerStats):
            self.stats = PlayerStats()

        # flags 기본값 설정 (None이거나 비어있을 때만)
        if self.flags is None:
            self.flags = {}

        # 필수 플래그 키 초기화 (없으면 추가)
        default_flags = {
            'backstory_revealed': False,  # 5월 집 방문 여부
            'tournament_result': 'strikeout', # <<< 수정: 8월 대회 결과를 저장할 플래그 (homerun, hit_steal, hit, strikeout)
            'steal_phobia_overcome': False,  # 도루 공포증 극복
        }
        for key, value in default_flags.items():
            if key not in self.flags:
                self.flags[key] = value

        if self.training_history is None:
            self.training_history = []

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
            'training_history': self.training_history,
            'current_phase': self.current_phase,
            'current_storybook_id': self.current_storybook_id,
            'storybook_completed': self.storybook_completed,
            'previous_month_stats': self.previous_month_stats,
            'next_action': self.next_action
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

    def mark_storybook_completed(self, storybook_id: str):
        """스토리북 완료 표시"""
        self.storybook_completed[storybook_id] = True

    def set_chat_mode(self):
        """채팅 모드로 전환"""
        self.current_phase = "chat"
        self.current_storybook_id = None
        # <<< 수정 시작: 채팅 모드로 전환될 때 next_action 초기화 >>>
        # 이유: 이벤트가 아닌 일반 채팅으로 돌아올 때, 이전 이벤트 상태가 남아있는 것을 방지합니다.
        self.next_action = None
        # <<< 수정 끝 >>>

    def set_storybook_mode(self, storybook_id: str):
        """스토리북 모드로 전환"""
        self.current_phase = "storybook"
        self.current_storybook_id = storybook_id

    def save_previous_month_stats(self):
        """현재 스탯을 이전 월 스탯으로 저장 (월 진행 시 호출)"""
        self.previous_month_stats = self.stats.to_dict()

    def get_stat_changes_from_previous_month(self) -> Dict[str, int]:
        """이전 월 대비 스탯 변화량 계산"""
        if not self.previous_month_stats:
            return {}

        current_stats = self.stats.to_dict()
        changes = {}

        for key, current_value in current_stats.items():
            previous_value = self.previous_month_stats.get(key, 0)
            change = current_value - previous_value
            if change != 0:
                changes[key] = change


        return changes

    def record_training_session(
        self,
        *,
        month: int,
        intensity: int,
        intensity_label: str,
        focuses: List[str],
        stat_changes: Dict[str, int],
        stamina_change: int,
        summary: str,
    ):
        """Store training outcome in the training history."""
        entry = {
            'month': month,
            'intensity': intensity,
            'intensity_label': intensity_label,
            'focuses': focuses,
            'stat_changes': stat_changes,
            'stamina_change': stamina_change,
            'summary': summary,
        }

        self.training_history.append(entry)

        # Keep the history small (latest 10 entries are enough for prompts)
        if len(self.training_history) > 10:
            self.training_history = self.training_history[-10:]

    def get_recent_training_summary(self, limit: int = 3) -> str:
        """Return a short summary of recent training sessions."""
        if not self.training_history:
            return ""

        recent_entries = self.training_history[-limit:]

        focus_map = {
            'batting': 'Batting',
            'speed': 'Speed',
            'defense': 'Defense',
        }

        lines = []
        for entry in reversed(recent_entries):
            focus_labels = [focus_map.get(f, f) for f in entry.get('focuses', [])]
            focus_text = ', '.join(focus_labels) if focus_labels else 'General'
            stat_changes = entry.get('stat_changes', {})
            change_parts = [
                f"{focus_map.get(stat, stat)} {value:+d}"
                for stat, value in stat_changes.items()
            ]
            stamina_delta = entry.get('stamina_change', 0)
            if stamina_delta:
                change_parts.append(f"Stamina {stamina_delta:+d}")

            change_text = ', '.join(change_parts) if change_parts else 'No change'
            lines.append(
                f"- Month {entry.get('month')} {entry.get('intensity_label')} training ({focus_text}) -> {change_text}"
            )

        return '\n'.join(lines)


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
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARNING] 게임 상태 로드 실패 ({type(e).__name__}): {e}")
                print(f"[WARNING] 새 게임으로 시작합니다")

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

        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"[GameStateManager] 게임 상태 저장 완료: {session_id}")

    def get_stat_summary(self, session_id: str) -> str:
        """
        현재 스탯 요약 텍스트 생성 (디버깅 또는 텍스트 기반 출력용)

        Args:
            session_id: 사용자 식별자

        Returns:
            포맷팅된 스탯 요약 문자열
        """
        state = self.get_or_create(session_id)
        stats = state.stats

        # <<< 수정: 새로운 스탯(batting, defense)을 포함하고, power는 제거
        return (
            "📊 현재 스탯\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💖 친밀도: {stats.intimacy}/100\n"
            f"🧠 멘탈: {stats.mental}/100\n"
            f"💪 체력: {stats.stamina}/100\n"
            f"🏏 타격: {stats.batting}/100\n"
            f"🏃 주루: {stats.speed}/100\n"
            f"⚾ 수비: {stats.defense}/100"
        )

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

        return f"📅 현재: {state.current_month}월 | 🎯 드래프트까지: {months_left}개월"

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
