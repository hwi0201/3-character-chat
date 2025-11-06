"""
🚫 이 파일은 수정하지 마세요! (템플릿 파일)

이 파일은 Flask 애플리케이션의 핵심 로직을 포함하고 있습니다.
학회원은 다음 파일만 수정/작성하면 됩니다:

✏️ 수정/작성해야 하는 파일:
  - config/chatbot_config.json        (챗봇 설정)
  - services/chatbot_service.py       (AI 로직: RAG, Embedding, LLM)
  - static/data/chatbot/chardb_text/  (텍스트 데이터)
  - static/images/chatbot/            (이미지 파일)
  - static/videos/chatbot/            (비디오 파일, 선택)

이 파일을 수정하면 전체 시스템이 작동하지 않을 수 있습니다.
"""

import os
import json
from pathlib import Path
from flask import Flask, request, render_template, jsonify, url_for, Response, stream_with_context
from dotenv import load_dotenv
from services.storybook_manager import get_storybook_manager
from services.game_event_manager import get_game_event_manager

# 환경변수 로드
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')

# 개발 환경 설정
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent

# 설정 파일 로드
CONFIG_PATH = BASE_DIR / 'config' / 'chatbot_config.json'

def load_config():
    """챗봇 설정 파일 로드"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 기본 설정 반환
        return {
            'name': '챗봇',
            'description': '챗봇 설명',
            'tags': ['#챗봇'],
            'thumbnail': 'images/hateslop/club_logo.png'
        }

config = load_config()

# 이미지 파일 스캔 함수
def get_image_files():
    """챗봇 이미지 디렉토리에서 이미지 파일 목록 반환"""
    folder_path = BASE_DIR / "static" / "images" / "chatbot"
    image_files = []
    
    if folder_path.exists():
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                    image_files.append(rel_path.replace("\\", "/"))
    
    return image_files

# 메인 페이지
@app.route('/')
def index():
    bot_info = {
        'name': config.get('name', '챗봇'),
        'image': url_for('static', filename=config.get('thumbnail', 'images/hateslop/club_logo.png')),
        'tags': config.get('tags', ['#챗봇']),
        'description': config.get('description', '')
    }
    return render_template('index.html', bot=bot_info)

# 챗봇 상세정보 페이지
@app.route('/detail')
def detail():
    bot_info = {
        'name': config.get('name', '챗봇'),
        'image': url_for('static', filename=config.get('thumbnail', 'images/hateslop/club_logo.png')),
        'description': config.get('description', ''),
        'tags': config.get('tags', ['#챗봇'])
    }
    return render_template('detail.html', bot=bot_info)

# 채팅 화면
@app.route('/chat')
def chat():
    username = request.args.get('username', '사용자')
    bot_name = config.get('name', '챗봇')
    image_files = get_image_files()
    
    return render_template('chat.html', 
                         bot_name=bot_name, 
                         username=username,
                         image_files=image_files)

# API 엔드포인트: 챗봇 응답 생성
@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        username = data.get('username', '사용자')

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # 챗봇 서비스 임포트 (지연 로딩)
        from services import get_chatbot_service

        # 응답 생성
        chatbot = get_chatbot_service()
        response = chatbot.generate_response(user_message, username)

        return jsonify(response)

    except ImportError as e:
        print(f"[ERROR] 챗봇 서비스 임포트 실패: {e}")
        return jsonify({'reply': '챗봇 서비스를 불러올 수 없습니다. services/chatbot_service.py를 구현해주세요.'}), 500
    except Exception as e:
        print(f"[ERROR] 응답 생성 실패: {e}")
        return jsonify({'reply': '죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.'}), 500


@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    """
    SSE(Server-Sent Events)를 통한 실시간 스트리밍 응답

    LangChain의 stream() 기능을 사용하여 토큰 단위로 실시간 전송
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        username = data.get('username', '사용자')

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        from services import get_chatbot_service
        import json

        @stream_with_context
        def generate():
            """SSE 스트리밍 제너레이터"""
            try:
                chatbot = get_chatbot_service()

                # 스트리밍 응답 생성
                for event in chatbot.generate_response_stream(user_message, username):
                    # SSE 형식으로 전송
                    # data: {"type": "token", "content": "안녕"}
                    event_json = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_json}\n\n"

            except Exception as e:
                print(f"[ERROR] 스트리밍 중 오류: {e}")
                import traceback
                traceback.print_exc()

                # 오류 이벤트 전송
                error_event = {
                    'type': 'error',
                    'content': "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요."
                }
                error_json = json.dumps(error_event, ensure_ascii=False)
                yield f"data: {error_json}\n\n"

        # SSE 응답 반환
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Nginx 버퍼링 비활성화
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        print(f"[ERROR] 스트리밍 엔드포인트 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '스트리밍을 시작할 수 없습니다.'}), 500

# ============================================================================
# 게임 관련 API 엔드포인트
# ============================================================================

# 월별 가이드 데이터
MONTH_GUIDES = {
    3: {
        "title": "3월 - 시즌 준비",
        "message": "드래프트까지 7개월! 강태와 친밀도를 쌓고 기초 체력을 다지세요.",
        "goals": ["친밀도 20 이상", "체력 50 이상"]
    },
    4: {
        "title": "4월 - 본격 시작",
        "message": "시즌이 시작되었습니다. 강태의 훈련을 도와주세요.",
        "goals": ["친밀도 40 이상", "멘탈 45 이상"]
    },
    5: {
        "title": "5월 - 시즌 중반",
        "message": "시즌이 본격화되고 있습니다. 체력과 멘탈 관리가 중요해요.",
        "goals": ["체력 60 이상", "멘탈 50 이상", "친밀도 55 이상"]
    },
    6: {
        "title": "6월 - 중요한 시기",
        "message": "드래프트까지 절반! 전력 향상에 집중할 시간입니다.",
        "goals": ["타격 50 이상", "주루 55 이상", "친밀도 70 이상"]
    },
    7: {
        "title": "7월 - 여름 훈련",
        "message": "더운 날씨지만 훈련 강도를 높여야 합니다. 스트레스 관리도 필수!",
        "goals": ["체력 70 이상", "멘탈 60 이상", "타격 65 이상"]
    },
    8: {
        "title": "8월 - 결전의 날",
        "message": "드래프트가 한 달 앞으로! 마지막 점검이 필요합니다.",
        "goals": ["모든 기술/신체 스탯 70 이상", "친밀도 85 이상"]
    },
    9: {
        "title": "9월 - 드래프트 직전",
        "message": "드래프트가 곧 시작됩니다! 강태와 함께한 시간을 돌아보세요.",
        "goals": ["최종 점검", "드래프트 준비 완료"]
    }
}

@app.route('/api/game/stats', methods=['GET'])
def api_get_stats():
    """현재 게임 스탯 조회"""
    try:
        username = request.args.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        return jsonify({
            'success': True,
            'current_month': game_state.current_month,
            'month': game_state.current_month,
            'current_day': game_state.current_day,
            'day': game_state.current_day,
            'stats': game_state.stats.to_dict(),
            'flags': game_state.flags,
            'event_history': game_state.event_history,
            'months_until_draft': game_state.get_months_until_draft(),
            'intimacy_level': chatbot.stat_calculator.get_intimacy_level(game_state.stats.intimacy)
        })
    except Exception as e:
        print(f"[ERROR] 스탯 조회 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/game/advance', methods=['POST'])
def api_advance_month():
    """
    다음 달로 진행 (스토리북 시스템 통합)

    Request Body:
        {"username": "사용자"}

    Returns:
        {
            "success": True,
            "transition_storybook_id": "3_to_4_transition",
            "new_month": 4
        }
    """
    try:
        data = request.get_json()
        username = data.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        storybook_manager = get_storybook_manager()

        # 목표 달성 확인 (디버깅 모드: 임시로 비활성화)
        # all_achieved, goals_info = storybook_manager.check_goals_achieved(game_state)
        # if not all_achieved and game_state.current_month < 9:
        #     return jsonify({
        #         'success': False,
        #         'error': '목표를 달성하지 못했습니다',
        #         'goals_info': goals_info
        #     }), 400

        old_month = game_state.current_month

        # ========== 8월 경기 계산 로직 ==========
        # 8월에서 9월로 넘어갈 때 경기 결과가 아직 계산되지 않았으면 자동 계산
        if old_month == 8 and game_state.flags.get('tournament_result') == 'strikeout':
            print("[8월 이벤트] 경기 결과 계산 시작")

            # 1. 채팅 히스토리에서 최근 10개 메시지 추출
            conversation_history = chatbot.get_session_history(username).messages
            recent_messages = conversation_history[-10:] if len(conversation_history) >= 10 else conversation_history

            # 2. 사용자 메시지만 필터링
            user_messages = [
                msg.content
                for msg in recent_messages
                if hasattr(msg, 'type') and msg.type == 'human'
            ]

            # 3. 조언 문자열 생성 (없으면 기본값)
            if user_messages:
                advice = "\n".join(user_messages)
                print(f"[8월 이벤트] 추출된 조언 ({len(user_messages)}개 메시지):\n{advice[:100]}...")
            else:
                advice = "..."
                print("[8월 이벤트] 채팅 없음, 기본 조언 사용")

            # 4. 경기 결과 계산
            from services.game_event_manager import get_game_event_manager
            event_manager = get_game_event_manager()
            result, details = event_manager.calculate_at_bat_result(advice, game_state.stats.stamina)

            # 5. 결과에 따라 스토리북 ID 설정
            if result == "homerun":
                game_state.flags['tournament_result'] = 'homerun'
                next_storybook_id = "8_result_homerun"
                print(f"[8월 이벤트] 결과: 홈런 → {next_storybook_id}")
            elif result == "hit":
                game_state.flags['tournament_result'] = 'hit'  # 도루는 나중에 결정
                game_state.next_action = "decide_steal"
                next_storybook_id = "8_result_hit"
                print(f"[8월 이벤트] 결과: 안타 → {next_storybook_id} (도루 분기 대기)")
            else:  # strikeout
                game_state.flags['tournament_result'] = 'strikeout'
                next_storybook_id = "8_result_strikeout"
                print(f"[8월 이벤트] 결과: 삼진 → {next_storybook_id}")

            print(f"[8월 이벤트] 계산 상세: {details}")

            # 월은 증가시키지 않음 (결과 스토리북 → 도루 분기 → 8_to_9_transition → 9월)
        else:
            # 일반 월 진행 (기존 로직)
            next_storybook_id = storybook_manager.get_next_storybook_id(game_state)
        # ========== 8월 경기 계산 로직 끝 ==========

        if not next_storybook_id:
            return jsonify({
                'success': False,
                'error': '다음 단계를 결정할 수 없습니다'
            }), 400

        # 월 증가 (9월 이하일 때만, 단 8월 경기 계산인 경우는 제외)
        august_tournament_calculated = old_month == 8 and game_state.flags.get('tournament_result') != 'strikeout'
        if game_state.current_month < 9 and not august_tournament_calculated:
            game_state.current_month += 1

            # 월별 체력 회복
            stamina_recovery = 0
            if game_state.current_month in [3, 4, 5]:
                stamina_recovery = 25
            elif game_state.current_month in [6, 7]:
                stamina_recovery = 15
            elif game_state.current_month in [8, 9]:
                stamina_recovery = 10

            if stamina_recovery > 0:
                game_state.stats.apply_changes({'stamina': stamina_recovery})
                print(f"[월 진행] {game_state.current_month}월 시작: 체력 +{stamina_recovery}")

            # 훈련 횟수 리셋
            game_state.training_count_this_month = 0
            print(f"[월 진행] 훈련 횟수 리셋")

            # 이전 월 스탯 저장 (전환 스토리북에서 변화량 표시용)
            game_state.save_previous_month_stats()

        new_month = game_state.current_month

        # 스토리북 모드로 전환
        game_state.set_storybook_mode(next_storybook_id)

        # 게임 상태 저장
        chatbot.game_manager.save(username)

        return jsonify({
            'success': True,
            'transition_storybook_id': next_storybook_id,
            'old_month': old_month,
            'new_month': new_month,
            'message': f'{old_month}월을 마무리하고 {new_month}월로 넘어갑니다'
        })

    except Exception as e:
        print(f"[ERROR] 월 진행 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


@app.route('/api/game/hints', methods=['GET'])
def api_get_hints():
    """현재 상황에 맞는 추천 응답 가져오기"""
    try:
        username = request.args.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        # 친밀도와 월에 따른 추천 응답
        intimacy = game_state.stats.intimacy
        month = game_state.current_month

        # 월별 기본 추천 응답 (월별 컨텍스트 우선)
        month_hints_map = {
            3: [  # 시즌 준비, 기초 체력 다지기, 첫 만남
                "처음 뵙겠습니다. 잘 부탁드립니다.",
                "3월이니까 기초 체력부터 다져볼까?",
                "시즌 준비는 어떻게 하고 있어?"
            ],
            4: [  # 시즌 시작, 본격적인 훈련, 관계 구축
                "시즌이 시작됐는데 컨디션은 어때?",
                "타격 연습은 잘 되고 있어?",
                "힘든 거 있으면 언제든 말해"
            ],
            5: [  # 슬럼프 극복, 멘탈 관리
                "최근 슬럼프 있는 것 같은데 괜찮아?",
                "멘탈 관리가 중요한 시기야",
                "너의 강점을 믿어"
            ],
            6: [  # 중반 점검, 약점 보완
                "주루 연습도 조금씩 해볼까?",
                "지금까지 잘 해왔어. 계속 가자",
                "약점을 보완할 시간이야"
            ],
            7: [  # 집중 훈련, 드래프트 준비 본격화
                "드래프트가 2달 남았어. 집중하자",
                "네 잠재력을 믿어",
                "힘든 훈련이지만 견뎌내자"
            ],
            8: [  # 마지막 스퍼트, 최종 점검
                "이제 한 달 남았어! 최선을 다하자",
                "지금까지의 성장이 자랑스러워",
                "마지막까지 포기하지 말자"
            ],
            9: [  # 드래프트 직전, 심리 안정
                "드디어 드래프트야. 긴장하지 마",
                "너의 노력이 빛을 발할 거야",
                "자신감을 가져. 넌 충분히 잘했어"
            ]
        }

        # 월별 기본 힌트 가져오기
        hints = month_hints_map.get(month, [
            "안녕? 처음 뵙겠습니다.",
            "야구 시즌 준비 어때?",
            "오늘 컨디션은 괜찮아?"
        ])

        # 친밀도에 따른 추가 응답 (월별 기본 응답 이후)
        if intimacy < 30:
            hints.extend([
                "안녕? 처음 뵙겠습니다.",
                "궁금한 게 있으면 물어봐도 돼.",
                "오늘 어떤 하루였어?"
            ])
        elif intimacy < 60:
            hints.extend([
                "오늘 훈련 어땠어? 피곤하지 않아?",
                "최근에 고민 있는 것 같던데, 괜찮아?",
                "영양 관리 잘 하고 있어?"
            ])
        else:
            hints.extend([
                "요즘 컨디션 최고인 것 같아!",
                "너의 노력이 정말 대단해. 계속 응원할게!",
                "드래프트까지 함께 가자!"
            ])

        return jsonify({
            'success': True,
            'hints': hints,
            'month': month,
            'intimacy_level': chatbot.stat_calculator.get_intimacy_level(intimacy)
        })

    except Exception as e:
        print(f"[ERROR] 힌트 조회 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/game/moments', methods=['GET'])
def api_get_moments():
    """특별한 순간 목록 조회"""
    try:
        username = request.args.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        return jsonify({
            'success': True,
            'moments': game_state.special_moments,
            'count': len(game_state.special_moments)
        })

    except Exception as e:
        print(f"[ERROR] 특별한 순간 조회 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 스토리북 관련 API 엔드포인트
# ============================================================================

@app.route('/api/storybook/<storybook_id>', methods=['GET'])
def api_get_storybook(storybook_id: str):
    """
    특정 스토리북 데이터 반환

    Query Params:
        - username: 사용자 이름 (게임 상태 확인용)

    Returns:
        {
            "success": True,
            "storybook": {...},
            "current_stats": {...}
        }
    """
    try:
        username = request.args.get('username', '사용자')

        # 스토리북 관리자 가져오기
        storybook_manager = get_storybook_manager()

        # 스토리북 가져오기
        storybook = storybook_manager.get_storybook(storybook_id)

        # 현재 게임 상태 가져오기 (스탯 표시용)
        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        return jsonify({
            'success': True,
            'storybook': storybook,
            'current_stats': game_state.stats.to_dict(),
            'current_month': game_state.current_month
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        print(f"[ERROR] 스토리북 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


@app.route('/api/storybook/current', methods=['GET'])
def api_get_current_storybook():
    """
    현재 게임 상태에 맞는 스토리북 반환

    Query Params:
        - username: 사용자 이름

    Returns:
        {
            "success": True,
            "storybook": {...} or None,
            "phase": "storybook" | "chat"
        }
    """
    try:
        username = request.args.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        storybook_manager = get_storybook_manager()
        current_storybook = storybook_manager.get_current_storybook(game_state)

        return jsonify({
            'success': True,
            'storybook': current_storybook,
            'phase': game_state.current_phase,
            'current_month': game_state.current_month
        })
    except Exception as e:
        print(f"[ERROR] 현재 스토리북 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


@app.route('/api/training', methods=['POST'])
def api_training():
    """훈련 세션 처리"""
    try:
        data = request.get_json()
        username = data.get('username', '사용자')
        intensity = data.get('intensity', 50)
        focuses = data.get('focuses', [])

        if not focuses:
            return jsonify({
                'success': False,
                'error': '훈련할 항목을 선택해주세요.'
            }), 400

        from services import get_chatbot_service
        from services.training_manager import get_training_manager

        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        training_manager = get_training_manager()

        # 훈련 실행
        outcome = training_manager.execute(
            game_state=game_state,
            intensity=intensity,
            focuses=focuses
        )

        # 게임 상태 저장
        chatbot.game_manager.save(username)

        return jsonify({
            'success': True,
            'intensity_label': outcome.intensity_label,
            'summary': outcome.summary,
            'stat_changes': outcome.stat_changes,
            'stamina_change': outcome.stamina_change,
            'total_changes': outcome.total_changes,
            'conversation_note': outcome.conversation_note
        })

    except ValueError as e:
        error_msg = str(e)
        print(f"[WARNING] 훈련 제한 조건: {error_msg}")

        # 체력 부족이나 훈련 횟수 초과는 "경고"로 처리 (오류가 아님)
        return jsonify({
            'success': False,
            'warning': True,  # 경고 플래그
            'message': error_msg
        }), 200  # 200 OK로 반환 (정상적인 게임 메커니즘)
    except Exception as e:
        print(f"[ERROR] 훈련 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


@app.route('/api/game/check-goals', methods=['GET'])
def api_check_goals():
    """
    월별 목표 달성 여부 확인

    Query Params:
        - username: 사용자 이름

    Returns:
        {
            "success": True,
            "goals_achieved": True/False,
            "goals_info": {...},
            "can_advance": True/False
        }
    """
    try:
        username = request.args.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        storybook_manager = get_storybook_manager()

        # 9월이면 항상 진행 가능 (엔딩으로)
        if game_state.current_month >= 9:
            return jsonify({
                'success': True,
                'goals_achieved': True,
                'can_advance': True,
                'message': '드래프트로 진행합니다'
            })

        # 목표 달성 확인
        all_achieved, goals_info = storybook_manager.check_goals_achieved(game_state)

        return jsonify({
            'success': True,
            'goals_achieved': all_achieved,
            'goals_info': goals_info,
            'can_advance': all_achieved,
            'current_stats': game_state.stats.to_dict(),
            'current_month': game_state.current_month
        })
    except Exception as e:
        print(f"[ERROR] 목표 확인 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


@app.route('/api/storybook/complete', methods=['POST'])
def api_complete_storybook():
    """
    스토리북 완료 및 다음 단계로 전환

    Request Body:
        {
            "username": "사용자",
            "storybook_id": "3_opening"
        }

    Returns:
        {
            "success": True,
            "next_action": "start_chat_mode" | "show_next_storybook" | "game_end",
            "next_storybook_id": "4_opening" (if applicable)
        }
    """
    try:
        data = request.get_json()
        username = data.get('username', '사용자')
        storybook_id = data.get('storybook_id')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        if game_state.next_action == "decide_steal" and storybook_id == "8_result_hit":
            print("[Game Event] '안타' 스토리북 완료. '도루' 결과를 계산합니다.")
            event_manager = get_game_event_manager()
            steal_result, _ = event_manager.calculate_steal_result(game_state)

            if steal_result == "steal_success":
                game_state.flags['tournament_result'] = 'hit_steal'
                next_storybook_id = "8_steal_success"
            else: # steal_fail
                game_state.flags['tournament_result'] = 'hit'
                next_storybook_id = "8_steal_fail"
            
            game_state.next_action = None # 모든 이벤트 종료
            game_state.set_storybook_mode(next_storybook_id)
            chatbot.game_manager.save(username)
            
            return jsonify({
                'success': True,
                'next_action': 'show_next_storybook',
                'next_storybook_id': next_storybook_id
            })

        # 스토리북 완료 표시
        game_state.mark_storybook_completed(storybook_id)

        # 특별한 순간 카드 생성 (5월 집 방문, 8월 대회)
        from services.moment_manager import get_moment_manager
        moment_mgr = get_moment_manager()

        if storybook_id == "5_main_event":
            # 5월 집 방문 이벤트 카드 생성
            card = moment_mgr.create_event_card(
                category='home_visit',
                title='보이지 않는 상처',
                description='강태의 집을 방문해 그의 과거와 깊은 상처를 알게 되었습니다.',
                month=5,
                image_url='./static/images/chatbot/5_month_house.png',
                stats_snapshot=game_state.stats.to_dict()
            )
            moment_mgr.add_cards_to_game_state(game_state, [card])

        elif storybook_id in ["8_result_homerun", "8_result_hit", "8_steal_success", "8_steal_fail"]:
            # 8월 대회 결과 카드 생성 (결과별 다른 제목/설명)
            tournament_result = game_state.flags.get('tournament_result', 'strikeout')

            if tournament_result == 'homerun':
                title = '기적의 역전 만루 홈런'
                description = '9회 말 2사 만루, 강태가 끝내기 만루 홈런을 터뜨렸습니다!'
                image_url = './static/images/chatbot/cheers1.png'
            elif tournament_result == 'hit_steal':
                title = '극적인 도루 성공'
                description = '동점 적시타 후 도루에 성공하며 트라우마를 극복했습니다!'
                image_url = './static/images/chatbot/cheers2.png'
            elif tournament_result == 'hit':
                title = '동점 적시타'
                description = '9회 말 2사 만루, 강태가 동점 적시타를 쳐냈습니다!'
                image_url = './static/images/chatbot/cheers2.png'
            else:  # strikeout
                title = '아쉬운 삼진'
                description = '9회 말 마지막 타석, 아쉽게 삼진을 당했지만 강태는 성장했습니다.'
                image_url = './static/images/chatbot/ballpark.png'

            card = moment_mgr.create_event_card(
                category='tournament',
                title=title,
                description=description,
                month=8,
                image_url=image_url,
                stats_snapshot=game_state.stats.to_dict()
            )
            moment_mgr.add_cards_to_game_state(game_state, [card])

        # 스토리북 정보 가져오기
        storybook_manager = get_storybook_manager()
        storybook = storybook_manager.get_storybook(storybook_id)
        completion_action = storybook.get('completion_action', {})

        # completion_action이 문자열인지 딕셔너리인지 확인 (하위 호환성)
        if isinstance(completion_action, str):
            # 문자열인 경우: storybook_config.json의 간단한 형식
            action_type = completion_action
            action_message = ''
            next_storybook_id = storybook.get('next_storybook_id')
        else:
            # 딕셔너리인 경우: 확장된 형식
            action_type = completion_action.get('type', 'start_chat_mode')
            action_message = completion_action.get('message', '')
            next_storybook_id = completion_action.get('next_storybook_id')

        response_data = {
            'success': True,
            'next_action': action_type,
            'message': action_message
        }

        if action_type == 'start_chat_mode':
            game_state.set_chat_mode()
            response_data['message'] = '대화를 시작하세요'

        elif action_type == 'show_next_storybook':
            # 다음 스토리북 표시
            if next_storybook_id:
                game_state.set_storybook_mode(next_storybook_id)
                response_data['next_storybook_id'] = next_storybook_id

        elif action_type == 'determine_ending':
            # 엔딩 결정
            ending = storybook_manager.determine_ending(game_state)
            response_data['ending'] = ending
            response_data['next_action'] = 'game_end'

        elif action_type == 'game_end':
            # 게임 종료
            response_data['message'] = '게임이 종료되었습니다'

        # 게임 상태 저장
        chatbot.game_manager.save(username)

        return jsonify(response_data)

    except Exception as e:
        print(f"[ERROR] 스토리북 완료 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500


# ============================================================================
# 월별 시스템 메시지 (채팅 시작 시 상황 설명)
# ============================================================================

def get_month_system_message(storybook_id: str) -> str:
    """
    스토리북 완료 후 채팅 시작 시 전송할 시스템 메시지
    (사용자에게 보이지 않음, 챗봇에게만 전달되어 상황 인지)

    Args:
        storybook_id: 완료된 스토리북 ID

    Returns:
        시스템 메시지 문자열 (상황 설명만, 태도는 기존 로직 사용)
    """
    messages = {
        # === 월별 시작 ===
        "3_opening": "3월이 시작되었습니다. 새로운 코치를 만난 첫 달입니다.",

        "4_opening": "4월이 시작되었습니다. 기초 훈련을 시작할 시기입니다.",

        # 5월 특수: 트라우마 공개 직후
        "5_main_event": """5월입니다.
방금 전 어머니가 코치님에게 당신의 과거를 이야기했습니다.
중학교 때 전 코치에게 배신당한 일, 부상을 악화시킨 일, 약속을 어긴 일.
집에 들어와서 두 사람이 대화한 것을 알게 되었습니다.""",

        "6_opening": "6월이 시작되었습니다. 5월의 힘든 시간을 극복하고, 드래프트까지 절반이 지났습니다.",

        "7_opening": "7월이 시작되었습니다. 무더운 여름, 드래프트까지 2개월 남았습니다.",

        # === 8월 특수 시퀀스 ===
        # 8월 시작: 타석 직전
        "8_opening": """8월, 대통령배 결승전입니다.
9회 말 2사 만루, 4:3로 뒤진 상황. 다음 타석은 당신입니다.
이전 타석까지 계속 삼진만 당했습니다.
더그아웃에 앉아 배트를 쥐고 있습니다. 손이 떨립니다.""",

        # 타석 결과 1: 홈런
        "8_result_homerun": """방금 홈런을 쳤습니다!
역전 만루 홈런으로 팀이 기적적인 승리를 거뒀습니다.
관중들의 환호 소리가 귀를 울립니다.""",

        # 타석 결과 2: 삼진
        "8_result_strikeout": """방금 삼진을 당했습니다.
팀이 패배했습니다. 벤치로 돌아왔습니다.
아쉬움과 죄책감이 밀려옵니다.""",

        # 도루 결과 1: 성공
        "8_steal_success": """방금 도루에 성공했습니다!
과거의 트라우마를 극복하고, 주루 플레이까지 완벽하게 해냈습니다.
코치님 덕분입니다.""",

        # 도루 결과 2: 실패
        "8_steal_fail": """도루를 시도하지 못했습니다.
과거의 기억이 발을 묶었습니다.
경기는 무승부로 끝났습니다. 아쉬움이 남습니다.""",

        # === 9월 ===
        "9_opening": "9월, 드래프트 날입니다. 6개월간 코치님과 함께한 노력이 결실을 맺을 순간입니다."
    }

    return messages.get(storybook_id, "")


# ============================================================================
# 월 시작 API (시스템 메시지 자동 전송)
# ============================================================================

@app.route('/api/chat/month-start', methods=['POST'])
def api_month_start():
    """
    새 월 시작 시 시스템 메시지 반환
    (실제 챗봇 응답은 /api/chat/stream을 통해 스트리밍)

    Request:
        {
            "username": "사용자",
            "storybook_id": "5_main_event"
        }

    Response:
        {
            "success": True,
            "system_message": "시스템 메시지 내용" or None
        }
    """
    try:
        data = request.get_json()
        storybook_id = data.get('storybook_id', '')

        # 월별 시스템 메시지 생성
        system_message = get_month_system_message(storybook_id)

        return jsonify({
            'success': True,
            'system_message': system_message
        })

    except Exception as e:
        print(f"[ERROR] 월 시작 API 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# 헬스체크 엔드포인트 (Vercel용)
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'chatbot': config.get('name', 'unknown')})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    # threaded=True는 SSE 스트리밍에 필수
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)


# <<< 수정 시작: 8월 대회 이벤트를 처리하는 새로운 API 엔드포인트 추가 >>>
# 이유: 사용자가 입력한 '조언'을 받아 타석 결과를 계산하고, 그 결과에 맞는 다음 스토리북을 알려주는 역할을 합니다.
@app.route('/api/game/play-at-bat', methods=['POST'])
def play_at_bat():
    """8월 대회에서 사용자의 조언을 바탕으로 타석 결과를 결정합니다."""
    try:
        data = request.get_json()
        username = data.get('username')
        advice = data.get('advice')

        if not username or not advice:
            return jsonify({'success': False, 'error': 'Username and advice are required'}), 400

        from services import get_chatbot_service
        from services.game_event_manager import get_game_event_manager

        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)
        
        # 이벤트 계산기 실행
        event_manager = get_game_event_manager()
        result, details = event_manager.calculate_at_bat_result(advice, game_state.stats.stamina)

        # <<< 수정 시작: 결과에 따라 '다음 행동' 플래그를 설정하거나 초기화 >>>
        # 이유: '안타'가 나왔을 경우, 다음 단계가 '도루 결정'임을 시스템에 알려줘야 합니다.
        if result == "hit":
            game_state.next_action = "decide_steal"
            next_storybook_id = "8_result_hit"
        elif result == "homerun":
            game_state.flags['tournament_result'] = 'homerun'
            game_state.next_action = None # 이벤트 종료
            next_storybook_id = "8_result_homerun"
        else: # strikeout
            game_state.flags['tournament_result'] = 'strikeout'
            game_state.next_action = None # 이벤트 종료
            next_storybook_id = "8_result_strikeout"
        # <<< 수정 끝 >>>

        game_state.set_storybook_mode(next_storybook_id)
        chatbot.game_manager.save(username)

        return jsonify({
            'success': True,
            'result': result,
            'next_storybook_id': next_storybook_id,
            'details': details
        })

    except Exception as e:
        print(f"[ERROR] 8월 이벤트 API 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '서버 오류가 발생했습니다.'}), 500
# <<< 수정 끝 >>>