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
from flask import Flask, request, render_template, jsonify, url_for
from dotenv import load_dotenv

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

# ============================================================================
# 게임 관련 API 엔드포인트
# ============================================================================

# 월별 가이드 데이터
MONTH_GUIDES = {
    3: {
        "title": "3월 - 시즌 준비",
        "message": "드래프트까지 7개월! 민석이와 친밀도를 쌓고 기초 체력을 다지세요.",
        "goals": ["친밀도 20 이상", "체력 60 이상"]
    },
    4: {
        "title": "4월 - 본격 시작",
        "message": "시즌이 시작되었습니다. 민석이의 훈련을 도와주세요.",
        "goals": ["친밀도 40 이상", "멘탈 60 이상"]
    },
    5: {
        "title": "5월 - 시즌 중반",
        "message": "시즌이 본격화되고 있습니다. 체력과 멘탈 관리가 중요해요.",
        "goals": ["체력 70 이상", "멘탈 65 이상", "친밀도 55 이상"]
    },
    6: {
        "title": "6월 - 중요한 시기",
        "message": "드래프트까지 절반! 전력 향상에 집중할 시간입니다.",
        "goals": ["힘 50 이상", "주루 50 이상", "친밀도 70 이상"]
    },
    7: {
        "title": "7월 - 여름 훈련",
        "message": "더운 날씨지만 훈련 강도를 높여야 합니다. 스트레스 관리도 필수!",
        "goals": ["체력 80 이상", "멘탈 75 이상", "힘 65 이상"]
    },
    8: {
        "title": "8월 - 막바지 준비",
        "message": "드래프트가 한 달 앞으로! 마지막 점검이 필요합니다.",
        "goals": ["모든 스탯 70 이상", "친밀도 85 이상"]
    },
    9: {
        "title": "9월 - 드래프트 직전",
        "message": "드래프트가 곧 시작됩니다! 민석이와 함께한 시간을 돌아보세요.",
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
            'month': game_state.current_month,
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
    """다음 달로 진행"""
    try:
        data = request.get_json()
        username = data.get('username', '사용자')

        from services import get_chatbot_service
        chatbot = get_chatbot_service()
        game_state = chatbot.game_manager.get_or_create(username)

        # 9월 이후면 진행 불가
        if game_state.current_month >= 9:
            return jsonify({
                'success': False,
                'message': '이미 9월입니다. 드래프트를 진행하세요!'
            })

        # 다음 달로 진행
        success = chatbot.game_manager.advance_month(username)

        if success:
            # 이벤트 체크
            conversation_history = chatbot.get_session_history(username).messages
            event_info = chatbot.event_detector.check_event(
                game_state=game_state,
                conversation_history=conversation_history,
                recent_messages=10
            )

            # 월별 가이드 가져오기
            guide = MONTH_GUIDES.get(game_state.current_month, None)

            return jsonify({
                'success': True,
                'new_month': game_state.current_month,
                'event': event_info,
                'guide': guide,
                'message': f'{game_state.current_month}월이 시작되었습니다!'
            })
        else:
            return jsonify({
                'success': False,
                'message': '월 진행에 실패했습니다.'
            })

    except Exception as e:
        print(f"[ERROR] 월 진행 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


# 헬스체크 엔드포인트 (Vercel용)
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'chatbot': config.get('name', 'unknown')})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
