"""
스토리북 시스템 통합 테스트

이 파일은 스토리북 시스템의 주요 기능을 테스트합니다.
"""

import sys
import io
from pathlib import Path

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 sys.path에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def test_json_config():
    """JSON 설정 파일 유효성 검사"""
    print("\n[Test 1] JSON 설정 파일 검증")
    print("="*50)

    import json

    config_path = BASE_DIR / "config" / "storybook_config.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"✓ JSON 파일 로드 성공")
        print(f"✓ 스토리북 개수: {len(config['storybooks'])}")
        print(f"✓ 엔딩 개수: {len(config['endings'])}")
        print(f"✓ 월별 목표 개수: {len(config['month_goals'])}")

        # 주요 스토리북 확인
        assert '3_opening' in config['storybooks'], "3월 오프닝 스토리북 없음"
        assert '3_to_4_transition' in config['storybooks'], "3→4월 전환 스토리북 없음"
        assert '9_ending' in config['storybooks'], "9월 엔딩 스토리북 없음"

        print("✓ 주요 스토리북 존재 확인")

        # 엔딩 확인
        assert 'A' in config['endings'], "A 엔딩 없음"
        assert 'B' in config['endings'], "B 엔딩 없음"
        assert 'C' in config['endings'], "C 엔딩 없음"

        print("✓ 모든 엔딩 존재 확인")

        return True

    except Exception as e:
        print(f"✗ JSON 검증 실패: {e}")
        return False


def test_storybook_manager():
    """StorybookManager 클래스 테스트"""
    print("\n[Test 2] StorybookManager 클래스 테스트")
    print("="*50)

    try:
        from services.storybook_manager import StorybookManager

        # 인스턴스 생성
        manager = StorybookManager()
        print("✓ StorybookManager 인스턴스 생성 성공")

        # 스토리북 가져오기
        storybook = manager.get_storybook('3_opening')
        print(f"✓ 스토리북 로드: {storybook['title']}")
        print(f"  - 페이지 수: {len(storybook['pages'])}")
        print(f"  - 타입: {storybook['type']}")

        # 월별 목표 가져오기
        goals = manager.get_month_goals(3)
        print(f"✓ 3월 목표 로드: {goals}")

        return True

    except Exception as e:
        print(f"✗ StorybookManager 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_state_extension():
    """GameState 클래스 확장 테스트"""
    print("\n[Test 3] GameState 클래스 확장 테스트")
    print("="*50)

    try:
        from services.game_state_manager import GameState, PlayerStats

        # GameState 인스턴스 생성
        game_state = GameState(session_id="test_user")
        print("✓ GameState 인스턴스 생성 성공")

        # 새 필드 확인
        assert hasattr(game_state, 'current_phase'), "current_phase 필드 없음"
        assert hasattr(game_state, 'current_storybook_id'), "current_storybook_id 필드 없음"
        assert hasattr(game_state, 'storybook_completed'), "storybook_completed 필드 없음"
        assert hasattr(game_state, 'previous_month_stats'), "previous_month_stats 필드 없음"

        print(f"✓ 새 필드 확인 완료")
        print(f"  - current_phase: {game_state.current_phase}")
        print(f"  - current_storybook_id: {game_state.current_storybook_id}")

        # 새 메서드 확인
        assert hasattr(game_state, 'mark_storybook_completed'), "mark_storybook_completed 메서드 없음"
        assert hasattr(game_state, 'set_chat_mode'), "set_chat_mode 메서드 없음"
        assert hasattr(game_state, 'set_storybook_mode'), "set_storybook_mode 메서드 없음"
        assert hasattr(game_state, 'save_previous_month_stats'), "save_previous_month_stats 메서드 없음"

        print("✓ 새 메서드 확인 완료")

        # 메서드 동작 테스트
        game_state.mark_storybook_completed('3_opening')
        assert game_state.storybook_completed['3_opening'] == True
        print("✓ mark_storybook_completed 동작 확인")

        game_state.set_chat_mode()
        assert game_state.current_phase == 'chat'
        print("✓ set_chat_mode 동작 확인")

        game_state.set_storybook_mode('4_opening')
        assert game_state.current_phase == 'storybook'
        assert game_state.current_storybook_id == '4_opening'
        print("✓ set_storybook_mode 동작 확인")

        game_state.save_previous_month_stats()
        assert len(game_state.previous_month_stats) > 0
        print("✓ save_previous_month_stats 동작 확인")

        return True

    except Exception as e:
        print(f"✗ GameState 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_goal_checking():
    """목표 달성 확인 로직 테스트"""
    print("\n[Test 4] 목표 달성 확인 로직 테스트")
    print("="*50)

    try:
        from services.game_state_manager import GameState
        from services.storybook_manager import StorybookManager

        manager = StorybookManager()

        # 테스트 게임 상태 생성
        game_state = GameState(session_id="test_user")
        game_state.current_month = 3
        game_state.stats.intimacy = 25
        game_state.stats.stamina = 65

        # 목표 달성 확인
        all_achieved, goals_info = manager.check_goals_achieved(game_state, 3)

        print(f"✓ 목표 달성 확인 완료")
        print(f"  - 전체 달성: {all_achieved}")
        print(f"  - 친밀도: {goals_info['current']['intimacy']}/{goals_info['required']['intimacy']} - {'달성' if goals_info['achieved']['intimacy'] else '미달성'}")
        print(f"  - 체력: {goals_info['current']['stamina']}/{goals_info['required']['stamina']} - {'달성' if goals_info['achieved']['stamina'] else '미달성'}")

        assert all_achieved == True, "목표를 달성했어야 함"
        print("✓ 목표 달성 로직 정상 동작")

        return True

    except Exception as e:
        print(f"✗ 목표 확인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ending_determination():
    """엔딩 결정 로직 테스트"""
    print("\n[Test 5] 엔딩 결정 로직 테스트")
    print("="*50)

    try:
        from services.game_state_manager import GameState
        from services.storybook_manager import StorybookManager

        manager = StorybookManager()

        # A 엔딩 테스트 (모든 스탯 80 이상)
        game_state = GameState(session_id="test_user_a")
        game_state.current_month = 9
        game_state.stats.intimacy = 90
        game_state.stats.stamina = 85
        game_state.stats.power = 85
        game_state.stats.speed = 80
        game_state.stats.mental = 85

        ending = manager.determine_ending(game_state)
        print(f"✓ A 엔딩 테스트: {ending['ending_type']}")
        assert ending['ending_type'] == 'A', "A 엔딩이어야 함"

        # B 엔딩 테스트 (평균 60 이상)
        game_state2 = GameState(session_id="test_user_b")
        game_state2.current_month = 9
        game_state2.stats.intimacy = 70
        game_state2.stats.stamina = 65
        game_state2.stats.power = 60
        game_state2.stats.speed = 60
        game_state2.stats.mental = 65

        ending2 = manager.determine_ending(game_state2)
        print(f"✓ B 엔딩 테스트: {ending2['ending_type']}")
        assert ending2['ending_type'] == 'B', "B 엔딩이어야 함"

        # C 엔딩 테스트 (그 외)
        game_state3 = GameState(session_id="test_user_c")
        game_state3.current_month = 9
        game_state3.stats.intimacy = 40
        game_state3.stats.stamina = 50
        game_state3.stats.power = 45
        game_state3.stats.speed = 40
        game_state3.stats.mental = 45

        ending3 = manager.determine_ending(game_state3)
        print(f"✓ C 엔딩 테스트: {ending3['ending_type']}")
        assert ending3['ending_type'] == 'C', "C 엔딩이어야 함"

        print("✓ 엔딩 결정 로직 정상 동작")

        return True

    except Exception as e:
        print(f"✗ 엔딩 결정 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_files():
    """이미지 파일 존재 확인"""
    print("\n[Test 6] 이미지 파일 확인")
    print("="*50)

    try:
        images_dir = BASE_DIR / "static" / "images" / "story"

        if not images_dir.exists():
            print(f"✗ 이미지 디렉토리 없음: {images_dir}")
            return False

        print(f"✓ 이미지 디렉토리 존재: {images_dir}")

        # placeholder 이미지 확인
        placeholder = images_dir / "placeholder.png"
        if placeholder.exists():
            print(f"✓ Placeholder 이미지 존재")
        else:
            print(f"✗ Placeholder 이미지 없음")
            return False

        return True

    except Exception as e:
        print(f"✗ 이미지 확인 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("="*50)
    print("스토리북 시스템 통합 테스트")
    print("="*50)

    results = []

    # 각 테스트 실행
    results.append(("JSON 설정", test_json_config()))
    results.append(("StorybookManager", test_storybook_manager()))
    results.append(("GameState 확장", test_game_state_extension()))
    results.append(("목표 확인", test_goal_checking()))
    results.append(("엔딩 결정", test_ending_determination()))
    results.append(("이미지 파일", test_image_files()))

    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)

    for name, result in results:
        status = "✓ 성공" if result else "✗ 실패"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(1 for _, result in results if result)

    print(f"\n총 {total}개 테스트 중 {passed}개 성공, {total - passed}개 실패")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
