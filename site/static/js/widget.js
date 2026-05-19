// site/static/js/widget.js — widget shell + mode switch.
import { renderWizard, resetWizardState } from "/static/js/wizard.js";
import { renderChat, resetChatState } from "/static/js/chat.js";

const STATE = { mode: "wizard", open: false };

function html(strings, ...values) {
  return strings.reduce((acc, s, i) => acc + s + (values[i] ?? ""), "");
}

function mount() {
  const fab = document.createElement("button");
  fab.className = "cwc-widget-fab";
  fab.type = "button";
  fab.textContent = "Get an instant price";
  fab.addEventListener("click", () => api.open());

  const panel = document.createElement("div");
  panel.className = "cwc-widget-panel";
  panel.id = "cwc-widget-panel";
  panel.innerHTML = html`
    <div class="cwc-widget-header">
      <strong id="cwc-widget-title">Get an instant price</strong>
      <button type="button" id="cwc-widget-close" aria-label="Close"
              style="background:none;border:0;color:white;cursor:pointer;font-size:1.5rem;">×</button>
    </div>
    <div class="cwc-widget-body" id="cwc-widget-body"></div>
    <div class="cwc-widget-footer" id="cwc-widget-footer">
      <a href="#" id="cwc-widget-switch" style="font-size:.9rem;"></a>
    </div>
  `;
  document.body.append(fab, panel);

  panel.querySelector("#cwc-widget-close").addEventListener("click", () => api.close());
  panel.querySelector("#cwc-widget-switch").addEventListener("click", (e) => {
    e.preventDefault();
    api.setMode(STATE.mode === "wizard" ? "chat" : "wizard");
  });
  return panel;
}

let panel = null;

function refresh() {
  const body = document.getElementById("cwc-widget-body");
  const title = document.getElementById("cwc-widget-title");
  const sw = document.getElementById("cwc-widget-switch");
  if (STATE.mode === "wizard") {
    title.textContent = "Get an instant price";
    sw.textContent = "Or ask me a question →";
    renderWizard(body);
  } else {
    title.textContent = "Ask me a question";
    sw.textContent = "Or get an instant price →";
    renderChat(body);
  }
}

const api = {
  open() {
    if (!panel) panel = mount();
    panel.classList.add("open");
    STATE.open = true;
    refresh();
  },
  close() { panel?.classList.remove("open"); STATE.open = false; },
  setMode(mode) {
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
