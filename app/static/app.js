const state = {
  sessionId: `web_${crypto.randomUUID().slice(0, 8)}`,
  history: [],
};

const $ = (id) => document.getElementById(id);
const messages = $("messages");

function money(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function appendMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = role === "buyer"
    ? "ml-auto max-w-md rounded-2xl rounded-tr-sm border border-signal/30 bg-panel px-4 py-3 text-sm leading-6 text-navy shadow-sm animate-fade-in"
    : "max-w-md rounded-2xl rounded-tl-sm border border-line bg-[#222] px-4 py-3 text-sm leading-6 text-navy shadow-sm animate-fade-in";
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function showVerdict(entry) {
  const card = $("verdict-card");
  if (!entry) return;
  const allowed = Boolean(entry.allowed);
  card.className = `rounded-lg border p-5 transition-all duration-300 ${allowed ? "border-signal bg-[#00E6CC]/10 shadow-glow" : "border-warn bg-[#F58220]/10 shadow-warnGlow"}`;
  $("verdict-title").textContent = allowed ? "Allowed — sent to Razorpay" : "Blocked by AgentGate";
  $("verdict-title").className = `mt-1 text-lg font-bold ${allowed ? "text-signal" : "text-warn"}`;
  $("verdict-reason").textContent = entry.reason;
  $("verdict-reason").className = `mt-2 text-sm leading-5 ${allowed ? "text-navy" : "text-navy"}`;
}

function renderAudit(entries) {
  $("audit-count").textContent = `${entries.length} event${entries.length === 1 ? "" : "s"}`;
  $("decision-count").textContent = entries.length ? `Decision ${entries[0].id}` : "Awaiting order";
  const log = $("audit-log");
  log.replaceChildren();
  if (!entries.length) {
    log.innerHTML = '<p class="py-3 text-slate-400">No session events yet.</p>';
    return;
  }
  entries.forEach((entry) => {
    const row = document.createElement("div");
    const time = new Date(entry.timestamp * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    row.className = "grid grid-cols-[52px_62px_1fr] gap-2 py-3 text-xs animate-fade-in items-start";
    row.innerHTML = `<span class="text-ink">${time}</span><span class="font-semibold ${entry.allowed ? "text-signal" : "text-warn"} border ${entry.allowed ? "border-signal/30 bg-signal/10" : "border-warn/30 bg-warn/10"} px-1.5 py-0.5 rounded text-center inline-block">${entry.allowed ? "ALLOW" : "BLOCK"}</span><span class="leading-5 text-navy">${entry.product_id || entry.action}</span>`;
    log.appendChild(row);
  });
  showVerdict(entries[0]);
}

async function refreshEvidence() {
  const response = await fetch(`/audit?session_id=${encodeURIComponent(state.sessionId)}&limit=20`);
  if (!response.ok) throw new Error("Could not load audit log");
  renderAudit(await response.json());
}

async function loadCatalog() {
  const response = await fetch("/catalog");
  if (!response.ok) throw new Error("Could not load catalog");
  const products = await response.json();
  const catalog = $("catalog");
  catalog.replaceChildren();
  products.forEach((product) => {
    const card = document.createElement("article");
    card.className = "flex min-h-40 flex-col rounded-xl border border-line bg-canvas p-5 transition-all duration-300 hover:border-signal hover:shadow-glow hover:-translate-y-1 group";
    card.innerHTML = `<p class="text-[10px] font-bold uppercase tracking-widest text-ink group-hover:text-signal transition-colors">${product.id}</p><h3 class="mt-2 font-semibold text-navy">${product.name}</h3><p class="mt-1 text-sm text-ink line-clamp-2">${product.description}</p><div class="mt-auto flex items-center justify-between pt-4"><span class="font-bold text-navy">${money(product.price_inr)}</span><button class="ask-product rounded-lg border border-line bg-panel px-3 py-1.5 text-xs font-semibold text-navy transition-colors hover:border-signal hover:bg-signal/10 hover:text-signal">Order</button></div>`;
    catalog.appendChild(card);
  });
  $("catalog-status").textContent = `${products.length} items available`;
  document.querySelectorAll(".ask-product").forEach((button) => button.addEventListener("click", () => {
    $("message-input").value = `I'd like to order 1 ${button.dataset.product}.`;
    $("message-input").focus();
  }));
}

async function sendMessage(text) {
  appendMessage("buyer", text);
  $("send-button").disabled = true;
  $("agent-status").innerHTML = `<div class="flex items-center gap-1.5"><div class="flex space-x-1"><div class="w-1.5 h-1.5 bg-signal rounded-full animate-bounce"></div><div class="w-1.5 h-1.5 bg-signal rounded-full animate-bounce" style="animation-delay: 0.1s"></div><div class="w-1.5 h-1.5 bg-signal rounded-full animate-bounce" style="animation-delay: 0.2s"></div></div><span class="text-signal">Agent thinking…</span></div>`;
  try {
    const response = await fetch("/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: state.sessionId, message: text, history: state.history }) });
    if (!response.ok) throw new Error("The agent request failed");
    const payload = await response.json();
    state.history = payload.history;
    appendMessage("agent", payload.reply);
    await refreshEvidence();
  } catch (error) {
    appendMessage("agent", "I couldn’t complete that request. Please check that the AgentGate API is running.");
  } finally {
    $("send-button").disabled = false;
    $("agent-status").innerHTML = "Agent ready";
  }
}

$("session-label").textContent = state.sessionId;
$("chat-form").addEventListener("submit", (event) => { event.preventDefault(); const input = $("message-input"); const text = input.value.trim(); if (!text) return; input.value = ""; sendMessage(text); });
$("refresh-button").addEventListener("click", () => refreshEvidence().catch(() => {}));
Promise.all([loadCatalog(), refreshEvidence()]).catch((error) => { $("catalog-status").textContent = error.message; });
