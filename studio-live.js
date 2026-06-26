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
      [state,bots]=await Promise.all([api("/api/state?briefing="+encodeURIComponent(window.CHAD_BRIEFING_KEY||"")),api("/api/bots")]);
      window.HANCOCK_BOT_DATA=state.botData;
      if(window.ChadWidget)window.ChadWidget.setUser(state.user.name.split(" ")[0]);
      const mode=q("mode");
      if(mode){
        mode.textContent=bots.ai?"Chad AI + bots live":"Bots online · AI unavailable";
        mode.className="mode"+(bots.ai?" live":"");
      }
      renderCrew();
      if(window.HancockCalendar)window.HancockCalendar.update(state);
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

  const calendar={
    state:null,
    view:"today",
    platforms:["LinkedIn","Facebook","Instagram","TikTok","YouTube","Email","Website"],
    update(next){
      this.state=next;
      this.fillControls();
      this.render();
    },
    fillControls(){
      if(!q("calAssigned")||!this.state)return;
      const userOptions=(this.state.users||[]).map(user=>`<option value="${user.id}">${escapeHtml(user.name)}</option>`).join("");
      if(!q("calAssigned").dataset.ready){q("calAssigned").innerHTML='<option value="">Unassigned</option>'+userOptions;q("calAssigned").dataset.ready="1"}
      if(!q("calAssigneeFilter").dataset.ready){q("calAssigneeFilter").innerHTML='<option value="">Everyone</option>'+userOptions;q("calAssigneeFilter").dataset.ready="1"}
      if(!q("calService").dataset.ready){q("calService").innerHTML='<option value="">Choose service line</option>'+(this.state.serviceLines||[]).map(line=>`<option>${escapeHtml(line)}</option>`).join("");q("calService").dataset.ready="1"}
      if(!q("calPlatforms").dataset.ready){q("calPlatforms").innerHTML=this.platforms.map(name=>`<label><input type="checkbox" value="${name}"> ${name}</label>`).join("");q("calPlatforms").dataset.ready="1"}
    },
    dateOnly(value){
      return String(value||"").slice(0,10);
    },
    localDate(value){
      if(!value)return null;
      const raw=this.dateOnly(value);
      const parts=raw.split("-").map(Number);
      return parts.length===3?new Date(parts[0],parts[1]-1,parts[2]):null;
    },
    isoDate(date){
      const local=new Date(date.getTime()-date.getTimezoneOffset()*60000);
      return local.toISOString().slice(0,10);
    },
    entryDate(item){
      return this.dateOnly(item.publish_at||item.due_date||item.requested_date);
    },
    statusLabel(status){
      return ({draft:"Draft",requested:"Requested",in_progress:"In Progress",ready_for_edit:"Ready for Edit",ready_to_post:"Ready to Post",posted:"Posted",archived:"Archived",blocked:"Blocked"})[status]||status;
    },
    filtered(){
      if(!this.state)return[];
      const status=q("calStatusFilter")?q("calStatusFilter").value:"";
      const assigned=q("calAssigneeFilter")?q("calAssigneeFilter").value:"";
      return (this.state.calendar||[]).filter(item=>(!status||item.status===status)&&(!assigned||String(item.assigned_to||"")===assigned));
    },
    setView(view,button){
      this.view=view;
      document.querySelectorAll("[data-cal-view]").forEach(el=>el.classList.toggle("active",el===button));
      q("calendar").classList.toggle("calendarFull",view==="month"||view==="leadership");
      this.render();
    },
    useExecutionView(){
      this.view="today";
      q("calendar").classList.remove("calendarFull");
      document.querySelectorAll("[data-cal-view]").forEach(el=>el.classList.toggle("active",el.dataset.calView==="today"));
    },
    render(){
      if(!q("calendarView")||!this.state)return;
      const all=this.state.calendar||[];
      const now=new Date(),today=this.isoDate(now);
      const month=today.slice(0,7);
      const weekEnd=new Date(now); weekEnd.setDate(now.getDate()+6);
      const weekEndIso=this.isoDate(weekEnd);
      q("calDueToday").textContent=all.filter(i=>this.dateOnly(i.due_date)===today&&!["posted","archived"].includes(i.status)).length;
      q("calWeek").textContent=all.filter(i=>{const d=this.dateOnly(i.due_date||i.publish_at);return d>=today&&d<=weekEndIso&&!["posted","archived"].includes(i.status)}).length;
      q("calReady").textContent=all.filter(i=>i.status==="ready_to_post").length;
      q("calPosted").textContent=all.filter(i=>i.status==="posted"&&String(i.completed_at||i.updated_at).slice(0,7)===month).length;
      this.renderGuidance(all,today,weekEndIso);
      if(this.view==="month")this.renderMonth();
      else if(this.view==="leadership")this.renderLeadership();
      else this.renderAgenda(this.view==="today"?today:null,this.view==="week"?weekEndIso:null);
    },
    renderGuidance(all,today,weekEnd){
      const mine=all.filter(i=>i.assigned_to===this.state.user.id&&!["posted","archived"].includes(i.status));
      const overdue=mine.filter(i=>this.dateOnly(i.due_date)&&this.dateOnly(i.due_date)<today);
      const due=mine.filter(i=>this.dateOnly(i.due_date)===today);
      const week=mine.filter(i=>{const d=this.dateOnly(i.due_date||i.publish_at);return d>=today&&d<=weekEnd});
      let message=`${this.state.user.name.split(" ")[0]}, Our Marketing Calendar has ${week.length} production item${week.length===1?"":"s"} forecasted for you this week.`;
      if(overdue.length)message=`${this.state.user.name.split(" ")[0]}, ${overdue.length} production item${overdue.length===1?" is":"s are"} overdue. Chad recommends clearing the oldest blocker first: ${overdue[0].title}.`;
      else if(due.length)message=`${this.state.user.name.split(" ")[0]}, today's priority is ${due[0].title}. Complete the asset, move it to the next status, and keep the publish date protected.`;
      else if(week.length)message+=` Chad recommends starting with ${week[0].title}.`;
      q("calendarGuidance").textContent=message;
    },
    renderAgenda(day,weekEnd){
      const today=this.isoDate(new Date());
      let items=this.filtered().filter(item=>{
        const due=this.dateOnly(item.due_date),publish=this.dateOnly(item.publish_at);
        if(day)return due===day||publish===day||(!["posted","archived"].includes(item.status)&&due&&due<day);
        if(weekEnd)return (due>=today&&due<=weekEnd)||(publish>=today&&publish<=weekEnd);
        return true;
      });
      items.sort((a,b)=>this.dateOnly(a.due_date||a.publish_at).localeCompare(this.dateOnly(b.due_date||b.publish_at)));
      q("calendarView").innerHTML=`<div class="calendarAgenda">${items.map(item=>this.rowHtml(item,today)).join("")||'<div class="panel empty"><h3>No production scheduled here</h3><p>Ask Chad to forecast the next useful content opportunity.</p></div>'}</div>`;
    },
    rowHtml(item,today){
      const overdue=this.dateOnly(item.due_date)&&this.dateOnly(item.due_date)<today&&!["posted","archived"].includes(item.status);
      return `<div class="calendarRow ${overdue?"overdue":""}"><div><span class="badge ${item.status==="posted"?"live":item.status==="blocked"?"hot":"warn"}">${escapeHtml(this.statusLabel(item.status))}</span><div class="calendarMeta">Due ${escapeHtml(this.dateOnly(item.due_date)||"not set")}<br>Publish ${escapeHtml(String(item.publish_at||"not set").replace("T"," "))}</div></div><div><h3>${escapeHtml(item.title)}</h3><div class="calendarMeta">${escapeHtml(item.content_type)} · ${escapeHtml(item.platforms||"No platform")} · ${escapeHtml(item.assigned_name||"Unassigned")} · ${escapeHtml(item.priority)} priority</div>${item.talking_points?`<div class="calendarBrief">${escapeHtml(item.talking_points)}</div>`:""}</div><div class="calendarActions"><button class="mini" onclick="HancockCalendar.edit(${item.id})">Open Brief</button>${item.status!=="posted"?`<button class="mini" onclick="HancockCalendar.status(${item.id},'in_progress')">Working</button><button class="mini" onclick="HancockCalendar.status(${item.id},'ready_to_post')">Ready</button><button class="mini" onclick="HancockCalendar.status(${item.id},'posted')">Produced</button>`:"<b>Produced ✓</b>"}</div></div>`;
    },
    renderMonth(){
      const now=new Date(),first=new Date(now.getFullYear(),now.getMonth(),1),start=new Date(first);
      start.setDate(1-first.getDay());
      const items=this.filtered();
      let html=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(day=>`<div class="calendarDow">${day}</div>`).join("");
      for(let i=0;i<42;i++){
        const date=new Date(start);date.setDate(start.getDate()+i);
        const iso=this.isoDate(date),muted=date.getMonth()!==now.getMonth();
        const dayItems=items.filter(item=>this.entryDate(item)===iso);
        html+=`<div class="calendarDay ${muted?"mutedDay":""}"><div class="calendarDate">${date.getDate()}</div>${dayItems.map(item=>`<button class="calendarEvent status-${item.status} priority-${item.priority}" onclick="HancockCalendar.edit(${item.id})"><b>${escapeHtml(item.title)}</b><br>${escapeHtml(item.assigned_name||"Unassigned")}</button>`).join("")}</div>`;
      }
      q("calendarView").innerHTML=`<div class="calendarMonth">${html}</div>`;
    },
    renderLeadership(){
      const items=this.filtered(),active=items.filter(i=>!["posted","archived"].includes(i.status)),posted=items.filter(i=>i.status==="posted");
      const counts=(key)=>Object.entries(items.reduce((map,item)=>{String(item[key]||"Unspecified").split(",").forEach(value=>{value=value.trim();if(value)map[value]=(map[value]||0)+1});return map},{})).sort((a,b)=>b[1]-a[1]);
      const blocks=(title,data)=>`<div class="leadershipBlock"><h3>${title}</h3>${data.map(([name,count])=>`<p><b>${count}</b> ${escapeHtml(name)}</p>`).join("")||'<p class="muted">No data yet.</p>'}</div>`;
      q("calendarView").innerHTML=`<div class="leadershipGrid"><div class="leadershipBlock"><h3>Execution</h3><p><b>${active.length}</b> forecasted</p><p><b>${posted.length}</b> produced</p><p><b>${items.filter(i=>i.status==="blocked").length}</b> blocked</p></div>${blocks("Service-line focus",counts("service_line"))}${blocks("Platform mix",counts("platforms"))}${blocks("Production types",counts("content_type"))}${blocks("Regional focus",counts("region"))}${blocks("Ownership",counts("assigned_name"))}</div><div class="panel" style="margin-top:14px"><h3>Forecast and production record</h3><div class="calendarAgenda">${items.map(item=>this.rowHtml(item,this.isoDate(new Date()))).join("")}</div></div>`;
    },
    clear(){
      ["calId","calTitle","calDue","calPublish","calRegion","calDuration","calTone","calLocation","calPeople","calTalking","calCta","calNotes","calPublishedUrl"].forEach(id=>{if(q(id))q(id).value=""});
      q("calStatus").value="draft";q("calPriority").value="medium";q("calAssigned").value="";q("calService").value="";
      q("calPlatforms").querySelectorAll("input").forEach(input=>input.checked=false);
      q("calFormHeading").textContent="Production Brief";q("calSaveStatus").textContent="";
    },
    newEntry(){this.useExecutionView();this.clear();showTab("calendar");q("calTitle").focus()},
    edit(id){
      const item=(this.state.calendar||[]).find(row=>row.id===id);if(!item)return;
      this.useExecutionView();
      const map={calId:item.id,calTitle:item.title,calStatus:item.status,calPriority:item.priority,calType:item.content_type,calAssigned:item.assigned_to||"",calDue:this.dateOnly(item.due_date),calPublish:String(item.publish_at||"").slice(0,16),calService:item.service_line||"",calRegion:item.region||"",calDuration:item.duration||"",calTone:item.tone||"",calLocation:item.location||"",calPeople:item.people||"",calTalking:item.talking_points||"",calCta:item.cta||"",calNotes:item.notes||"",calPublishedUrl:item.published_url||""};
      Object.entries(map).forEach(([id,value])=>{if(q(id))q(id).value=value});
      const chosen=String(item.platforms||"").split(",").map(x=>x.trim());
      q("calPlatforms").querySelectorAll("input").forEach(input=>input.checked=chosen.includes(input.value));
      q("calFormHeading").textContent="Edit Production Brief";showTab("calendar");window.scrollTo({top:0,behavior:"smooth"});
    },
    payload(){
      return {id:q("calId").value,title:q("calTitle").value,status:q("calStatus").value,priority:q("calPriority").value,content_type:q("calType").value,assigned_to:q("calAssigned").value,due_date:q("calDue").value,publish_at:q("calPublish").value,service_line:q("calService").value,region:q("calRegion").value,platforms:Array.from(q("calPlatforms").querySelectorAll("input:checked")).map(input=>input.value).join(", "),duration:q("calDuration").value,tone:q("calTone").value,location:q("calLocation").value,people:q("calPeople").value,talking_points:q("calTalking").value,cta:q("calCta").value,notes:q("calNotes").value,published_url:q("calPublishedUrl").value,requested_date:new Date().toISOString().slice(0,10),source_type:q("calId").value?"Manual edit":"Manual"};
    },
    async save(){
      try{await api("/api/calendar",this.payload());this.clear();q("calSaveStatus").textContent="Production brief saved to Our Marketing Calendar for the team and Chad.";await load();showTab("calendar")}catch(error){q("calSaveStatus").textContent=error.message}
    },
    async status(id,status){
      await api("/api/calendar-status",{id,status});await load();showTab("calendar");
    },
    prefill(data){
      this.useExecutionView();this.clear();showTab("calendar");
      Object.entries(data).forEach(([id,value])=>{if(q(id))q(id).value=value});
      (data.platforms||[]).forEach(name=>{const input=Array.from(q("calPlatforms").querySelectorAll("input")).find(node=>node.value===name);if(input)input.checked=true});
      q("calFormHeading").textContent="Review Chad's Production Brief";q("calSaveStatus").textContent="Review the brief, assign the owner, and save it to Our Marketing Calendar.";
    },
    async autoForecastStorm(alerts){
      if(!this.state||!alerts||!alerts.length)return;
      const jennifer=(this.state.users||[]).find(user=>/jennifer/i.test(user.name));
      const seen=new Set(),selected=[];
      alerts.forEach(alert=>{const key=`${alert.event||"Storm"}|${alert._state||""}`;if(!seen.has(key)&&selected.length<3){seen.add(key);selected.push(alert)}});
      const due=new Date();due.setDate(due.getDate()+1);
      const publish=new Date();publish.setDate(publish.getDate()+1);publish.setHours(9,0,0,0);
      for(const alert of selected){
        const sourceRef=alert.id||alert["@id"]||`${alert.event}|${alert._state}|${alert.areaDesc}|${alert.sent||alert.effective||""}`;
        await api("/api/calendar",{title:`${alert.event||"Storm"} Response — ${alert._state||"Region"}`,status:"draft",content_type:"Video",platforms:"LinkedIn, Facebook, TikTok, YouTube",assigned_to:jennifer?jennifer.id:"",priority:"urgent",requested_date:new Date().toISOString().slice(0,10),due_date:this.isoDate(due),publish_at:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),service_line:"Storm / CAT Damage",region:alert._state||"",location:alert.areaDesc||"",duration:"60-second master with 15-second cut",tone:"Safety-first, professional, conversational",talking_points:`Active ${alert.event||"weather alert"} in ${alert.areaDesc||alert._state||"the region"}.\n- Lead with public safety while the threat is active.\n- Prepare a clear post-event documentation message.\n- Explain how organized field evidence helps adjusters without implying a coverage decision.`,cta:"Follow local emergency guidance. When conditions are safe, learn how Hancock supports clear property documentation.",source_type:"Storm Watch",source_ref:sourceRef,notes:"Auto-forecasted by Chad from a live National Weather Service alert. Jennifer reviews before production."});
      }
      await load();
    },
    fromStorm(index){
      const alert=(window.HANCOCK_STORM_ALERTS||[])[index];if(!alert)return;
      const due=new Date();due.setDate(due.getDate()+1);const publish=new Date();publish.setDate(publish.getDate()+1);publish.setHours(9,0,0,0);
      this.prefill({calTitle:`${alert.event||"Storm"} Response — ${alert._state||alert.areaDesc||"Region"}`,calType:"Video",calPriority:"urgent",calDue:this.isoDate(due),calPublish:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),calService:"Storm / CAT Damage",calRegion:alert._state||"",calLocation:alert.areaDesc||"",calDuration:"60-second master with 15-second cut",calTone:"Safety-first, professional, conversational",calTalking:`Active ${alert.event||"weather alert"} in ${alert.areaDesc||alert._state||"the region"}.\n- Lead with public safety while the threat is active.\n- Explain what property owners should document only when conditions are safe.\n- Show how clear field documentation helps adjusters and supports a defensible file.\n- Prepare post-event inspection guidance without implying coverage decisions.`,calCta:"Follow local emergency guidance now. After the event, learn how Hancock supports clear property documentation.",platforms:["LinkedIn","Facebook","TikTok","YouTube"]});
    },
    fromRadar(index){
      const story=(window.HANCOCK_BOT_DATA?.stories||[])[index];if(!story)return;
      const due=new Date();due.setDate(due.getDate()+3);const publish=new Date();publish.setDate(publish.getDate()+5);publish.setHours(9,0,0,0);
      this.prefill({calTitle:story.title,calType:"Blog",calPriority:story.tag==="Hot"?"high":"medium",calDue:this.isoDate(due),calPublish:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),calTalking:`Research signal: ${story.summary||""}\nHancock angle: ${story.angle||""}\nVerify source claims, write the core article, then prepare platform-specific promotion.`,calCta:"Learn how Hancock helps carriers build clearer, more defensible inspection files.",platforms:["Website","LinkedIn","Email"]});
    },
    fromContent(){
      const output=q("contentOut")?.innerText.trim()||"",title=(output.match(/^(.+)/)||[])[1]||`${q("contentLine").value} ${q("contentType").value}`;
      const due=new Date();due.setDate(due.getDate()+2);const publish=new Date();publish.setDate(publish.getDate()+4);publish.setHours(9,0,0,0);
      this.prefill({calTitle:title.slice(0,180),calType:q("contentType").value.includes("Blog")?"Blog":"Social Post",calPriority:"medium",calDue:this.isoDate(due),calPublish:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),calService:q("contentLine").value,calRegion:q("region").value,calTone:q("tone").value,calTalking:`Finish and review the generated source asset.\nCreate platform-specific captions and supporting visuals.\nSEO/AEO target: ${q("keywords").value||"confirm target keyword"}.\nHancock angle: ${q("angle").value}`,calCta:"Use the approved CTA from the source asset.",platforms:["Website","LinkedIn"]});
    },
    exportCsv(){
      const rows=[["Title","Status","Type","Platforms","Assigned","Priority","Due","Publish","Service Line","Region","Produced"]];
      this.filtered().forEach(i=>rows.push([i.title,i.status,i.content_type,i.platforms,i.assigned_name||"",i.priority,i.due_date,i.publish_at,i.service_line,i.region,i.completed_at||""]));
      const csv=rows.map(row=>row.map(value=>`"${String(value||"").replace(/"/g,'""')}"`).join(",")).join("\n");
      const blob=new Blob([csv],{type:"text/csv"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="hancock-marketing-calendar.csv";a.click();URL.revokeObjectURL(url);
    }
  };
  window.HancockCalendar=calendar;

  window.HancockLive={
    api,
    refresh:load,
    runBots,
    openChad:()=>window.ChadWidget&&window.ChadWidget.open()
  };
  load();
  setInterval(load,30000);
})();
