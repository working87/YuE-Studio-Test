// YuE Studio web UI. The form is generated from studio/flow.json, the same
// definition the agent wizard walks, so both expose identical presets.
const $ = (sel, root = document) => root.querySelector(sel);
const api = async (path, opts = {}) => {
  const res = await fetch(path, { headers: opts.body && !(opts.body instanceof FormData) ? { "Content-Type": "application/json" } : {}, ...opts });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
};

let FLOW = null;
let answers = {};
let jobs = [];
let pollTimer = null;

function stepsOf(feature) {
  return ["category", "feature", ...FLOW.features[feature].steps];
}

function stepDef(id) {
  const s = FLOW.steps[id];
  const from = s.options_from ? { options: FLOW.steps[s.options_from].options } : {};
  return { ...s, ...from, ...(FLOW.step_when?.[id] ? { when: FLOW.step_when[id] } : {}) };
}

// Mirrors flow.visible(agent=False).
function visible(id, steps) {
  if (steps.includes("lyrics_source")) {
    if (["lyrics_source", "theme", "structure"].includes(id)) return false;
    if (id === "lyrics") return true;
  }
  const when = stepDef(id).when;
  if (!when) return true;
  const relevant = Object.entries(when).filter(([k]) => steps.includes(k));
  return !relevant.length || relevant.some(([k, allowed]) => allowed.includes(answers[k] ?? null));
}

function optionsOf(id) {
  return (stepDef(id).options || []).filter(o => !o.agent_only && (!o.only || o.only.includes(answers.feature)));
}

// ---------- features nav ----------
function renderNav() {
  const nav = $("#features");
  nav.innerHTML = "";
  for (const cat of FLOW.categories) {
    const group = document.createElement("div");
    group.className = "group";
    group.innerHTML = `<p class="group-label">${cat.label}</p>`;
    for (const [key, f] of Object.entries(FLOW.features)) {
      if (f.category !== cat.value) continue;
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.feature = key;
      b.innerHTML = `${f.label}<small>${f.desc}</small>`;
      b.onclick = () => selectFeature(key);
      group.appendChild(b);
    }
    nav.appendChild(group);
  }
}

function selectFeature(key, preset = {}) {
  const f = FLOW.features[key];
  // 哼唱 → 纯音乐: about half the takes still hum along, and a take is only ~30 s, so default to four to choose from.
  answers = { category: f.category, feature: key, variants: key === "hum_instrumental" ? "4" : "1", vram: "auto", ...preset };
  if (f.steps.includes("language")) answers.language = "auto";  // sung language = the lyrics' language
  if (key === "text_song") answers.plan_mode = "full";
  document.querySelectorAll("nav button").forEach(b => b.classList.toggle("active", b.dataset.feature === key));
  $("#intro").hidden = true;
  $("#form").hidden = false;
  $("#form-title").textContent = f.label;
  $("#form-desc").textContent = f.desc;
  renderFields();
}

// ---------- form fields ----------
function renderFields() {
  const box = $("#fields");
  box.innerHTML = "";
  const steps = stepsOf(answers.feature);
  for (const id of steps.slice(2)) {
    if (!visible(id, steps)) continue;
    const def = stepDef(id);
    const field = document.createElement("div");
    field.className = "field";
    field.innerHTML = `<label>${def.q}</label>`;
    const render = { choice: choiceField, file: fileField, text: textField, lyrics: lyricsField,
                     number: numberField, job: jobField, abc: abcField }[def.type];
    render(field, id, def);
    box.appendChild(field);
  }
  updatePreview();
}

function set(id, value, rerender = false) {
  if (value === "" || value == null) delete answers[id]; else answers[id] = value;
  rerender ? renderFields() : updatePreview();
}

// Pinned options are chips; the rest go into a dropdown (grouped when options carry a group).
function choiceField(field, id, def) {
  const chips = document.createElement("div");
  chips.className = "chips";
  const opts = optionsOf(id);
  const known = opts.some(o => o.value === answers[id]);
  const pinned = opts.some(o => o.pin) ? opts.filter(o => o.pin) : opts;
  const rest = opts.filter(o => !pinned.includes(o));
  for (const o of pinned) {
    const c = document.createElement("button");
    c.type = "button";
    c.className = "chip";
    c.setAttribute("aria-pressed", answers[id] === o.value);
    c.title = o.desc || "";
    c.innerHTML = o.label + (o.desc ? `<small>${o.desc}</small>` : "");
    c.onclick = () => set(id, answers[id] === o.value ? null : o.value, true);
    chips.appendChild(c);
  }
  field.appendChild(chips);
  if (rest.length) {
    const sel = document.createElement("select");
    sel.className = "more-select";
    const inRest = rest.some(o => o.value === answers[id]);
    sel.classList.toggle("active", inRest);
    sel.add(new Option(`更多选项（${rest.length}）…`, ""));
    const groups = new Map();
    for (const o of rest) {
      const g = o.group || "";
      if (!groups.has(g)) groups.set(g, []);
      groups.get(g).push(o);
    }
    for (const [g, list] of groups) {
      const parent = g ? Object.assign(document.createElement("optgroup"), { label: g }) : sel;
      for (const o of list) parent.appendChild(new Option(o.label + (o.desc ? ` — ${o.desc}` : ""), o.value));
      if (g) sel.appendChild(parent);
    }
    sel.value = inRest ? answers[id] : "";
    sel.onchange = () => set(id, sel.value || null, true);
    field.appendChild(sel);
  }
  if (def.custom) {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "custom-input";
    input.placeholder = "或自己写，例如：synthwave, 80s drum machine";
    if (answers[id] && !known) input.value = answers[id];
    input.oninput = () => {
      chips.querySelectorAll(".chip").forEach(c => c.setAttribute("aria-pressed", "false"));
      const sel = field.querySelector(".more-select");
      if (sel) { sel.value = ""; sel.classList.remove("active"); }
      set(id, input.value.trim());
    };
    field.appendChild(input);
  }
}

function textField(field, id) {
  const input = document.createElement("input");
  input.type = "text";
  input.value = answers[id] || "";
  input.oninput = () => set(id, input.value.trim());
  field.appendChild(input);
}

function numberField(field, id, def) {
  const input = document.createElement("input");
  input.type = "number";
  input.min = def.min; input.max = def.max;
  input.value = answers[id] || "";
  input.oninput = () => set(id, input.value ? Number(input.value) : null);
  field.appendChild(input);
}

function lyricsField(field, id) {
  const bar = document.createElement("div");
  bar.className = "tagbar";
  const area = document.createElement("textarea");
  area.rows = 10;
  area.placeholder = "[Verse]\n晚风轻轻吹过窗前\n你留下的笑还在昨天\n\n[Chorus]\n让这首歌陪你走远";
  area.value = answers[id] || "";
  for (const tag of ["Verse", "Pre-Chorus", "Chorus", "Bridge", "Outro"]) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "ghost"; b.textContent = `[${tag}]`;
    b.onclick = () => { area.setRangeText(`\n[${tag}]\n`, area.selectionStart, area.selectionEnd, "end"); area.focus(); set(id, area.value); };
    bar.appendChild(b);
  }
  area.oninput = () => set(id, area.value.trim());
  field.append(bar, area);
  const transcribed = FLOW.features[answers.feature].pipeline.transcribe;
  {
    const hint = document.createElement("p");
    hint.className = "muted";
    hint.textContent = id === "orig_lyrics"
      ? "按原曲旋律演唱原词，长度跟随原曲。从剪辑软件复制的字幕（含 SRT/LRC 时间码）可以直接粘贴。"
      : transcribed
        ? (answers.feature === "cover" ? "粘贴原曲歌词就按原词唱（可以直接粘字幕，含 SRT/LRC 时间码），写新词就是换词。" : "")
        + "也可以留空：先扒谱，完成后右侧会显示每句的音符数，再按音符数填词。歌曲长度跟随原曲/哼唱。"
        : "歌曲长度由歌词决定：实测大约每 4 句 25~35 秒。想要 1 分钟左右就写一段主歌加一段副歌。";
    field.appendChild(hint);
  }
}

function fileField(field, id, def) {
  const row = document.createElement("div");
  row.className = "row";
  const input = document.createElement("input");
  input.type = "file";
  input.accept = def.accept || "audio/*";
  const rec = document.createElement("button");
  rec.type = "button"; rec.className = "rec"; rec.textContent = "● 录音";
  const metro = document.createElement("label");
  metro.className = "muted";
  metro.innerHTML = `<input type="checkbox"> 节拍器 <input type="number" value="90" min="40" max="200" style="width:64px"> BPM（戴耳机）`;
  const status = document.createElement("div");
  status.className = "muted";
  const player = document.createElement("audio");
  player.controls = true; player.hidden = true;
  if (answers[id]) { status.textContent = `已上传：${answers[id]}`; }
  row.append(input, id === "hum_audio" ? rec : "", id === "hum_audio" ? metro : "");
  field.append(row, player, status);

  const send = async (blob, name) => {
    status.textContent = "上传中…";
    const fd = new FormData();
    fd.append("file", blob, name);
    try {
      const r = await api("/api/upload", { method: "POST", body: fd });
      player.src = URL.createObjectURL(blob); player.hidden = false;
      status.textContent = `已上传：${name}`;
      set(id, r.path);
    } catch (e) { status.textContent = `上传失败：${e.message}`; }
  };
  input.onchange = () => input.files[0] && send(input.files[0], input.files[0].name);

  let recorder = null, clickTimer = null, ctx = null;
  rec.onclick = async () => {
    if (recorder) { recorder.stop(); return; }
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch (e) { status.textContent = "无法使用麦克风：" + e.message; return; }
    const chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      clearInterval(clickTimer); ctx && ctx.close();
      recorder = null; rec.textContent = "● 录音";
      send(new Blob(chunks, { type: chunks[0]?.type || "audio/webm" }), "hum.webm");
    };
    const [on, bpm] = metro.querySelectorAll("input");
    if (on.checked) {
      ctx = new AudioContext();
      const tick = () => { const o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = 1200; g.gain.setValueAtTime(.3, ctx.currentTime); g.gain.exponentialRampToValueAtTime(.001, ctx.currentTime + .05);
        o.connect(g).connect(ctx.destination); o.start(); o.stop(ctx.currentTime + .06); };
      tick(); clickTimer = setInterval(tick, 60000 / Number(bpm.value || 90));
    }
    recorder.start();
    const t0 = Date.now();
    rec.textContent = "■ 停止";
    const show = setInterval(() => recorder ? (status.textContent = `录音中 ${((Date.now() - t0) / 1000).toFixed(0)} 秒…（建议 15–60 秒）`) : clearInterval(show), 500);
  };
}

function jobField(field, id) {
  const sel = document.createElement("select");
  const usable = jobs.filter(j => j.status === "done" && (j.takes || []).some(t => t.score));
  sel.innerHTML = `<option value="">选择一首已完成且有乐谱的作品</option>` +
    usable.map(j => `<option value="${j.id}">${j.title} · ${j.id}</option>`).join("");
  sel.value = answers[id] || "";
  sel.onchange = () => { set(id, sel.value, true); };
  field.appendChild(sel);
}

function abcField(field, id) {
  const area = document.createElement("textarea");
  area.rows = 14;
  const view = document.createElement("div");
  view.className = "score";
  const draw = () => renderScore(view, area.value);
  area.oninput = () => { set(id, area.value); draw(); };
  field.append(area, view);
  if (answers[id]) { area.value = answers[id]; draw(); return; }
  const base = jobs.find(j => j.id === answers.base_job);
  const take = base && (base.takes || []).find(t => t.score);
  if (take) fetch(`/files/${base.id}/${take.score}`).then(r => r.text()).then(t => { area.value = t; set(id, t); draw(); });
  else area.placeholder = "先在上面选择要精修的作品";
}

async function updatePreview() {
  try {
    const r = await api("/api/preview", { method: "POST", body: JSON.stringify({ answers }) });
    $("#style-preview").textContent = r.spec ? (r.spec.style || "(沿用原作品风格)") : "—";
    const names = r.missing.map(s => FLOW.steps[s].q.replace(/[（(].*$/, "").replace(/？$/, ""));
    const mismatch = r.spec?.language_mismatch;
    $("#missing").textContent = r.missing.length ? `还差：${names.join("、")}` : mismatch ? "" : "参数齐了";
    $("#submit").disabled = r.missing.length > 0 || !!mismatch;
    renderLanguageNote(r, mismatch);
  } catch (e) { $("#missing").textContent = e.message; }
}

const LANG_NAME = { zh: "中文", yue: "粤语", en: "英语", ja: "日语", ko: "韩语" };

// Shows which language the lyrics are in; on a mismatch, blocks submit and offers an AI translation.
function renderLanguageNote(r, mismatch) {
  const box = $("#lang-note");
  box.innerHTML = "";
  if (r.lyrics_language_name && !mismatch) box.textContent = `歌词语言：${r.lyrics_language_name}（会按${r.lyrics_language_name}演唱）`;
  if (!mismatch) return;
  box.innerHTML = `<span class="error">歌词是${LANG_NAME[mismatch.lyrics]}，但选了用${LANG_NAME[mismatch.chosen]}唱。模型唱的就是歌词本身，两者必须一致。</span> `;
  if (r.can_translate) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "ghost"; b.textContent = `用 AI 把歌词翻译成${LANG_NAME[mismatch.chosen]}`;
    b.onclick = async () => {
      b.disabled = true; b.textContent = "翻译中…";
      try {
        const key = answers.orig_lyrics ? "orig_lyrics" : "lyrics";
        const t = await api("/api/translate_lyrics", { method: "POST", body: JSON.stringify({ lyrics: answers[key], language: mismatch.chosen }) });
        answers[key] = t.lyrics;
        renderFields();  // textarea shows the translation for review
      } catch (e) { b.disabled = false; b.textContent = "翻译失败：" + e.message.replace(/^\d+ /, ""); }
    };
    box.appendChild(b);
  } else {
    box.insertAdjacentHTML("beforeend", `<span class="muted">可以改选「跟随歌词」，或粘贴${LANG_NAME[mismatch.chosen]}歌词；在「AI 助手 → 设置」配好模型后这里能一键翻译。</span>`);
  }
}

$("#form").onsubmit = async e => {
  e.preventDefault();
  $("#submit").disabled = true;
  try {
    const job = await api("/api/jobs", { method: "POST", body: JSON.stringify({ answers }) });
    await loadJobs();
    location.hash = `job=${job.id}`;
  } catch (err) { $("#missing").textContent = err.message; }
  $("#submit").disabled = false;
};

// ---------- score display ----------
// Draw in the theme's ink colour on the card background, with Chinese part names; an instrument part that
// only rests is hidden so the melody reads as a single staff.
function displayAbc(abc) {
  const lines = abc.split(/\r?\n/);
  const insHasNotes = (() => {
    let voice = null;
    for (const l of lines) {
      const m = l.trim().match(/^V:\s*(Vocal|Ins)\s*$/);
      if (m) { voice = m[1]; continue; }
      if (voice === "Ins" && !l.trim().startsWith("%") && /[A-Ga-g]/.test(l.replace(/"[^"]*"/g, ""))) return true;
    }
    return false;
  })();
  const out = [];
  let voice = null;
  for (const l of lines) {
    const t = l.trim();
    const m = t.match(/^V:\s*(Vocal|Ins)\s*$/);
    if (m) voice = m[1];
    else if (t.startsWith("%")) voice = null;
    if (!insHasNotes && (voice === "Ins" || /^V:\s*Ins\b/.test(t))) continue;
    out.push(l.replace(/name="Vocal Melody" snm="Vocal"/, 'name="旋律" snm="旋律"')
              .replace(/name="Ins Melody" snm="Inst\."/, 'name="器乐" snm="器乐"'));
  }
  return out.join("\n");
}

function renderScore(el, abc) {
  if (!window.ABCJS || !abc) return;
  const ink = getComputedStyle(document.documentElement).getPropertyValue("--ink").trim() || "#1d1d1f";
  ABCJS.renderAbc(el, displayAbc(abc), {
    responsive: "resize", foregroundColor: ink, scale: 0.85,
    paddingtop: 4, paddingbottom: 4, paddingleft: 4, paddingright: 4,
  });
}

// ---------- jobs ----------
const STATUS = { queued: "排队", running: "生成中", needs_lyrics: "等歌词", done: "完成", failed: "失败", cancelled: "已取消" };

// Cards are kept between polls and only rebuilt when their content changes, so audio that is
// playing, an open score or lyrics being typed are never interrupted. Running jobs only get
// their progress bar and log updated in place.
const cards = new Map();  // job id -> { el, sig }
let loading = false;

function signature(j) {
  const takes = (j.takes || []).map(t => t.audio || t.failure?.reason || "").join(",");
  return [j.status, j.title, j.error || "", takes, j.status === "running" ? "" : j.stage].join("|");
}

async function loadJobs() {
  if (loading) return;
  loading = true;
  clearTimeout(pollTimer);
  try {
    jobs = await api("/api/jobs");
    const box = $("#jobs");
    $(".no-jobs", box)?.remove();
    if (!jobs.length) box.insertAdjacentHTML("afterbegin", `<p class="muted no-jobs">还没有作品。</p>`);
    const seen = new Set();
    let prev = null;
    for (const j of jobs) {
      seen.add(j.id);
      let card = cards.get(j.id);
      const sig = signature(j);
      const playing = card && [...card.el.querySelectorAll("audio")].some(a => !a.paused);
      if (!card || (card.sig !== sig && !playing)) {
        const el = await renderJob(j);
        if (card) card.el.replaceWith(el);
        card = { el, sig };
        cards.set(j.id, card);
      } else if (j.status === "running") {
        updateLive(card.el, await api(`/api/jobs/${j.id}`));
      }
      const anchor = prev ? prev.nextElementSibling : box.firstElementChild;
      if (card.el !== anchor) box.insertBefore(card.el, anchor);
      prev = card.el;
    }
    for (const [id, card] of cards) if (!seen.has(id)) { card.el.remove(); cards.delete(id); }
  } finally {
    loading = false;
  }
  if (jobs.some(j => ["queued", "running"].includes(j.status))) pollTimer = setTimeout(loadJobs, 3000);
}

function fmtTime(sec) {
  sec = Math.max(0, Math.round(sec));
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

// Progress bar, step chips, elapsed time and log for a running job, updated in place.
function updateLive(el, j) {
  const box = $(".progress", el);
  const p = j.progress;
  $(".job-stage", el).textContent = j.stage || "";
  if (j.log_tail) {
    const log = $(".log", el);
    const atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 4;
    log.textContent = j.log_tail.join("\n");
    if (atBottom) log.scrollTop = log.scrollHeight;
  }
  if (!p) { box.hidden = true; return; }
  box.hidden = false;
  $(".steps", box).innerHTML = p.labels.map((label, i) => {
    const state = i + 1 < p.step ? "done" : i + 1 === p.step ? "now" : "";
    return `<span class="step ${state}">${state === "done" ? "✓ " : ""}${label}</span>`;
  }).join("");
  const fill = $(".fill", box);
  fill.classList.toggle("indeterminate", p.percent == null);
  fill.style.width = p.percent == null ? "" : `${p.percent}%`;
  const elapsed = j.started ? ` · 已用时 ${fmtTime(Date.now() / 1000 - j.started)}` : "";
  $(".progress-text", box).textContent =
    `${p.take ? p.take + " · " : ""}${p.phase}${p.percent != null ? " " + p.percent + "%" : ""}${p.detail ? " · " + p.detail : ""}${elapsed}`;
}

async function renderJob(summary) {
  const j = ["running", "needs_lyrics", "failed"].includes(summary.status) || summary.takes?.length
    ? await api(`/api/jobs/${summary.id}`) : summary;
  const el = $("#tpl-job").content.firstElementChild.cloneNode(true);
  el.id = `job-${j.id}`;
  if (j.status === "running") setTimeout(() => updateLive(el, j));
  $(".job-title", el).textContent = j.title;
  const pill = $(".pill", el);
  pill.textContent = STATUS[j.status] || j.status;
  pill.classList.add(j.status);
  $(".job-meta", el).textContent = `${j.id}${j.final_style ? " · " + j.final_style : ""}`;
  const total = j.started && j.finished ? ` · 总用时 ${fmtTime(j.finished - j.started)}` : "";
  $(".job-stage", el).innerHTML = j.error ? `<span class="error">${j.error}</span>` : (j.stage || "") + total;
  for (const t of j.takes || []) {
    const div = document.createElement("div");
    if (t.audio) {
      const timing = [t.audio_seconds != null && `时长 ${fmtTime(t.audio_seconds)}`,
                      t.generation_seconds != null && `生成 ${fmtTime(t.generation_seconds)}`].filter(Boolean).join(" · ");
      div.innerHTML = `<div class="take-label"><span>${t.name} · seed ${t.seed}${timing ? " · " + timing : ""}</span><a href="/files/${j.id}/${t.audio}" download>下载 FLAC</a></div><audio controls preload="none" src="/files/${j.id}/${t.audio}"></audio>`;
      if (t.truncated) div.insertAdjacentHTML("beforeend", `<div class="muted">⚠ 到达长度上限被截断，结尾可能不完整</div>`);
      if (t.post?.length) div.insertAdjacentHTML("beforeend", `<div class="muted">乐谱调整：${t.post.join("；")}</div>`);
      if (window.pywebview) {  // desktop app: reveal the file in Explorer instead of a browser download
        const a = $("a", div);
        a.textContent = "在文件夹中显示";
        a.removeAttribute("download");
        a.onclick = e => { e.preventDefault(); window.pywebview.api.open_folder(j.id, t.audio); };
      }
    } else if (t.failure) {
      div.innerHTML = `<div class="error">${t.name} 失败：${t.failure.reason}</div>`;
    }
    $(".takes", el).appendChild(div);
  }
  if (j.score && window.ABCJS) {
    $(".score-box", el).hidden = false;
    $(".score-box", el).addEventListener("toggle", () => renderScore($(".score", el), j.score), { once: true });
  }
  if (j.log_tail) $(".log", el).textContent = j.log_tail.join("\n");
  if (j.status === "needs_lyrics") {
    const box = $(".lyrics-needed", el);
    box.hidden = false;
    const sections = j.phrases?.sections || [];
    $(".phrases", el).innerHTML = sections.map(s =>
      `<tr><td>${s.section}</td><td>${s.lines.length} 句</td><td class="muted">每句字数约 ${s.lines.map(l => l.notes).join(" / ")}</td></tr>`).join("");
    // Template mirrors the transcribed melody: one tag per section, one line per phrase with its note count.
    const tag = name => "[" + name.replace(/(^|[-\s])\w/g, c => c.toUpperCase()) + "]";
    $("textarea", box).placeholder = sections.map(s =>
      [tag(s.section), ...s.lines.map((l, i) => `第 ${i + 1} 句（约 ${l.notes} 个字）`)].join("\n")).join("\n\n");
    $(".send-lyrics", el).onclick = async () => {
      try {
        await api(`/api/jobs/${j.id}/lyrics`, { method: "POST", body: JSON.stringify({ lyrics: $("textarea", box).value }) });
        loadJobs();
      } catch (e) {
        box.querySelector(".lyrics-error")?.remove();
        box.insertAdjacentHTML("beforeend", `<p class="error lyrics-error">${e.message.replace(/^\d+ /, "").replace(/^\{"detail":"|"\}$/g, "")}</p>`);
      }
    };
  }
  $(".remix", el).hidden = !(j.status === "done" && (j.takes || []).some(t => t.score));
  $(".remix", el).onclick = () => { selectFeature("remix", { base_job: j.id }); window.scrollTo({ top: 0, behavior: "smooth" }); };
  $(".cancel", el).hidden = !["queued", "running"].includes(j.status);
  $(".cancel", el).onclick = async () => { await api(`/api/jobs/${j.id}/cancel`, { method: "POST" }); loadJobs(); };
  return el;
}

$("#refresh").onclick = loadJobs;
window.addEventListener("hashchange", () => {
  const id = location.hash.match(/job=([\w-]+)/)?.[1];
  id && document.getElementById(`job-${id}`)?.scrollIntoView({ behavior: "smooth" });
});

// The only memory setting: the app picks the best profile for the GPU, the user just chooses speed vs. memory.
function renderVramMode(sys) {
  const box = $("#vram-mode");
  box.hidden = !sys.gpu || sys.gpu.memory_gib < 15;  // smaller cards have a single (memory-saving) profile
  box.innerHTML = "";
  for (const [mode, label] of Object.entries(sys.vram_modes)) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.classList.toggle("active", sys.vram_mode === mode);
    b.onclick = async () => renderVramMode(await api("/api/vram_mode", { method: "POST", body: JSON.stringify({ mode }) }));
    box.appendChild(b);
  }
}

// ---------- boot ----------
(async () => {
  FLOW = await api("/api/flow");
  renderNav();
  const sys = await api("/api/system");
  $("#gpu").textContent = sys.gpu ? `${sys.gpu.name} · ${sys.gpu.memory_gib} GB` : "未检测到 NVIDIA 显卡";
  renderVramMode(sys);
  const missing = Object.entries(sys.ready).filter(([, ok]) => !ok).map(([k]) => k);
  if (missing.length) { $("#ready").hidden = false; $("#ready").textContent = `未就绪：${missing.join(", ")}（见 README 安装步骤）`; }
  await loadJobs();
  window.dispatchEvent(new HashChangeEvent("hashchange"));
})();
