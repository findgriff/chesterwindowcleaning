// site/static/js/widget.js — widget shell + mode switch.
import { renderWizard, resetWizardState } from "/static/js/wizard.js?v=20260611b";
import { renderChat, resetChatState } from "/static/js/chat.js?v=20260611b";

const STATE = { mode: "wizard", open: false };

const CHAT_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
</svg>`;

function mount() {
  const fab = document.createElement("button");
  fab.className = "cwc-widget-fab";
  fab.type = "button";
  fab.innerHTML = `${CHAT_ICON}<span>Price &amp; questions</span><span class="dot" aria-hidden="true"></span>`;
  fab.setAttribute("aria-label", "Open the price and chat widget");
  fab.addEventListener("click", () => api.open());

  const panel = document.createElement("div");
  panel.className = "cwc-widget-panel";
  panel.id = "cwc-widget-panel";
  panel.innerHTML = `
    <div class="cwc-widget-header">
      <div class="bar">
        <div>
          <strong>Chester Window Cleaner</strong>
          <span class="sub" id="cwc-widget-sub">Instant prices · honest answers</span>
        </div>
        <button type="button" class="cwc-widget-close" id="cwc-widget-close" aria-label="Close">✕</button>
      </div>
      <div class="cwc-widget-tabs" role="tablist">
        <button type="button" id="cwc-tab-wizard" role="tab">Instant price</button>
        <button type="button" id="cwc-tab-chat" role="tab">Ask the bot</button>
      </div>
    </div>
    <div class="cwc-widget-body" id="cwc-widget-body"></div>
    <div class="cwc-widget-footer">I'm a bot — I answer questions and pass your details to the owner. No spam, ever.</div>
  `;
  document.body.append(fab, panel);

  panel.querySelector("#cwc-widget-close").addEventListener("click", () => api.close());
  panel.querySelector("#cwc-tab-wizard").addEventListener("click", () => api.setMode("wizard"));
  panel.querySelector("#cwc-tab-chat").addEventListener("click", () => api.setMode("chat"));
  return panel;
}

let panel = null;

function refresh() {
  const body = document.getElementById("cwc-widget-body");
  const tabW = document.getElementById("cwc-tab-wizard");
  const tabC = document.getElementById("cwc-tab-chat");
  tabW.classList.toggle("active", STATE.mode === "wizard");
  tabC.classList.toggle("active", STATE.mode === "chat");
  tabW.setAttribute("aria-selected", STATE.mode === "wizard");
  tabC.setAttribute("aria-selected", STATE.mode === "chat");
  if (STATE.mode === "wizard") renderWizard(body);
  else renderChat(body);
}

const api = {
  // open() keeps the last mode; open("chat") / open("wizard") jumps to one.
  open(mode) {
    if (!panel) panel = mount();
    if (mode === "wizard" || mode === "chat") STATE.mode = mode;
    panel.classList.add("open");
    STATE.open = true;
    refresh();
  },
  close() { panel?.classList.remove("open"); STATE.open = false; },
  setMode(mode) {
    if (STATE.mode === mode) return;
    STATE.mode = mode;
    if (mode === "wizard") resetWizardState(); else resetChatState();
    refresh();
  },
};

window.cwcWidget = api;

// Auto-mount the FAB so users can find the widget.
document.addEventListener("DOMContentLoaded", () => {
  if (!panel) panel = mount();
});
