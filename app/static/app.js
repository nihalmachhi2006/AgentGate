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
    ? "ml-auto max-w-md rounded-xl rounded-tr-sm bg-blue-500 px-4 py-3 text-sm leading-6 text-slate-950"
    : "max-w-md rounded-xl rounded-tl-sm border border-line bg-[#0c1421] px-4 py-3 text-sm leading-6 text-slate-300";
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function showVerdict(entry) {
  const card = $("verdict-card");
  if (!entry) return;
  const allowed = Boolean(entry.allowed);
  card.className = `rounded-lg border p-4 ${allowed ? "border-emerald-800 bg-emerald-950/40" : "border-amber-800 bg-amber-950/30"}`;
  $("verdict-title").textContent = allowed ? "Allowed — sent to Razorpay" : "Blocked by AgentGate";
  $("verdict-title").className = `mt-1 text-lg font-bold ${allowed ? "text-emerald-300" : "text-amber-300"}`;
  $("verdict-reason").textContent = entry.reason;
  $("verdict-reason").className = `mt-1 text-sm leading-5 ${allowed ? "text-emerald-200" : "text-amber-200"}`;
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
    row.className = "grid grid-cols-[52px_62px_1fr] gap-2 py-3 text-xs";
    row.innerHTML = `<span class="text-slate-400">${time}</span><span class="font-semibold ${entry.allowed ? "text-emerald-300" : "text-amber-300"}">${entry.allowed ? "ALLOW" : "BLOCK"}</span><span class="leading-5 text-slate-200">${entry.product_id || entry.action}</span>`;
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
    card.className = "flex min-h-40 flex-col rounded-lg border border-line bg-[#0c1421] p-4 transition hover:border-signal";
    card.innerHTML = `<p class="text-xs font-medium text-signal">${product.id}</p><h3 class="mt-2 font-semibold text-navy">${product.name}</h3><p class="mt-1 text-sm text-slate-400">${product.description}</p><div class="mt-auto flex items-center justify-between pt-4"><span class="font-bold text-navy">${money(product.price_inr)}</span><button class="ask-product rounded-md border border-line px-2.5 py-1.5 text-xs font-semibold text-slate-300 hover:border-signal hover:text-white" data-product="${product.name}">Order</button></div>`;
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
  $("agent-status").textContent = "Agent thinking…";
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
    $("agent-status").textContent = "Agent ready";
  }
}

$("session-label").textContent = state.sessionId;
$("chat-form").addEventListener("submit", (event) => { event.preventDefault(); const input = $("message-input"); const text = input.value.trim(); if (!text) return; input.value = ""; sendMessage(text); });
$("refresh-button").addEventListener("click", () => refreshEvidence().catch(() => {}));
Promise.all([loadCatalog(), refreshEvidence()]).catch((error) => { $("catalog-status").textContent = error.message; });
