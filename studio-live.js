(function(){
  let state=null;
  let bots=null;
  const q=id=>document.getElementById(id);

  async function api(path,body){
    const options=body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{};
    const response=await fetch(path,options);
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||data.output||"Request failed");
    return data;
  }

  async function load(){
    try{
      [state,bots]=await Promise.all([api("/api/state"),api("/api/bots")]);
      window.HANCOCK_BOT_DATA=state.botData;
      if(window.ChadWidget)window.ChadWidget.setUser(state.user.name.split(" ")[0]);
      const mode=q("mode");
      if(mode){
        mode.textContent=bots.ai?"Live AI + bots":"Bots online · AI key needed";
        mode.className="mode"+(bots.ai?" live":"");
      }
      renderCrew();
    }catch(error){
      const mode=q("mode");
      if(mode)mode.textContent="Bot connection unavailable";
    }
  }

  function renderCrew(){
    const host=q("botCrew");
    if(!host)return;
    host.innerHTML=(bots.bots||[]).map(bot=>`
      <div class="card">
        <span class="badge live">${escapeHtml(bot.status)}</span>
        <h3>${escapeHtml(bot.name)}</h3>
        <p>${escapeHtml(bot.summary)}</p>
      </div>`).join("");
    const status=q("chadStatus");
    if(status){
      const doctrine=bots.doctrine&&bots.doctrine.loaded?"Ryan's Playbook foundation loaded":"Playbook unavailable";
      status.textContent=`${doctrine}. Chad retains traceable signals and emerging patterns. Last run: ${bots.last_run||"not run yet"}. Next scheduled run: ${bots.next_run||"pending"}.`;
    }
  }

  async function runBots(){
    const status=q("chadStatus");
    if(status)status.textContent="The specialist bots are scanning now...";
    try{
      await api("/api/run-council",{});
      await load();
      if(typeof window.runBriefing==="function")window.runBriefing();
      if(status)status.textContent="Scan complete. Chad has the new briefing.";
    }catch(error){
      if(status)status.textContent=error.message;
    }
  }

  window.HancockLive={
    api,
    refresh:load,
    runBots,
    openChad:()=>window.ChadWidget&&window.ChadWidget.open()
  };
  load();
  setInterval(load,30000);
})();
