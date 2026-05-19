// site/static/js/chat.js
let messages = [];
let pending = false;

export function resetChatState() { messages = []; pending = false; }

export function renderChat(root) {
  root.innerHTML = `
    <div id="cwc-chat-log" style="display:flex;flex-direction:column;gap:.5rem;
         max-height:50vh;overflow-y:auto;padding-bottom:.5rem;"></div>
    <label>Your message<br>
      <textarea id="cwc-chat-input" rows=2 placeholder="Ask anything…"></textarea></label>
    <div class="row"><button type=button id="cwc-chat-send">Send</button></div>
    <p style="font-size:.85em;color:#666;margin-top:.5rem;">
      I'm a bot — I can answer questions and pass your details to the owner.</p>
  `;
  renderLog(root);
  root.querySelector("#cwc-chat-send").addEventListener("click", () => send(root));
  root.querySelector("#cwc-chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send(root);
  });
}

function renderLog(root) {
  const log = root.querySelector("#cwc-chat-log");
  log.innerHTML = messages.map(m => {
    const align = m.role === "user" ? "flex-end" : "flex-start";
    const bg = m.role === "user" ? "#e7f1f5" : "#f6efde";
    const text = typeof m.content === "string"
      ? m.content
      : (m.content.map?.(c => c.text ?? "").join(" ") ?? "");
    return `<div style="align-self:${align};background:${bg};
            padding:.5rem .75rem;border-radius:8px;max-width:85%;">
            ${escapeHtml(text)}</div>`;
  }).join("");
  log.scrollTop = log.scrollHeight;
}

async function send(root) {
  if (pending) return;
  const input = root.querySelector("#cwc-chat-input");
  const text = input.value.trim();
  if (!text) return;
  messages.push({ role: "user", content: text });
  input.value = "";
  pending = true;
  renderLog(root);
  try {
    const r = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    const body = await r.json();
    if (r.ok) messages.push({ role: "assistant", content: body.reply });
    else messages.push({ role: "assistant", content: "Sorry — I'm offline right now. Try the price widget or email hello@chesterwindowcleaner.co.uk." });
  } catch {
    messages.push({ role: "assistant", content: "Network error. Try again or email hello@chesterwindowcleaner.co.uk." });
  } finally {
    pending = false;
    renderLog(root);
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}
