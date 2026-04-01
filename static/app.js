(function () {
  const body = document.body;
  const token = body.dataset.token;
  const messagesEl = document.getElementById("messages");
  const inputEl = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const welcomeCard = document.getElementById("welcomeCard");
  const recentPromptsEl = document.getElementById("recentPrompts");

  const STORAGE_KEY = "jarvis-ui-history-v2";
  let isSending = false;

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderContent(text) {
    if (!text) return "<p>—</p>";

    let html = escapeHtml(text);
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, _lang, code) => `<pre><code>${code.trim()}</code></pre>`);
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

    const paragraphs = html.split("\n\n");
    return paragraphs.map((paragraph) => {
      if (paragraph.startsWith("<pre>")) return paragraph;
      return `<p>${paragraph.replace(/\n/g, "<br>")}</p>`;
    }).join("");
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function createMessage(role, content) {
    const wrapper = document.createElement("article");
    wrapper.className = `message ${role}`;
    wrapper.innerHTML = `
      <div class="avatar">${role === "user" ? "You" : "J"}</div>
      <div class="bubble">${renderContent(content)}</div>
    `;
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function updateAssistantBubble(node, content) {
    const bubble = node.querySelector(".bubble");
    bubble.innerHTML = renderContent(content);
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
        html: node.querySelector(".bubble").innerHTML,
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
        wrapper.innerHTML = `
          <div class="avatar">${entry.role === "user" ? "You" : "J"}</div>
          <div class="bubble">${entry.html}</div>
        `;
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

  async function sendMessage(forcedText) {
    const text = (forcedText || inputEl.value).trim();
    if (!text || isSending) return;

    hideWelcome();
    createMessage("user", text);
    rememberPrompt(text);
    saveConversation();

    inputEl.value = "";
    autoResize();
    isSending = true;
    sendBtn.disabled = true;

    const assistantNode = createMessage("assistant", "Thinking...");
    let buffer = "";

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Jarvis-Token": token,
        },
        body: JSON.stringify({ message: text }),
      });

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
            updateAssistantBubble(assistantNode, buffer);
            return;
          }
          if (payload.token) {
            buffer += payload.token;
            updateAssistantBubble(assistantNode, buffer);
          }
        });
      }
    } catch (error) {
      buffer = `Connection error: ${error.message}`;
      updateAssistantBubble(assistantNode, buffer);
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      inputEl.focus();
      saveConversation();
      fetchStatus();
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

      const runtimeBanner = document.getElementById("runtimeBanner");
      runtimeBanner.textContent = data.chat_ready
        ? `Model-backed chat is available, and Jarvis can still fall back to repo/local memory paths. Foundation: ${data.foundation_model_roles || 0} roles, ${data.foundation_verifier_stages || 0} verifier stages.`
        : `Jarvis is currently relying on grounded local logic, repo Q&A, and offline memory. Foundation: ${data.foundation_autonomy_jobs || 0} autonomy jobs, ${data.foundation_benchmark_tracks || 0} benchmark tracks.`;
      runtimeBanner.classList.toggle("degraded", !data.chat_ready);
    } catch (_error) {
      document.getElementById("modelName").textContent = "Disconnected";
      document.getElementById("chatReady").textContent = "Offline";
    }
  }

  function clearLocalConversation() {
    messagesEl.querySelectorAll(".message").forEach((node) => node.remove());
    localStorage.removeItem(STORAGE_KEY);
    if (welcomeCard) {
      welcomeCard.style.display = "block";
    }
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
  sendBtn.addEventListener("click", () => sendMessage());
  clearChatBtn.addEventListener("click", clearLocalConversation);

  document.querySelectorAll("[data-quick]").forEach((button) => {
    button.addEventListener("click", () => {
      inputEl.value = button.dataset.quick;
      autoResize();
      sendMessage();
    });
  });

  loadConversation();
  renderRecentPrompts();
  fetchStatus();
  inputEl.focus();
  setInterval(fetchStatus, 20000);
})();
