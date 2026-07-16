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
      renderAtmosphere();
      renderCrew();
      if(window.HancockEvents)window.HancockEvents.update(state);
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

  function ensureAtmosphere(){
    if(!document.querySelector(".studioBackdrop")){
      const backdrop=document.createElement("div");
      backdrop.className="studioBackdrop";
      backdrop.setAttribute("aria-hidden","true");
      document.body.prepend(backdrop);
    }
    const header=document.querySelector(".header");
    if(header&&!document.getElementById("liveTicker")){
      const ticker=document.createElement("div");
      ticker.id="liveTicker";
      ticker.className="liveTicker";
      ticker.innerHTML='<div class="tickerTrack"><span class="tickerLabel">Live Intelligence</span><span class="tickerItem">Chad is syncing the workspace</span></div>';
      const tabs=document.getElementById("tabs");
      header.insertBefore(ticker,tabs||null);
    }
    const hero=document.querySelector("#radar .hero");
    if(hero&&!document.getElementById("chadPulseBar")){
      const pulse=document.createElement("div");
      pulse.id="chadPulseBar";
      pulse.className="chadPulseBar";
      hero.querySelector("p")?.insertAdjacentElement("afterend",pulse);
    }
  }

  function renderAtmosphere(){
    ensureAtmosphere();
    const trigger=(state.seasonalTriggers||[])[0];
    const calendar=state.calendar||[];
    const teamEvents=state.teamEvents||[];
    const today=new Date().toISOString().slice(0,10);
    const horizon=new Date();horizon.setDate(horizon.getDate()+60);
    const horizonIso=new Date(horizon.getTime()-horizon.getTimezoneOffset()*60000).toISOString().slice(0,10);
    const openCalendar=calendar.filter(item=>!["posted","archived"].includes(item.status)).length;
    const dueToday=calendar.filter(item=>String(item.due_date||"").slice(0,10)===today&&!["posted","archived"].includes(item.status)).length;
    const upcomingEvents=teamEvents.filter(item=>String(item.end_date||item.start_date||"").slice(0,10)>=today&&String(item.start_date||"").slice(0,10)<=horizonIso).sort((a,b)=>String(a.start_date||"").localeCompare(String(b.start_date||"")));
    const botStamp=state.botData&&state.botData.generatedHuman?state.botData.generatedHuman:"scan pending";
    const ticker=q("liveTicker");
    if(ticker){
      const pieces=[
        bots&&bots.ai?"Chad AI online":"Bots online",
        trigger?`${trigger.name}: ${trigger.phase}`:"Seasonal triggers ready",
        upcomingEvents.length?`Next event: ${upcomingEvents[0].title} (${String(upcomingEvents[0].start_date||"").slice(0,10)})`:"Team Events ready",
        dueToday?`${dueToday} production item${dueToday===1?"":"s"} due today`:`${openCalendar} forecasted calendar item${openCalendar===1?"":"s"}`,
        `Latest scan: ${botStamp}`
      ];
      ticker.innerHTML='<div class="tickerTrack"><span class="tickerLabel">Live Intelligence</span>'+pieces.map(piece=>`<span class="tickerItem">${escapeHtml(piece)}</span>`).join("")+'</div>';
    }
    const pulse=q("chadPulseBar");
    if(pulse){
      const items=[
        "Scanning industry signals",
        upcomingEvents.length?`Tracking ${upcomingEvents[0].title}`:"Watching team events",
        trigger?`Watching ${trigger.name}`:"Watching seasonal windows",
        "Preparing content angles"
      ];
      pulse.innerHTML=items.map(item=>`<span class="chadPulsePill">${escapeHtml(item)}</span>`).join("");
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

  const fallbackTeamEvents=[
    {id:"sample-1",title:"NY Claims Assoc Golf Outing (Long Island)",start_date:"2026-07-19",end_date:"2026-07-19",location:"Long Island, NY",category:"Golf Outing",description:"Team event imported from the SharePoint Team Events calendar."},
    {id:"sample-2",title:"KCA Conference (Florence, IN)",start_date:"2026-07-22",end_date:"2026-07-24",location:"Florence, IN",category:"Conference",description:"Team event imported from the SharePoint Team Events calendar."},
    {id:"sample-3",title:"Swing Fore Sight Annual Golf Tournament",start_date:"2026-07-27",end_date:"2026-07-27",location:"",category:"Golf Outing",description:"Team event imported from the SharePoint Team Events calendar."}
  ];

  const events={
    state:null,
    month:new Date(2026,6,1),
    update(next){
      this.state=next;
      if(q("eventsGrid"))this.render();
    },
    dateOnly(value){
      return String(value||"").slice(0,10);
    },
    localDate(value){
      const raw=this.dateOnly(value);
      const parts=raw.split("-").map(Number);
      return parts.length===3&&parts.every(Boolean)?new Date(parts[0],parts[1]-1,parts[2]):null;
    },
    isoDate(date){
      const local=new Date(date.getTime()-date.getTimezoneOffset()*60000);
      return local.toISOString().slice(0,10);
    },
    monthLabel(date){
      return date.toLocaleDateString(undefined,{month:"long",year:"numeric"});
    },
    eventItems(){
      const items=(this.state&&Array.isArray(this.state.teamEvents)&&this.state.teamEvents.length)?this.state.teamEvents:fallbackTeamEvents;
      return items.slice().sort((a,b)=>this.dateOnly(a.start_date).localeCompare(this.dateOnly(b.start_date))||String(a.title||"").localeCompare(String(b.title||"")));
    },
    categoryClass(item){
      const category=String(item.category||"").toLowerCase();
      if(category.includes("conference"))return"conference";
      if(category.includes("golf"))return"golf";
      return"team";
    },
    eventRange(item){
      const start=this.localDate(item.start_date);
      const end=this.localDate(item.end_date||item.start_date)||start;
      return {start,end:end&&start&&end<start?start:end};
    },
    occursOn(item,iso){
      const range=this.eventRange(item);
      if(!range.start||!range.end)return false;
      const start=this.isoDate(range.start),end=this.isoDate(range.end);
      return iso>=start&&iso<=end;
    },
    render(){
      if(!q("eventsGrid"))return;
      this.renderMini();
      this.renderGrid();
      this.renderAgenda();
    },
    renderMini(){
      const year=this.month.getFullYear();
      q("eventsMiniYear").textContent=year;
      const names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      q("eventsMonths").innerHTML=names.map((name,index)=>`<button class="eventsMonthBtn ${index===this.month.getMonth()?"active":""}" onclick="HancockEvents.setMonth(${year},${index})">${name}</button>`).join("");
      const today=new Date();
      q("eventsToday").innerHTML=`Today is <b>${escapeHtml(today.toLocaleDateString(undefined,{weekday:"long",month:"long",day:"numeric",year:"numeric"}))}</b>`;
    },
    renderGrid(){
      const first=new Date(this.month.getFullYear(),this.month.getMonth(),1);
      const start=new Date(first);start.setDate(1-first.getDay());
      const todayIso=this.isoDate(new Date());
      const items=this.eventItems();
      q("eventsMonthTitle").textContent=this.monthLabel(this.month);
      const monthIso=this.isoDate(first).slice(0,7);
      const monthItems=items.filter(item=>this.dateOnly(item.start_date).slice(0,7)===monthIso||this.dateOnly(item.end_date||item.start_date).slice(0,7)===monthIso);
      q("eventsMonthSummary").textContent=`${monthItems.length} team event${monthItems.length===1?"":"s"} in view.`;
      let html=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"].map(day=>`<div class="eventsDow">${day}</div>`).join("");
      for(let i=0;i<42;i++){
        const date=new Date(start);date.setDate(start.getDate()+i);
        const iso=this.isoDate(date),muted=date.getMonth()!==this.month.getMonth();
        const dayItems=items.filter(item=>this.occursOn(item,iso));
        html+=`<div class="eventsDay ${muted?"mutedDay":""}"><div class="eventsDate ${iso===todayIso?"today":""}">${date.getDate()}</div>${dayItems.map(item=>`<button class="teamEvent ${this.categoryClass(item)}" title="${escapeHtml(item.title)}" onclick="HancockEvents.edit('${escapeHtml(item.id)}')">${escapeHtml(item.title)}</button>`).join("")}</div>`;
      }
      q("eventsGrid").innerHTML=html;
    },
    renderAgenda(){
      const month=this.isoDate(new Date(this.month.getFullYear(),this.month.getMonth(),1)).slice(0,7);
      const items=this.eventItems().filter(item=>this.dateOnly(item.start_date).slice(0,7)===month||this.dateOnly(item.end_date||item.start_date).slice(0,7)===month);
      q("eventsAgenda").innerHTML=items.map(item=>{
        const start=this.dateOnly(item.start_date),end=this.dateOnly(item.end_date||item.start_date);
        const span=end&&end!==start?`${start} to ${end}`:start;
        return `<div class="eventsAgendaItem ${this.categoryClass(item)}"><span class="badge">${escapeHtml(item.category||"Team Event")}</span><h3>${escapeHtml(item.title)}</h3><p class="muted">${escapeHtml(span)}${item.location?" · "+escapeHtml(item.location):""}</p>${item.description?`<p>${escapeHtml(item.description)}</p>`:""}<button class="mini" onclick="HancockEvents.edit('${escapeHtml(item.id)}')">Edit</button></div>`;
      }).join("")||'<div class="panel empty"><h3>No events this month</h3><p>Add the next industry conference, outing, or team date.</p></div>';
    },
    setMonth(year,month){
      this.month=new Date(year,month,1);
      this.render();
    },
    shiftYear(delta){
      this.month=new Date(this.month.getFullYear()+delta,this.month.getMonth(),1);
      this.render();
    },
    shiftMonth(delta){
      this.month=new Date(this.month.getFullYear(),this.month.getMonth()+delta,1);
      this.render();
    },
    goToday(){
      const today=new Date();
      this.month=new Date(today.getFullYear(),today.getMonth(),1);
      this.render();
    },
    clear(){
      ["eventId","eventTitle","eventStart","eventEnd","eventLocation","eventDescription","eventSourceUrl"].forEach(id=>{if(q(id))q(id).value=""});
      q("eventCategory").value="Team Event";
      q("eventFormHeading").textContent="Event Details";
      q("eventSaveStatus").textContent="";
    },
    newEvent(){
      this.clear();
      q("eventsForm").classList.add("open");
      const defaultDate=this.isoDate(new Date(this.month.getFullYear(),this.month.getMonth(),1));
      q("eventStart").value=defaultDate;
      q("eventEnd").value=defaultDate;
      q("eventTitle").focus();
    },
    edit(id){
      const item=this.eventItems().find(event=>String(event.id)===String(id));
      if(!item)return;
      q("eventsForm").classList.add("open");
      const map={eventId:item.id,eventTitle:item.title,eventStart:this.dateOnly(item.start_date),eventEnd:this.dateOnly(item.end_date||item.start_date),eventCategory:item.category||"Team Event",eventLocation:item.location||"",eventDescription:item.description||"",eventSourceUrl:item.source_url||""};
      Object.entries(map).forEach(([key,value])=>{if(q(key))q(key).value=value});
      q("eventFormHeading").textContent="Edit Event";
      q("eventSaveStatus").textContent="";
      q("eventsForm").scrollIntoView({behavior:"smooth",block:"start"});
    },
    payload(){
      return {id:q("eventId").value,title:q("eventTitle").value,start_date:q("eventStart").value,end_date:q("eventEnd").value,category:q("eventCategory").value,location:q("eventLocation").value,description:q("eventDescription").value,source_url:q("eventSourceUrl").value};
    },
    async save(){
      try{
        await api("/api/team-event",this.payload());
        q("eventSaveStatus").textContent="Event saved to Team Events. Chad has the updated event context.";
        this.clear();
        await load();
        showTab("events");
      }catch(error){
        q("eventSaveStatus").textContent=error.message;
      }
    },
    async remove(){
      const id=q("eventId").value;
      if(!id){q("eventSaveStatus").textContent="Choose an event first.";return}
      try{
        await api("/api/team-event-delete",{id});
        this.clear();
        await load();
        showTab("events");
      }catch(error){
        q("eventSaveStatus").textContent=error.message;
      }
    }
  };
  window.HancockEvents=events;

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
        const h=alert._hancock||alert;
        const service=h.service||h.service_line||"Storm / CAT Damage";
        const hazard=h.hazard||alert.event||"Storm";
        const angle=h.angle||h.content_angle||"Prepare clear post-event documentation guidance without implying coverage decisions.";
        const sourceRef=alert.id||alert["@id"]||`${alert.event}|${alert._state}|${alert.areaDesc}|${alert.sent||alert.effective||""}`;
        await api("/api/calendar",{title:`${hazard} Response — ${alert._state||alert.state||"Region"}`,status:"draft",content_type:"Video",platforms:"LinkedIn, Facebook, TikTok, YouTube",assigned_to:jennifer?jennifer.id:"",priority:"urgent",requested_date:new Date().toISOString().slice(0,10),due_date:this.isoDate(due),publish_at:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),service_line:service,region:alert._state||alert.state||"",location:alert.areaDesc||alert.areas||"",duration:"60-second master with 15-second cut",tone:"Safety-first, professional, conversational",talking_points:`Active ${hazard} signal in ${alert.areaDesc||alert.areas||alert._state||alert.state||"the region"}.\n- Lead with public safety while the threat is active.\n- Hancock angle: ${angle}\n- Explain how organized field evidence helps adjusters without implying a coverage decision.`,cta:"Follow local emergency guidance. When conditions are safe, learn how Hancock supports clear property documentation.",source_type:"Storm Watch",source_ref:sourceRef,notes:"Auto-forecasted by Chad from a live official weather alert. Jennifer reviews before production."});
      }
      await load();
    },
    fromStorm(index){
      const alert=(window.HANCOCK_STORM_ALERTS||[])[index];if(!alert)return;
      const h=alert._hancock||alert;
      const service=h.service||h.service_line||"Storm / CAT Damage";
      const hazard=h.hazard||alert.event||"Storm";
      const angle=h.angle||h.content_angle||"Prepare clear post-event documentation guidance without implying coverage decisions.";
      const due=new Date();due.setDate(due.getDate()+1);const publish=new Date();publish.setDate(publish.getDate()+1);publish.setHours(9,0,0,0);
      this.prefill({calTitle:`${hazard} Response — ${alert._state||alert.state||alert.areaDesc||alert.areas||"Region"}`,calType:"Video",calPriority:"urgent",calDue:this.isoDate(due),calPublish:new Date(publish.getTime()-publish.getTimezoneOffset()*60000).toISOString().slice(0,16),calService:service,calRegion:alert._state||alert.state||"",calLocation:alert.areaDesc||alert.areas||"",calDuration:"60-second master with 15-second cut",calTone:"Safety-first, professional, conversational",calTalking:`Active ${hazard} signal in ${alert.areaDesc||alert.areas||alert._state||alert.state||"the region"}.\n- Lead with public safety while the threat is active.\n- Hancock angle: ${angle}\n- Explain what property owners should document only when conditions are safe.\n- Show how clear field documentation helps adjusters and supports a defensible file.`,calCta:"Follow local emergency guidance now. After the event, learn how Hancock supports clear property documentation.",platforms:["LinkedIn","Facebook","TikTok","YouTube"]});
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
