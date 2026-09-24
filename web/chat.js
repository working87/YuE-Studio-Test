// AI assistant panel: any OpenAI-compatible tool-calling model (Doubao/Ark by default)
// drives the same wizard as the manual form, through /api/assistant/chat.

// ---------- mode switch ----------
function setMode(chat) {
  $("#mode-chat").classList.toggle("active", chat);
  $("#mode-manual").classList.toggle("active", !chat);
  $("#chat").hidden = !chat;
  $("#features").hidden = chat;
  $("#editor").hidden = chat;
  try { localStorage.setItem("mode", chat ? "chat" : "manual"); } catch {}
  if (chat) { loadSettings(); $("#chat-input").focus(); }
}
$("#mode-chat").onclick = () => setMode(true);
$("#mode-manual").onclick = () => setMode(false);

// ---------- chat ----------
let chatSession = "s" + Date.now();
let chatBusy = false;
let chatRecorder = null;

function addMsg(kind, text) {
  const div = document.createElement("div");
  div.className = `msg ${kind}`;
  div.textContent = text;
  $("#chat-log").appendChild(div);
  $("#chat-log").scrollTop = $("#chat-log").scrollHeight;
  return div;
}

async function loadSettings() {
  const s = await api("/api/assistant/settings");
  const f = $("#chat-settings");
  f.base_url.value = s.base_url;
  f.model.value = s.model;
  f.api_key.placeholder = s.has_key ? `已保存 ${s.key_hint}（留空保持不变）` : "粘贴你的 API Key";
  if (!s.has_key || !s.model) f.hidden = false;
  if (!$("#chat-log").children.length) {
    addMsg("bot", "想做点什么？直接说就行，比如：\n· 哼一段旋律，变成一首粤语抒情歌\n· 写一首关于夏天海边的轻快流行歌\n"
      + "· 拿一首歌换成我的歌词 / 换成爵士风\n· 或者说“随便写首歌”，我来定");
    renderStarters();
  }
}

// One-click openers for people without a plan yet; the model takes it from there.
function renderStarters() {
  const box = $("#chat-quick");
  box.innerHTML = "";
  for (const text of ["哼一段变成歌", "用文字写首歌", "改编一首歌", "随便写首歌"]) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip"; b.textContent = text;
    b.onclick = () => sendChat(text);
    box.appendChild(b);
  }
}

$("#chat-settings-btn").onclick = () => { $("#chat-settings").hidden = !$("#chat-settings").hidden; };
$("#chat-settings").onsubmit = async e => {
  e.preventDefault();
  const f = e.target;
  try {
    await api("/api/assistant/settings", { method: "POST",
      body: JSON.stringify({ base_url: f.base_url.value, model: f.model.value, api_key: f.api_key.value || null }) });
    f.api_key.value = "";
    $("#settings-msg").textContent = "已保存";
    setTimeout(() => { f.hidden = true; $("#settings-msg").textContent = ""; }, 700);
    loadSettings();
  } catch (err) { $("#settings-msg").textContent = err.message; }
};

$("#chat-new").onclick = async () => {
  await api("/api/assistant/reset", { method: "POST", body: JSON.stringify({ session: chatSession }) });
  chatSession = "s" + Date.now();
  $("#chat-log").innerHTML = "";
  $("#chat-quick").innerHTML = "";
  loadSettings();
};

// Quick replies mirror the wizard's current question, so a click is one answer.
function renderQuick(q) {
  const box = $("#chat-quick");
  box.innerHTML = "";
  if (!q || q.done) return;
  const chip = (label, text) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip"; b.textContent = label;
    b.onclick = () => sendChat(text);
    box.appendChild(b);
  };
  // Common choices come first; long preset lists show only those, the rest can be typed ("来点爵士").
  for (const o of (q.options || []).slice(0, 8)) chip(o.label, o.label);
  if (q.type === "file") {
    const input = document.createElement("input");
    input.type = "file"; input.accept = q.accept || "audio/*";
    input.onchange = () => input.files[0] && uploadForChat(input.files[0], input.files[0].name);
    const rec = document.createElement("button");
    rec.type = "button"; rec.className = "rec"; rec.textContent = "● 录音";
    rec.onclick = () => recordForChat(rec);
    box.append(input, rec);
  }
  if (q.can_go_back) chip("↩ 上一步", "上一步");
}

async function uploadForChat(blob, name) {
  const fd = new FormData();
  fd.append("file", blob, name);
  const note = addMsg("note", "上传中…");
  try {
    const r = await api("/api/upload", { method: "POST", body: fd });
    note.textContent = `已上传 ${name}`;
    sendChat(`我上传好了音频：${r.path}`);
  } catch (e) { note.textContent = "上传失败：" + e.message; }
}

async function recordForChat(btn) {
  if (chatRecorder) { chatRecorder.stop(); return; }
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
  catch (e) { addMsg("note", "无法使用麦克风：" + e.message); return; }
  const chunks = [];
  chatRecorder = new MediaRecorder(stream);
  chatRecorder.ondataavailable = e => chunks.push(e.data);
  chatRecorder.onstop = () => {
    stream.getTracks().forEach(t => t.stop());
    chatRecorder = null;
    btn.textContent = "● 录音";
    uploadForChat(new Blob(chunks, { type: chunks[0]?.type || "audio/webm" }), "hum.webm");
  };
  chatRecorder.start();
  btn.textContent = "■ 停止录音";
}

async function sendChat(text) {
  text = (text || "").trim();
  if (!text || chatBusy) return;
  chatBusy = true;
  $("#chat-send").disabled = true;
  addMsg("user", text);
  $("#chat-quick").innerHTML = "";
  const wait = addMsg("note", "思考中…");
  try {
    const r = await api("/api/assistant/chat", { method: "POST", body: JSON.stringify({ session: chatSession, message: text }) });
    wait.remove();
    if (r.reply) addMsg("bot", r.reply);
    renderQuick(r.question);
    if (r.tools.some(t => ["submit_song", "provide_lyrics", "cancel_job"].includes(t))) loadJobs();
  } catch (e) {
    wait.textContent = "出错了：" + e.message.replace(/^\d+ /, "");
    if (e.message.includes("设置")) $("#chat-settings").hidden = false;
  }
  chatBusy = false;
  $("#chat-send").disabled = false;
}

$("#chat-form").onsubmit = e => {
  e.preventDefault();
  const t = $("#chat-input").value;
  $("#chat-input").value = "";
  sendChat(t);
};
$("#chat-input").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); $("#chat-form").requestSubmit(); }
});
try { if (localStorage.getItem("mode") === "chat") setMode(true); } catch {}

// ---------- connect an external agent (MCP) ----------
let connectInfo = null;

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch {}
  const ta = document.createElement("textarea");  // WebView fallback
  ta.value = text; document.body.appendChild(ta); ta.select();
  const ok = document.execCommand("copy"); ta.remove();
  return ok;
}

$("#connect-btn").onclick = async () => {
  connectInfo = await api("/api/agent/connect");
  $("#connect-prompt").textContent = connectInfo.prompt;
  $("#connect-url").textContent = connectInfo.url;
  $("#connect-http").textContent = JSON.stringify(connectInfo.http_config, null, 2);
  $("#connect-stdio").textContent = JSON.stringify(connectInfo.stdio_config, null, 2);
  $("#connect-msg").textContent = "";
  $("#connect").showModal();
};
$("#connect-close").onclick = () => $("#connect").close();
document.querySelectorAll("#connect [data-copy]").forEach(btn => {
  btn.onclick = async () => {
    const k = btn.dataset.copy;
    const text = k === "prompt" ? connectInfo.prompt : k === "url" ? connectInfo.url
      : JSON.stringify(k === "http" ? connectInfo.http_config : connectInfo.stdio_config, null, 2);
    const ok = await copyText(text);
    const old = btn.textContent;
    btn.textContent = ok ? "已复制 ✓" : "复制失败";
    setTimeout(() => { btn.textContent = old; }, 1400);
  };
});
