console.log("챗봇 JS 로드 완료");

// ============================================================================
// 전역 상태 관리
// ============================================================================

const AppState = {
  // 스토리북 상태
  storybook: {
    current: null,          // 현재 스토리북 데이터
    currentPage: 0,         // 현재 페이지 번호
    isActive: false,        // 스토리북 모드 여부
    isProcessing: false     // 처리 중 플래그 (중복 클릭 방지)
  },

  // 온보딩 상태
  onboarding: {
    currentPage: 1,
    totalPages: 5
  },

  // 카운터
  counters: {
    message: 0,
    notification: 0
  },

  // 게임 상태 (서버에서 받아옴)
  game: null,

  training: {
    isAvailable: false,
    isOpen: false,
    isSubmitting: false,
    intensity: 60,
    focuses: ['batting']
  },

  // 초기화 상태
  initialization: {
    status: 'pending',      // 'pending' | 'loading' | 'ready' | 'error'
    storybookChecked: false,
    gameStateLoaded: false
  },

  // 스탯 애니메이션을 위한 이전 값 저장
  previousStats: {
    intimacy: null,
    mental: null,
    stamina: null,
    batting: null,
    speed: null,
    defense: null
  }
};

// ============================================================================
// 월별 정보 매핑
// ============================================================================

const MONTH_INFO = {
  3: {
    title: "3월 - 첫 만남",
    subtitle: "강태와의 여정이 시작됩니다",
    description: "드래프트까지 6개월, 신뢰를 쌓아가는 시간"
  },
  4: {
    title: "4월 - 봄의 시작",
    subtitle: "기초를 다지는 시간\n\n※스탯조절 창에 있는 훈련 조절 버튼을 눌러서 훈련을 시작하세요!",
    description: "탄탄한 기본기로 미래를 준비합니다"
  },
  5: {
    title: "5월 - 보이지 않는 상처",
    subtitle: "강태의 과거와 마주하다",
    description: "강태를 이해하고 보듬으며 성장시킵니다"
  },
  6: {
    title: "6월 - 중반전",
    subtitle: "반환점을 돌았습니다\n\n※스탯조절 창에 있는 훈련 조절 버튼을 눌러서 훈련을 시작하세요!",
    description: "약점을 보완하고 강점을 극대화합니다"
  },
  7: {
    title: "7월 - 여름 강화",
    subtitle: "무더위를 뚫고 전진\n\n※스탯조절 창에 있는 훈련 조절 버튼을 눌러서 훈련을 시작하세요!",
    description: "체력과 멘탈을 끌어올립니다"
  },
  8: {
    title: "8월 - 결전의 날",
    subtitle: "마지막 스퍼트",
    description: "드래프트가 한 달 앞으로 다가왔습니다"
  },
  9: {
    title: "9월 - 드래프트",
    subtitle: "운명의 순간",
    description: "6개월의 노력이 결실을 맺을 시간"
  }
};


const TRAINING_MONTHS = new Set([4, 6, 7]);

// ============================================================================
// DOM 요소
// ============================================================================

const chatBookContainer = document.querySelector(".chat-book-container");
const username = chatBookContainer ? chatBookContainer.dataset.username : "사용자";
const chatLog = document.getElementById("chat-log");
const userMessageInput = document.getElementById("user-message");
const sendBtn = document.getElementById("send-btn");

// 월별 페이지 요소
const monthImageContainer = document.getElementById("month-image-container");
const monthTitle = document.getElementById("month-title");
const chatBookLeft = document.querySelector(".chat-book-left");

const trainingButton = document.getElementById("training-button");
const trainingModal = document.getElementById("training-modal");
const trainingIntensityInput = document.getElementById("training-intensity");
const trainingIntensityLabel = document.getElementById("training-intensity-label");
const trainingSubmitBtn = document.getElementById("training-submit");
const trainingCloseBtn = document.getElementById("training-close");


const TRAINING_FOCUS_LABELS = {
  batting: "타격",
  speed: "주루",
  defense: "수비",
};

function getTrainingFocusInputs() {
  return document.querySelectorAll('input[name="training-focus"]');
}

function describeTrainingIntensity(value) {
  const val = Number(value);
  if (val <= 20) return "회복 세션";
  if (val <= 40) return "가벼운 훈련";
  if (val <= 70) return "기본 훈련";
  if (val <= 85) return "집중 훈련";
  return "고강도 훈련";
}

function updateTrainingIntensityLabel(value) {
  if (!trainingIntensityLabel) return;
  const label = describeTrainingIntensity(value);
  trainingIntensityLabel.textContent = "강도 " + value + " - " + label;
}

function getCurrentMonthValue() {
  if (AppState.game && typeof AppState.game.current_month === 'number') {
    return AppState.game.current_month;
  }
  const monthElem = document.getElementById('current-month');
  if (!monthElem) return null;
  const parsed = parseInt(monthElem.textContent, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function refreshTrainingAvailability() {
  if (!trainingButton) return;
  const month = getCurrentMonthValue();
  const available = typeof month === 'number' && TRAINING_MONTHS.has(month) && !AppState.storybook.isActive;
  AppState.training.isAvailable = available;
  trainingButton.style.display = available ? 'block' : 'none';
  trainingButton.disabled = !available;
}

function openTrainingModal() {
  if (!AppState.training.isAvailable || !trainingModal) {
    showError('지금은 훈련을 진행할 수 없습니다.');
    return;
  }
  AppState.training.isOpen = true;
  trainingModal.classList.add('open');
  updateTrainingIntensityLabel(AppState.training.intensity);
}

function closeTrainingModal() {
  if (!trainingModal) return;
  AppState.training.isOpen = false;
  trainingModal.classList.remove('open');
}

function getSelectedTrainingFocuses() {
  return Array.from(getTrainingFocusInputs())
    .filter((input) => input.checked)
    .map((input) => input.value);
}

function formatTrainingChanges(statChanges, staminaChange) {
  const parts = [];
  if (statChanges) {
    Object.entries(statChanges).forEach(([key, delta]) => {
      const label = TRAINING_FOCUS_LABELS[key] || key;
      parts.push(label + ' ' + (delta > 0 ? '+' : '') + delta);
    });
  }
  if (typeof staminaChange === 'number' && staminaChange !== 0) {
    parts.push('체력 ' + (staminaChange > 0 ? '+' : '') + staminaChange);
  }
  return parts.join(', ');
}

async function submitTraining(event) {
  if (event) {
    event.preventDefault();
  }
  if (!AppState.training.isAvailable || AppState.training.isSubmitting) {
    return;
  }

  const focuses = getSelectedTrainingFocuses();
  if (focuses.length === 0) {
    showError('훈련할 항목을 최소 하나 선택해 주세요.');
    return;
  }

  AppState.training.focuses = focuses;
  AppState.training.isSubmitting = true;

  try {
    const intensityValue = trainingIntensityInput ? Number(trainingIntensityInput.value) : AppState.training.intensity;
    if (!Number.isNaN(intensityValue)) {
      AppState.training.intensity = intensityValue;
    }

    const payload = {
      username,
      intensity: AppState.training.intensity,
      focuses,
    };

    const response = await fetch('/api/training', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    // 경고 처리 (체력 부족, 훈련 횟수 초과 등)
    if (!data.success && data.warning) {
      closeTrainingModal();
      showWarning(data.message);
      return;
    }

    // 실제 오류 처리
    if (!response.ok || !data.success) {
      throw new Error(data.error || '훈련 요청이 실패했습니다.');
    }

    closeTrainingModal();

    // 훈련 결과를 카드 형식으로 표시
    showTrainingResultCard(data);

    await fetchGameState();
  } catch (error) {
    showError('훈련 처리 중 오류가 발생했습니다.', error);
    console.error('[TRAINING] Error', error);
  } finally {
    AppState.training.isSubmitting = false;
  }
}

function initializeTrainingUI() {
  if (!trainingButton) {
    return;
  }

  trainingButton.addEventListener('click', openTrainingModal);

  if (trainingCloseBtn) {
    trainingCloseBtn.addEventListener('click', closeTrainingModal);
  }

  if (trainingIntensityInput) {
    trainingIntensityInput.value = AppState.training.intensity;
    updateTrainingIntensityLabel(AppState.training.intensity);
    trainingIntensityInput.addEventListener('input', (event) => {
      const nextValue = Number(event.target.value);
      AppState.training.intensity = nextValue;
      updateTrainingIntensityLabel(nextValue);
    });
  }

  if (trainingSubmitBtn) {
    trainingSubmitBtn.addEventListener('click', submitTraining);
  }

  if (trainingModal) {
    trainingModal.addEventListener('click', (event) => {
      if (event.target === trainingModal) {
        closeTrainingModal();
      }
    });
  }

  // 훈련 카드 클릭 이벤트 초기화
  initializeTrainingCards();

  // 강도 마커 클릭 이벤트 추가
  initializeIntensityMarkers();

  refreshTrainingAvailability();
}

/**
 * 훈련 카드 클릭 이벤트 초기화
 */
function initializeTrainingCards() {
  const trainingCards = document.querySelectorAll('.training-card');

  trainingCards.forEach(card => {
    card.addEventListener('click', () => {
      const checkbox = card.querySelector('input[type="checkbox"]');
      if (!checkbox) return;

      // 체크박스 상태 토글
      checkbox.checked = !checkbox.checked;

      // 카드 active 클래스 토글
      card.classList.toggle('active', checkbox.checked);

      // 최소 1개는 선택되어 있어야 함
      const allCheckboxes = document.querySelectorAll('.training-card input[type="checkbox"]');
      const checkedCount = Array.from(allCheckboxes).filter(cb => cb.checked).length;

      if (checkedCount === 0) {
        // 마지막 하나를 해제하려고 할 때 다시 체크
        checkbox.checked = true;
        card.classList.add('active');
      }
    });
  });
}

/**
 * 강도 마커 클릭 이벤트 초기화
 */
function initializeIntensityMarkers() {
  const intensityMarkers = document.querySelectorAll('.intensity-marker');

  intensityMarkers.forEach(marker => {
    marker.addEventListener('click', () => {
      const value = Number(marker.getAttribute('data-value'));
      if (trainingIntensityInput && !isNaN(value)) {
        trainingIntensityInput.value = value;
        AppState.training.intensity = value;
        updateTrainingIntensityLabel(value);
      }
    });
  });
}

/**
 * 훈련 결과를 카드 형식으로 표시
 * @param {Object} data - 훈련 결과 데이터
 */
function showTrainingResultCard(data) {
  const chatLog = document.getElementById('chat-log');
  if (!chatLog) return;

  // 강도 레이블 한글 매핑
  const intensityLabelsKR = {
    'Recovery Session': '회복 세션',
    'Light Training': '가벼운 훈련',
    'Standard Training': '기본 훈련',
    'Focused Training': '집중 훈련',
    'High-Intensity Training': '고강도 훈련'
  };

  // 아이콘 매핑
  const intensityIcons = {
    'Recovery Session': '😌',
    'Light Training': '🏃',
    'Standard Training': '💪',
    'Focused Training': '🔥',
    'High-Intensity Training': '⚡'
  };

  const statIcons = {
    'batting': '🏏',
    'speed': '🏃',
    'defense': '⚾'
  };

  const icon = intensityIcons[data.intensity_label] || '💪';
  const intensityKR = intensityLabelsKR[data.intensity_label] || data.intensity_label;

  // 스탯 변화 항목 생성
  const statItems = [];

  if (data.stat_changes && Object.keys(data.stat_changes).length > 0) {
    Object.entries(data.stat_changes).forEach(([key, value]) => {
      const label = TRAINING_FOCUS_LABELS[key] || key;
      const valueClass = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
      const sign = value > 0 ? '+' : '';

      statItems.push(`
        <div class="training-result-stat-item">
          <span class="training-result-stat-label">${statIcons[key] || ''} ${label}</span>
          <span class="training-result-stat-value ${valueClass}">${sign}${value}</span>
        </div>
      `);
    });
  }

  // 체력 변화 추가
  if (typeof data.stamina_change === 'number' && data.stamina_change !== 0) {
    const valueClass = data.stamina_change > 0 ? 'positive' : data.stamina_change < 0 ? 'negative' : 'neutral';
    const sign = data.stamina_change > 0 ? '+' : '';

    statItems.push(`
      <div class="training-result-stat-item">
        <span class="training-result-stat-label">💚 체력</span>
        <span class="training-result-stat-value ${valueClass}">${sign}${data.stamina_change}</span>
      </div>
    `);
  }

  // 훈련 결과 카드 HTML 생성 (summary 제거, 깔끔한 레이아웃)
  const resultCard = document.createElement('div');
  resultCard.className = 'message training-result-card';
  resultCard.innerHTML = `
    <div class="training-result-header">
      <div class="training-result-icon">${icon}</div>
      <div class="training-result-title">
        <h3>${intensityKR}</h3>
      </div>
    </div>
    ${statItems.length > 0 ? `
      <div class="training-result-stats">
        ${statItems.join('')}
      </div>
    ` : '<p style="text-align: center; color: #666; margin: 10px 0;">훈련을 완료했습니다.</p>'}
  `;

  chatLog.appendChild(resultCard);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// ============================================================================
// 오류 처리 유틸리티
// ============================================================================

/**
 * 사용자 친화적인 오류 메시지 표시
 * @param {string} userMessage - 사용자에게 표시할 메시지
 * @param {Error} error - 콘솔에 출력할 오류 객체 (선택)
 */
function showError(userMessage, error = null) {
  if (error) {
    console.error(error);
  }
  appendMessageSync("bot", `❌ ${userMessage}`);
}

/**
 * 알림 자동 제거 (공통 함수)
 * @param {string} notifId - 알림 ID
 * @param {number} delay - 제거까지 대기 시간 (ms)
 */
function autoRemoveNotification(notifId, delay = 7000) {
  setTimeout(() => {
    const element = document.getElementById(notifId);
    if (element) {
      element.style.opacity = '0';
      element.style.transform = 'translateY(-20px)';
      setTimeout(() => element.remove(), 300);
    }
  }, delay);
}

/**
 * 경고 알림 표시 (7초 후 자동 사라짐)
 * @param {string} message - 경고 메시지
 */
function showWarning(message) {
  const notifId = `warning-${AppState.counters.notification++}`;
  const container = document.getElementById("notifications-container");
  if (!container) {
    // 컨테이너가 없으면 콘솔에만 출력
    console.warn('[WARNING]', message);
    return;
  }

  const notification = document.createElement("div");
  notification.className = "notification-item warning";
  notification.id = notifId;
  notification.innerHTML = `
    <div class="notification-title">
      ⚠️ ${message}
    </div>
  `;

  container.appendChild(notification);

  // 7초 후 자동 제거
  autoRemoveNotification(notifId, 7000);
}

// ============================================================================
// 입력 필드 상태 관리
// ============================================================================

/**
 * 채팅 입력 필드 비활성화
 * @param {string} reason - 비활성화 이유 (플레이스홀더에 표시)
 */
function disableChatInput(reason = "로딩 중...") {
  if (userMessageInput) {
    userMessageInput.disabled = true;
    userMessageInput.placeholder = reason;
    userMessageInput.classList.add('disabled');
  }
  if (sendBtn) {
    sendBtn.disabled = true;
  }
  console.log('[입력] 비활성화:', reason);
}

/**
 * 채팅 입력 필드 활성화
 */
function enableChatInput() {
  if (userMessageInput) {
    userMessageInput.disabled = false;
    userMessageInput.placeholder = "메시지를 입력하세요...";
    userMessageInput.classList.remove('disabled');
  }
  if (sendBtn) {
    sendBtn.disabled = false;
  }
  console.log('[입력] 활성화');
}

// 메시지 전송 함수 (EventSource 스트리밍 사용)
async function sendMessage(isInitial = false) {
  let message;

  if (isInitial) {
    message = "init";
  } else {
    message = userMessageInput.value.trim();
    if (!message) return;

    appendMessageSync("user", message);
    userMessageInput.value = "";
  }

  // 로딩 표시
  const loadingId = appendMessageSync("loading", "생각 중...");

  try {
    // fetch로 POST 요청만 보내고 즉시 반환
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        username: username,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 로딩 메시지 제거
    removeMessage(loadingId);

    // 봇 메시지 컨테이너 생성 (빈 상태)
    const messageId = createBotMessageContainer();

    // 응답 읽기 (ReadableStream)
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let fullResponse = '';
    let metadata = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // 버퍼에 추가
      buffer += decoder.decode(value, { stream: true });

      // SSE 이벤트 파싱 (data: {...}\n\n 형식)
      const events = buffer.split('\n\n');
      buffer = events.pop(); // 마지막 불완전한 이벤트는 버퍼에 유지

      for (const eventStr of events) {
        if (!eventStr.trim() || !eventStr.startsWith('data: ')) continue;

        try {
          const jsonStr = eventStr.substring(6); // 'data: ' 제거
          const event = JSON.parse(jsonStr);

          if (event.type === 'token') {
            // 토큰을 실시간으로 추가
            fullResponse += event.content;
            updateBotMessageContent(messageId, fullResponse);

          } else if (event.type === 'metadata') {
            // 메타데이터 즉시 처리 (스탯 업데이트 및 알림)
            metadata = event.content;
            handleChatMetadata(metadata);

          } else if (event.type === 'done') {
            // 스트리밍 완료
            console.log('[STREAM] 완료');

          } else if (event.type === 'event_update') {
            // 이벤트 업데이트 (비동기)
            console.log('[EVENT] 이벤트 업데이트');
            const eventInfo = event.content;
            if (eventInfo && eventInfo.choices) {
              showEventWithOptions(eventInfo);
            } else if (eventInfo) {
              showEventNotification(eventInfo);
            }

          } else if (event.type === 'hint_update') {
            // 힌트 업데이트 (비동기, 컨텍스트 포함)
            console.log('[HINT] 힌트 업데이트');
            const hintInfo = event.content;
            if (hintInfo && hintInfo.hint) {
              showHintWithContext(hintInfo);
            }

          } else if (event.type === 'error') {
            // 오류 처리
            console.error('[STREAM] 오류:', event.content);
            fullResponse = event.content;
            updateBotMessageContent(messageId, fullResponse);
          }

        } catch (e) {
          console.error('[STREAM] 이벤트 파싱 실패:', e, eventStr);
        }
      }
    }

  } catch (error) {
    removeMessage(loadingId);
    showError("메시지 전송에 실패했습니다. 다시 시도해주세요.", error);
    console.error('[STREAM] 전체 오류:', error);
  }
}

// 동기 메시지 추가 (즉시 표시, 스트리밍 없음)
function appendMessageSync(sender, text, imageSrc = null) {
  const messageId = `msg-${AppState.counters.message++}`;
  const messageElem = document.createElement("div");
  messageElem.classList.add("message", sender === "loading" ? "bot" : sender);
  messageElem.id = messageId;

  if (sender === "user") {
    messageElem.textContent = text;
  } else if (sender === "guide") {
    messageElem.classList.add("guide");
    messageElem.innerHTML = text;
  } else {
    // bot 또는 loading 메시지
    const textContainer = document.createElement("div");
    textContainer.classList.add("bot-text-container");
    textContainer.textContent = text;

    if (imageSrc) {
      const botImg = document.createElement("img");
      botImg.classList.add("bot-big-img");
      botImg.src = imageSrc;
      botImg.alt = "챗봇 이미지";
      messageElem.appendChild(botImg);
    }

    messageElem.appendChild(textContainer);
  }

  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  return messageId;
}

// 봇 메시지 컨테이너 생성 (스트리밍용, 빈 상태로 생성)
function createBotMessageContainer(imageSrc = null) {
  const messageId = `msg-${AppState.counters.message++}`;
  const messageElem = document.createElement("div");
  messageElem.classList.add("message", "bot");
  messageElem.id = messageId;

  // 이미지가 있으면 추가
  if (imageSrc) {
    const botImg = document.createElement("img");
    botImg.classList.add("bot-big-img");
    botImg.src = imageSrc;
    botImg.alt = "챗봇 이미지";
    messageElem.appendChild(botImg);
  }

  // 텍스트 컨테이너 (빈 상태)
  const textContainer = document.createElement("div");
  textContainer.classList.add("bot-text-container");
  textContainer.dataset.messageId = messageId; // 나중에 찾기 위한 ID 저장
  messageElem.appendChild(textContainer);

  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  return messageId;
}

// 봇 메시지 내용 업데이트 (스트리밍 토큰 추가)
function updateBotMessageContent(messageId, content) {
  const messageElem = document.getElementById(messageId);
  if (!messageElem) return;

  const textContainer = messageElem.querySelector('.bot-text-container');
  if (!textContainer) return;

  textContainer.textContent = content;

  // 자동 스크롤
  if (chatLog) {
    chatLog.scrollTop = chatLog.scrollHeight;
  }
}

// 메시지 제거
function removeMessage(messageId) {
  const elem = document.getElementById(messageId);
  if (elem) {
    elem.remove();
  }
}

// ============================================================================
// 채팅 화면 관리 함수
// ============================================================================

/**
 * 프론트엔드 채팅 화면 초기화 (시각적으로만)
 * 주의: 백엔드의 실제 대화 기록(챗봇이 보는 기록)은 유지됨
 */
function clearChatDisplay() {
  if (chatLog) {
    chatLog.innerHTML = '';
    AppState.counters.message = 0;
    console.log("[Chat] 채팅 화면 초기화 완료 (백엔드 기록은 유지)");
  }
}

/**
 * 새 월 시작 처리
 * 1. 채팅 화면 초기화
 * 2. 시스템 메시지 자동 전송
 * 3. 챗봇 응답 표시
 *
 * @param {string} storybookId - 완료된 스토리북 ID
 */
async function startNewMonth(storybookId) {
  console.log(`[Month] 월 시작 처리: ${storybookId}`);

  // 1. 채팅 화면 초기화
  clearChatDisplay();

  // 2. 시스템 메시지 가져오기
  try {
    const response = await fetch('/api/chat/month-start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        storybook_id: storybookId
      })
    });

    const data = await response.json();

    if (!data.success || !data.system_message) {
      console.log("[Month] 시스템 메시지 없음, 월 시작 처리 완료");
      return;
    }

    const systemMessage = data.system_message;
    console.log("[Month] 시스템 메시지:", systemMessage.substring(0, 50) + "...");

    // 3. 기존 streaming 로직 재사용하여 챗봇 응답 받기
    await sendSystemMessageStreaming(systemMessage);

    console.log("[Month] 월 시작 처리 완료");

  } catch (error) {
    console.error("[ERROR] 월 시작 처리 실패:", error);
  }
}

/**
 * 시스템 메시지를 streaming으로 전송하고 응답 받기
 * (기존 sendMessage의 streaming 로직 재사용)
 */
async function sendSystemMessageStreaming(systemMessage) {
  // 로딩 표시
  const loadingId = appendMessageSync("loading", "생각 중...");

  try {
    // 기존 /api/chat/stream 사용 (코드 재사용)
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: systemMessage,
        username: username,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 로딩 메시지 제거
    removeMessage(loadingId);

    // 봇 메시지 컨테이너 생성 (빈 상태)
    const messageId = createBotMessageContainer();

    // 응답 읽기 (ReadableStream) - 기존 로직과 동일
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let fullResponse = '';
    let metadata = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop();

      for (const eventStr of events) {
        if (!eventStr.trim() || !eventStr.startsWith('data: ')) continue;

        try {
          const jsonStr = eventStr.substring(6);
          const event = JSON.parse(jsonStr);

          if (event.type === 'token') {
            fullResponse += event.content;
            updateBotMessageContent(messageId, fullResponse);

          } else if (event.type === 'metadata') {
            metadata = event.content;

          } else if (event.type === 'done') {
            console.log('[STREAM] 완료');

          } else if (event.type === 'error') {
            console.error('[STREAM] 오류:', event.content);
            fullResponse = event.content;
            updateBotMessageContent(messageId, fullResponse);
          }

        } catch (e) {
          console.error('[STREAM] 이벤트 파싱 실패:', e, eventStr);
        }
      }
    }

    // 메타데이터 처리 (기존 로직과 동일)
    if (metadata) {
      handleChatMetadata(metadata);
    }

  } catch (error) {
    removeMessage(loadingId);
    showError('네트워크 오류가 발생했습니다. 다시 시도해주세요.', error);
  }
}

/**
 * 채팅 메타데이터 처리 (sendMessage에서 분리, 재사용)
 */
function handleChatMetadata(data) {
  // 1. 이벤트에 선택지(choices)가 있는지 확인
  if (data.event && data.event.choices) {
    showEventWithOptions(data.event);
    return; // 선택지가 있으면 다른 처리는 건너뜀
  }

  // 2. 디버그 정보 출력
  if (data.debug) {
    console.group("🎮 게임 상태 업데이트");
    console.log("📅 현재 시점:", `${data.debug.game_state.current_month}월 ${data.debug.game_state.current_day}일`);
    console.log("🎯 드래프트까지:", `${data.debug.game_state.months_until_draft}개월`);
    console.log("💖 친밀도 레벨:", data.debug.game_state.intimacy_level);

    console.group("📊 스탯 변화");
    if (data.debug.stat_changes && Object.keys(data.debug.stat_changes.changes).length > 0) {
      console.log("변화량:", data.debug.stat_changes.changes);
      console.log("이유:", data.debug.stat_changes.reason);
      console.table({
        "이전": data.debug.stat_changes.old_stats,
        "이후": data.debug.stat_changes.new_stats
      });
    } else {
      console.log("스탯 변화 없음");
    }
    console.groupEnd();

    if (data.debug.event_check?.triggered) {
      console.log("🎭 이벤트 발생:", data.debug.event_check.event_name);
    }

    if (data.debug.hint_provided) {
      console.log("💡 힌트 제공됨");
    }

    console.log("💬 대화 횟수:", data.debug.conversation_count);
    console.log("📜 이벤트 히스토리:", data.debug.event_history);
    console.groupEnd();

    // 스탯 UI 업데이트
    updateStatsUI(data.debug.game_state);
  }

  // 3. 단순 이벤트 알림 표시 (선택지 없는 경우)
  if (data.event && !data.event.choices) {
    showEventNotification(data.event);
  }

  // 4. 힌트 표시
  if (data.hint) {
    showHintNotification(data.hint);
  }

  // 5. 스토리북 이벤트 확인 (기존에 없던 로직 추가)
  if (data.storybook_id) {
    console.log(`[이벤트] 스토리북 발동: ${data.storybook_id}`);
    setTimeout(() => {
      loadAndShowStorybook(data.storybook_id);
    }, 500);
  }
}

// 엔터키로 전송
if (userMessageInput) {
  userMessageInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  });
}

// 전송 버튼
if (sendBtn) {
  sendBtn.addEventListener("click", () => sendMessage());
}

// ============================================================================
// 모달 관리 함수
// ============================================================================

/**
 * 모달 열기
 * @param {string} modalId - 모달 ID
 */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

/**
 * 모달 닫기
 * @param {string} modalId - 모달 ID
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

/**
 * 상세 모달 닫기 (힌트, 순간 등)
 * @param {string} modalId - 모달 ID
 */
function closeDetailModal(modalId) {
  closeModal(modalId);
}

// 모달 닫기 버튼
document.querySelectorAll(".modal-close").forEach((btn) => {
  btn.addEventListener("click", () => {
    const modalId = btn.dataset.closeModal;
    closeModal(modalId);
  });
});

// 모달 배경 클릭 시 닫기 (모든 모달 타입 통합)
document.querySelectorAll(".modal, .detail-modal").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });
});

// ============================================================================
// 월별 페이지 업데이트
// ============================================================================

/**
 * 왼쪽 월별 페이지 업데이트
 * @param {number} month - 현재 월 (3-9)
 */
function updateMonthPage(month) {
  if (!month || month < 3 || month > 9) {
    console.warn('[월 업데이트] 유효하지 않은 월:', month);
    return;
  }

  const monthInfo = MONTH_INFO[month];
  if (!monthInfo) {
    console.warn('[월 업데이트] 월 정보 없음:', month);
    return;
  }

  // 제목 업데이트
  if (monthTitle) {
    monthTitle.textContent = monthInfo.title;
  }

  // 부제목 업데이트
  const subtitle = document.querySelector('.month-subtitle');
  if (subtitle) {
    subtitle.textContent = monthInfo.subtitle;
  }

  // 배경 클래스 업데이트 (월별 그라데이션 적용)
  if (chatBookLeft) {
    // 기존 월 클래스 제거
    for (let i = 3; i <= 9; i++) {
      chatBookLeft.classList.remove(`month-${i}`);
    }
    // 새 월 클래스 추가
    chatBookLeft.classList.add(`month-${month}`);
  }

  console.log('[월 업데이트] 완료:', monthInfo.title);
}

// ============================================================================
// 스탯 UI 업데이트
// ============================================================================

/**
 * 스탯 UI 전체 업데이트
 * @param {object} gameState - 게임 상태 객체
 */
function updateStatsUI(gameState) {
  if (!gameState || !gameState.stats) {
    console.warn("[UI] 스탯 업데이트 실패: 게임 상태 정보 없음");
    return;
  }

  const stats = gameState.stats;

  // 스탯 바 업데이트
  // 수정: 'power'를 제거하고, 새로운 스탯 'batting'과 'defense'를 추가합니다.
  updateStatBar("intimacy", stats.intimacy);
  updateStatBar("mental", stats.mental);
  updateStatBar("stamina", stats.stamina);
  updateStatBar("batting", stats.batting);
  updateStatBar("speed", stats.speed);
  updateStatBar("defense", stats.defense);

  // 월 정보 업데이트 (current_month 또는 month 둘 다 처리)
  const monthElem = document.getElementById("current-month");
  const month = gameState.current_month !== undefined ? gameState.current_month : gameState.month;

  if (monthElem && month !== undefined) {
    monthElem.textContent = `${month}월`;
  }

  // 월별 페이지 업데이트
  if (month !== undefined) {
    updateMonthPage(month);
  }

  refreshTrainingAvailability();

  // 친밀도 레벨 업데이트
  const intimacyLevelElem = document.getElementById("intimacy-level");
  if (intimacyLevelElem) {
    intimacyLevelElem.textContent = gameState.intimacy_level;
  }
}

function updateStatBar(statName, value) {
  // 이유: 스탯 값을 '현재값/최대값' 형식으로 표시하고, 바의 너비와 색상을 업데이트합니다.
  const statValue = document.getElementById(`${statName}-value`);
  const statBar = document.getElementById(`${statName}-bar`);

  // 해당 ID를 가진 요소가 없으면 함수를 조용히 종료합니다.
  if (!statValue || !statBar) {
    return;
  }

  // 이전 값과 비교하여 변화 감지
  const previousValue = AppState.previousStats[statName];
  const hasChanged = previousValue !== null && previousValue !== value;
  const change = hasChanged ? value - previousValue : 0;

  // 수정: 모든 스탯의 최대값이 100이므로, 텍스트를 '값/100' 형식으로 업데이트합니다.
  statValue.textContent = `${value}/100`;
  statBar.style.width = `${value}%`;

  // 값에 따라 바 색상 변경
  if (value >= 80) {
    statBar.style.backgroundColor = "#4CAF50"; // 매우 높음 (녹색)
  } else if (value >= 50) {
    statBar.style.backgroundColor = "#2196F3"; // 보통 (파란색)
  } else if (value >= 30) {
    statBar.style.backgroundColor = "#FF9800"; // 낮음 (주황색)
  } else {
    statBar.style.backgroundColor = "#F44336"; // 매우 낮음 (빨간색)
  }

  // 변화가 있으면 애니메이션 적용
  if (hasChanged && change !== 0) {
    // 기존 애니메이션 클래스 제거
    statBar.classList.remove('stat-increased', 'stat-decreased');

    // 새 애니메이션 클래스 추가
    const animationClass = change > 0 ? 'stat-increased' : 'stat-decreased';
    statBar.classList.add(animationClass);

    // 변화량 표시 인디케이터 생성
    createStatChangeIndicator(statBar, change);

    // 애니메이션 종료 후 클래스 제거
    setTimeout(() => {
      statBar.classList.remove(animationClass);
    }, 600);
  }

  // 현재 값을 이전 값으로 저장
  AppState.previousStats[statName] = value;
}

function createStatChangeIndicator(statBar, change) {
  // 이유: 스탯 변화량을 시각적으로 표시하는 부유 인디케이터를 생성합니다.
  const indicator = document.createElement('div');
  indicator.className = 'stat-change-indicator';
  indicator.textContent = change > 0 ? `+${change}` : `${change}`;
  indicator.style.color = change > 0 ? '#4CAF50' : '#F44336';

  // 스탯 바의 부모 요소(stat-bar-container)에 추가
  const container = statBar.parentElement;
  if (container) {
    container.style.position = 'relative'; // 위치 기준 설정
    container.appendChild(indicator);

    // 애니메이션 종료 후 제거
    setTimeout(() => {
      if (indicator.parentElement) {
        indicator.remove();
      }
    }, 1200);
  }
}
/* <<< 수정 끝 >>> */

// 이벤트 알림 표시 (스탯 패널 아래)
function showEventNotification(eventInfo) {
  const notifId = `notif-${AppState.counters.notification++}`;
  const container = document.getElementById("notifications-container");
  if (!container) return;

  const notification = document.createElement("div");
  notification.className = "notification-item event";
  notification.id = notifId;
  notification.innerHTML = `
    <div class="notification-header" onclick="toggleNotification('${notifId}')">
      <div class="notification-title">
        🎭 ${eventInfo.event_name}
      </div>
      <button class="notification-close" onclick="removeNotification(event, '${notifId}')">×</button>
    </div>
    <div class="notification-body">
      ${eventInfo.trigger_message}
    </div>
  `;

  container.appendChild(notification);

  // 7초 후 자동 제거
  autoRemoveNotification(notifId, 7000);
}

// 힌트 알림 표시 (스탯 패널 아래)
function showHintNotification(hint) {
  const notifId = `notif-${AppState.counters.notification++}`;
  const container = document.getElementById("notifications-container");
  if (!container) return;

  const notification = document.createElement("div");
  notification.className = "notification-item hint";
  notification.id = notifId;
  notification.innerHTML = `
    <div class="notification-header" onclick="toggleNotification('${notifId}')">
      <div class="notification-title">
        💡 힌트
      </div>
      <button class="notification-close" onclick="removeNotification(event, '${notifId}')">×</button>
    </div>
    <div class="notification-body">
      ${hint}
    </div>
  `;

  container.appendChild(notification);

  // 7초 후 자동 제거
  autoRemoveNotification(notifId, 7000);
}

// 힌트 알림 표시 (컨텍스트 포함)
function showHintWithContext(hintInfo) {
  const notifId = `notif-${AppState.counters.notification++}`;
  const container = document.getElementById("notifications-container");
  if (!container) return;

  const notification = document.createElement("div");
  notification.className = "notification-item hint";
  notification.id = notifId;
  notification.innerHTML = `
    <div class="notification-header" onclick="toggleNotification('${notifId}')">
      <div class="notification-title">
        💡 힌트
      </div>
      <button class="notification-close" onclick="removeNotification(event, '${notifId}')">×</button>
    </div>
    <div class="notification-body">
      ${hintInfo.hint}
      ${hintInfo.related_message ? `<br><small style="opacity: 0.7;">💬 관련 대화: "${hintInfo.related_message}"</small>` : ''}
    </div>
  `;

  container.appendChild(notification);

  // 7초 후 자동 제거
  autoRemoveNotification(notifId, 7000);
}

// 알림 펼치기/접기
function toggleNotification(notifId) {
  const notification = document.getElementById(notifId);
  if (notification) {
    notification.classList.toggle("expanded");
  }
}

// 알림 제거
function removeNotification(event, notifId) {
  event.stopPropagation(); // 헤더 클릭 이벤트 방지
  const notification = document.getElementById(notifId);
  if (notification) {
    notification.classList.add("slide-out");
    setTimeout(() => {
      notification.remove();
    }, 300);
  }
}

// ============================================================================
// 게임 API 함수들
// ============================================================================

// 스탯 상세 버튼 제거됨 (기존 스탯 패널에 통합)

// 가이드 메시지 표시
function showGuideMessage(guide) {
  if (!guide) return;

  const guideHTML = `
    <div class="guide-icon">🎯</div>
    <div class="guide-content">
      <div class="guide-title">${guide.title}</div>
      <div class="guide-message">${guide.message}</div>
      <div class="guide-goals">
        <strong>목표:</strong>
        <ul>
          ${guide.goals.map(goal => `<li>${goal}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;

  appendMessage("guide", guideHTML);
}


// 추천 응답 조회
async function fetchHints() {
  const response = await fetch(`/api/game/hints?username=${username}`);
  const data = await response.json();

  if (data.success) {
    const hintsList = document.getElementById("hints-list");
    hintsList.innerHTML = "";

    data.hints.forEach((hint) => {
      const li = document.createElement("li");
      li.className = "hint-item";
      li.textContent = hint;
      li.dataset.hint = hint;
      li.addEventListener("click", () => useHint(hint));
      hintsList.appendChild(li);
    });

    openModal("hintsModal");
  }
}

// 힌트 사용 (입력창에 자동 입력)
function useHint(hint) {
  if (userMessageInput) {
    userMessageInput.value = hint;
    userMessageInput.focus();
  }
  closeModal("hintsModal");
}

// 특별한 순간 조회
async function fetchMoments() {
  const response = await fetch(`/api/game/moments?username=${username}`);
  const data = await response.json();

  if (data.success) {
    const momentsList = document.getElementById("moments-list");

    if (data.moments.length > 0) {
      momentsList.innerHTML = data.moments
        .map(
          (moment) => `
        <div class="moment-card">
          <h4>${moment.title || "특별한 순간"}</h4>
          <p>${moment.description || ""}</p>
          <p style="font-size: 0.9rem; margin-top: 10px">
            📅 ${moment.date || "날짜 미상"}
          </p>
        </div>
      `
        )
        .join("");
    } else {
      momentsList.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>아직 특별한 순간이 없습니다</p>
          <p style="font-size: 0.9rem">강태와 대화하며 추억을 만들어보세요!</p>
        </div>
      `;
    }

    openModal("momentsModal");
  }
}

// ============================================================================
// 버튼 이벤트 리스너
// ============================================================================

// 다음 달 버튼
const btnAdvance = document.getElementById("btn-advance");
if (btnAdvance) {
  btnAdvance.addEventListener("click", advanceToNextMonth);
}

// 추천 응답 버튼
const btnHints = document.getElementById("btn-hints");
if (btnHints) {
  btnHints.addEventListener("click", fetchHints);
}

// 특별한 순간 버튼
const btnMoments = document.getElementById("btn-moments");
if (btnMoments) {
  btnMoments.addEventListener("click", fetchMoments);
}

// ============================================================================
// 온보딩 스토리북 기능
// ============================================================================

// 온보딩 표시 체크 및 모달 열기
// 반환값: 온보딩을 표시했으면 true, 아니면 false
function checkAndShowOnboarding() {
  const hasSeenOnboarding = localStorage.getItem('onboarding_completed');

  if (!hasSeenOnboarding) {
    const modal = document.getElementById('onboardingModal');
    if (modal) {
      modal.classList.add('active');
      updateOnboardingNavigation();
    }
    return true; // 온보딩 표시됨
  }
  return false; // 온보딩 표시 안 됨
}

// 온보딩 닫기
async function closeOnboarding() {
  const dontShowAgain = document.getElementById('dontShowAgain');

  if (dontShowAgain && dontShowAgain.checked) {
    localStorage.setItem('onboarding_completed', 'true');
  }

  const modal = document.getElementById('onboardingModal');
  if (modal) {
    modal.classList.remove('active');
  }

  console.log('[온보딩] 종료, 앱 초기화 시작');

  // 3월 가이드 표시
  show3MonthGuide();

  // 앱 초기화 (async/await로 명확한 순서 보장)
  await initializeApp();
}

// 다음 페이지
function nextPage() {
  if (AppState.onboarding.currentPage < AppState.onboarding.totalPages) {
    goToPage(AppState.onboarding.currentPage + 1);
  }
}

// 이전 페이지
function previousPage() {
  if (AppState.onboarding.currentPage > 1) {
    goToPage(AppState.onboarding.currentPage - 1);
  }
}

// 특정 페이지로 이동
function goToPage(pageNumber) {
  if (pageNumber < 1 || pageNumber > AppState.onboarding.totalPages) return;

  // 현재 페이지 비활성화
  const currentPageElem = document.querySelector(`.storybook-page[data-page="${AppState.onboarding.currentPage}"]`);
  if (currentPageElem) {
    currentPageElem.classList.remove('active');
  }

  // 새 페이지 활성화
  const newPageElem = document.querySelector(`.storybook-page[data-page="${pageNumber}"]`);
  if (newPageElem) {
    newPageElem.classList.add('active');
  }

  // 현재 페이지 번호 업데이트
  AppState.onboarding.currentPage = pageNumber;

  // 네비게이션 업데이트
  updateOnboardingNavigation();
}

// 네비게이션 업데이트 (버튼 활성화/비활성화, 닷 표시)
function updateOnboardingNavigation() {
  // 이전/다음 버튼
  const prevBtn = document.querySelector('.storybook-prev');
  const nextBtn = document.querySelector('.storybook-next');

  if (prevBtn) {
    prevBtn.disabled = (AppState.onboarding.currentPage === 1);
  }

  if (nextBtn) {
    nextBtn.disabled = (AppState.onboarding.currentPage === AppState.onboarding.totalPages);
  }

  // 닷 네비게이션
  document.querySelectorAll('.storybook-dots .dot').forEach((dot, index) => {
    if (index + 1 === AppState.onboarding.currentPage) {
      dot.classList.add('active');
    } else {
      dot.classList.remove('active');
    }
  });
}

// ============================================================================
// 3월 가이드 메시지
// ============================================================================

// 3월 초기 가이드 표시
function show3MonthGuide() {
  // 이미 가이드를 본 적이 있는지 확인
  const hasSeenMarchGuide = localStorage.getItem('march_guide_shown');

  if (hasSeenMarchGuide) {
    return; // 이미 봤으면 표시하지 않음
  }

  // 3월 가이드 메시지 구성
  const guideMsgElement = document.createElement('div');
  guideMsgElement.className = 'guide-message march-guide';
  guideMsgElement.innerHTML = `
    <div class="guide-header">
      <h2>3월 - 시즌 준비</h2>
    </div>
    <div class="guide-content">
      <p>드래프트까지 7개월! 강태와 친밀도를 쌓고 기초 체력을 다지세요.</p>
      <div class="guide-goals">
        <h3>목표:</h3>
        <ul>
          <li>친밀도 20 이상</li>
          <li>체력 60 이상</li>
        </ul>
      </div>
    </div>
    <div class="guide-footer">
      <button onclick="closeMarchGuide()" class="guide-close-btn">시작하기</button>
    </div>
  `;

  // 채팅 로그에 추가
  if (chatLog) {
    chatLog.appendChild(guideMsgElement);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  // localStorage에 표시 기록
  localStorage.setItem('march_guide_shown', 'true');
}

// 3월 가이드 닫기
function closeMarchGuide() {
  const guideMsg = document.querySelector('.march-guide');
  if (guideMsg) {
    guideMsg.remove();
  }
}

// ============================================================================
// 스토리북 기능 (책 통합 버전)
// ============================================================================

/**
 * 스토리북 로드 및 표시 (책 안에서)
 * @param {string} storybookId - 스토리북 ID
 */
async function loadAndShowStorybook(storybookId) {
  try {
    console.log('[스토리북] 로딩 시작:', storybookId);
    const response = await fetch(`/api/storybook/${storybookId}?username=${username}`);
    const data = await response.json();

    console.log('[스토리북] API 응답:', data);

    if (data.success) {
      AppState.storybook.current = data.storybook;
      AppState.storybook.currentPage = 0;
      AppState.storybook.isActive = true;
      refreshTrainingAvailability();

      console.log('[스토리북] 데이터 저장 완료:', {
        title: AppState.storybook.current.title,
        pages: AppState.storybook.current.pages.length
      });

      // 책 안에서 스토리북 표시
      showStorybookInBook();
      renderStorybookPageInBook(0);

      console.log('[스토리북] 로드 완료:', AppState.storybook.current.title);
    } else {
      showError('스토리북을 불러올 수 없습니다.');
      console.error('[스토리북] 로드 실패:', data.error);
    }
  } catch (error) {
    showError('네트워크 오류가 발생했습니다. 다시 시도해주세요.', error);
    console.error('[스토리북] 로드 예외:', error);
  }
}

/**
 * 책 안에서 스토리북 모드 표시
 */
function showStorybookInBook() {
  // 채팅 UI 숨기기
  const monthImage = document.getElementById('month-image-container');
  const chatContent = document.getElementById('chat-content');

  if (monthImage) monthImage.classList.add('hidden');
  if (chatContent) chatContent.classList.add('hidden');

  // 스토리북 UI 표시
  const storybookLeft = document.getElementById('storybook-content-left');
  const storybookRight = document.getElementById('storybook-content-right');
  const storybookNav = document.getElementById('storybook-nav');

  if (storybookLeft) storybookLeft.classList.remove('hidden');
  if (storybookRight) storybookRight.classList.remove('hidden');
  if (storybookNav) storybookNav.classList.remove('hidden');

  console.log('[스토리북] 모드 활성화');
}

/**
 * 책 안에서 채팅 모드로 복귀
 */
function hideStorybookInBook() {
  // 스토리북 UI 숨기기
  const storybookLeft = document.getElementById('storybook-content-left');
  const storybookRight = document.getElementById('storybook-content-right');
  const storybookNav = document.getElementById('storybook-nav');

  if (storybookLeft) storybookLeft.classList.add('hidden');
  if (storybookRight) storybookRight.classList.add('hidden');
  if (storybookNav) storybookNav.classList.add('hidden');

  // 채팅 UI 표시
  const monthImage = document.getElementById('month-image-container');
  const chatContent = document.getElementById('chat-content');

  if (monthImage) monthImage.classList.remove('hidden');
  if (chatContent) chatContent.classList.remove('hidden');

  AppState.storybook.isActive = false;
  refreshTrainingAvailability();
  console.log('[스토리북] 모드 비활성화');
}


/**
 * 책 안에서 스토리북 페이지 렌더링 (스트리밍 방식)
 * @param {number} pageIndex - 페이지 인덱스 (0부터 시작)
 */
async function renderStorybookPageInBook(pageIndex) {
  if (!AppState.storybook.current || !AppState.storybook.current.pages) {
    console.error('[스토리북] 스토리북 데이터 없음');
    return;
  }

  const page = AppState.storybook.current.pages[pageIndex];
  if (!page) {
    console.error('[스토리북] 페이지 데이터 없음:', pageIndex);
    return;
  }

  console.log('[스토리북] 페이지 렌더링:', {
    pageIndex,
    text: page.text,
    image: page.image
  });

  // 왼쪽 페이지: 제목
  const storyTitle = document.getElementById('story-title');
  if (storyTitle) {
    storyTitle.textContent = AppState.storybook.current.title;
  }

  // 오른쪽 페이지: 이미지 먼저 로드
  const imageContainer = document.getElementById('story-image-container');
  if (imageContainer) {
    if (page.image) {
      imageContainer.innerHTML = `<img src="${page.image}" alt="스토리 이미지" onerror="this.parentElement.innerHTML='<p class=\\'no-image-text\\'>이미지 로드 실패</p>'">`;
    } else {
      imageContainer.innerHTML = '<p class="no-image-text">이미지 없음</p>';
    }
  }

  // 왼쪽 페이지: 텍스트 (즉시 표시)
  const storyText = document.getElementById('story-text');
  if (storyText) {
    const text = page.text || '내용 없음';
    storyText.textContent = text;
  }

  console.log('[스토리북] 렌더링 완료');

  // 네비게이션 업데이트
  updateStorybookNavigationInBook();
}

/**
 * 책 안 스토리북 네비게이션 업데이트
 */
function updateStorybookNavigationInBook() {
  const prevBtn = document.getElementById('story-prev-btn');
  const nextBtn = document.getElementById('story-next-btn');
  const startBtn = document.getElementById('story-start-btn');
  const progress = document.getElementById('story-progress');

  if (!AppState.storybook.current) return;

  const totalPages = AppState.storybook.current.pages.length;
  const currentPage = AppState.storybook.currentPage;
  const isFirstPage = currentPage === 0;
  const isLastPage = currentPage === totalPages - 1;

  // 이전/다음 버튼 상태
  if (prevBtn) prevBtn.disabled = isFirstPage;
  if (nextBtn) nextBtn.disabled = isLastPage;

  // 진행도 표시
  if (progress) {
    progress.textContent = `${currentPage + 1} / ${totalPages}`;
  }

  // 시작 버튼 (마지막 페이지에서만 표시)
  if (startBtn) {
    if (isLastPage) {
      startBtn.classList.remove('hidden');

      const completionAction = AppState.storybook.current.completion_action;
      if (completionAction === 'game_end') {
        startBtn.textContent = '게임 종료';
      } else {
        startBtn.textContent = '대화 시작하기';
      }
    } else {
      startBtn.classList.add('hidden');
    }
  }
}

/**
 * 책 안 스토리북: 이전 페이지
 */
function storybookPrevInBook() {
  if (AppState.storybook.currentPage > 0) {
    AppState.storybook.currentPage--;
    renderStorybookPageInBook(AppState.storybook.currentPage);
    console.log('[스토리북] 이전 페이지:', AppState.storybook.currentPage);
  }
}

/**
 * 책 안 스토리북: 다음 페이지
 */
function storybookNextInBook() {
  if (AppState.storybook.current && AppState.storybook.currentPage < AppState.storybook.current.pages.length - 1) {
    AppState.storybook.currentPage++;
    renderStorybookPageInBook(AppState.storybook.currentPage);
    console.log('[스토리북] 다음 페이지:', AppState.storybook.currentPage);
  }
}

/**
 * 책 안 스토리북: 대화 시작하기
 */
async function storybookStartFromBook() {
  // 이미 처리 중이면 무시
  if (AppState.storybook.isProcessing) {
    console.log('[스토리북] 이미 처리 중...');
    return;
  }

  AppState.storybook.isProcessing = true;
  console.log('[스토리북] 대화 시작하기 버튼 클릭');

  try {
    await completeStorybook();
  } finally {
    AppState.storybook.isProcessing = false;
  }
}

/**
 * 스토리북 완료
 */
async function completeStorybook() {
  try {
    const storybookId = AppState.storybook.current.id; // 스토리북 ID 저장
    const completionAction = AppState.storybook.current.completion_action;

    // ⭐ 엔딩인 경우 API 호출 없이 바로 게임 종료 처리
    if (completionAction === 'game_end') {
      console.log('[엔딩] 게임 종료 처리');
      hideStorybookModal();
      alert('게임이 종료되었습니다. 플레이해주셔서 감사합니다!');
      // 선택사항: 게임 상태 초기화 또는 메인 화면으로 이동
      return;
    }

    const response = await fetch('/api/storybook/complete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        username: username,
        storybook_id: storybookId
      })
    });

    const data = await response.json();

    if (data.success) {
      console.log('[스토리북] 완료:', data);

      // 다음 액션에 따라 분기
      if (data.next_action === 'start_chat_mode') {
        // ⭐ UX 개선: 즉시 채팅 화면 전환 → 백그라운드에서 메시지 처리
        console.log('[스토리북] 채팅 모드로 즉시 전환');

        // 1. 먼저 채팅 화면으로 전환 (즉각 반응, 사용자 답답함 해소)
        await transitionToChatMode(null);

        // 2. 백그라운드에서 시스템 메시지 처리 및 스트리밍 (await 없이 비동기 실행)
        //    사용자는 로딩 표시 → 실시간 타이핑을 보게 됨
        startNewMonth(storybookId);

      } else if (data.next_action === 'show_next_storybook') {
        // 다음 스토리북 표시
        await transitionToStorybookMode(data.next_storybook_id);

      } else if (data.next_action === 'game_end') {
        // 게임 종료 (엔딩 표시)
        if (data.ending && data.ending.pages && data.ending.pages.length > 0) {
          // 엔딩 스토리북으로 전환
          const endingStorybook = {
            id: data.ending.id || 'ending',
            title: data.ending.title || '엔딩',
            pages: data.ending.pages,
            completion_action: 'game_end'
          };

          await transitionToEnding(endingStorybook);
        } else {
          // 엔딩 데이터가 없으면 간단한 메시지
          hideStorybookModal();
          alert('게임이 종료되었습니다. 플레이해주셔서 감사합니다!');
        }
      }
    } else {
      showError('오류가 발생했습니다.');
      console.error('[스토리북] 완료 실패:', data.error);
    }
  } catch (error) {
    showError('네트워크 오류가 발생했습니다. 다시 시도해주세요.', error);
  }
}

/**
 * 채팅 모드로 부드럽게 전환 (책 안에서)
 * @param {string|null} storybookId - 완료된 스토리북 ID (시스템 메시지용)
 *                                     null인 경우 시스템 메시지 전송 생략 (이미 처리된 경우)
 */
async function transitionToChatMode(storybookId = null) {
  console.log('[전환] 채팅 모드로 전환 시작, 스토리북 ID:', storybookId);

  // 스토리북 UI 숨기기
  hideStorybookInBook();

  // 입력 필드 활성화 (채팅 모드 진입)
  enableChatInput();

  // 월 시작 처리 (채팅 화면 초기화 + 시스템 메시지)
  // storybookId가 null이면 이미 처리되었으므로 생략
  if (storybookId) {
    await startNewMonth(storybookId);
  }

  // 게임 상태 새로고침
  await fetchGameState();

  console.log('[전환] 채팅 모드로 전환 완료');
}

/**
 * 스토리북 모드로 부드럽게 전환 (책 안에서)
 * @param {string} storybookId - 스토리북 ID
 */
async function transitionToStorybookMode(storybookId) {
  console.log('[전환] 스토리북 모드로 전환 시작');

  // 스토리북 로드 및 표시
  await loadAndShowStorybook(storybookId);

  console.log('[전환] 스토리북 모드로 전환 완료');
}

/**
 * 엔딩 스토리북으로 전환 (책 안에서)
 * @param {object} endingStorybook - 엔딩 스토리북 데이터
 */
async function transitionToEnding(endingStorybook) {
  console.log('[전환] 엔딩으로 전환 시작');

  // 엔딩 스토리북 설정
  AppState.storybook.current = endingStorybook;
  AppState.storybook.currentPage = 0;
  AppState.storybook.isActive = true;
      refreshTrainingAvailability();

  // 스토리북 모드로 전환 및 렌더링
  showStorybookInBook();
  renderStorybookPageInBook(0);

  console.log('[전환] 엔딩으로 전환 완료:', endingStorybook.title);
}

/**
 * 비동기 대기 함수
 * @param {number} ms - 대기 시간 (밀리초)
 * @returns {Promise} - 지정된 시간 후 resolve되는 Promise
 */
function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 다음 달로 진행
 */
async function advanceToNextMonth() {
  try {
    const response = await fetch('/api/game/advance', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: username})
    });

    const data = await response.json();

    if (data.success) {
      console.log('[월 진행] 성공:', data);

      // 전환 스토리북 표시
      await transitionToStorybookMode(data.transition_storybook_id);
    } else {
      showError(data.error || '월 진행에 실패했습니다.');
      console.error('[월 진행] 실패:', data.error);
    }
  } catch (error) {
    showError('월 진행에 실패했습니다. 다시 시도해주세요.', error);
  }
}

/**
 * 게임 상태 가져오기
 */
async function fetchGameState() {
  const response = await fetch(`/api/game/stats?username=${username}`);
  const data = await response.json();

  if (data.success) {
    AppState.game = data;
    updateStatsUI(data);
    console.log('[게임 상태] 업데이트 완료');
  }
}

/**
 * 페이지 로드 시 현재 스토리북 확인
 */
async function checkInitialStorybook() {
  const response = await fetch(`/api/storybook/current?username=${username}`);
  const data = await response.json();

  if (data.success) {
    if (data.phase === 'storybook' && data.storybook) {
      // 스토리북 모드: 스토리북 표시
      console.log('[초기화] 스토리북 모드');
      await loadAndShowStorybook(data.storybook.id);
    } else {
      // 채팅 모드
      console.log('[초기화] 채팅 모드');
    }
  }
}

// ============================================================================
// 페이지 로드
// ============================================================================

/**
 * 앱 초기화 함수 (async/await 기반)
 * - setTimeout 제거, 명확한 순서 보장
 * - 로딩 오버레이 관리
 * - 입력 필드 상태 관리
 */
async function initializeApp() {
  const overlay = document.getElementById('init-overlay');

  try {
    // 초기화 시작
    AppState.initialization.status = 'loading';
    console.log('[초기화] 시작');

    // 입력 필드 비활성화
    disableChatInput('게임을 불러오는 중...');

    // 병렬로 스토리북 확인 및 게임 상태 로드
    await Promise.all([
      checkInitialStorybook(),
      fetchGameState()
    ]);

    // 초기화 완료
    AppState.initialization.status = 'ready';
    console.log('[초기화] 완료');

    // 오버레이 숨기기 (부드러운 전환)
    if (overlay) {
      overlay.classList.remove('active');
    }

    // 채팅 모드인 경우에만 입력 활성화 및 초기 메시지 전송
    if (!AppState.storybook.isActive) {
      enableChatInput();

      // 채팅 로그가 비어있으면 초기 메시지 전송
      if (chatLog && chatLog.childElementCount === 0) {
        console.log('[초기화] 초기 메시지 전송');
        sendMessage(true);
      }
    }
    // 스토리북 모드인 경우 입력은 비활성화 상태 유지

  } catch (error) {
    // 초기화 실패 처리
    AppState.initialization.status = 'error';
    console.error('[초기화] 실패:', error);

    if (overlay) {
      const overlayText = overlay.querySelector('p');
      if (overlayText) {
        overlayText.textContent = '오류가 발생했습니다. 새로고침해주세요.';
      }
    }

    showError('초기화에 실패했습니다. 페이지를 새로고침해주세요.', error);
  }
}

// 페이지 로드 시 초기화
window.addEventListener("load", async () => {
  console.log("페이지 로드 완료");

  // Training UI 초기화
  initializeTrainingUI();

  // 초기 월 설정 (기본값: 3월)
  updateMonthPage(3);

  // 1. 온보딩 체크 및 표시 (최우선)
  const onboardingShown = checkAndShowOnboarding();

  if (!onboardingShown) {
    // 2. 온보딩을 표시하지 않은 경우 앱 초기화
    await initializeApp();
  } else {
    // 3. 온보딩이 표시된 경우 오버레이 숨김 (온보딩 종료 시 initializeApp 호출)
    const overlay = document.getElementById('init-overlay');
    if (overlay) {
      overlay.classList.remove('active');
    }
  }
});

/**
 * 선택지가 있는 이벤트 메시지와 버튼을 채팅창에 표시하는 함수
 * @param {object} eventInfo - 서버에서 받은 이벤트 정보 (choices 포함)
 */
function showEventWithOptions(eventInfo) {
  const messageId = `msg-${AppState.counters.message++}`;
  const messageElem = document.createElement("div");
  messageElem.classList.add("message", "bot", "event-choices"); // 봇 메시지 스타일 + 커스텀 클래스
  messageElem.id = messageId;

  // 이벤트 설명 텍스트
  const textElem = document.createElement('p');
  textElem.textContent = eventInfo.trigger_message;
  messageElem.appendChild(textElem);

  // 선택지 버튼들을 담을 컨테이너
  const optionsContainer = document.createElement('div');
  optionsContainer.className = 'event-options-container';

  // 각 선택지에 대한 버튼 생성
  eventInfo.choices.forEach(choice => {
    const button = document.createElement('button');
    button.className = 'event-option-btn';
    button.textContent = choice.text;
    button.onclick = (event) => {
      // 버튼 클릭 시, 선택 비활성화 및 스토리북 로드
      handleEventChoice(event, eventInfo.event_key, choice.id, optionsContainer);
    };
    optionsContainer.appendChild(button);
  });

  messageElem.appendChild(optionsContainer);
  
  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  }
}

// 5월 이벤트 선택지 시스템 제거됨 - flags로 단순화됨

// ============================================================================
// 특별한 순간 모달
// ============================================================================

/**
 * 특별한 순간 모달 열기
 */
async function openMomentsModal() {
  const modal = document.getElementById('moments-modal');
  if (!modal) return;

  modal.classList.add('open');

  // 카드 로드 및 렌더링
  await loadAndRenderMoments();
}

/**
 * 특별한 순간 모달 닫기
 */
function closeMomentsModal() {
  const modal = document.getElementById('moments-modal');
  if (modal) {
    modal.classList.remove('open');
  }
}

/**
 * 특별한 순간 카드 로드 및 렌더링
 */
async function loadAndRenderMoments() {
  try {
    const response = await fetch(`/api/moments?username=${username}`);
    const data = await response.json();

    if (data.success) {
      renderMomentCards(data.moments);
    } else {
      console.error('[MOMENTS] 로드 실패:', data.error);
    }
  } catch (error) {
    console.error('[MOMENTS] 로드 오류:', error);
  }
}

/**
 * 특별한 순간 카드 렌더링
 * @param {Array} moments - 카드 데이터 배열
 */
function renderMomentCards(moments) {
  const list = document.getElementById('moments-list');
  if (!list) return;

  if (!moments || moments.length === 0) {
    list.innerHTML = `
      <div style="text-align: center; padding: 40px;">
        <p style="color: #999; margin: 0;">아직 특별한 순간이 기록되지 않았습니다.</p>
        <p style="color: #999; font-size: 0.9rem; margin-top: 8px;">강태와 함께 소중한 기억을 만들어보세요!</p>
      </div>
    `;
    return;
  }

  // 최신순 정렬 (timestamp 기준)
  const sortedMoments = moments.sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  list.innerHTML = sortedMoments.map(moment => {
    if (moment.type === 'event') {
      // 이벤트 카드 (이미지 포함)
      return `
        <div class="moment-card">
          <img src="${moment.image_url}" alt="${moment.title}" class="moment-card-image" onerror="this.style.display='none'">
          <div class="moment-card-content" style="color: #1A1A1A;">
            <div class="moment-card-header">
              <h3 class="moment-card-title" style="color: #1A1A1A;">${moment.title}</h3>
              <span class="moment-card-month" style="color: #666;">${moment.month}월</span>
            </div>
            <p class="moment-card-description" style="color: #555;">${moment.description}</p>
          </div>
        </div>
      `;
    } else {
      // 마일스톤 카드 (그라데이션 배경)
      const visual = moment.visual_data || {};
      const gradient = visual.gradient || ['#4A90E2', '#50C878'];
      const emoji = visual.emoji || '⭐';

      return `
        <div class="moment-card milestone" style="--gradient-start: ${gradient[0]}; --gradient-end: ${gradient[1]};">
          <div class="moment-card-content" style="color: #1A1A1A;">
            <div class="moment-card-emoji">${emoji}</div>
            <div class="moment-card-header">
              <h3 class="moment-card-title" style="color: #1A1A1A;">${moment.title}</h3>
              <span class="moment-card-month" style="color: #1A1A1A;">${moment.month}월</span>
            </div>
            <p class="moment-card-description" style="color: #1A1A1A;">${moment.description}</p>
          </div>
        </div>
      `;
    }
  }).join('');
}

