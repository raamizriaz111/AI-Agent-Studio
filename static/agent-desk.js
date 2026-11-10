/**
 * Agent Studio — High-Performance Client Logic
 * Linear/Raycast-grade micro-interactions, live viewport morphing, audio synthesis & transcript inspection.
 */

(function () {
  let presetsData = {};
  let currentConfig = {};
  let currentSessionId = "visitor_" + Math.random().toString(36).substring(2, 9) + "_" + Date.now();
  let currentEmbedTab = "html";

  // Seamless tunnel header for live tunnels
  const _origFetch = window.fetch;
  window.fetch = function (url, opts) {
    opts = opts || {};
    opts.headers = opts.headers || {};
    if (opts.headers instanceof Headers) {
      opts.headers.set("bypass-tunnel-reminder", "1");
    } else {
      opts.headers["bypass-tunnel-reminder"] = "1";
    }
    return _origFetch(url, opts);
  };

  // Web Audio Synthesizer for delicate micro-interactions (zero external audio files needed)
  const AudioFeedback = {
    ctx: null,
    init() {
      if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      }
    },
    pop() {
      try {
        this.init();
        if (!this.ctx) return;
        if (this.ctx.state === "suspended") this.ctx.resume();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(600, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, this.ctx.currentTime + 0.08);
        gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.08);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.08);
      } catch (e) {}
    },
    chime() {
      try {
        this.init();
        if (!this.ctx) return;
        if (this.ctx.state === "suspended") this.ctx.resume();
        const now = this.ctx.currentTime;
        [523.25, 659.25, 783.99].forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = "triangle";
          osc.frequency.setValueAtTime(freq, now + idx * 0.06);
          gain.gain.setValueAtTime(0.05, now + idx * 0.06);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.15);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.06);
          osc.stop(now + idx * 0.06 + 0.15);
        });
      } catch (e) {}
    }
  };

  // DOM Elements - Left Panel
  const clientPresetSelect = document.getElementById("client-preset-select");
  const businessNameInput = document.getElementById("business-name-input");
  const agentNameInput = document.getElementById("agent-name-input");
  const brandColorInput = document.getElementById("brand-color-input");
  const brandColorHex = document.getElementById("brand-color-hex");
  const toneInput = document.getElementById("tone-input");
  const agentGoalInput = document.getElementById("agent-goal-input");
  const quickPromptsInput = document.getElementById("quick-prompts-input");
  const knowledgeBaseTextarea = document.getElementById("knowledge-base-textarea");
  const applyBtn = document.getElementById("btn-apply-config");
  const embedCodeBtn = document.getElementById("btn-embed-code");
  const activePresetBadge = document.getElementById("active-preset-badge");
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeToggleLabel = document.getElementById("theme-toggle-label");

  // DOM Elements - Center Preview
  const browserWindowEl = document.getElementById("browser-window-el");
  const browserDomainText = document.getElementById("browser-domain-text");
  const heroBadge = document.getElementById("preview-hero-badge");
  const heroTitle = document.getElementById("preview-hero-title");
  const heroSubtitle = document.getElementById("preview-hero-subtitle");
  const previewCardsContainer = document.getElementById("preview-cards-container");
  const chatHeader = document.getElementById("chat-header");
  const chatHeaderTitle = document.getElementById("chat-header-title");
  const chatAvatarLetter = document.getElementById("chat-avatar-letter");
  const chatMessages = document.getElementById("chat-messages");
  const quickPromptsRow = document.getElementById("quick-prompts-row");
  const chatInputField = document.getElementById("chat-input-field");
  const chatSendBtn = document.getElementById("chat-send-btn");
  const btnViewDesktop = document.getElementById("btn-view-desktop");
  const btnViewMobile = document.getElementById("btn-view-mobile");

  // DOM Elements - Right Panel
  const metricChats = document.getElementById("metric-chats");
  const metricLeads = document.getElementById("metric-leads");
  const leadsListBox = document.getElementById("leads-list-box");
  const newVisitorBtn = document.getElementById("btn-new-visitor");
  const clearLeadsBtn = document.getElementById("btn-clear-leads");
  const btnTopExport = document.getElementById("btn-top-export");
  const btnTopEmbed = document.getElementById("btn-top-embed");
  const btnExportCsvSidebar = document.getElementById("btn-export-csv-sidebar");

  // Modals & Toasts
  const embedModal = document.getElementById("embed-modal");
  const embedModalClose = document.getElementById("embed-modal-close");
  const embedCodeSnippet = document.getElementById("embed-code-snippet");
  const btnCopyEmbedCode = document.getElementById("btn-copy-embed-code");
  const embedInstructionText = document.getElementById("embed-instruction-text");
  const modalTabBtns = document.querySelectorAll(".modal-tab-btn");
  const transcriptModal = document.getElementById("transcript-modal");
  const transcriptModalClose = document.getElementById("transcript-modal-close");
  const transcriptMessagesContainer = document.getElementById("transcript-messages-container");
  const toastContainer = document.getElementById("toast-container");

  // DOM Elements - Mobile Navigation & Panels
  const mobileNavTabs = document.querySelectorAll(".mobile-tab-btn");
  const workspaceContainer = document.getElementById("workspace-container");
  const mobileLeadsCount = document.getElementById("mobile-leads-count");

  // Show Toast Utility (Single Active Alert — Replaces Previous Toast, Never Stacks)
  let currentToastTimer = null;
  function showToast(message, type = "info") {
    if (!toastContainer) return;

    if (currentToastTimer) {
      clearTimeout(currentToastTimer);
      currentToastTimer = null;
    }

    // Immediately clear any existing alert so rapid clicks never stack toasts
    toastContainer.innerHTML = "";

    const toast = document.createElement("div");
    toast.className = "toast-item";
    const icon = type === "success" 
      ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>` 
      : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    currentToastTimer = setTimeout(() => {
      toast.style.transition = "opacity 0.25s ease, transform 0.25s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => {
        if (toast.parentNode) toast.remove();
      }, 250);
    }, 2400);
  }

  // Mobile Navigation Switcher
  function switchMobileTab(targetTab) {
    if (!targetTab) return;
    mobileNavTabs.forEach((btn) => {
      if (btn.getAttribute("data-tab") === targetTab) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    if (workspaceContainer) {
      workspaceContainer.setAttribute("data-active-panel", targetTab);
    }
  }

  mobileNavTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      switchMobileTab(target);
      AudioFeedback.pop();
    });
  });

  // Initialize
  async function init() {
    try {
      const [presetsRes, configRes, leadsRes] = await Promise.all([
        fetch("/api/presets"),
        fetch("/api/config"),
        fetch("/api/leads")
      ]);

      presetsData = await presetsRes.json();
      currentConfig = await configRes.json();
      const leadsData = await leadsRes.json();

      renderPresetsDropdown();
      populateForm(currentConfig);
      applyPreviewStyling(currentConfig);
      renderPreviewCards(currentConfig.previewCards || []);
      renderQuickPrompts(currentConfig.quickPrompts || []);
      renderLeads(leadsData.leads || []);
      updateMetrics(leadsData.chatsCount || 0, leadsData.leadsCount || 0);

      resetChatView(currentConfig.welcomeMessage);
    } catch (err) {
      console.error("Initialization error:", err);
    }
  }

  function renderPresetsDropdown() {
    clientPresetSelect.innerHTML = "";
    Object.values(presetsData).forEach((preset) => {
      const opt = document.createElement("option");
      opt.value = preset.id;
      opt.textContent = preset.name;
      if (currentConfig.id === preset.id || preset.businessName === currentConfig.businessName) {
        opt.selected = true;
      }
      clientPresetSelect.appendChild(opt);
    });
  }

  function populateForm(cfg) {
    businessNameInput.value = cfg.businessName || "";
    agentNameInput.value = cfg.agentName || "";
    updateBrandColor(cfg.brandColor || "#00a884");
    toneInput.value = cfg.tone || "";
    agentGoalInput.value = cfg.agentGoal || "";
    knowledgeBaseTextarea.value = cfg.knowledgeBase || "";
    if (quickPromptsInput) {
      quickPromptsInput.value = (cfg.quickPrompts || []).join(", ");
    }
    if (activePresetBadge) {
      activePresetBadge.textContent = cfg.name || "Custom Setup";
    }
  }

  function getContrastColor(hex) {
    if (!hex) return "#ffffff";
    const c = hex.replace("#", "");
    const r = parseInt(c.substr(0, 2), 16) || 0;
    const g = parseInt(c.substr(2, 2), 16) || 0;
    const b = parseInt(c.substr(4, 2), 16) || 0;
    const yiq = (r * 299 + g * 587 + b * 114) / 1000;
    return yiq >= 165 ? "#090c13" : "#ffffff";
  }

  function updateBrandColor(color) {
    currentConfig.brandColor = color;
    brandColorInput.value = color;
    brandColorHex.textContent = color.toUpperCase();
    const contrastText = getContrastColor(color);

    document.documentElement.style.setProperty("--brand-primary", color);
    document.documentElement.style.setProperty("--brand-glow", `${color}40`);
    document.documentElement.style.setProperty("--brand-soft", `${color}18`);
    document.documentElement.style.setProperty("--brand-contrast-text", contrastText);
    chatHeader.style.backgroundColor = color;

    // Reactively update all existing text message bubbles in real time
    document.querySelectorAll(".chat-bubble.user").forEach((bubble) => {
      bubble.style.backgroundColor = color;
      bubble.style.color = contrastText;
    });
  }

  function applyPreviewStyling(cfg) {
    const brandColor = cfg.brandColor || "#00a884";
    updateBrandColor(brandColor);

    browserDomainText.textContent = cfg.domain || `${(cfg.businessName || "acme").toLowerCase().replace(/[^a-z0-9]/g, "")}.com`;
    heroBadge.textContent = cfg.heroBadge || `Official Assistant for ${cfg.businessName}`;
    heroTitle.textContent = cfg.heroTitle || `Welcome to ${cfg.businessName}`;
    heroSubtitle.textContent = cfg.heroSubtitle || "Exceptional services tailored to your needs.";

    chatHeaderTitle.textContent = `${cfg.agentName || "Assistant"} at ${cfg.businessName || "Company"}`;
    chatAvatarLetter.textContent = (cfg.agentName || "A").charAt(0).toUpperCase();
  }

  function renderPreviewCards(cards) {
    previewCardsContainer.innerHTML = "";
    if (!cards || cards.length === 0) {
      cards = [
        { icon: "⭐", title: "Premium Quality", desc: "Crafted for maximum performance.", price: "Included" },
        { icon: "⚡", title: "Instant Delivery", desc: "Swift execution with 24/7 care.", price: "Fast" },
        { icon: "🛡️", title: "Verified Trust", desc: "Top ratings and customer success.", price: "Guaranteed" }
      ];
    }

    cards.forEach((card) => {
      const cardEl = document.createElement("div");
      cardEl.className = "client-feature-card";
      cardEl.innerHTML = `
        <div class="card-top-icon-row">
          <span class="feature-icon-badge">${card.icon || "✨"}</span>
          <span class="feature-price-badge">${escapeHtml(card.price || "")}</span>
        </div>
        <div class="feature-card-title">${escapeHtml(card.title || "Feature")}</div>
        <div class="feature-card-desc">${escapeHtml(card.desc || "")}</div>
      `;
      previewCardsContainer.appendChild(cardEl);
    });
  }

  function getEffectivePrompts(prompts) {
    if (Array.isArray(prompts) && prompts.length > 0) {
      return prompts;
    }
    const biz = currentConfig.businessName || "our company";
    return [
      `What services does ${biz} provide?`,
      "What are your pricing and plans?",
      "Can I book an appointment or consultation?"
    ];
  }

  function renderQuickPrompts(prompts) {
    const effective = getEffectivePrompts(prompts);
    quickPromptsRow.innerHTML = "";
    effective.forEach((p) => {
      const pill = document.createElement("button");
      pill.className = "prompt-pill";
      pill.textContent = p;
      pill.addEventListener("click", () => {
        chatInputField.value = p;
        sendMessage();
      });
      quickPromptsRow.appendChild(pill);
    });
  }

  function resetChatView(welcomeMsg) {
    chatMessages.innerHTML = "";
    const msg = welcomeMsg || `Hi, I'm ${currentConfig.agentName || 'your assistant'} from ${currentConfig.businessName || 'our company'}. How can I help you today?`;
    appendChatMessage("bot", msg);

    // Populate the clean prompt pills row above the input field
    renderQuickPrompts(currentConfig.quickPrompts);
  }

  function appendChatMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    bubble.textContent = text;
    if (role === "user") {
      const activeColor = currentConfig.brandColor || brandColorInput.value || "#00a884";
      bubble.style.backgroundColor = activeColor;
      bubble.style.color = getContrastColor(activeColor);
    }
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    AudioFeedback.pop();
  }

  function showTyping() {
    const typing = document.createElement("div");
    typing.className = "chat-typing";
    typing.id = "chat-typing-indicator";
    typing.innerHTML = `
      <div class="chat-typing-dot"></div>
      <div class="chat-typing-dot"></div>
      <div class="chat-typing-dot"></div>
    `;
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function hideTyping() {
    const el = document.getElementById("chat-typing-indicator");
    if (el) el.remove();
  }

  // Preset Selection
  clientPresetSelect.addEventListener("change", (e) => {
    const presetId = e.target.value;
    const selectedPreset = presetsData[presetId];
    if (selectedPreset) {
      currentConfig = { ...selectedPreset };
      populateForm(currentConfig);
      applyPreviewStyling(currentConfig);
      renderPreviewCards(currentConfig.previewCards || []);
      renderQuickPrompts(currentConfig.quickPrompts || []);
      resetChatView(currentConfig.welcomeMessage);
      showToast(`Switched template to "${selectedPreset.name}"`, "info");
    }
  });

  // Color picker & Quick swatches
  brandColorInput.addEventListener("input", (e) => updateBrandColor(e.target.value));
  document.querySelectorAll(".color-swatch-btn").forEach((btn) => {
    btn.addEventListener("click", () => updateBrandColor(btn.getAttribute("data-color")));
  });

  // Viewport Switcher (Desktop vs Mobile)
  btnViewDesktop.addEventListener("click", () => {
    btnViewDesktop.classList.add("active");
    btnViewMobile.classList.remove("active");
    browserWindowEl.classList.remove("mobile-mode");
    setTimeout(() => {
      renderQuickPrompts(currentConfig.quickPrompts);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
  });

  btnViewMobile.addEventListener("click", () => {
    btnViewMobile.classList.add("active");
    btnViewDesktop.classList.remove("active");
    browserWindowEl.classList.add("mobile-mode");
    setTimeout(() => {
      renderQuickPrompts(currentConfig.quickPrompts);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
  });

  // Apply and Restart Chat
  applyBtn.addEventListener("click", async () => {
    currentConfig.businessName = businessNameInput.value.trim();
    currentConfig.agentName = agentNameInput.value.trim();
    currentConfig.brandColor = brandColorInput.value;
    currentConfig.tone = toneInput.value.trim();
    currentConfig.agentGoal = agentGoalInput.value.trim();
    currentConfig.knowledgeBase = knowledgeBaseTextarea.value.trim();
    currentConfig.domain = `${currentConfig.businessName.toLowerCase().replace(/[^a-z0-9]/g, "")}.com`;

    if (quickPromptsInput && quickPromptsInput.value.trim()) {
      currentConfig.quickPrompts = quickPromptsInput.value.split(",").map(s => s.trim()).filter(Boolean);
    }

    applyBtn.disabled = true;
    applyBtn.innerHTML = `<span>Saving...</span>`;

    try {
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentConfig)
      });

      // Reset visitor session
      await fetch("/api/session/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: currentSessionId })
      });

      applyPreviewStyling(currentConfig);
      renderQuickPrompts(currentConfig.quickPrompts);
      resetChatView(currentConfig.welcomeMessage);
      showToast("Config applied & AI agent restarted!", "success");

      // On mobile screens, automatically transition smoothly to the preview chat
      if (window.innerWidth <= 1024) {
        switchMobileTab("preview");
      }
    } catch (err) {
      console.error("Failed to save config:", err);
      showToast("Failed to apply configuration", "info");
    } finally {
      applyBtn.disabled = false;
      applyBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>Apply & restart conversation</span>
      `;
    }
  });

  // Send Chat Message
  async function sendMessage() {
    const text = chatInputField.value.trim();
    if (!text) return;

    appendChatMessage("user", text);
    chatInputField.value = "";
    chatInputField.disabled = true;
    chatSendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sessionId: currentSessionId,
          message: text,
          config: currentConfig
        })
      });

      hideTyping();
      const data = await res.json();
      appendChatMessage("bot", data.reply);

      updateMetrics(data.chatsCount, data.leadsCount);

      if (data.leadCaptured) {
        AudioFeedback.chime();
        showToast(`Verified Lead: ${data.leadCaptured.name || "Client"} (${data.leadCaptured.email})`, "success");
        refreshLeadsList();
      }
    } catch (err) {
      hideTyping();
      appendChatMessage("bot", "I am having trouble connecting. Please check your network and try again.");
      console.error("Chat error:", err);
    } finally {
      chatInputField.disabled = false;
      chatSendBtn.disabled = false;
      chatInputField.focus();
    }
  }

  chatSendBtn.addEventListener("click", sendMessage);
  chatInputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Leads rendering & metrics
  function updateMetrics(chats, leads) {
    if (metricChats) metricChats.textContent = chats !== undefined ? chats : 0;
    if (metricLeads) metricLeads.textContent = leads !== undefined ? leads : 0;
    if (mobileLeadsCount) mobileLeadsCount.textContent = leads !== undefined ? leads : 0;
  }

  async function refreshLeadsList() {
    try {
      const res = await fetch("/api/leads");
      const data = await res.json();
      renderLeads(data.leads || []);
      updateMetrics(data.chatsCount, data.leadsCount);
    } catch (e) {
      console.error("Error refreshing leads:", e);
    }
  }

  function renderLeads(leads) {
    if (!leads || leads.length === 0) {
      leadsListBox.innerHTML = `
        <div class="empty-leads-text">
          No leads captured yet. Chat as a visitor and share contact details to see a verified lead record appear here.
        </div>
      `;
      return;
    }

    leadsListBox.innerHTML = "";
    leads.forEach((lead) => {
      const item = document.createElement("div");
      item.className = "lead-card-item";
      const timeStr = new Date(lead.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const initial = (lead.name || "C").charAt(0).toUpperCase();

      item.innerHTML = `
        <div class="lead-card-header">
          <div class="lead-name-badge">
            <span class="lead-avatar-sm">${initial}</span>
            <span class="lead-card-name">${escapeHtml(lead.name || "Interested Visitor")}</span>
          </div>
          <span class="lead-card-time">${timeStr}</span>
        </div>
        <a href="mailto:${escapeHtml(lead.email)}" class="lead-card-email" onclick="event.stopPropagation()">${escapeHtml(lead.email)}</a>
        <div class="lead-card-interest">${escapeHtml(lead.interest || "Service Inquiry")}</div>
        <div class="lead-view-transcript-btn">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>View conversation transcript</span>
        </div>
      `;

      item.addEventListener("click", () => openTranscriptModal(lead.session_id, lead.name));
      leadsListBox.appendChild(item);
    });
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.innerText = str || "";
    return d.innerHTML;
  }

  // Transcript Inspection Modal
  async function openTranscriptModal(sessionId, clientName) {
    transcriptMessagesContainer.innerHTML = `<div style="text-align: center; color: var(--text-tertiary); padding: 20px;">Loading transcript...</div>`;
    document.getElementById("transcript-modal-title").textContent = `Conversation with ${clientName || "Visitor"}`;
    transcriptModal.classList.add("active");

    try {
      const res = await fetch(`/api/session/transcript?sessionId=${encodeURIComponent(sessionId)}`);
      const data = await res.json();
      if (!data.messages || data.messages.length === 0) {
        transcriptMessagesContainer.innerHTML = `<div style="text-align:center; color:var(--text-tertiary); padding: 20px;">No messages recorded in this session.</div>`;
        return;
      }

      transcriptMessagesContainer.innerHTML = data.messages.map((m) => {
        const isBot = m.role === "assistant";
        const userColor = currentConfig.brandColor || "#00a884";
        const bubbleBg = isBot ? "#172132" : userColor;
        const bubbleColor = isBot ? "#ffffff" : getContrastColor(userColor);
        const roleLabel = isBot ? (currentConfig.agentName || "Assistant") : (clientName || "Visitor");
        return `
          <div style="display:flex; flex-direction:column; align-items: ${isBot ? 'flex-start' : 'flex-end'};">
            <span style="font-size:10px; color:var(--text-tertiary); margin-bottom:2px;">${roleLabel}</span>
            <div style="background:${bubbleBg}; color:${bubbleColor}; padding:8px 12px; border-radius:10px; font-size:12.5px; max-width:85%; box-shadow: 0 2px 6px rgba(0,0,0,0.25);">
              ${escapeHtml(m.content)}
            </div>
          </div>
        `;
      }).join("");
    } catch (e) {
      transcriptMessagesContainer.innerHTML = `<div style="color:#ef4444; text-align:center;">Failed to load transcript.</div>`;
    }
  }

  transcriptModalClose.addEventListener("click", () => transcriptModal.classList.remove("active"));
  transcriptModal.addEventListener("click", (e) => {
    if (e.target === transcriptModal) transcriptModal.classList.remove("active");
  });

  // Start new visitor chat
  newVisitorBtn.addEventListener("click", async () => {
    currentSessionId = "visitor_" + Math.random().toString(36).substring(2, 9) + "_" + Date.now();
    await fetch("/api/session/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: currentSessionId })
    });
    resetChatView(currentConfig.welcomeMessage);
    showToast("Started fresh visitor session", "info");
    refreshLeadsList();
  });

  // Clear leads
  clearLeadsBtn.addEventListener("click", async () => {
    if (confirm("Clear all captured leads?")) {
      await fetch("/api/leads/clear", { method: "POST" });
      renderLeads([]);
      updateMetrics(metricChats.textContent, 0);
      showToast("All leads cleared", "info");
    }
  });

  // CSV Export
  function exportCsv() {
    window.location.href = "/api/leads/export";
    showToast("Exporting captured_leads.csv...", "success");
  }
  if (btnTopExport) btnTopExport.addEventListener("click", exportCsv);
  if (btnExportCsvSidebar) btnExportCsvSidebar.addEventListener("click", exportCsv);

  // Embed Modal Tab Handling
  function updateEmbedSnippet() {
    const origin = window.location.origin;
    if (currentEmbedTab === "html") {
      embedInstructionText.textContent = "Paste these 2 lines into the <head> or before </body> of your client's HTML, Webflow, or Shopify site:";
      embedCodeSnippet.textContent = 
`<!-- ${currentConfig.businessName || "Chatbot"} Widget Embed -->\n` +
`<link rel="stylesheet" href="${origin}/static/chat-widget.css">\n` +
`<script src="${origin}/static/chat-widget.js" defer></script>`;
    } else if (currentEmbedTab === "react") {
      embedInstructionText.textContent = "Use next/script in your Next.js app or a standard useEffect in React:";
      embedCodeSnippet.textContent =
`import Script from 'next/script';\n\n` +
`export default function ChatbotWidget() {\n` +
`  return (\n` +
`    <>\n` +
`      <link rel="stylesheet" href="${origin}/static/chat-widget.css" />\n` +
`      <Script src="${origin}/static/chat-widget.js" strategy="lazyOnload" />\n` +
`    </>\n` +
`  );\n` +
`}`;
    } else if (currentEmbedTab === "wordpress") {
      embedInstructionText.textContent = "In WordPress: Go to Appearance -> Theme File Editor (or use 'Insert Headers and Footers' plugin):";
      embedCodeSnippet.textContent =
`<!-- Add to header.php before </head> -->\n` +
`<link rel="stylesheet" href="${origin}/static/chat-widget.css">\n` +
`<script src="${origin}/static/chat-widget.js" defer></script>`;
    }
  }

  modalTabBtns.forEach((tab) => {
    tab.addEventListener("click", () => {
      modalTabBtns.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentEmbedTab = tab.getAttribute("data-tab");
      updateEmbedSnippet();
    });
  });

  function openEmbedModal() {
    updateEmbedSnippet();
    embedModal.classList.add("active");
  }

  if (btnTopEmbed) btnTopEmbed.addEventListener("click", openEmbedModal);
  if (embedCodeBtn) embedCodeBtn.addEventListener("click", openEmbedModal);
  embedModalClose.addEventListener("click", () => embedModal.classList.remove("active"));
  embedModal.addEventListener("click", (e) => {
    if (e.target === embedModal) embedModal.classList.remove("active");
  });

  btnCopyEmbedCode.addEventListener("click", () => {
    navigator.clipboard.writeText(embedCodeSnippet.textContent);
    showToast("Code copied to clipboard!", "success");
  });

  // Theme Management (Light / Dark Mode with LocalStorage persistence)
  const THEME_STORAGE_KEY = "agent_studio_theme_mode";

  function applyTheme(theme) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      if (themeToggleLabel) themeToggleLabel.textContent = "Light";
    } else {
      document.documentElement.removeAttribute("data-theme");
      if (themeToggleLabel) themeToggleLabel.textContent = "Dark";
    }
  }

  function toggleTheme() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const nextTheme = isLight ? "dark" : "light";
    applyTheme(nextTheme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    } catch (e) {}
    AudioFeedback.pop();
    showToast(`Switched to ${nextTheme === "light" ? "Light" : "Dark"} Mode`, "info");
  }

  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || "dark";
  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", toggleTheme);
  }

  // Start
  init();
})();
