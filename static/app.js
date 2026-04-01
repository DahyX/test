(function () {
  const body = document.body;
  const token = body.dataset.token;
  const messagesEl = document.getElementById("messages");
  const inputEl = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const welcomeCard = document.getElementById("welcomeCard");
  const recentPromptsEl = document.getElementById("recentPrompts");
  const modeSummaryEl = document.getElementById("modeSummary");
  const composerModeEl = document.getElementById("composerMode");
  const streamStateEl = document.getElementById("streamState");
  const composerHintEl = document.getElementById("composerHint");
  const missionTextEl = document.getElementById("missionText");
  const activityFeedEl = document.getElementById("activityFeed");
  const chatPresenceEl = document.getElementById("chatPresence");
  const liveStatusEl = document.getElementById("liveStatus");
  const signalDotEl = document.getElementById("signalDot");

  const STORAGE_KEY = "jarvis-ui-history-v3";
  const ACTIVITY_KEY = "jarvis-ui-activity-v1";
  const MODE_KEY = "jarvis-ui-mode-v1";

  const MODE_PRESETS = {
    general: {
      label: "General",
      summary: "General conversation and runtime guidance.",
      mission: "Use Jarvis to inspect code, track runtime health, and grow the training stack deliberately.",
      placeholder: "Ask Jarvis about the repo, memory, or its LLM roadmap...",
      replyTag: "General reply",
    },
    repo: {
      label: "Repo",
      summary: "Codebase inspection, file tracing, and grounded repo answers.",
      mission: "Stay grounded in local files, symbols, and runtime paths before answering.",
      placeholder: "Ask about files, functions, symbols, modules, or architecture paths...",
      replyTag: "Repo answer",
    },
    cognitive: {
      label: "Cognitive",
      summary: "Architecture, verifier, autonomy, and runtime system design.",
      mission: "Inspect the model stack, verifier gates, autonomy jobs, and safety boundaries.",
      placeholder: "Ask about cognitive status, verifier design, autonomy, or safety architecture...",
      replyTag: "System answer",
    },
    training: {
      label: "LLM Lab",
      summary: "Training data, LLM roadmap, dataset export, and fine-tuning direction.",
      mission: "Use the LLM lab to curate data, plan fine-tuning, and keep the training loop disciplined.",
      placeholder: "Ask about training data, llm roadmap, dataset export, or model specialization...",
      replyTag: "LLM lab",
    },
  };

  let isSending = false;
  let activeController = null;
  let currentMode = localStorage.getItem(MODE_KEY) || "general";
  if (!MODE_PRESETS[currentMode]) {
    currentMode = "general";
  }
  let lastStatusSignature = "";
  let wasDisconnected = false;

  function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderContent(text) {
    if (!text) return "<p>-</p>";

    let html = escapeHtml(text);
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, _lang, code) => `<pre><code>${code.trim()}</code></pre>`);
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

    return html
      .split("\n\n")
      .map((paragraph) => {
        if (paragraph.startsWith("<pre>")) return paragraph;
        return `<p>${paragraph.replace(/\n/g, "<br>")}</p>`;
      })
      .join("");
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function buildMessageMarkup(role, content, options = {}) {
    const mode = MODE_PRESETS[options.mode] || MODE_PRESETS[currentMode];
    const stamp = options.timestamp || formatTime();
    const tag = options.tag || (role === "user" ? mode.label : "Jarvis");
    const roleClass = role === "user" ? "user" : "assistant";

    return `
      <div class="avatar">${role === "user" ? "You" : "J"}</div>
      <div class="message-body">
        <div class="message-meta">
          <span class="role-pill ${roleClass}">${escapeHtml(tag)}</span>
          <span class="message-time">${escapeHtml(stamp)}</span>
        </div>
        <div class="bubble">${renderContent(content)}</div>
      </div>
    `;
  }

  function createMessage(role, content, options = {}) {
    const wrapper = document.createElement("article");
    wrapper.className = `message ${role}`;
    wrapper.innerHTML = buildMessageMarkup(role, content, options);
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function updateAssistantBubble(node, content, options = {}) {
    const bubble = node.querySelector(".bubble");
    bubble.innerHTML = renderContent(content);

    const rolePill = node.querySelector(".role-pill");
    if (options.tag && rolePill) {
      rolePill.textContent = options.tag;
    }

    const timeNode = node.querySelector(".message-time");
    if (options.timestamp && timeNode) {
      timeNode.textContent = options.timestamp;
    }

    scrollToBottom();
  }

  function hideWelcome() {
    if (welcomeCard) {
      welcomeCard.style.display = "none";
    }
  }

  function saveConversation() {
    const transcript = [];
    messagesEl.querySelectorAll(".message").forEach((node) => {
      transcript.push({
        role: node.classList.contains("user") ? "user" : "assistant",
        markup: node.innerHTML,
      });
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(transcript));
  }

  function loadConversation() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;

    try {
      const transcript = JSON.parse(raw);
      if (!Array.isArray(transcript) || transcript.length === 0) return;
      hideWelcome();
      transcript.forEach((entry) => {
        const wrapper = document.createElement("article");
        wrapper.className = `message ${entry.role}`;
        if (entry.markup) {
          wrapper.innerHTML = entry.markup;
        } else {
          wrapper.innerHTML = buildMessageMarkup(entry.role, entry.html || "", { mode: currentMode });
        }
        messagesEl.appendChild(wrapper);
      });
      scrollToBottom();
    } catch (_error) {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  function rememberPrompt(prompt) {
    const key = `${STORAGE_KEY}-prompts`;
    const previous = JSON.parse(localStorage.getItem(key) || "[]");
    const next = [prompt, ...previous.filter((item) => item !== prompt)].slice(0, 8);
    localStorage.setItem(key, JSON.stringify(next));
    renderRecentPrompts();
  }

  function renderRecentPrompts() {
    const prompts = JSON.parse(localStorage.getItem(`${STORAGE_KEY}-prompts`) || "[]");
    recentPromptsEl.innerHTML = "";

    if (!prompts.length) {
      recentPromptsEl.innerHTML = '<div class="empty-state">No prompts yet.</div>';
      return;
    }

    prompts.forEach((prompt) => {
      const button = document.createElement("button");
      button.className = "recent-prompt";
      button.textContent = prompt;
      button.addEventListener("click", () => {
        inputEl.value = prompt;
        autoResize();
        sendMessage();
      });
      recentPromptsEl.appendChild(button);
    });
  }

  function getActivityHistory() {
    try {
      const history = JSON.parse(localStorage.getItem(ACTIVITY_KEY) || "[]");
      return Array.isArray(history) ? history : [];
    } catch (_error) {
      return [];
    }
  }

  function renderActivityFeed() {
    const history = getActivityHistory();
    activityFeedEl.innerHTML = "";

    if (!history.length) {
      activityFeedEl.innerHTML = '<div class="activity-empty">No activity yet.</div>';
      return;
    }

    history.forEach((entry) => {
      const item = document.createElement("div");
      item.className = `activity-item ${entry.tone || "system"}`;
      item.innerHTML = `
        <div class="activity-header">
          <strong>${escapeHtml(entry.title)}</strong>
          <span>${escapeHtml(entry.time)}</span>
        </div>
        <p>${escapeHtml(entry.detail)}</p>
      `;
      activityFeedEl.appendChild(item);
    });
  }

  function logActivity(title, detail, tone = "system") {
    const history = getActivityHistory();
    const next = [
      {
        title,
        detail,
        tone,
        time: formatTime(),
      },
      ...history,
    ].slice(0, 12);
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify(next));
    renderActivityFeed();
  }

  function setMode(mode, options = {}) {
    if (!MODE_PRESETS[mode]) return;
    currentMode = mode;
    localStorage.setItem(MODE_KEY, mode);

    document.querySelectorAll(".mode-chip").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.mode === mode);
    });

    const preset = MODE_PRESETS[mode];
    modeSummaryEl.textContent = preset.summary;
    composerModeEl.textContent = preset.label;
    missionTextEl.textContent = preset.mission;
    inputEl.placeholder = preset.placeholder;

    if (options.log !== false) {
      logActivity("Focus changed", `${preset.label} mode selected.`, "system");
    }
  }

  function inferModeFromPrompt(text) {
    const lowered = (text || "").toLowerCase();

    if (/\b(cognitive status|architecture status|jarvis architecture|verifier|autonomy|claude status|self-check)\b/.test(lowered)) {
      return "cognitive";
    }

    if (/\b(llm|dataset|mlabonne|qlora|fine[- ]?tune|training|export)\b/.test(lowered)) {
      return "training";
    }

    if (/\b(explain|where is|which file|what file|code-review|pluginloader|main_loop|web_server|\.py|repo|module|symbol)\b/.test(lowered)) {
      return "repo";
    }

    return currentMode;
  }

  function setBusy(active) {
    isSending = active;
    body.classList.toggle("is-streaming", active);
    sendBtn.textContent = active ? "Stop" : "Send";
    sendBtn.classList.toggle("stop", active);
    streamStateEl.textContent = active ? "Streaming" : "Idle";
    chatPresenceEl.textContent = active ? "Streaming" : "Idle";
    composerHintEl.textContent = active
      ? "Streaming reply. Click Stop to interrupt the current response."
      : "Enter sends. Shift+Enter adds a new line. Click Stop while streaming to interrupt.";
  }

  function stopStreaming() {
    if (activeController) {
      activeController.abort();
    }
  }

  async function sendMessage(forcedText) {
    const text = (forcedText || inputEl.value).trim();
    if (!text || isSending) return;

    const promptMode = inferModeFromPrompt(text);
    setMode(promptMode, { log: false });
    hideWelcome();
    createMessage("user", text, { mode: promptMode, tag: MODE_PRESETS[promptMode].label });
    rememberPrompt(text);
    saveConversation();
    logActivity("Prompt sent", text.length > 90 ? `${text.slice(0, 90)}...` : text, "user");

    inputEl.value = "";
    autoResize();
    setBusy(true);

    const assistantNode = createMessage("assistant", "Thinking...", {
      mode: promptMode,
      tag: MODE_PRESETS[promptMode].replyTag,
    });

    let buffer = "";
    let completionTone = "assistant";
    let completionDetail = "Reply completed.";

    activeController = new AbortController();

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Jarvis-Token": token,
        },
        body: JSON.stringify({ message: text }),
        signal: activeController.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let pending = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        pending += decoder.decode(value, { stream: true });

        const chunks = pending.split("\n\n");
        pending = chunks.pop() || "";

        chunks.forEach((chunk) => {
          const trimmed = chunk.trim();
          if (!trimmed.startsWith("data:")) return;
          const payload = JSON.parse(trimmed.slice(5).trim());
          if (payload.error) {
            buffer = `Error: ${payload.error}`;
            completionTone = "warn";
            completionDetail = payload.error;
            updateAssistantBubble(assistantNode, buffer, {
              tag: "Runtime issue",
              timestamp: formatTime(),
            });
            return;
          }

          if (payload.token) {
            buffer += payload.token;
            updateAssistantBubble(assistantNode, buffer, {
              tag: MODE_PRESETS[promptMode].replyTag,
              timestamp: formatTime(),
            });
          }
        });
      }

      if (!buffer.trim()) {
        buffer = "No reply arrived from the runtime.";
        completionTone = "warn";
        completionDetail = "No reply arrived from the runtime.";
        updateAssistantBubble(assistantNode, buffer, {
          tag: "Runtime issue",
          timestamp: formatTime(),
        });
      } else {
        completionDetail = buffer.replace(/\s+/g, " ").trim();
      }
    } catch (error) {
      if (error.name === "AbortError") {
        completionTone = "warn";
        completionDetail = "Streaming reply stopped by user.";
        buffer = buffer ? `${buffer}\n\nStopped by user.` : "Response stopped by user.";
        updateAssistantBubble(assistantNode, buffer, {
          tag: "Stopped",
          timestamp: formatTime(),
        });
      } else {
        completionTone = "warn";
        completionDetail = error.message;
        buffer = `Connection error: ${error.message}`;
        updateAssistantBubble(assistantNode, buffer, {
          tag: "Connection issue",
          timestamp: formatTime(),
        });
      }
    } finally {
      activeController = null;
      setBusy(false);
      inputEl.focus();
      saveConversation();
      fetchStatus();
      logActivity(
        completionTone === "assistant" ? "Reply ready" : "Reply interrupted",
        completionDetail.length > 110 ? `${completionDetail.slice(0, 110)}...` : completionDetail,
        completionTone,
      );
    }
  }

  async function fetchStatus() {
    try {
      const response = await fetch("/api/status", {
        headers: { "X-Jarvis-Token": token },
      });
      const data = await response.json();

      document.getElementById("modelName").textContent = data.model || "offline";
      document.getElementById("chatReady").textContent = data.chat_ready ? "Ready" : "Degraded";
      document.getElementById("episodeCount").textContent = String(data.episodes || 0);
      document.getElementById("repoFiles").textContent = String(data.repo_files || 0);
      document.getElementById("claudeAssets").textContent = `${data.claude_commands || 0} / ${data.claude_agents || 0}`;
      document.getElementById("llmLab").textContent = data.llm_lab_phase || "curriculum";

      const llmLabMeta = [];
      if (data.llm_lab_dataset_examples) {
        llmLabMeta.push(`${data.llm_lab_dataset_examples} examples exported`);
      }
      if (data.llm_lab_dataset_path) {
        llmLabMeta.push(data.llm_lab_dataset_path);
      }
      document.getElementById("llmLabFocus").textContent =
        [data.llm_lab_focus || "No active lab plan yet."].concat(llmLabMeta).join(" | ");

      document.getElementById("workingItems").textContent = String(data.working_items || 0);
      document.getElementById("profileItems").textContent = String(data.profile_items || 0);
      document.getElementById("repoPythonFiles").textContent = String(data.repo_python_files || 0);
      document.getElementById("toolCount").textContent = String(data.tool_count || 0);

      document.getElementById("heroRoles").textContent = String(data.foundation_model_roles || 0);
      document.getElementById("heroVerifiers").textContent = String(data.foundation_verifier_stages || 0);
      document.getElementById("heroAutonomy").textContent = String(data.foundation_autonomy_jobs || 0);
      document.getElementById("heroBenchmarks").textContent = String(data.foundation_benchmark_tracks || 0);
      document.getElementById("stackRoles").textContent = String(data.foundation_model_roles || 0);
      document.getElementById("stackVerifiers").textContent = String(data.foundation_verifier_stages || 0);
      document.getElementById("stackAutonomy").textContent = String(data.foundation_autonomy_jobs || 0);
      document.getElementById("stackBenchmarks").textContent = String(data.foundation_benchmark_tracks || 0);

      const runtimeBanner = document.getElementById("runtimeBanner");
      runtimeBanner.textContent = data.chat_ready
        ? `Model-backed chat is available, and Jarvis can still fall back to repo and local memory paths. Foundation: ${data.foundation_model_roles || 0} roles, ${data.foundation_verifier_stages || 0} verifier stages.`
        : `Jarvis is currently relying on grounded local logic, repo Q&A, and offline memory. Foundation: ${data.foundation_autonomy_jobs || 0} autonomy jobs, ${data.foundation_benchmark_tracks || 0} benchmark tracks.`;
      runtimeBanner.classList.toggle("degraded", !data.chat_ready);

      liveStatusEl.textContent = data.chat_ready
        ? `Runtime steady on ${data.model || "local"}`
        : "Local-first degraded mode";
      signalDotEl.classList.toggle("degraded", !data.chat_ready);
      signalDotEl.classList.toggle("active", !!data.chat_ready);

      if (!isSending) {
        chatPresenceEl.textContent = data.chat_ready ? "Ready" : "Degraded";
      }

      const signature = [
        data.model || "offline",
        data.chat_ready ? "ready" : "degraded",
        data.llm_lab_phase || "curriculum",
        data.foundation_model_roles || 0,
        data.foundation_autonomy_jobs || 0,
      ].join("|");

      if (signature !== lastStatusSignature) {
        if (lastStatusSignature) {
          logActivity(
            "Runtime sync",
            `Model ${data.model || "offline"} | ${data.chat_ready ? "ready" : "degraded"} | lab ${data.llm_lab_phase || "curriculum"}`,
            data.chat_ready ? "system" : "warn",
          );
        }
        lastStatusSignature = signature;
      }

      wasDisconnected = false;
    } catch (_error) {
      document.getElementById("modelName").textContent = "Disconnected";
      document.getElementById("chatReady").textContent = "Offline";
      liveStatusEl.textContent = "Status endpoint unavailable";
      signalDotEl.classList.remove("active");
      signalDotEl.classList.add("degraded");
      if (!isSending) {
        chatPresenceEl.textContent = "Offline";
      }

      if (!wasDisconnected) {
        logActivity("Runtime disconnected", "Could not fetch live status from the web server.", "warn");
        wasDisconnected = true;
      }
    }
  }

  function clearLocalConversation() {
    messagesEl.querySelectorAll(".message").forEach((node) => node.remove());
    localStorage.removeItem(STORAGE_KEY);
    if (welcomeCard) {
      welcomeCard.style.display = "block";
    }
    logActivity("Conversation cleared", "Removed the local UI transcript without touching Jarvis memory.", "system");
  }

  function autoResize() {
    inputEl.style.height = "auto";
    inputEl.style.height = `${Math.min(inputEl.scrollHeight, 200)}px`;
  }

  inputEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  inputEl.addEventListener("input", autoResize);
  sendBtn.addEventListener("click", () => {
    if (isSending) {
      stopStreaming();
    } else {
      sendMessage();
    }
  });
  clearChatBtn.addEventListener("click", clearLocalConversation);

  document.querySelectorAll("[data-quick]").forEach((button) => {
    button.addEventListener("click", () => {
      inputEl.value = button.dataset.quick;
      autoResize();
      sendMessage();
    });
  });

  document.querySelectorAll(".mode-chip").forEach((button) => {
    button.addEventListener("click", () => {
      setMode(button.dataset.mode);
      inputEl.focus();
    });
  });

  setMode(currentMode, { log: false });
  loadConversation();
  renderRecentPrompts();
  renderActivityFeed();
  fetchStatus();
  inputEl.focus();
  setInterval(fetchStatus, 20000);
})();
