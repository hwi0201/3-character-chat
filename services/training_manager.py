"""
Training manager module.

Handles the logic for adjustable training sessions so that the backend
can keep the rules in one place and the UI simply requests outcomes.
"""

from dataclasses import dataclass
from typing import Dict, List, Sequence


TRAINABLE_MONTHS = {4, 6, 7}
VALID_FOCUSES = {"batting", "speed", "defense"}
FOCUS_LABELS = {
    "batting": "Batting",
    "speed": "Speed",
    "defense": "Defense",
}


@dataclass
class TrainingOutcome:
    """Structured response for a training session."""

    intensity: int
    intensity_label: str
    focuses: List[str]
    stat_changes: Dict[str, int]
    stamina_change: int
    total_changes: Dict[str, int]
    summary: str
    conversation_note: str


class TrainingManager:
    """
    Encapsulates training computations so the rest of the codebase can remain
    agnostic of the exact balancing values.
    """

    def execute(
        self,
        *,
        game_state,
        intensity: int,
        focuses: Sequence[str],
    ) -> TrainingOutcome:
        """
        Run a training session and return the outcome.

        Args:
            game_state: GameState instance (mutated by the caller after applying changes).
            intensity: 0-100 lever value chosen by the player.
            focuses: sequence of focus keys (batting, speed, defense).
        """
        month = game_state.current_month
        if month not in TRAINABLE_MONTHS:
            raise ValueError("Training is only available in April, June, and July.")

        intensity = max(0, min(100, int(intensity)))
        focus_list = self._normalise_focuses(focuses)
        focus_count = len(focus_list)

        # Determine training tier based on intensity.
        if intensity <= 20:
            intensity_label = "Recovery Session"
            base_gain = 0
            stamina_change = 10
        elif intensity <= 40:
            intensity_label = "Light Training"
            base_gain = 1
            stamina_change = 4
        elif intensity <= 70:
            intensity_label = "Standard Training"
            base_gain = 2
            stamina_change = -6
        elif intensity <= 85:
            intensity_label = "Focused Training"
            base_gain = 3
            stamina_change = -12
        else:
            intensity_label = "High-Intensity Training"
            base_gain = 4
            stamina_change = -20

        per_stat_gain = self._calculate_stat_gain(base_gain, focus_count, intensity)

        stat_changes: Dict[str, int] = {}
        if per_stat_gain > 0:
            for focus in focus_list:
                stat_changes[focus] = per_stat_gain

        total_changes = dict(stat_changes)
        if stamina_change != 0:
            total_changes["stamina"] = stamina_change

        # Mutate stats directly via the shared helper to keep clamping logic.
        if total_changes:
            game_state.stats.apply_changes(total_changes)

        focus_label_text = ', '.join(FOCUS_LABELS[f] for f in focus_list)
        change_parts = [
            f"{FOCUS_LABELS.get(stat, stat)} {delta:+d}"
            for stat, delta in stat_changes.items()
        ]
        if stamina_change:
            change_parts.append(f"Stamina {stamina_change:+d}")

        change_summary = ', '.join(change_parts) if change_parts else 'No change'
        summary = (
            f"Month {month} {intensity_label} focused on {focus_label_text}. "
            f"Result: {change_summary}."
        )

        conversation_note = (
            f"[Training] {intensity_label} completed. "
            f"Focus areas: {focus_label_text}. Result: {change_summary}."
        )

        game_state.record_training_session(
            month=month,
            intensity=intensity,
            intensity_label=intensity_label,
            focuses=focus_list,
            stat_changes=stat_changes,
            stamina_change=stamina_change,
            summary=summary,
        )

        return TrainingOutcome(
            intensity=intensity,
            intensity_label=intensity_label,
            focuses=focus_list,
            stat_changes=stat_changes,
            stamina_change=stamina_change,
            total_changes=total_changes,
            summary=summary,
            conversation_note=conversation_note,
        )

    @staticmethod
    def _normalise_focuses(focuses: Sequence[str]) -> List[str]:
        cleaned = []
        for focus in focuses or []:
            key = str(focus).strip().lower()
            if key in VALID_FOCUSES and key not in cleaned:
                cleaned.append(key)

        if not cleaned:
            return list(VALID_FOCUSES)
        return cleaned

    @staticmethod
    def _calculate_stat_gain(base_gain: int, focus_count: int, intensity: int) -> int:
        """
        Derive the stat gain for each focused area.
        """
        if base_gain <= 0 or focus_count <= 0:
            return 0

        gain = base_gain
        if focus_count > 1:
            gain = max(1, gain - 1)
        if focus_count > 2:
            gain = max(1, gain - 1)

        if intensity >= 90 and focus_count == 1:
            gain += 1

        return gain


_training_manager: TrainingManager | None = None


def get_training_manager() -> TrainingManager:
    global _training_manager
    if _training_manager is None:
        _training_manager = TrainingManager()
    return _training_manager
