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
// DOM 요소
// ============================================================================

const chatArea = document.querySelector(".chat-area");
const username = chatArea ? chatArea.dataset.username : "사용자";
const chatLog = document.getElementById("chat-log");
const userMessageInput = document.getElementById("user-message");
const sendBtn = document.getElementById("send-btn");

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
  appendMessage("bot", `❌ ${userMessage}`);
}

// 메시지 전송 함수
async function sendMessage(isInitial = false) {
  let message;

  if (isInitial) {
    message = "init";
  } else {
    message = userMessageInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    userMessageInput.value = "";
  }

  // 로딩 표시
  const loadingId = appendMessage("bot", "생각 중...");

  try {
    const response = await fetch("/api/chat", {
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

    const data = await response.json();

    // 로딩 메시지 제거
    removeMessage(loadingId);

    // 응답 파싱 (간소화)
    const replyText = (typeof data.reply === "object" && data.reply !== null)
      ? (data.reply.reply || data.reply)
      : data.reply;
    const imagePath = (typeof data.reply === "object" && data.reply !== null)
      ? (data.reply.image || null)
      : null;

    // 디버그 정보 콘솔 출력
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

    appendMessage("bot", replyText, imagePath);

    // 이벤트 알림 표시
    if (data.event) {
      showEventNotification(data.event);
    }

    // 힌트 표시
    if (data.hint) {
      showHintNotification(data.hint);
    }
  } catch (error) {
    removeMessage(loadingId);
    showError("메시지 전송에 실패했습니다. 다시 시도해주세요.", error);
  }
}

// 메시지 DOM에 추가
function appendMessage(sender, text, imageSrc = null) {
  const messageId = `msg-${AppState.counters.message++}`;
  const messageElem = document.createElement("div");
  messageElem.classList.add("message", sender);
  messageElem.id = messageId;

  if (sender === "user") {
    messageElem.textContent = text;
  } else if (sender === "guide") {
    // 가이드 메시지 타입
    messageElem.classList.add("guide");
    messageElem.innerHTML = text; // HTML 형식으로 표시
  } else {
    // 이미지가 있으면 먼저 표시
    if (imageSrc) {
      const botImg = document.createElement("img");
      botImg.classList.add("bot-big-img");
      botImg.src = imageSrc;
      botImg.alt = "챗봇 이미지";
      messageElem.appendChild(botImg);
    }

    // 텍스트 추가
    const textContainer = document.createElement("div");
    textContainer.classList.add("bot-text-container");
    textContainer.textContent = text;
    messageElem.appendChild(textContainer);
  }

  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  return messageId;
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

// 통합 모달 관리 함수
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
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

// 스탯 UI 업데이트
function updateStatsUI(gameState) {
  if (!gameState || !gameState.stats) return;

  const stats = gameState.stats;

  // 스탯 바 업데이트
  updateStatBar("intimacy", stats.intimacy);
  updateStatBar("mental", stats.mental);
  updateStatBar("stamina", stats.stamina);
  updateStatBar("power", stats.power);
  updateStatBar("speed", stats.speed);

  // 월 정보 업데이트 (current_month 또는 month 둘 다 처리)
  const monthElem = document.getElementById("current-month");
  if (monthElem) {
    const month = gameState.current_month !== undefined ? gameState.current_month : gameState.month;
    if (month !== undefined) {
      monthElem.textContent = `${month}월`;
    }
  }

  // 친밀도 레벨 업데이트
  const intimacyLevelElem = document.getElementById("intimacy-level");
  if (intimacyLevelElem) {
    intimacyLevelElem.textContent = gameState.intimacy_level;
  }
}

function updateStatBar(statName, value) {
  const statValue = document.getElementById(`${statName}-value`);
  const statBar = document.getElementById(`${statName}-bar`);

  if (statValue) {
    statValue.textContent = value;
  }

  if (statBar) {
    statBar.style.width = `${value}%`;

    // 색상 변경 (값에 따라)
    if (value >= 80) {
      statBar.style.backgroundColor = "#4CAF50"; // 녹색
    } else if (value >= 50) {
      statBar.style.backgroundColor = "#2196F3"; // 파란색
    } else if (value >= 30) {
      statBar.style.backgroundColor = "#FF9800"; // 주황색
    } else {
      statBar.style.backgroundColor = "#F44336"; // 빨간색
    }
  }
}

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
          <p style="font-size: 0.9rem">민석이와 대화하며 추억을 만들어보세요!</p>
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
    // 1. 3월 가이드 메시지 표시
    show3MonthGuide();

    // 2. 스토리북 확인
    await checkInitialStorybook();

    // 3. 초기 메시지 요청
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
      <p>드래프트까지 7개월! 민석이와 친밀도를 쌓고 기초 체력을 다지세요.</p>
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
// 스토리북 기능 (간소화 버전)
// ============================================================================

/**
 * 스토리북 로드 및 표시
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

      showStorybookModal();
      renderStorybookPage(0);

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
 * 스토리북 모달 표시
 */
function showStorybookModal() {
  const modal = document.getElementById('storybook-modal');
  if (modal) {
    modal.classList.remove('hidden');
    document.getElementById('storybook-title').textContent = AppState.storybook.current?.title || '';
  }
}

/**
 * 스토리북 모달 숨기기
 */
function hideStorybookModal() {
  const modal = document.getElementById('storybook-modal');
  if (modal) {
    modal.classList.add('hidden');
    AppState.storybook.isActive = false;
  }
}

/**
 * 스토리북 페이지 렌더링 (간소화 버전)
 * @param {number} pageIndex - 페이지 인덱스 (0부터 시작)
 */
function renderStorybookPage(pageIndex) {
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

  // 이미지 렌더링
  const imageContainer = document.getElementById('storybook-image-container');
  if (imageContainer) {
    if (page.image) {
      imageContainer.innerHTML = `<img src="${page.image}" alt="스토리 이미지" onerror="this.parentElement.innerHTML='<p class=\\'no-image-text\\'>이미지 로드 실패</p>'">`;
    } else {
      imageContainer.innerHTML = '<p class="no-image-text">이미지 없음</p>';
    }
  }

  // 텍스트 렌더링
  const textElem = document.getElementById('storybook-text');
  if (textElem) {
    textElem.textContent = page.text || '내용 없음';
  }

  console.log('[스토리북] 렌더링 완료');

  // 네비게이션 업데이트
  updateStorybookNavigation();
}

// 기존 복잡한 목표/스탯 변화 렌더링 함수 제거 (간소화된 버전에서는 불필요)

/**
 * 스토리북 네비게이션 업데이트 (책 펼침 레이아웃)
 */
function updateStorybookNavigation() {
  const prevBtn = document.getElementById('storybook-prev');
  const nextBtn = document.getElementById('storybook-next');
  const startBtn = document.getElementById('storybook-start');

  if (!AppState.storybook.current) return;

  const totalPages = AppState.storybook.current.pages.length;
  const isFirstPage = AppState.storybook.currentPage === 0;
  const isLastPage = AppState.storybook.currentPage === totalPages - 1;
  const completionAction = AppState.storybook.current.completion_action;

  // 이전 버튼 (첫 페이지에서는 비활성화)
  if (prevBtn) {
    prevBtn.disabled = isFirstPage;
  }

  // 다음 버튼 (마지막 페이지에서는 비활성화)
  if (nextBtn) {
    nextBtn.disabled = isLastPage;
  }

  // "대화 시작하기" 버튼 (마지막 페이지에서만 표시)
  if (startBtn) {
    if (isLastPage) {
      startBtn.style.display = 'block';

      // 게임 종료 액션이면 버튼 텍스트 변경
      if (completionAction === 'game_end') {
        startBtn.textContent = '게임 종료';
        startBtn.onclick = () => {
          hideStorybookModal();
          alert('플레이해주셔서 감사합니다! 새로운 게임을 시작하려면 페이지를 새로고침하세요.');
        };
      } else {
        startBtn.textContent = '대화 시작하기';
        startBtn.onclick = storybookStart;
      }
    } else {
      startBtn.style.display = 'none';
    }
  }
}

/**
 * 이전 페이지로 이동
 */
function storybookPrev() {
  if (AppState.storybook.currentPage > 0) {
    AppState.storybook.currentPage--;
    renderStorybookPage(AppState.storybook.currentPage);
    console.log('[스토리북] 이전 페이지:', AppState.storybook.currentPage);
  }
}

/**
 * 다음 페이지로 이동
 */
function storybookNext() {
  if (AppState.storybook.current && AppState.storybook.currentPage < AppState.storybook.current.pages.length - 1) {
    AppState.storybook.currentPage++;
    renderStorybookPage(AppState.storybook.currentPage);
    console.log('[스토리북] 다음 페이지:', AppState.storybook.currentPage);
  }
}

/**
 * 대화 시작하기 버튼 (스토리북 완료)
 */
async function storybookStart() {
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
 * 채팅 모드로 부드럽게 전환
 */
async function transitionToChatMode() {
  const layer = document.getElementById('transition-layer');

  // 페이드 아웃
  layer.classList.add('active');
  await wait(500);

  // 모달 숨기기
  hideStorybookModal();

  // 게임 상태 새로고침
  await fetchGameState();

  // 페이드 인
  await wait(100);
  layer.classList.remove('active');

  console.log('[전환] 채팅 모드로 전환 완료');
}

/**
 * 스토리북 모드로 부드럽게 전환
 * @param {string} storybookId - 스토리북 ID
 */
async function transitionToStorybookMode(storybookId) {
  const layer = document.getElementById('transition-layer');

  // 페이드 아웃
  layer.classList.add('active');
  await wait(500);

  // 스토리북 로드
  await loadAndShowStorybook(storybookId);

  // 페이드 인
  await wait(100);
  layer.classList.remove('active');

  console.log('[전환] 스토리북 모드로 전환 완료');
}

/**
 * 엔딩 스토리북으로 전환
 * @param {object} endingStorybook - 엔딩 스토리북 데이터
 */
async function transitionToEnding(endingStorybook) {
  const layer = document.getElementById('transition-layer');

  // 페이드 아웃
  layer.classList.add('active');
  await wait(500);

  // 엔딩 스토리북 설정
  AppState.storybook.current = endingStorybook;
  AppState.storybook.currentPage = 0;
  AppState.storybook.isActive = true;

  // 타이틀 업데이트
  document.getElementById('storybook-title').textContent = endingStorybook.title;

  // 첫 페이지 렌더링
  renderStorybookPage(0);

  // 모달 표시
  showStorybookModal();

  // 페이드 인
  await wait(100);
  layer.classList.remove('active');

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

  // 1. 온보딩 체크 및 표시 (최우선)
  const onboardingShown = checkAndShowOnboarding();

  // 2. 온보딩을 표시하지 않은 경우에만 스토리북/채팅 초기화
  if (!onboardingShown) {
    // 초기 스토리북 확인
    await checkInitialStorybook();

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
