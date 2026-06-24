/* ============================================================================
   CHAD WIDGET — a floating, voice-first Chad that follows users page to page.
   JARVIS-style Hancock-blue orb in the corner; click it to chat/talk; he greets,
   briefs the team, and speaks back. Talks to Chad's brain (chad_server.py).

   EMBED on every page of the site (one line, before </body>):
     <script>window.CHAD_CONFIG={apiBase:"https://your-brain-url",user:"Cassie"};</script>
     <script src="chad-widget.js"></script>
   - apiBase: Chad's authenticated server URL (empty means this same site)
   - user:    the logged-in person's name (so briefings + greetings are personal).
              Omit it and the widget asks once.

   FOR A FULL "CHAD" TAB: just call  ChadWidget.open()  when that tab is shown
   (the same panel works as a docked section), or embed the widget and let the
   floating orb be the entry point on every page.
   ============================================================================ */
(function () {
  if (window.__chadWidgetLoaded) return; window.__chadWidgetLoaded = true;
  var CFG = window.CHAD_CONFIG || {};
  var API = (CFG.apiBase || "").replace(/\/$/, "");
  var USER = CFG.user || localStorage.getItem("chad_widget_user") || null;
  var muted = localStorage.getItem("chad_widget_mute") === "1";
  var greeted = false;

  /* ---------- styles ---------- */
  var css = ''
    + '#chadw{position:fixed;right:22px;bottom:22px;z-index:2147483000;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}'
    + '#chadw *{box-sizing:border-box}'
    + '#chadw .cw-orbwrap{display:flex;flex-direction:column;align-items:center;gap:5px;cursor:pointer}'
    + '#chadw .cw-lbl{font-size:9px;font-weight:800;letter-spacing:2.5px;color:#4f93e0;text-transform:uppercase;text-shadow:0 0 9px rgba(79,147,224,.6)}'
    + '#chadw .cw-lbl b{color:#fff}'
    + '#chadw svg{width:96px;height:96px;display:block;filter:drop-shadow(0 0 12px rgba(47,111,191,.5))}'
    + '#chadw .cw-spin1{transform-box:fill-box;transform-origin:center;animation:cwspin 26s linear infinite}'
    + '#chadw .cw-spin2{transform-box:fill-box;transform-origin:center;animation:cwspin 12s linear infinite reverse}'
    + '#chadw .cw-spin3{transform-box:fill-box;transform-origin:center;animation:cwspin 9s linear infinite}'
    + '@keyframes cwspin{to{transform:rotate(360deg)}}'
    + '#chadw #cwCore{transform-box:fill-box;transform-origin:center;transition:transform .07s linear}'
    + '#chadw .cw-panel{position:absolute;right:0;bottom:120px;width:340px;max-width:88vw;height:460px;max-height:72vh;'
    + 'background:linear-gradient(180deg,#0d2c4a,#0a2236);border:1px solid rgba(79,147,224,.35);border-radius:16px;'
    + 'box-shadow:0 24px 70px rgba(4,12,22,.6);display:none;flex-direction:column;overflow:hidden}'
    + '#chadw.cw-open .cw-panel{display:flex;animation:cwrise .22s ease both}'
    + '@keyframes cwrise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}'
    + '#chadw .cw-head{display:flex;align-items:center;justify-content:space-between;padding:11px 13px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(79,147,224,.25)}'
    + '#chadw .cw-head .t{font-size:13.5px;font-weight:800;color:#eaf2fb}#chadw .cw-head .t span{color:#4f93e0;font-size:10px;font-weight:700;letter-spacing:1px}'
    + '#chadw .cw-x{background:none;border:none;color:#9fb4c9;font-size:18px;cursor:pointer;line-height:1}'
    + '#chadw .cw-brief{font-size:12px;color:#bcd2ea;padding:10px 13px;border-bottom:1px solid rgba(79,147,224,.18);line-height:1.5;background:rgba(47,111,191,.08)}'
    + '#chadw .cw-msgs{flex:1;overflow-y:auto;padding:12px 12px 4px;display:flex;flex-direction:column;gap:8px}'
    + '#chadw .cw-m{max-width:85%;padding:9px 12px;border-radius:13px;font-size:13px;line-height:1.5;animation:cwrise .2s ease both}'
    + '#chadw .cw-m.chad{align-self:flex-start;background:rgba(47,111,191,.22);border:1px solid rgba(79,147,224,.4);color:#eaf2fb;border-bottom-left-radius:4px}'
    + '#chadw .cw-m.me{align-self:flex-end;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);color:#fff;border-bottom-right-radius:4px}'
    + '#chadw .cw-chips{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 8px}'
    + '#chadw .cw-chip{background:rgba(255,255,255,.07);border:1px solid rgba(79,147,224,.4);color:#dbeafe;font-size:11.5px;font-weight:700;padding:6px 10px;border-radius:16px;cursor:pointer}'
    + '#chadw .cw-chip:hover{background:#2f6fbf;color:#fff}'
    + '#chadw .cw-comp{display:flex;gap:7px;padding:10px 12px;border-top:1px solid rgba(79,147,224,.2);align-items:center}'
    + '#chadw .cw-comp input{flex:1;padding:10px 12px;border-radius:11px;border:1px solid rgba(79,147,224,.3);background:rgba(255,255,255,.06);color:#fff;font-size:13px}'
    + '#chadw .cw-comp input::placeholder{color:#8da6bf}'
    + '#chadw .cw-mic,#chadw .cw-send{flex:none;width:40px;height:40px;border-radius:11px;border:none;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}'
    + '#chadw .cw-mic{background:rgba(255,255,255,.08);border:1px solid rgba(79,147,224,.3);color:#dbeafe}#chadw .cw-mic.on{background:#c0392b;color:#fff}'
    + '#chadw .cw-send{background:#2f6fbf;color:#fff}#chadw .cw-send:hover{background:#4f93e0}'
    + '#chadw .cw-pick{padding:14px 13px;color:#cfe0f2;font-size:13px}#chadw .cw-pick b{color:#fff}'
    + '#chadw .cw-pick .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}'
    + '#chadw .cw-pick button{background:rgba(47,111,191,.2);border:1px solid rgba(79,147,224,.5);color:#eaf2fb;font-weight:700;font-size:13px;padding:9px 14px;border-radius:10px;cursor:pointer}'
    + '#chadw .cw-pick button:hover{background:#2f6fbf;color:#fff}';
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  /* ---------- markup ---------- */
  var root = document.createElement("div"); root.id = "chadw";
  root.innerHTML =
    '<div class="cw-panel">'
    + '<div class="cw-head"><div class="t">Chad <span id="cwState">ONLINE</span></div>'
    + '<div><button class="cw-x" id="cwMute" title="Mute">' + (muted ? '&#128263;' : '&#128266;') + '</button> '
    + '<button class="cw-x" id="cwClose" title="Close">&#10005;</button></div></div>'
    + '<div class="cw-brief" id="cwBrief" style="display:none"></div>'
    + '<div class="cw-msgs" id="cwMsgs"></div>'
    + '<div class="cw-chips"><button class="cw-chip" data-q="catch me up">Catch me up</button>'
    + '<button class="cw-chip" data-q="prepare the suggested post">Prepare suggested post</button>'
    + '<button class="cw-chip" data-q="run the studio">Run the studio</button></div>'
    + '<div class="cw-comp"><input id="cwInput" placeholder="Talk to Chad…"><button class="cw-mic" id="cwMic" title="Speak">&#127908;</button><button class="cw-send" id="cwSend">&#10148;</button></div>'
    + '</div>'
    + '<div class="cw-orbwrap" id="cwOrbWrap"><div class="cw-lbl"><b>CHAD</b></div>'
    + '<svg id="cwSvg" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"></svg></div>';
  document.body.appendChild(root);

  /* ---------- orb (JARVIS-style, Hancock blue) ---------- */
  var NS = "http://www.w3.org/2000/svg", svg = root.querySelector("#cwSvg"), C = 100, B = "#2f6fbf", B2 = "#4f93e0", G = "#8fc1ff";
  function e(t, a) { var x = document.createElementNS(NS, t); for (var k in a) x.setAttribute(k, a[k]); return x; }
  var defs = e("defs", {});
  defs.innerHTML = '<radialGradient id="cwCoreG" cx="38%" cy="32%" r="75%"><stop offset="0%" stop-color="#bfe0ff"/><stop offset="45%" stop-color="' + B2 + '"/><stop offset="100%" stop-color="#123a63"/></radialGradient><radialGradient id="cwHalo" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="' + B + '" stop-opacity=".4"/><stop offset="100%" stop-color="' + B + '" stop-opacity="0"/></radialGradient>';
  svg.appendChild(defs);
  svg.appendChild(e("circle", { cx: C, cy: C, r: 96, fill: "url(#cwHalo)" }));
  var g1 = e("g", { class: "cw-spin1" });
  g1.appendChild(e("circle", { cx: C, cy: C, r: 90, fill: "none", stroke: B2, "stroke-width": "1", "stroke-opacity": ".5", "stroke-dasharray": "2 7" }));
  svg.appendChild(g1);
  var gt = e("g", { class: "cw-spin2" });
  for (var i = 0; i < 72; i++) { var a = i * 5 * Math.PI / 180, lg = (i % 6 === 0), r1 = 78, r2 = lg ? 68 : 73; gt.appendChild(e("line", { x1: C + r1 * Math.cos(a), y1: C + r1 * Math.sin(a), x2: C + r2 * Math.cos(a), y2: C + r2 * Math.sin(a), stroke: B2, "stroke-width": lg ? "1.6" : "0.9", "stroke-opacity": lg ? ".8" : ".4" })); }
  svg.appendChild(gt);
  var g3 = e("g", { class: "cw-spin3" });
  g3.appendChild(e("circle", { cx: C, cy: C, r: 56, fill: "none", stroke: B, "stroke-width": "1.3", "stroke-opacity": ".55", "stroke-dasharray": "22 10" }));
  for (var j = 0; j < 3; j++) { var aa = j * 120 * Math.PI / 180; g3.appendChild(e("circle", { cx: C + 56 * Math.cos(aa), cy: C + 56 * Math.sin(aa), r: 2.6, fill: G })); }
  svg.appendChild(g3);
  var core = e("g", { id: "cwCore" });
  core.appendChild(e("circle", { cx: C, cy: C, r: 40, fill: "url(#cwCoreG)" }));
  var clip = e("clipPath", { id: "cwClip" }); clip.appendChild(e("circle", { cx: C, cy: C, r: 40 })); defs.appendChild(clip);
  var mesh = e("g", { "clip-path": "url(#cwClip)", stroke: G, "stroke-width": "0.7", "stroke-opacity": ".42", fill: "none" });
  for (var k = 1; k <= 4; k++) { mesh.appendChild(e("ellipse", { cx: C, cy: C, rx: 40, ry: k * 9 })); mesh.appendChild(e("ellipse", { cx: C, cy: C, rx: k * 9, ry: 40 })); }
  mesh.appendChild(e("line", { x1: C - 40, y1: C, x2: C + 40, y2: C })); mesh.appendChild(e("line", { x1: C, y1: C - 40, x2: C, y2: C + 40 }));
  core.appendChild(mesh);
  core.appendChild(e("circle", { cx: C, cy: C, r: 40, fill: "none", stroke: G, "stroke-width": "1.3", "stroke-opacity": ".8" }));
  svg.appendChild(core);

  /* ---------- refs + state ---------- */
  var msgs = root.querySelector("#cwMsgs"), brief = root.querySelector("#cwBrief"), input = root.querySelector("#cwInput"),
    stateEl = root.querySelector("#cwState"), coreEl = root.querySelector("#cwCore");
  var actx = null, analyser = null, freq = null, raf = null, curAudio = null;

  function setState(s) { stateEl.textContent = s; }
  function bubble(t, who) { var d = document.createElement("div"); d.className = "cw-m " + who; d.innerHTML = t; msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; }
  function esc(s) { return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  /* ---------- voice (audio-reactive orb) ---------- */
  function speak(text) {
    if (muted) return;
    fetch(API + "/api/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: text.replace(/<[^>]+>/g, "") }) })
      .then(function (r) { if (!r.ok) throw new Error("ElevenLabs unavailable"); return r.blob(); })
      .then(function (b) {
        var url = URL.createObjectURL(b); if (curAudio) { try { curAudio.pause(); } catch (e) {} }
        var au = new Audio(url); curAudio = au; setState("SPEAKING");
        au.onended = function () { vizStop(); URL.revokeObjectURL(url); };
        au.play().then(function () { vizStart(au); }).catch(function () { setState("TAP TO HEAR"); });
      }).catch(function () { setState("VOICE UNAVAILABLE"); });
  }
  function vizStart(au) {
    try {
      if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)(); if (actx.state === "suspended") actx.resume();
      if (!analyser) { analyser = actx.createAnalyser(); analyser.fftSize = 128; freq = new Uint8Array(analyser.frequencyBinCount); }
      actx.createMediaElementSource(au).connect(analyser); analyser.connect(actx.destination);
      var loop = function () { analyser.getByteFrequencyData(freq); var s = 0; for (var i = 0; i < freq.length; i++) s += freq[i]; var lv = Math.min(1, (s / freq.length) / 95); coreEl.style.transform = "scale(" + (1 + lv * 0.5) + ")"; raf = requestAnimationFrame(loop); }; loop();
    } catch (e) {}
  }
  function vizStop() { if (raf) cancelAnimationFrame(raf); raf = null; coreEl.style.transform = ""; setState("ONLINE"); }

  /* ---------- talk to the brain ---------- */
  function send(text) {
    if (!text.trim()) return; bubble(esc(text), "me"); setState("…");
    fetch(API + "/api/bot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text }) })
      .then(function (r) { return r.json(); })
      .then(function (d) { var reply = d.reply || "…"; bubble(esc(reply), "chad"); speak(reply); setState("ONLINE"); if (/run the studio|refresh the radar/i.test(text)) {} })
      .catch(function () { bubble("I can't reach my brain right now — is the Chad service running?", "chad"); setState("OFFLINE"); });
  }
  function loadBrief() {
    if (!USER) return;
    fetch(API + "/api/state").then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.chadBriefing) {
          brief.style.display = "block";
          brief.textContent = d.chadBriefing.headline + " — " + d.chadBriefing.proposal;
        } else if (d.welcome) {
          brief.style.display = "block"; brief.textContent = d.welcome;
        }
      })
      .catch(function () {});
  }

  /* ---------- open / greet ---------- */
  function open() { root.classList.add("cw-open"); if (!greeted) firstGreet(); }
  function close() { root.classList.remove("cw-open"); }
  function firstGreet() {
    if (!USER) { showPicker(); return; }
    greeted = true; loadBrief();
    var hi = "Good to see you, " + USER + ". I am pulling your briefing.";
    fetch(API + "/api/state").then(function (r) { return r.json(); })
      .then(function (d) {
        var message=d.welcome || hi;
        bubble(esc(message), "chad");
        speak(message);
      }).catch(function () { bubble(esc(hi), "chad"); speak(hi); });
  }
  function autoOpen() {
    if (!USER) return;
    var key="chad_auto_open_"+USER+"_"+new Date().toISOString().slice(0,10);
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key,"1");
    setTimeout(open,1200);
  }
  function showPicker() {
    var p = document.createElement("div"); p.className = "cw-pick";
    p.innerHTML = "<b>Who's here?</b><div>So I can greet you and pull your briefing.</div><div class='row'><button data-u='Ryan'>Ryan</button><button data-u='Cassie'>Cassie</button><button data-u='Jennifer'>Jennifer</button></div>";
    msgs.appendChild(p);
    p.querySelectorAll("button").forEach(function (b) { b.onclick = function () { USER = b.getAttribute("data-u"); localStorage.setItem("chad_widget_user", USER); p.remove(); greeted = false; firstGreet(); }; });
  }

  /* ---------- wire events ---------- */
  root.querySelector("#cwOrbWrap").onclick = function () { root.classList.contains("cw-open") ? close() : open(); };
  root.querySelector("#cwClose").onclick = close;
  root.querySelector("#cwMute").onclick = function () { muted = !muted; localStorage.setItem("chad_widget_mute", muted ? "1" : "0"); this.innerHTML = muted ? "&#128263;" : "&#128266;"; if (muted && window.speechSynthesis) window.speechSynthesis.cancel(); if (muted && curAudio) { try { curAudio.pause(); } catch (e) {} } };
  root.querySelector("#cwSend").onclick = function () { send(input.value); input.value = ""; };
  input.addEventListener("keydown", function (ev) { if (ev.key === "Enter") { send(input.value); input.value = ""; } });
  root.querySelectorAll(".cw-chip").forEach(function (c) { c.onclick = function () { send(c.getAttribute("data-q")); }; });
  root.querySelector("#cwMic").onclick = function () {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) { bubble("Voice input needs Chrome or Safari — you can still type.", "chad"); return; }
    var rec = new SR(); rec.lang = "en-US"; var btn = this;
    rec.onstart = function () { btn.classList.add("on"); setState("LISTENING"); };
    rec.onresult = function (ev2) { input.value = ev2.results[0][0].transcript; };
    rec.onend = function () { btn.classList.remove("on"); setState("ONLINE"); if (input.value.trim()) { send(input.value); input.value = ""; } };
    rec.start();
  };

  /* ---------- public API (for a docked "Chad tab") ---------- */
  window.ChadWidget = { open: open, close: close, setUser: function (u) { USER = u; localStorage.setItem("chad_widget_user", u); autoOpen(); }, send: send };
  if (USER) autoOpen();
})();
