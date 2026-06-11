// site/static/js/chat.js — bot chat UI inside the widget panel.
let messages = [];
let pending = false;

const GREETING = "Hi — I'm the Chester Window Cleaner bot. I can quote an "
  + "exact price for your home, check if you're in the service area, or "
  + "answer questions about how it all works. What can I help with?";

const SUGGESTIONS = [
  "How much for a 3-bed semi?",
  "Are you in my area?",
  "What's pure water cleaning?",
];

export function resetChatState() { messages = []; pending = false; }

export function renderChat(root) {
  root.innerHTML = `
    <div class="cwc-chat">
      <div class="cwc-chat-log" id="cwc-chat-log" aria-live="polite"></div>
      <div class="cwc-chat-inputrow">
        <textarea id="cwc-chat-input" rows="1" placeholder="Type a message…"
                  aria-label="Your message"></textarea>
        <button type="button" id="cwc-chat-send" aria-label="Send">Send</button>
      </div>
    </div>
  `;
  renderLog(root);
  const input = root.querySelector("#cwc-chat-input");
  root.querySelector("#cwc-chat-send").addEventListener("click", () => send(root));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(root); }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 112) + "px";
  });
  input.focus();
}

function renderLog(root) {
  const log = root.querySelector("#cwc-chat-log");
  let html = `<div class="cwc-msg bot">${escapeHtml(GREETING)}</div>`;

  if (!messages.length && !pending) {
    html += `<div class="cwc-chips">` + SUGGESTIONS.map((s, i) =>
      `<button type="button" data-suggest="${i}">${escapeHtml(s)}</button>`
    ).join("") + `</div>`;
  }

  html += messages.map((m) => {
    const cls = m.role === "user" ? "user" : "bot";
    const text = typeof m.content === "string"
      ? m.content
      : (m.content?.map?.((c) => c.text ?? "").join(" ") ?? "");
    return `<div class="cwc-msg ${cls}">${escapeHtml(text)}</div>`;
  }).join("");

  if (pending) html += `<div class="cwc-typing" aria-label="The bot is typing"><span></span><span></span><span></span></div>`;

  log.innerHTML = html;
  log.querySelectorAll("[data-suggest]").forEach((b) =>
    b.addEventListener("click", () => {
      const input = root.querySelector("#cwc-chat-input");
      input.value = SUGGESTIONS[Number(b.dataset.suggest)];
      send(root);
    }));
  log.scrollTop = log.scrollHeight;
}

async function send(root) {
  if (pending) return;
  const input = root.querySelector("#cwc-chat-input");
  const text = input.value.trim();
  if (!text) return;
  messages.push({ role: "user", content: text });
  input.value = "";
  input.style.height = "auto";
  pending = true;
  renderLog(root);
  try {
    const r = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    const body = await r.json();
    if (r.ok) messages.push({ role: "assistant", content: body.reply });
    else messages.push({ role: "assistant", content: "Sorry — I'm offline right now. Try the price tab or email hello@chesterwindowcleaner.co.uk." });
  } catch {
    messages.push({ role: "assistant", content: "Network error. Try again or email hello@chesterwindowcleaner.co.uk." });
  } finally {
    pending = false;
    renderLog(root);
    root.querySelector("#cwc-chat-input")?.focus();
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
}
