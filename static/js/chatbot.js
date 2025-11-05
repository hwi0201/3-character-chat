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
  game: null
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
    subtitle: "기초를 다지는 시간",
    description: "탄탄한 기본기로 미래를 준비합니다"
  },
  5: {
    title: "5월 - 보이지 않는 상처",
    subtitle: "강태의 과거와 마주하다",
    description: "강태를 이해하고 보듬으며 성장시킵니다"
  },
  6: {
    title: "6월 - 중반전",
    subtitle: "반환점을 돌았습니다",
    description: "약점을 보완하고 강점을 극대화합니다"
  },
  7: {
    title: "7월 - 여름 강화",
    subtitle: "무더위를 뚫고 전진",
    description: "체력과 멘탈을 끌어올립니다"
  },
  8: {
    title: "8월 - 막바지 준비",
    subtitle: "마지막 스퍼트",
    description: "드래프트가 한 달 앞으로 다가왔습니다"
  },
  9: {
    title: "9월 - 드래프트",
    subtitle: "운명의 순간",
    description: "6개월의 노력이 결실을 맺을 시간"
  }
};

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
            // 메타데이터 저장 (스탯 업데이트용)
            metadata = event.content;

          } else if (event.type === 'done') {
            // 스트리밍 완료
            console.log('[STREAM] 완료');

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

    if (metadata) {
      const data = metadata;

      // 1. 이벤트에 선택지(choices)가 있는지 확인
      if (data.event && data.event.choices) {
        // 선택지가 있으면 버튼을 표시하는 함수를 호출
        showEventWithOptions(data.event);
      } else {
        // 2. 선택지가 없는 일반적인 경우, 기존 로직 실행
        if (data.debug) {
            console.group("🎮 게임 상태 업데이트");
            console.log("📅 현재 시점:", `${data.debug.game_state.current_month}월 ${data.debug.game_state.current_day}일`);
            console.log("🎯 드래프트까지:", `${data.debug.game_state.months_until_draft}개월`);
            console.log("💖 친밀도 레벨:", data.debug.game_state.intimacy_level);

            console.group("📊 스탯 변화");
            if (Object.keys(data.debug.stat_changes.changes).length > 0) {
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

            if (data.debug.event_check.triggered) {
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
        // 단순 이벤트 알림 표시
        if (data.event) {
          showEventNotification(data.event);
        }
      }

      // 3. 힌트 표시는 이벤트 종류와 상관없이 항상 처리
      if (data.hint) {
        showHintNotification(data.hint);
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

  // 온보딩 종료 후 게임 초기화
  setTimeout(async () => {
    // 1. 게임 상태 가져오기 (월 정보 포함)
    await fetchGameState();

    // 2. 3월 가이드 메시지 표시
    show3MonthGuide();

    // 3. 스토리북 확인
    await checkInitialStorybook();

    // 4. 초기 메시지 요청
    setTimeout(() => {
      if (chatLog && chatLog.childElementCount === 0) {
        console.log("초기 메시지 요청");
        sendMessage(true);
      }
    }, 500);
  }, 500); // 모달이 완전히 닫힌 후 처리
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
    const response = await fetch('/api/storybook/complete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        username: username,
        storybook_id: AppState.storybook.current.id
      })
    });

    const data = await response.json();

    if (data.success) {
      console.log('[스토리북] 완료:', data);

      // 다음 액션에 따라 분기
      if (data.next_action === 'start_chat_mode') {
        // 채팅 모드로 전환
        await transitionToChatMode();

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
 */
async function transitionToChatMode() {
  console.log('[전환] 채팅 모드로 전환 시작');

  // 스토리북 UI 숨기기
  hideStorybookInBook();

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

// 페이지 로드 시 초기화
window.addEventListener("load", async () => {
  console.log("페이지 로드 완료");

  // 초기 월 설정 (기본값: 3월)
  updateMonthPage(3);

  // 1. 온보딩 체크 및 표시 (최우선)
  const onboardingShown = checkAndShowOnboarding();

  // 2. 온보딩을 표시하지 않은 경우에만 스토리북/채팅 초기화
  if (!onboardingShown) {
    // 초기 스토리북 확인
    await checkInitialStorybook();

    // 게임 상태 가져오기 (월 정보 업데이트)
    await fetchGameState();

    // 초기 메시지 요청
    setTimeout(() => {
      if (chatLog && chatLog.childElementCount === 0) {
        console.log("초기 메시지 요청");
        sendMessage(true);
      }
    }, 500);
  }
  // 온보딩이 표시된 경우, closeOnboarding()에서 3월 가이드와 스토리북 체크를 처리
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

/**
 * 사용자가 선택한 이벤트 버튼을 처리하는 함수
 * @param {Event} event - 클릭 이벤트 객체
 * @param {string} eventKey - 이벤트의 고유 키 (예: "5월_갈등")
 * @param {string} choiceId - 선택지의 고유 ID (예: "visit_home")
 * @param {HTMLElement} optionsContainer - 비활성화할 버튼들의 부모 컨테이너
 */
async function handleEventChoice(event, eventKey, choiceId, optionsContainer) {
  // 모든 버튼 비활성화 (중복 클릭 방지)
  optionsContainer.querySelectorAll('button').forEach(btn => {
    btn.disabled = true;
    if (btn !== event.target) {
      btn.style.opacity = '0.5';
    }
  });

  // 5월 갈등 이벤트 분기 처리
  if (eventKey === '5월_갈등') {
    if (choiceId === 'visit_home') {
      // "집으로 찾아간다" 선택 -> 5_conflict_visit 스토리북 로드
      appendMessageSync("guide", "당신은 강태의 집으로 향하기로 결심했다...");
      await loadAndShowStorybook("5_conflict_visit");
      
    } else if (choiceId === 'wait') {
      // "기다린다" 선택 -> 5_conflict_wait 스토리북 로드
      appendMessageSync("guide", "당신은 강태가 스스로 돌아오길 기다리기로 했다...");
      await loadAndShowStorybook("5_conflict_wait");
    }
  }
}

