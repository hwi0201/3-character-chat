"""
특별한 순간 카드 관리 시스템

게임 진행 중 중요한 순간을 카드 형태로 저장하고 관리합니다.
- 이벤트 카드: 5월 집 방문, 8월 대회 등 (이미지 포함)
- 마일스톤 카드: 친밀도 달성, 스탯 조합 등 (그라데이션/아이콘)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
from datetime import datetime
import random


@dataclass
class MomentCard:
    """
    특별한 순간 카드

    두 가지 유형:
    1. 이벤트 카드 (event): 스토리북 이미지 포함
    2. 마일스톤 카드 (milestone): 그라데이션/아이콘 기반
    """
    id: str  # 고유 ID (timestamp 기반)
    type: str  # 'event' | 'milestone'
    category: str  # 'home_visit', 'tournament', 'intimacy', 'stat_combo'
    title: str  # 카드 제목
    description: str  # 카드 설명
    timestamp: str  # 발생 시각 (ISO format)
    month: int  # 발생 월

    # 이벤트 카드용
    image_url: Optional[str] = None  # 스토리북 이미지 경로

    # 마일스톤 카드용 (시각화 데이터)
    visual_data: Optional[Dict] = None  # gradient, icons 등

    # 메타데이터
    stats_snapshot: Optional[Dict] = None  # 당시 스탯 스냅샷

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


class MomentManager:
    """
    특별한 순간 관리자

    게임 상태에 카드를 추가하고, 중복 방지 로직을 처리합니다.
    """

    def __init__(self):
        # 친밀도 마일스톤 (이미 달성한 것은 기록하지 않음)
        self.intimacy_milestones = [30, 50, 70, 90]

        # 스탯 조합 조건 (예: 타격 + 주루 + 수비 합계)
        self.stat_combo_thresholds = [
            {'total': 150, 'title': '실력 향상의 시작', 'desc': '기술 스탯 합계 150 달성'},
            {'total': 200, 'title': '프로의 기운', 'desc': '기술 스탯 합계 200 달성'},
            {'total': 250, 'title': '드래프트 유망주', 'desc': '기술 스탯 합계 250 달성'},
        ]

    def create_event_card(
        self,
        category: str,
        title: str,
        description: str,
        month: int,
        image_url: str,
        stats_snapshot: Dict
    ) -> MomentCard:
        """
        이벤트 카드 생성 (이미지 포함)

        Args:
            category: 'home_visit' | 'tournament'
            title: 카드 제목
            description: 카드 설명
            month: 발생 월
            image_url: 스토리북 이미지 경로
            stats_snapshot: 당시 스탯
        """
        card_id = f"event_{category}_{int(datetime.now().timestamp())}"

        return MomentCard(
            id=card_id,
            type='event',
            category=category,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            month=month,
            image_url=image_url,
            visual_data=None,
            stats_snapshot=stats_snapshot
        )

    def create_milestone_card(
        self,
        category: str,
        title: str,
        description: str,
        month: int,
        visual_data: Dict,
        stats_snapshot: Dict
    ) -> MomentCard:
        """
        마일스톤 카드 생성 (그라데이션/아이콘 기반)

        Args:
            category: 'intimacy' | 'stat_combo'
            title: 카드 제목
            description: 카드 설명
            month: 발생 월
            visual_data: 시각화 데이터 (gradient, icon, emoji 등)
            stats_snapshot: 당시 스탯
        """
        card_id = f"milestone_{category}_{int(datetime.now().timestamp())}"

        return MomentCard(
            id=card_id,
            type='milestone',
            category=category,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            month=month,
            image_url=None,
            visual_data=visual_data,
            stats_snapshot=stats_snapshot
        )

    def check_and_create_intimacy_milestones(
        self,
        game_state,
        old_intimacy: int,
        new_intimacy: int
    ) -> List[MomentCard]:
        """
        친밀도 마일스톤 체크 및 카드 생성

        Args:
            game_state: 게임 상태
            old_intimacy: 이전 친밀도
            new_intimacy: 새 친밀도

        Returns:
            새로 생성된 카드 리스트
        """
        cards = []

        for milestone in self.intimacy_milestones:
            # 마일스톤을 방금 넘었는지 확인
            if old_intimacy < milestone <= new_intimacy:
                # 이미 이 마일스톤 카드가 있는지 확인
                existing = any(
                    m.get('category') == 'intimacy' and
                    m.get('visual_data', {}).get('milestone') == milestone
                    for m in game_state.special_moments
                )

                if not existing:
                    # 마일스톤별 시각화 데이터
                    visual_configs = {
                        30: {
                            'gradient': ['#FFC1C1', '#FF9999'],
                            'emoji': '💗',
                            'title': '마음이 열리다',
                            'desc': f'친밀도 {milestone} 달성! 선수가 조금씩 마음을 열고 있습니다.'
                        },
                        50: {
                            'gradient': ['#FF99CC', '#FF66B2'],
                            'emoji': '💖',
                            'title': '신뢰의 시작',
                            'desc': f'친밀도 {milestone} 달성! 코치님을 진심으로 믿기 시작했습니다.'
                        },
                        70: {
                            'gradient': ['#FF66B2', '#FF1493'],
                            'emoji': '💝',
                            'title': '깊어지는 유대',
                            'desc': f'친밀도 {milestone} 달성! 서로에게 없어서는 안 될 존재가 되었습니다.'
                        },
                        90: {
                            'gradient': ['#FF1493', '#C71585'],
                            'emoji': '💕',
                            'title': '영원한 인연',
                            'desc': f'친밀도 {milestone} 달성! 이 인연은 야구를 넘어 평생 이어질 것입니다.'
                        }
                    }

                    config = visual_configs.get(milestone)
                    if config:
                        visual_data = {
                            'gradient': config['gradient'],
                            'emoji': config['emoji'],
                            'milestone': milestone
                        }

                        card = self.create_milestone_card(
                            category='intimacy',
                            title=config['title'],
                            description=config['desc'],
                            month=game_state.current_month,
                            visual_data=visual_data,
                            stats_snapshot=game_state.stats.to_dict()
                        )

                        cards.append(card)

        return cards

    def check_and_create_stat_combo_milestones(
        self,
        game_state,
        old_stats: Dict,
        new_stats: Dict
    ) -> List[MomentCard]:
        """
        스탯 조합 마일스톤 체크 및 카드 생성

        Args:
            game_state: 게임 상태
            old_stats: 이전 스탯
            new_stats: 새 스탯

        Returns:
            새로 생성된 카드 리스트
        """
        cards = []

        old_total = old_stats.get('batting', 0) + old_stats.get('speed', 0) + old_stats.get('defense', 0)
        new_total = new_stats.get('batting', 0) + new_stats.get('speed', 0) + new_stats.get('defense', 0)

        for threshold in self.stat_combo_thresholds:
            target = threshold['total']

            # 마일스톤을 방금 넘었는지 확인
            if old_total < target <= new_total:
                # 이미 이 마일스톤 카드가 있는지 확인
                existing = any(
                    m.get('category') == 'stat_combo' and
                    m.get('visual_data', {}).get('total') == target
                    for m in game_state.special_moments
                )

                if not existing:
                    # 스탯별 색상 그라데이션
                    visual_data = {
                        'gradient': ['#4A90E2', '#50C878', '#FFD700'],  # Blue → Green → Gold
                        'emoji': '⚡' if target == 150 else '🔥' if target == 200 else '🏆',
                        'total': target,
                        'stats': {
                            'batting': new_stats.get('batting', 0),
                            'speed': new_stats.get('speed', 0),
                            'defense': new_stats.get('defense', 0)
                        }
                    }

                    card = self.create_milestone_card(
                        category='stat_combo',
                        title=threshold['title'],
                        description=threshold['desc'],
                        month=game_state.current_month,
                        visual_data=visual_data,
                        stats_snapshot=new_stats
                    )

                    cards.append(card)

        return cards

    def add_cards_to_game_state(self, game_state, cards: List[MomentCard]):
        """
        카드를 게임 상태에 추가

        Args:
            game_state: 게임 상태
            cards: 추가할 카드 리스트
        """
        for card in cards:
            game_state.special_moments.append(card.to_dict())
            print(f"[MOMENT] ✨ 특별한 순간 카드 생성: {card.title} ({card.category})")


# 싱글톤 인스턴스
_moment_manager: MomentManager | None = None


def get_moment_manager() -> MomentManager:
    """싱글톤 MomentManager 인스턴스 반환"""
    global _moment_manager
    if _moment_manager is None:
        _moment_manager = MomentManager()
    return _moment_manager
