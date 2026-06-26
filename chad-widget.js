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
  var conversationMode = localStorage.getItem("chad_widget_conversation") !== "0";
  var standby = false;
  var minimized = localStorage.getItem("chad_widget_minimized") === "1";
  var greeted = false;
  function stateUrl() {
    return API+"/api/state"+(CFG.briefingKey ? "?briefing="+encodeURIComponent(CFG.briefingKey) : "");
  }

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
    + '#chadw .cw-panel{position:fixed;right:22px;bottom:142px;width:340px;max-width:88vw;height:460px;max-height:72vh;'
    + 'background:linear-gradient(180deg,#0d2c4a,#0a2236);border:1px solid rgba(79,147,224,.35);border-radius:16px;'
    + 'box-shadow:0 24px 70px rgba(4,12,22,.6);display:none;flex-direction:column;overflow:hidden}'
    + '#chadw.cw-open .cw-panel{display:flex;animation:cwrise .22s ease both}'
    + '#chadw.cw-min .cw-panel{height:auto;min-height:0}'
    + '#chadw.cw-min .cw-brief,#chadw.cw-min .cw-msgs,#chadw.cw-min .cw-chips,#chadw.cw-min .cw-comp{display:none!important}'
    + '@keyframes cwrise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}'
    + '#chadw .cw-head{display:flex;align-items:center;justify-content:space-between;padding:11px 13px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(79,147,224,.25);cursor:move;user-select:none;touch-action:none}'
    + '#chadw .cw-head .t{font-size:13.5px;font-weight:800;color:#eaf2fb}#chadw .cw-head .t span{color:#4f93e0;font-size:10px;font-weight:700;letter-spacing:1px}'
    + '#chadw .cw-actions{display:flex;align-items:center;gap:3px}'
    + '#chadw .cw-x{background:none;border:none;color:#9fb4c9;font-size:18px;cursor:pointer;line-height:1}'
    + '#chadw .cw-x.ready{color:#55d6a5;text-shadow:0 0 10px rgba(85,214,165,.6)}'
    + '#chadw .cw-brief{font-size:12px;color:#bcd2ea;padding:10px 13px;border-bottom:1px solid rgba(79,147,224,.18);line-height:1.5;background:rgba(47,111,191,.08)}'
    + '#chadw .cw-transcript{display:none;padding:8px 13px;border-bottom:1px solid rgba(79,147,224,.18);background:rgba(85,214,165,.08);color:#d8f8ea;font-size:12px;line-height:1.4}'
    + '#chadw .cw-transcript.on{display:block}'
    + '#chadw .cw-msgs{flex:1;overflow-y:auto;padding:12px 12px 4px;display:flex;flex-direction:column;gap:8px}'
    + '#chadw .cw-m{max-width:85%;padding:9px 12px;border-radius:13px;font-size:13px;line-height:1.5;animation:cwrise .2s ease both}'
    + '#chadw .cw-m.chad{align-self:flex-start;background:rgba(47,111,191,.22);border:1px solid rgba(79,147,224,.4);color:#eaf2fb;border-bottom-left-radius:4px}'
    + '#chadw .cw-m.chad a{color:#a9d1ff;text-decoration:underline;overflow-wrap:anywhere}'
    + '#chadw .cw-m.me{align-self:flex-end;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);color:#fff;border-bottom-right-radius:4px}'
    + '#chadw .cw-chips{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 8px}'
    + '#chadw .cw-chip{background:rgba(255,255,255,.07);border:1px solid rgba(79,147,224,.4);color:#dbeafe;font-size:11.5px;font-weight:700;padding:6px 10px;border-radius:16px;cursor:pointer}'
    + '#chadw .cw-chip:hover{background:#2f6fbf;color:#fff}'
    + '#chadw .cw-chip.on{background:#1f9d68;border-color:#55d6a5;color:#fff;box-shadow:0 0 12px rgba(85,214,165,.3)}'
    + '#chadw .cw-chip.standby{background:#7a3940;border-color:#d77882;color:#fff;box-shadow:0 0 12px rgba(215,120,130,.22)}'
    + '#chadw .cw-comp{display:flex;gap:7px;padding:10px 12px;border-top:1px solid rgba(79,147,224,.2);align-items:center}'
    + '#chadw .cw-comp input{flex:1;padding:10px 12px;border-radius:11px;border:1px solid rgba(79,147,224,.3);background:rgba(255,255,255,.06);color:#fff;font-size:13px}'
    + '#chadw .cw-comp input::placeholder{color:#8da6bf}'
    + '#chadw .cw-mic,#chadw .cw-send{flex:none;width:40px;height:40px;border-radius:11px;border:none;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}'
    + '#chadw .cw-mic{background:rgba(255,255,255,.08);border:1px solid rgba(79,147,224,.3);color:#dbeafe}#chadw .cw-mic.on{background:#c0392b;color:#fff}'
    + '#chadw .cw-send{background:#2f6fbf;color:#fff}#chadw .cw-send:hover{background:#4f93e0}'
    + '#chadw .cw-pick{padding:14px 13px;color:#cfe0f2;font-size:13px}#chadw .cw-pick b{color:#fff}'
    + '#chadw .cw-pick .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}'
    + '#chadw .cw-pick button{background:rgba(47,111,191,.2);border:1px solid rgba(79,147,224,.5);color:#eaf2fb;font-weight:700;font-size:13px;padding:9px 14px;border-radius:10px;cursor:pointer}'
    + '#chadw .cw-pick button:hover{background:#2f6fbf;color:#fff}'
    + '@media(max-width:600px){#chadw .cw-panel{left:10px!important;right:10px!important;top:auto!important;bottom:126px!important;width:auto;max-width:none;height:min(520px,70vh)}}';
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  /* ---------- markup ---------- */
  var root = document.createElement("div"); root.id = "chadw";
  root.innerHTML =
    '<div class="cw-panel">'
    + '<div class="cw-head"><div class="t">Chad <span id="cwState">ONLINE</span></div>'
    + '<div class="cw-actions"><button class="cw-x" id="cwHear" title="Play or replay Chad">&#9654;</button> '
    + '<button class="cw-x" id="cwMute" title="Mute">' + (muted ? '&#128263;' : '&#128266;') + '</button> '
    + '<button class="cw-x" id="cwMin" title="Minimize">&#8722;</button> '
    + '<button class="cw-x" id="cwClose" title="Close">&#10005;</button></div></div>'
    + '<div class="cw-brief" id="cwBrief" style="display:none"></div>'
    + '<div class="cw-transcript" id="cwTranscript"></div>'
    + '<div class="cw-msgs" id="cwMsgs"></div>'
    + '<div class="cw-chips"><button class="cw-chip" data-q="catch me up">Catch me up</button>'
    + '<button class="cw-chip" data-q="prepare the suggested post">Prepare suggested post</button>'
    + '<button class="cw-chip" data-q="run the studio">Run the studio</button>'
    + '<button class="cw-chip" id="cwStandby" title="Pause Chad voice and microphone">Standby</button>'
    + '<button class="cw-chip' + (conversationMode ? ' on' : '') + '" id="cwConversation" title="Keep the microphone listening until you turn voice off">' + (conversationMode ? 'Always listening' : 'Voice off') + '</button></div>'
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
  var msgs = root.querySelector("#cwMsgs"), brief = root.querySelector("#cwBrief"), transcript = root.querySelector("#cwTranscript"), input = root.querySelector("#cwInput"),
    stateEl = root.querySelector("#cwState"), coreEl = root.querySelector("#cwCore");
  var actx = null, analyser = null, freq = null, raf = null, curSource = null, lastAudioBuffer = null, lastSpokenText = "";
  var recognition = null, recognitionGeneration = 0, listenSilenceTimer = null, bargeRecognition = null, bargeTimer = null, requestNumber = 0, activeRequest = null, listenTimer = null, micDeniedNotice = false, lastStudioFocus = null;
  var panel = root.querySelector(".cw-panel"), head = root.querySelector(".cw-head");
  if (minimized) root.classList.add("cw-min");

  function setState(s) { stateEl.textContent = s; }
  function setTranscript(text) {
    var value=String(text || "").replace(/\s+/g," ").trim();
    transcript.textContent=value ? 'Hearing: "'+value+'"' : "";
    transcript.classList.toggle("on",!!value);
  }
  function bubble(t, who) {
    var d = document.createElement("div"); d.className = "cw-m " + who;
    d.innerHTML = who === "chad" ? t.replace(/(https?:\/\/[^\s<]+)/g,'<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>') : t;
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight;
  }
  function esc(s) { return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function compactText(value,limit) {
    return String(value || "").replace(/\s+/g," ").trim().slice(0,limit || 700);
  }
  function studioTabLabel(view) {
    if (!view) return document.title || "Studio";
    var id=view.id || "";
    var tab=Array.from(document.querySelectorAll(".tab")).find(function (button) {
      return button.classList.contains("active") ||
        (button.getAttribute("onclick") || "").indexOf("'"+id+"'") !== -1;
    });
    return compactText(tab ? tab.textContent : (view.querySelector("h1,h2") || {}).textContent || id,120);
  }
  function collectStudioPageContext() {
    var view=document.querySelector(".view.active") || document.querySelector("main") || document.body;
    var controls=[];
    Array.from(view.querySelectorAll("input,select,textarea")).slice(0,30).forEach(function (control) {
      var type=(control.type || "").toLowerCase();
      if (type==="password" || type==="file" || type==="hidden") return;
      var value=type==="checkbox" || type==="radio" ? (control.checked ? "selected" : "") : control.value;
      if (!value) return;
      var label="";
      if (control.id) {
        var explicit=document.querySelector('label[for="'+control.id.replace(/"/g,"")+'"]');
        if (explicit) label=explicit.textContent;
      }
      if (!label && control.previousElementSibling && control.previousElementSibling.tagName==="LABEL") label=control.previousElementSibling.textContent;
      controls.push({name:compactText(label || control.placeholder || control.id || control.name || "field",100),value:compactText(value,500)});
    });
    var selected=[];
    Array.from(view.querySelectorAll(".chip.gold,.tab.active,.badge.hot,.badge.live,[aria-selected='true']")).slice(0,30).forEach(function (node) {
      var text=compactText(node.textContent,160);
      if (text && selected.indexOf(text)===-1) selected.push(text);
    });
    var items=[];
    Array.from(view.querySelectorAll(".card,.panel,.libItem,.updateItem,.task,.draftItem")).slice(0,16).forEach(function (node,index) {
      if (node.closest("#chadw")) return;
      var text=compactText(node.innerText || node.textContent,900);
      if (text) items.push({position:index+1,text:text});
    });
    var headings=Array.from(view.querySelectorAll("h1,h2,h3")).slice(0,18).map(function (node) {
      return compactText(node.textContent,180);
    }).filter(Boolean);
    return {
      page_title:compactText(document.title,160),
      page_url:location.pathname+location.hash,
      active_tab_id:view.id || "",
      active_tab:studioTabLabel(view),
      headings:headings,
      selected: selected,
      controls:controls,
      visible_items:items,
      last_interaction:lastStudioFocus,
      captured_at:new Date().toISOString()
    };
  }
  document.addEventListener("click",function (event) {
    var target=event.target && event.target.closest ? event.target.closest(".card,.panel,.libItem,.updateItem,.task,.draftItem") : null;
    var action=event.target && event.target.closest ? event.target.closest("button,a") : null;
    if ((!target && !action) || (target && target.closest("#chadw")) || (action && action.closest("#chadw"))) return;
    var activeView=document.querySelector(".view.active");
    if (target && !target.closest(".view.active,main")) target=null;
    if (action && !action.closest(".view.active,main")) action=null;
    if (!target && !action) return;
    var surrounding=target || (action ? action.closest(".hero,.card,.panel,section") : null);
    lastStudioFocus={
      tab:studioTabLabel(activeView),
      action:compactText(action ? action.textContent : "",160),
      text:compactText(surrounding ? (surrounding.innerText || surrounding.textContent) : "",1200),
      captured_at:new Date().toISOString()
    };
  },true);

  /* ---------- voice (audio-reactive orb) ---------- */
  function ensureAudioContext() {
    if (!actx) {
      var AC=window.AudioContext || window.webkitAudioContext;
      if (!AC) return Promise.reject(new Error("Web Audio unavailable"));
      actx=new AC();
      analyser=actx.createAnalyser(); analyser.fftSize=128;
      freq=new Uint8Array(analyser.frequencyBinCount);
      analyser.connect(actx.destination);
    }
    var ready=actx.state === "suspended" ? actx.resume() : Promise.resolve();
    return ready.then(function () {
      if (actx.state !== "running") throw new Error("Audio needs a user gesture");
    });
  }
  function decodeAudio(bytes) {
    return new Promise(function (resolve,reject) {
      var copy=bytes.slice(0);
      var result=actx.decodeAudioData(copy,resolve,reject);
      if (result && typeof result.then === "function") result.then(resolve).catch(reject);
    });
  }
  function stopSpeech() {
    stopBargeIn();
    if (curSource) {
      try { curSource.onended=null; curSource.stop(0); } catch (e) {}
      curSource = null;
    }
    vizStop();
  }
  function clearListenTimer() {
    if (listenTimer) window.clearTimeout(listenTimer);
    listenTimer=null;
  }
  function clearListenSilenceTimer() {
    if (listenSilenceTimer) window.clearTimeout(listenSilenceTimer);
    listenSilenceTimer=null;
  }
  function stopRecognition() {
    clearListenSilenceTimer();
    recognitionGeneration++;
    if (recognition) {
      var current=recognition;
      recognition=null;
      try { current.abort(); } catch (e) {}
    }
    root.querySelector("#cwMic").classList.remove("on");
  }
  function stopBargeIn() {
    if (bargeTimer) window.clearTimeout(bargeTimer);
    bargeTimer=null;
    if (bargeRecognition) {
      var current=bargeRecognition;
      bargeRecognition=null;
      try { current.abort(); } catch (e) {}
    }
  }
  function normalizedWords(text) {
    return (text || "").toLowerCase().replace(/[^a-z0-9\s]/g," ").split(/\s+/).filter(function (word) { return word.length > 1; });
  }
  function likelyChadEcho(heard,spoken) {
    var heardWords=normalizedWords(heard), spokenWords=normalizedWords(spoken);
    if (!heardWords.length || !spokenWords.length) return false;
    var spokenMap={};
    spokenWords.forEach(function (word) { spokenMap[word]=true; });
    var overlap=heardWords.filter(function (word) { return spokenMap[word]; }).length;
    return overlap/heardWords.length >= .75;
  }
  function mergeTranscript(base,next) {
    base=String(base || "").trim();
    next=String(next || "").trim();
    if (!base) return next;
    if (!next) return base;
    var lowerBase=base.toLowerCase(), lowerNext=next.toLowerCase();
    if (lowerNext.indexOf(lowerBase)===0) return next;
    if (lowerBase.indexOf(lowerNext)>=0) return base;
    return base+" "+next;
  }
  function startBargeIn(spokenText,delay) {
    stopBargeIn();
    if (!conversationMode || muted || standby) return;
    var SR=window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    bargeTimer=window.setTimeout(function () {
      bargeTimer=null;
      if (!conversationMode || recognition || bargeRecognition || (!curSource && !activeRequest)) return;
      var rec=new SR(), interrupted=false;
      bargeRecognition=rec;
      rec.lang="en-US"; rec.interimResults=true; rec.continuous=true;
      rec.onresult=function (event) {
        var heard="";
        for (var i=event.resultIndex;i<event.results.length;i++) {
          heard+=(event.results[i][0].transcript || "")+" ";
        }
        heard=heard.trim();
        if (interrupted || heard.length<3 || likelyChadEcho(heard,spokenText || lastSpokenText)) return;
        interrupted=true;
        bargeRecognition=null;
        try { rec.abort(); } catch (e) {}
        setState("INTERRUPTED");
        stopSpeech();
        if (activeRequest) {
          try { activeRequest.abort(); } catch (e) {}
          activeRequest=null;
          requestNumber++;
        }
        input.value=heard;
        setTranscript(heard);
        window.setTimeout(function () { startListening(true,heard); },160);
      };
      rec.onerror=function () {
        if (bargeRecognition===rec) bargeRecognition=null;
      };
      rec.onend=function () {
        if (bargeRecognition===rec) bargeRecognition=null;
        if (!interrupted && conversationMode && (curSource || activeRequest)) startBargeIn(spokenText,250);
      };
      try { rec.start(); } catch (e) { bargeRecognition=null; }
    },delay || 450);
  }
  function queueListening(delay) {
    clearListenTimer();
    if (!conversationMode || standby || curSource || activeRequest || recognition) return;
    listenTimer=window.setTimeout(function () {
      listenTimer=null;
      startListening(false);
    },delay || 350);
  }
  function playBuffer(buffer,spokenText) {
    if (!buffer || muted || standby) return;
    ensureAudioContext().then(function () {
      stopSpeech();
      var source=actx.createBufferSource(); source.buffer=buffer; source.connect(analyser);
      curSource=source; setState("SPEAKING"); root.querySelector("#cwHear").classList.remove("ready");
      source.onended=function () {
        if (curSource!==source) return;
        curSource=null; vizStop();
        queueListening(350);
      };
      source.start(0); vizStart();
      startBargeIn(spokenText || lastSpokenText,450);
    }).catch(function () {
      setState("TAP PLAY");
      root.querySelector("#cwHear").classList.add("ready");
    });
  }
  function speak(text) {
    if (muted || standby) { queueListening(250); return; }
    setState("GETTING VOICE");
    fetch(API + "/api/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: text.replace(/<[^>]+>/g, "") }) })
      .then(function (r) {
        if (r.ok) return r.arrayBuffer();
        return r.json().catch(function () { return {}; }).then(function (d) { throw new Error(d.error || "ElevenLabs unavailable"); });
      })
      .then(function (bytes) {
        return ensureAudioContext().catch(function () {}).then(function () {
          if (!actx) throw new Error("Web Audio unavailable");
          return decodeAudio(bytes);
        });
      })
      .then(function (buffer) {
        lastAudioBuffer=buffer;
        lastSpokenText=text;
        playBuffer(buffer,text);
      }).catch(function (error) {
        var quota=error && /quota|credit/i.test(error.message || "");
        setState(quota ? "VOICE CREDITS NEEDED" : "VOICE UNAVAILABLE");
        queueListening(500);
      });
  }
  function vizStart() {
    var loop = function () {
      if (!analyser || !freq) return;
      analyser.getByteFrequencyData(freq); var s=0;
      for (var i=0;i<freq.length;i++) s+=freq[i];
      var lv=Math.min(1,(s/freq.length)/95);
      coreEl.style.transform="scale("+(1+lv*0.5)+")";
      raf=requestAnimationFrame(loop);
    }; loop();
  }
  function vizStop() { if (raf) cancelAnimationFrame(raf); raf = null; coreEl.style.transform = ""; setState("ONLINE"); }
  function navigate(action) {
    if (!action || !action.target) return;
    if (action.type === "tab" && typeof window.showTab === "function") {
      window.showTab(action.target);
      return;
    }
    if (action.type === "tab" && typeof window.openTab === "function") {
      var workspaceTarget=action.target==="dashboard" ? "dash" : action.target;
      if (document.getElementById(workspaceTarget)) {
        window.openTab(workspaceTarget);
        return;
      }
      window.location.href="/studio#"+encodeURIComponent(action.target);
      return;
    }
    if (action.type === "external") {
      var opened=window.open(action.target,"_blank","noopener,noreferrer");
      if (!opened) window.location.href=action.target;
      return;
    }
    if (action.type === "url") window.location.href = action.target;
  }
  function sourceButtons(sources) {
    if (!sources || !sources.length) return;
    var wrap=document.createElement("div"); wrap.className="cw-chips";
    sources.slice(0,4).forEach(function (source,index) {
      var button=document.createElement("button"); button.className="cw-chip";
      button.textContent="Open source "+(index+1)+(source.name ? " · "+source.name : "");
      button.onclick=function () { navigate({type:"external",target:source.url}); };
      wrap.appendChild(button);
    });
    msgs.appendChild(wrap); msgs.scrollTop=msgs.scrollHeight;
  }
  function updateStandbyControl() {
    var control=root.querySelector("#cwStandby");
    control.textContent=standby ? "Resume voice" : "Standby";
    control.title=standby ? "Resume Chad voice and microphone" : "Pause Chad voice and microphone";
    control.classList.toggle("standby",standby);
  }
  function enterStandby(showMessage) {
    standby=true;
    clearListenTimer();
    setTranscript("");
    stopSpeech();
    stopRecognition();
    stopBargeIn();
    if (activeRequest) {
      try { activeRequest.abort(); } catch (e) {}
      activeRequest=null;
      requestNumber++;
    }
    setState("STANDBY");
    updateStandbyControl();
    if (showMessage) bubble("Standing by. Voice and microphone are paused. Press Resume voice when you are ready.", "chad");
  }
  function leaveStandby(showMessage) {
    standby=false;
    setState("ONLINE");
    updateStandbyControl();
    if (showMessage) bubble("I am back. Voice conversation is ready.", "chad");
    if (conversationMode) {
      ensureAudioContext().then(function () { startListening(false); }).catch(function () { setState("AUDIO UNAVAILABLE"); });
    }
  }
  function isStandbyCommand(text) {
    var value=String(text || "").toLowerCase().replace(/[,.!?]/g," ").replace(/\s+/g," ").trim();
    return /^(hey |hi )?(chad )?(can you |will you )?(stand ?by|go on standby|pause( your| the)? voice|pause talking|pause for (a |one )?minute|stop talking|be quiet|hold on|give me (a |one )?minute)( please)?( chad)?$/.test(value);
  }
  function isResumeCommand(text) {
    var value=String(text || "").toLowerCase().replace(/[,.!?]/g," ").replace(/\s+/g," ").trim();
    return /^(hey |hi )?(chad )?(you can |can you |will you )?(resume( voice| talking)?|come back|wake up|start talking|i am back|i'm back)( please)?( chad)?$/.test(value);
  }

  /* ---------- talk to the brain ---------- */
  function send(text) {
    if (!text.trim()) return;
    if (isStandbyCommand(text)) {
      bubble(esc(text), "me");
      enterStandby(true);
      input.value="";
      return;
    }
    if (isResumeCommand(text)) {
      bubble(esc(text), "me");
      leaveStandby(true);
      input.value="";
      return;
    }
    ensureAudioContext().catch(function () {});
    setTranscript("");
    clearListenTimer();
    stopSpeech();
    stopRecognition();
    if (activeRequest) { try { activeRequest.abort(); } catch (e) {} }
    var thisRequest=++requestNumber;
    var requestId=Date.now().toString(36)+"-"+thisRequest.toString(36);
    activeRequest=window.AbortController ? new AbortController() : null;
    bubble(esc(text), "me"); setState("THINKING");
    startBargeIn("",650);
    fetch(API + "/api/bot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, request_id: requestId, page_context: collectStudioPageContext() }),
      signal: activeRequest ? activeRequest.signal : undefined
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (thisRequest !== requestNumber || d.superseded) return;
        activeRequest=null;
        var reply = d.reply || "…";
        bubble(esc(reply), "chad");
        sourceButtons(d.sources);
        speak(reply);
        if (!curSource) setState("ONLINE");
        if (d.ui_action) setTimeout(function () { navigate(d.ui_action); }, 450);
      })
      .catch(function (error) {
        if (error && error.name === "AbortError") return;
        if (thisRequest !== requestNumber) return;
        activeRequest=null;
        bubble("I can't reach my brain right now — is the Chad service running?", "chad");
        setState("OFFLINE");
        queueListening(1000);
      });
  }
  function loadBrief() {
    if (!USER) return;
    fetch(stateUrl()).then(function (r) { return r.json(); })
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
  function restorePanelPosition() {
    if (window.innerWidth <= 600) return;
    try {
      var saved=JSON.parse(localStorage.getItem("chad_widget_position") || "null");
      if (!saved || typeof saved.left !== "number" || typeof saved.top !== "number") return;
      var maxLeft=Math.max(8,window.innerWidth-panel.offsetWidth-8);
      var maxTop=Math.max(8,window.innerHeight-panel.offsetHeight-8);
      panel.style.left=Math.min(Math.max(8,saved.left),maxLeft)+"px";
      panel.style.top=Math.min(Math.max(8,saved.top),maxTop)+"px";
      panel.style.right="auto"; panel.style.bottom="auto";
    } catch (e) {}
  }
  function open() {
    ensureAudioContext().catch(function () {});
    root.classList.add("cw-open");
    restorePanelPosition();
    if (!greeted) firstGreet();
    else queueListening(300);
  }
  function ask(text) {
    ensureAudioContext().catch(function () {});
    root.classList.add("cw-open");
    restorePanelPosition();
    if (!greeted) {
      greeted=true;
      loadBrief();
    }
    send(text);
  }
  function close() {
    root.classList.remove("cw-open");
    clearListenTimer();
    if (conversationMode) queueListening(250);
    else {
      stopBargeIn();
      stopRecognition();
    }
  }
  function toggleMinimize() {
    minimized=!root.classList.contains("cw-min");
    root.classList.toggle("cw-min",minimized);
    localStorage.setItem("chad_widget_minimized",minimized ? "1" : "0");
    root.querySelector("#cwMin").innerHTML=minimized ? "&#9633;" : "&#8722;";
    root.querySelector("#cwMin").title=minimized ? "Restore" : "Minimize";
    if (minimized) {
      if (conversationMode) queueListening(250);
    } else {
      restorePanelPosition();
      queueListening(300);
    }
  }
  function firstGreet() {
    if (!USER) { showPicker(); return; }
    greeted = true; loadBrief();
    var hi = "Good to see you, " + USER + ". I am pulling your briefing.";
    fetch(stateUrl()).then(function (r) { return r.json(); })
      .then(function (d) {
        var message=d.welcome || hi;
        bubble(esc(message), "chad");
        speak(message);
        if (d.chadBriefing && d.chadBriefing.ui_action && !CFG.holdBriefingNavigation) {
          setTimeout(function () { navigate(d.chadBriefing.ui_action); }, 650);
        }
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
  root.querySelector("#cwMin").onclick = function (ev) { ev.stopPropagation(); toggleMinimize(); };
  root.querySelector("#cwMin").innerHTML=minimized ? "&#9633;" : "&#8722;";
  root.querySelector("#cwMin").title=minimized ? "Restore" : "Minimize";
  root.querySelector("#cwHear").onclick = function () {
    if (standby) leaveStandby(false);
    muted=false; root.querySelector("#cwMute").innerHTML="&#128266;";
    localStorage.setItem("chad_widget_mute","0");
    ensureAudioContext().then(function () { playBuffer(lastAudioBuffer,lastSpokenText); }).catch(function () { setState("AUDIO UNAVAILABLE"); });
  };
  root.querySelector("#cwMute").onclick = function () { muted = !muted; localStorage.setItem("chad_widget_mute", muted ? "1" : "0"); this.innerHTML = muted ? "&#128263;" : "&#128266;"; if (muted) { stopSpeech(); queueListening(250); } };
  root.querySelector("#cwStandby").onclick = function () {
    if (standby) leaveStandby(true);
    else enterStandby(true);
  };
  root.querySelector("#cwSend").onclick = function () { ensureAudioContext().catch(function () {}); send(input.value); input.value = ""; };
  input.addEventListener("keydown", function (ev) { if (ev.key === "Enter") { ensureAudioContext().catch(function () {}); send(input.value); input.value = ""; } });
  root.querySelectorAll(".cw-chip[data-q]").forEach(function (c) { c.onclick = function () { send(c.getAttribute("data-q")); }; });
  function startListening(force,seedText) {
    if (standby) return;
    if (!conversationMode && !force) return;
    if (curSource || activeRequest || recognition) return;
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) { bubble("Voice input needs Chrome or Safari — you can still type.", "chad"); conversationMode=false; updateConversationControl(); return; }
    stopSpeech();
    var rec = new SR(), generation=++recognitionGeneration;
    recognition=rec; rec.lang = "en-US"; rec.interimResults=true; rec.continuous=true; rec.maxAlternatives=1;
    var btn=root.querySelector("#cwMic"), committed=String(seedText || "").trim(), latest="", denied=false, submitted=false;
    function submitAfterPause(delay) {
      clearListenSilenceTimer();
      listenSilenceTimer=window.setTimeout(function () {
        listenSilenceTimer=null;
        var heard=(committed+" "+latest).trim();
        if (!heard || submitted || generation!==recognitionGeneration) return;
        submitted=true;
        input.value="";
        stopRecognition();
        send(heard);
      },delay);
    }
    rec.onstart = function () {
      btn.classList.add("on");
      setState("LISTENING");
      setTranscript((committed+" "+latest).trim());
    };
    rec.onresult = function (ev2) {
      if (generation!==recognitionGeneration) return;
      latest="";
      for (var i=ev2.resultIndex;i<ev2.results.length;i++) {
        var phrase=(ev2.results[i][0].transcript || "").trim();
        if (!phrase) continue;
        if (ev2.results[i].isFinal) committed=mergeTranscript(committed,phrase);
        else latest=(latest+" "+phrase).trim();
      }
      var visible=(committed+" "+latest).trim();
      if (visible) {
        input.value=visible;
        setTranscript(visible);
      }
      submitAfterPause(latest ? 1600 : 1100);
    };
    rec.onerror = function (ev3) {
      denied=ev3 && (ev3.error === "not-allowed" || ev3.error === "service-not-allowed");
      if (denied) {
        conversationMode=false; updateConversationControl(); setState("MIC PERMISSION NEEDED");
        setTranscript("");
        if (!micDeniedNotice) {
          micDeniedNotice=true;
          bubble("Microphone access is off. Use the microphone button and allow access when your browser asks.", "chad");
        }
      } else if (generation===recognitionGeneration) {
        setState("RECONNECTING MIC");
      }
    };
    rec.onend = function () {
      if (generation!==recognitionGeneration) return;
      recognition=null; btn.classList.remove("on"); clearListenSilenceTimer();
      var heard=(committed+" "+latest).trim();
      if (heard && !submitted) { submitted=true; input.value=""; send(heard); return; }
      setTranscript("");
      setState(conversationMode ? "RECONNECTING MIC" : "ONLINE");
      if (!denied) queueListening(250);
    };
    try { rec.start(); } catch (e) {
      if (generation===recognitionGeneration) recognition=null;
      setState(conversationMode ? "RECONNECTING MIC" : "MIC UNAVAILABLE");
      if (conversationMode) queueListening(400);
    }
  }
  root.querySelector("#cwMic").onclick = function () {
    ensureAudioContext().catch(function () {});
    if (standby) leaveStandby(false);
    if (!conversationMode) {
      conversationMode=true;
      updateConversationControl();
    }
    startListening(true);
  };
  function updateConversationControl() {
    var control=root.querySelector("#cwConversation");
    control.textContent=conversationMode ? "Always listening" : "Voice off";
    control.classList.toggle("on",conversationMode);
    localStorage.setItem("chad_widget_conversation",conversationMode ? "1" : "0");
  }
  root.querySelector("#cwConversation").onclick = function () {
    conversationMode=!conversationMode; updateConversationControl();
    if (conversationMode) {
      if (standby) leaveStandby(false);
      muted=false; root.querySelector("#cwMute").innerHTML="&#128266;";
      localStorage.setItem("chad_widget_mute","0");
      ensureAudioContext().then(function () { startListening(false); }).catch(function () { setState("AUDIO UNAVAILABLE"); });
    } else {
      stopBargeIn();
      stopRecognition();
      stopSpeech(); setState("ONLINE");
    }
  };
  document.addEventListener("visibilitychange",function () {
    if (!document.hidden && conversationMode) queueListening(200);
  });
  window.addEventListener("focus",function () {
    if (conversationMode) queueListening(200);
  });
  window.addEventListener("online",function () {
    if (conversationMode) queueListening(250);
  });

  /* ---------- drag the panel by its header ---------- */
  var drag=null;
  function dragStart(ev) {
    if (ev.target.closest && ev.target.closest("button")) return;
    if (window.innerWidth <= 600) return;
    var point=ev.touches ? ev.touches[0] : ev;
    var rect=panel.getBoundingClientRect();
    drag={dx:point.clientX-rect.left,dy:point.clientY-rect.top};
    panel.style.left=rect.left+"px"; panel.style.top=rect.top+"px";
    panel.style.right="auto"; panel.style.bottom="auto";
    if (ev.cancelable) ev.preventDefault();
  }
  function dragMove(ev) {
    if (!drag) return;
    var point=ev.touches ? ev.touches[0] : ev;
    var left=Math.min(Math.max(8,point.clientX-drag.dx),window.innerWidth-panel.offsetWidth-8);
    var top=Math.min(Math.max(8,point.clientY-drag.dy),window.innerHeight-panel.offsetHeight-8);
    panel.style.left=left+"px"; panel.style.top=top+"px";
    if (ev.cancelable) ev.preventDefault();
  }
  function dragEnd() {
    if (!drag) return;
    drag=null;
    var rect=panel.getBoundingClientRect();
    localStorage.setItem("chad_widget_position",JSON.stringify({left:Math.round(rect.left),top:Math.round(rect.top)}));
  }
  head.addEventListener("mousedown",dragStart);
  head.addEventListener("touchstart",dragStart,{passive:false});
  window.addEventListener("mousemove",dragMove);
  window.addEventListener("touchmove",dragMove,{passive:false});
  window.addEventListener("mouseup",dragEnd);
  window.addEventListener("touchend",dragEnd);
  window.addEventListener("resize",function () { if (root.classList.contains("cw-open")) restorePanelPosition(); });

  /* ---------- public API (for a docked "Chad tab") ---------- */
  window.ChadWidget = {
    open: open,
    close: close,
    standby: function () { enterStandby(true); },
    resumeVoice: function () { leaveStandby(true); },
    startVoice: function () {
      open();
      if (standby) leaveStandby(false);
      if (!conversationMode) {
        conversationMode=true;
        updateConversationControl();
      }
      ensureAudioContext().then(function () { startListening(true); }).catch(function () { setState("AUDIO UNAVAILABLE"); });
    },
    pageContext: collectStudioPageContext,
    setUser: function (u) { USER = u; localStorage.setItem("chad_widget_user", u); autoOpen(); },
    send: send,
    ask: ask
  };
  if (USER) autoOpen();
})();
