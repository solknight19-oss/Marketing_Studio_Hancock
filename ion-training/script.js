const slides = [
  {
    section: "Open ION App",
    title: "Open the ION dashboard",
    image: "IMG_3424.PNG",
    hotspot: [24, 28],
    summary: "Start from the Hancock Claims Consultants home screen powered by ION. The trainee begins by opening the Inbox because new underwriting assignments arrive there.",
    actions: [
      "Open the ION app on the phone.",
      "Confirm the dashboard loads and shows Inbox, Drafts, Outbox, Sent, Search, and Group Inbox.",
      "Tap Inbox to find the assignment that needs to be completed."
    ],
    fields: [
      ["Starting tile", "Inbox"],
      ["Assignment count", "3 visible items"],
      ["Expected status", "New or editable assignment"]
    ],
    checks: [
      "Refresh if the Inbox count looks stale.",
      "Do not begin from Drafts unless you already started the form.",
      "Confirm the app is online before field work."
    ],
    practice: "Tap the Inbox tile and explain why Outbox should be checked after submission.",
    filled: "The trainee chooses Inbox because this is where new assignments are received. Outbox is only used later to verify the completed form uploaded."
  },
  {
    section: "Inbox",
    title: "Select the correct underwriting report",
    image: "IMG_3425.PNG",
    hotspot: [58, 39],
    summary: "The Inbox lists open reports. The trainee selects the assigned underwriting report and checks the name/date before opening it.",
    actions: [
      "Stay on the List tab unless you need map routing.",
      "Find the assignment title that matches the insured or claim file.",
      "Tap the correct report row to open the ION Underwriting Form."
    ],
    fields: [
      ["Assignment", "Insured Guy Underwriting Report"],
      ["Form type", "test UW form"],
      ["Backup example", "Insured Lady Underwriting Report 2026-05-11"]
    ],
    checks: [
      "Do not open an assignment only because it is first in the list.",
      "Compare the insured name and date against the work order.",
      "If the assignment is missing, refresh before calling support."
    ],
    practice: "Choose the correct report for the sample property: Insured Guy at 12321 Kingdom Way.",
    filled: "Selected: Insured Guy Underwriting Report. Reason: it matches the sample insured and property file used throughout this training."
  },
  {
    section: "ION Underwriting Form",
    title: "Review the required sections before entering data",
    image: "IMG_3455.PNG",
    hotspot: [49, 30],
    summary: "The form overview shows every required section. Red warning icons mean a required section is incomplete.",
    actions: [
      "Open the ION Underwriting Form.",
      "Scan the section list from top to bottom before typing.",
      "Plan to complete the form in order: instructions, inspector ID, home information, exterior, roof, interior, electrical, plumbing, HVAC, and wrap up."
    ],
    fields: [
      ["Required sections", "9 major sections"],
      ["Warning meaning", "Required fields still missing"],
      ["Submission button", "Send appears when the form is ready"]
    ],
    checks: [
      "Do not skip ahead just because a section opens.",
      "Use the arrows only after completing the visible required fields.",
      "Return to sections with warning icons before sending."
    ],
    practice: "Name the first three required sections the trainee should complete.",
    filled: "Start Here Instructions, Inspector Identification, and Home Information are completed first."
  },
  {
    section: "START HERE! INSTRUCTIONS",
    title: "Read the pre-inspection duties",
    image: "IMG_3428.PNG",
    hotspot: [88, 9],
    summary: "The instructions explain what the inspector must do before, during, and after the property visit.",
    actions: [
      "Read the pre-inspection section before going onsite.",
      "Search the property online for street view and access concerns.",
      "Save a satellite image and floorplan if available.",
      "Contact the insured and schedule the inspection.",
      "Remember to check Outbox after submitting the completed form."
    ],
    fields: [
      ["Pre-inspection", "Research property online"],
      ["Required saved item", "Satellite view screenshot"],
      ["Required follow-up", "Check Outbox after sending"]
    ],
    checks: [
      "Bring any ladder/access needs discovered from street view.",
      "Keep photos clear and taken from inside the ION app when required.",
      "Submit before leaving the risk whenever possible."
    ],
    practice: "List the two screenshots the trainee should save before the inspection.",
    filled: "Saved before arrival: satellite view screenshot and available floorplan screenshot."
  },
  {
    section: "Inspector Identification*",
    title: "Confirm inspector information",
    image: "IMG_3429.PNG",
    hotspot: [90, 94],
    summary: "The inspector verifies their identity, enters N/A for the license number, confirms phone and email, then checks the confirmation box.",
    actions: [
      "Review the inspector name.",
      "For Inspector License Number, type N/A for now.",
      "Enter or confirm the inspector phone number.",
      "Confirm the email address is correct.",
      "Check the confirmation box stating you are the assigned inspector completing the inspection."
    ],
    fields: [
      ["Inspector Name", "Ryan Knight"],
      ["License Number", "N/A"],
      ["Phone Number", "(727) 555-0198"],
      ["Email Address", "rknight@hancockclaims.com"],
      ["Confirmation", "Checked"]
    ],
    checks: [
      "Use the assigned inspector's information, not the trainee's practice data.",
      "Inspector License Number should be entered as N/A until Hancock gives different guidance.",
      "Make sure the email address is spelled correctly.",
      "The confirmation checkbox is required."
    ],
    practice: "Enter N/A for the license number, fill the missing phone field, and check the confirmation box.",
    filled: "Inspector License Number: N/A. Inspector Phone Number: (727) 555-0198. Confirmation: checked."
  },
  {
    section: "Home Information*",
    title: "Enter home and insured information",
    image: "IMG_3431.PNG",
    hotspot: [48, 79],
    summary: "This section records the insured, property address, county, policy number, community type, occupancy, and inspection setup details.",
    actions: [
      "Enter the insured name exactly as shown on the assignment.",
      "Enter the full risk address, including city and state.",
      "Confirm the county and policy number.",
      "Select the community type and occupancy from the dropdowns."
    ],
    fields: [
      ["Insured Name", "Insured Guy"],
      ["Risk Address", "12321 Kingdom Way, Hudson, FL, USA"],
      ["County", "Hernando"],
      ["Policy Number", "PN8973478"],
      ["Community Type", "Residential neighborhood"],
      ["Occupancy", "Owner occupied"]
    ],
    checks: [
      "Match the address to the work order before taking photos.",
      "County and policy number should not be guessed.",
      "Dropdowns must be selected; placeholder text is not an answer."
    ],
    practice: "Complete the two blank dropdowns using the sample file.",
    filled: "Community type: Residential neighborhood. Occupancy: Owner occupied."
  },
  {
    section: "Home Information*",
    title: "Capture date, risk ID, location, and map evidence",
    image: "IMG_3432.PNG",
    hotspot: [50, 70],
    summary: "Before moving into the property details, the trainee records the inspection date, uploads the risk identification photo, captures geolocation, and uploads the satellite view.",
    actions: [
      "Set the date and time of the inspection.",
      "Upload one clear risk identification photo.",
      "Stand within 10 feet of the front door and tap to acquire location.",
      "Upload the satellite view screenshot saved before arrival."
    ],
    fields: [
      ["Inspection Date/Time", "07/08/2026 10:00 AM"],
      ["Risk ID Photo", "Front address marker photo"],
      ["Geo Location", "Acquired at front door"],
      ["Satellite View", "Maps screenshot uploaded"]
    ],
    checks: [
      "Location capture should be done onsite, not from the vehicle down the street.",
      "The risk ID photo should prove the correct property.",
      "Satellite screenshot should show the full structure and surroundings."
    ],
    practice: "Mark the geolocation field complete and describe where you should stand.",
    filled: "Geo location acquired while standing within 10 feet of the property's front door."
  },
  {
    section: "Home Information*",
    title: "Fill property characteristics",
    image: "IMG_3433.PNG",
    hotspot: [48, 26],
    summary: "Four Point Data captures construction year, dwelling type, bed/bath counts, foundation, fire hydrant distance, road access, grade, and water exposure.",
    actions: [
      "Enter the year of construction.",
      "Select dwelling type and foundation type.",
      "Enter bedroom and bathroom counts.",
      "Answer property condition questions such as paved road access, waterfront, below grade, pool, trampoline, debris, overhanging trees, railings, animals, and other structures."
    ],
    fields: [
      ["Year of Construction", "2004"],
      ["Dwelling Type", "Single family"],
      ["Bedrooms", "3"],
      ["Bathrooms", "2"],
      ["Foundation Type", "Slab"],
      ["Fire Hydrant Distance", "Within 1,000 feet"],
      ["Paved Road", "Yes"],
      ["Waterfront", "No"]
    ],
    checks: [
      "Use observed facts and assignment data, not assumptions.",
      "If a hazard is present, add notes and photos where prompted.",
      "Every required yes/no dropdown must be answered."
    ],
    practice: "Fill the core property details for the sample single-family home.",
    filled: "2004 single-family home, 3 bedrooms, 2 bathrooms, slab foundation, within 1,000 feet of a hydrant, paved road access, not waterfront."
  },
  {
    section: "Exterior Inspection*",
    title: "Photograph all elevations and exterior conditions",
    image: "IMG_3435.PNG",
    hotspot: [48, 39],
    summary: "The exterior section requires overview photos for every elevation and asks whether there are damages or discrepancies.",
    actions: [
      "Upload front elevation overview photos.",
      "Upload left, rear, and right elevation overview photos.",
      "Upload AC system exterior photos if prompted here.",
      "Answer whether any elevation damage or discrepancy was observed.",
      "Select construction type and siding material."
    ],
    fields: [
      ["Front Elevation", "2 overview photos"],
      ["Left Elevation", "2 overview photos"],
      ["Rear Elevation", "2 overview photos"],
      ["Right Elevation", "2 overview photos"],
      ["Exterior Damage", "No"],
      ["Construction Type", "Masonry"],
      ["Siding Material", "Stucco"]
    ],
    checks: [
      "Photograph straight-on overview shots before close-ups.",
      "Capture all sides even when no damage is present.",
      "If selecting Other for siding, enter the material in the text field."
    ],
    practice: "Complete the exterior section for a no-damage masonry/stucco home.",
    filled: "All four elevation photo groups uploaded. Damage: No. Construction type: Masonry. Siding: Stucco."
  },
  {
    section: "Roof Inspection*",
    title: "Document roof slopes, damages, and materials",
    image: "IMG_3441.PNG",
    hotspot: [50, 50],
    summary: "The roof workflow starts with slope photos, then damage questions, then roof shape, covering material, age, condition, gutters, porch, and permit dates.",
    actions: [
      "Upload front, left, rear, and right roof slope photos.",
      "Upload optional extra roof photos if useful.",
      "Answer whether roof damage or discrepancies were observed.",
      "Select roof shape, covering material, condition, gutters, and porch details.",
      "Enter permit dates if they are verified."
    ],
    fields: [
      ["Roof Slope Photos", "Front, left, rear, right"],
      ["Roof Damage", "No"],
      ["Primary Roof Shape", "Hip"],
      ["Covering Material", "Asphalt shingles"],
      ["Covering Age", "1 year"],
      ["Covering Condition", "Good"],
      ["Gutters Installed", "Yes"]
    ],
    checks: [
      "Roof photos should show each slope clearly.",
      "Do not enter permit dates unless verified.",
      "If damage is observed, describe location and severity."
    ],
    practice: "Fill the roof material section using the sample values.",
    filled: "Primary roof shape: Hip. Covering: Asphalt shingles. Age: 1 year. Condition: Good. Gutters: Yes."
  },
  {
    section: "Interior Inspection*",
    title: "Upload floorplan and add each room",
    image: "IMG_3446.PNG",
    hotspot: [22, 89],
    summary: "Interior documentation starts with smoke/renovation questions and a floorplan upload, then each room is added as a separate entry.",
    actions: [
      "Answer whether smoke detectors are installed.",
      "Answer whether renovations are in progress.",
      "Upload a sketch, floorplan, or diagram showing how rooms connect.",
      "Tap Add Entry for each room inspected.",
      "Choose the room type, answer whether damage exists, and upload overview photos."
    ],
    fields: [
      ["Smoke Detectors", "Yes"],
      ["Renovations", "No"],
      ["Floorplan", "Uploaded"],
      ["Room Entry", "Bathroom 1"],
      ["Room Damage", "No"],
      ["Room Photos", "2 overview photos"]
    ],
    checks: [
      "Every room inspected should have its own entry.",
      "Use Other only when the room name is not available in the dropdown.",
      "If damage exists, create a room-specific note and photo set."
    ],
    practice: "Add Bathroom 1 as a room with no issues and required overview photos.",
    filled: "Room type: Bathroom 1. Damages/discrepancies: No. Overview photos: uploaded."
  },
  {
    section: "Electrical Inspection*",
    title: "Document electrical photos and panel details",
    image: "IMG_3447.PNG",
    hotspot: [48, 55],
    summary: "Electrical requires photos of the system, main panel, panel labels, damage/discrepancy answer, and panel information.",
    actions: [
      "Upload photos of electrical systems inside the dwelling.",
      "Upload main electrical panel photos.",
      "Upload close-up label photos inside the panel box.",
      "Answer whether electrical damage or discrepancies exist.",
      "Enter panel location, manufacturer, disconnect amperage rating, and wiring type."
    ],
    fields: [
      ["System Photos", "Uploaded"],
      ["Main Panel Photos", "Uploaded"],
      ["Panel Label Photos", "Uploaded"],
      ["Electrical Damage", "No"],
      ["Main Panel Location", "Garage"],
      ["Panel Manufacturer", "Square D"],
      ["Disconnect Rating", "200 amp"],
      ["Wiring Type", "Copper"]
    ],
    checks: [
      "Label photos must be close enough to read.",
      "Open-panel photos should follow safety rules and company policy.",
      "If exposed wiring exists, photograph and note it."
    ],
    practice: "Fill the panel info for a standard garage panel.",
    filled: "Main panel location: Garage. Manufacturer: Square D. Disconnect rating: 200 amp. Wiring type: Copper."
  },
  {
    section: "Plumbing Inspection*",
    title: "Document plumbing and water heater information",
    image: "IMG_3450.PNG",
    hotspot: [48, 60],
    summary: "Plumbing requires photos of supply lines, valves, the water heater, labels, material selections, locations, manufacture year, and installation height.",
    actions: [
      "Upload plumbing system photos, including supply lines and valves under sinks and toilets.",
      "Upload water heater overview photos.",
      "Upload close-up photos of water heater labels.",
      "Use ChatGPT as a helper if you need plain-language support identifying visible plumbing materials or reading label information from a clear photo.",
      "Select branch plumbing material, supply line material, and branch drain material.",
      "Select water main and water heater locations.",
      "Enter water heater manufacture year and installation height if raised."
    ],
    fields: [
      ["Branch Plumbing", "CPVC"],
      ["Supply Lines", "Braided stainless"],
      ["Branch Drain", "PVC"],
      ["Water Main Location", "Exterior side wall"],
      ["Water Heater Location", "Garage"],
      ["Water Heater Year", "2021"],
      ["Height Off Ground", "18 inches"]
    ],
    checks: [
      "Photograph labels until the model/serial information is readable.",
      "Use material selections based on observation.",
      "ChatGPT suggestions should be verified against what you can clearly see onsite.",
      "If installed on the floor, the height field may be left blank only when the form allows it."
    ],
    practice: "Complete the plumbing system info for the sample home.",
    filled: "Branch plumbing: CPVC. Supply line: Braided stainless. Drain: PVC. Water heater: garage, 2021, 18 inches off ground."
  },
  {
    section: "Plumbing Inspection*",
    title: "Use ChatGPT to help with plumbing and HVAC wording",
    image: "IMG_3450.PNG",
    hotspot: [50, 28],
    summary: "ChatGPT can be used as a field support tool when a trainee is unsure how to describe visible plumbing or HVAC items. It should help explain, organize, and draft answers, not replace the inspector's observation.",
    actions: [
      "Take a clear close-up photo of the label, component, valve, line, panel, or unit you are trying to identify.",
      "Ask ChatGPT a focused question using the exact field name from ION.",
      "Include what you can see: material color, markings, location, label text, and whether the system appears damaged.",
      "Use the answer to understand the likely wording or dropdown choice.",
      "Verify the suggestion against the property before entering the final ION answer."
    ],
    fields: [
      ["Good plumbing prompt", "Based on this photo, what plumbing material appears to be visible under this sink? I need help choosing the ION field for supply line material."],
      ["Good HVAC prompt", "Can you help me read this HVAC label and identify the manufacture year or model information visible in the photo?"],
      ["Good wording prompt", "Rewrite this note clearly for an underwriting inspection: no visible leaks at water heater, label readable, garage location."],
      ["Do not do", "Do not ask ChatGPT to guess when the photo is unclear."]
    ],
    checks: [
      "Never enter a ChatGPT answer that you cannot confirm from the photo, label, or onsite observation.",
      "Avoid sharing claim-sensitive personal details unless your company policy allows it.",
      "If ChatGPT says it is uncertain, take a better photo or ask a supervisor.",
      "Final responsibility stays with the inspector completing the ION form."
    ],
    practice: "Write a safe ChatGPT prompt for identifying an HVAC label from a photo.",
    filled: "Example: I am completing an ION underwriting inspection. From this clear HVAC label photo, what manufacture year and model information are visible? If you cannot read it, say what is unclear rather than guessing."
  },
  {
    section: "HVAC Inspection*",
    title: "Document HVAC photos, function, location, and age",
    image: "IMG_3452.PNG",
    hotspot: [48, 64],
    summary: "HVAC requires system and label photos, a damage answer, then HVAC type, normal function, location, and manufacture year.",
    actions: [
      "Upload overview photos of the HVAC system.",
      "Upload close-up photos of HVAC labels.",
      "Use ChatGPT to help read label text or draft a clear note when the label photo is readable.",
      "Answer whether there are HVAC damages or discrepancies.",
      "Select HVAC type and whether it functions normally.",
      "Select location and enter the manufacture year."
    ],
    fields: [
      ["HVAC Photos", "Uploaded"],
      ["Label Photos", "Uploaded"],
      ["HVAC Damage", "No"],
      ["HVAC Type", "Split system"],
      ["Functioning Normally", "Yes"],
      ["HVAC Location", "Exterior side yard"],
      ["Manufacture Year", "2020"]
    ],
    checks: [
      "Label photos should show brand, model, and serial when possible.",
      "Do not let ChatGPT infer manufacture year from a blurry or incomplete label.",
      "If the system is not functioning, describe the observed condition.",
      "Use observed location wording that is easy for desk review to understand."
    ],
    practice: "Fill the HVAC section for a normally functioning split system.",
    filled: "HVAC type: Split system. Function: Yes. Location: Exterior side yard. Manufacture year: 2020."
  },
  {
    section: "Inspection Wrap Up*",
    title: "Answer final questions and sign",
    image: "IMG_3454.PNG",
    hotspot: [88, 94],
    summary: "The final section asks about code issues, business use, insurability, final remarks, and the inspector signature before sending.",
    actions: [
      "Answer whether possible code issues were observed.",
      "Answer whether a business is located on premises.",
      "Answer whether you would insure the home based on observed conditions.",
      "Enter final remarks when there is anything important not already covered.",
      "Initial/sign the acknowledgement that the inspection is truthful.",
      "Tap Send only after every required section is complete."
    ],
    fields: [
      ["Possible Code Issues", "No"],
      ["Business On Premises", "No"],
      ["Would Insure", "Yes"],
      ["Final Remarks", "No additional concerns observed during inspection."],
      ["Signature", "RK"],
      ["Final Action", "Send"]
    ],
    checks: [
      "Do not use final remarks to replace missing section notes.",
      "Signature confirms the answers are truthful.",
      "If Send is blocked, return to sections with warning icons."
    ],
    practice: "Complete the final questions and prepare the form for sending.",
    filled: "Code issues: No. Business: No. Would insure: Yes. Remarks: No additional concerns observed during inspection. Signature: RK."
  },
  {
    section: "Outbox Check",
    title: "Verify upload and keep the report with the file",
    image: "IMG_3424.PNG",
    hotspot: [24, 54],
    summary: "After sending, the trainee should confirm the report leaves the device and does not remain stuck in Outbox.",
    actions: [
      "Return to the dashboard after tapping Send.",
      "Open Outbox and confirm the completed form is not stuck there.",
      "If an item remains in Outbox, reconnect to service or Wi-Fi and refresh.",
      "Use Sent to confirm the submission if needed.",
      "Keep the generated underwriting report with the claim file."
    ],
    fields: [
      ["Outbox", "0 items expected"],
      ["Sent", "Completed report visible"],
      ["Training report", "JAMIE KNIGHT - ION Underwriting Report.pdf"],
      ["Completion status", "Uploaded"]
    ],
    checks: [
      "Outbox count should be zero after upload.",
      "Never assume the form submitted until upload is confirmed.",
      "Escalate if the form remains in Outbox after reconnecting."
    ],
    practice: "Explain what to do if the form remains in Outbox.",
    filled: "Reconnect to service or Wi-Fi, refresh/sync the app, and confirm the Outbox clears before leaving the file unresolved."
  }
];

let current = 0;
let practice = false;
const completed = new Set();

const el = {
  progressText: document.getElementById("progressText"),
  progressPercent: document.getElementById("progressPercent"),
  progressBar: document.getElementById("progressBar"),
  stepNav: document.getElementById("stepNav"),
  screenLabel: document.getElementById("screenLabel"),
  screenFile: document.getElementById("screenFile"),
  screenImage: document.getElementById("screenImage"),
  hotspot: document.getElementById("hotspot"),
  sectionName: document.getElementById("sectionName"),
  lessonTitle: document.getElementById("lessonTitle"),
  lessonSummary: document.getElementById("lessonSummary"),
  actionList: document.getElementById("actionList"),
  sampleFields: document.getElementById("sampleFields"),
  qualityList: document.getElementById("qualityList"),
  practicePrompt: document.getElementById("practicePrompt"),
  filledPreview: document.getElementById("filledPreview"),
  fillButton: document.getElementById("fillButton"),
  guideMode: document.getElementById("guideMode"),
  practiceMode: document.getElementById("practiceMode"),
  prevButton: document.getElementById("prevButton"),
  nextButton: document.getElementById("nextButton"),
  completeButton: document.getElementById("completeButton")
};

function renderNav() {
  el.stepNav.innerHTML = "";
  slides.forEach((slide, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "step-link";
    if (index === current) button.classList.add("active");
    if (completed.has(index)) button.classList.add("complete");
    button.innerHTML = `<span class="step-number">${completed.has(index) ? "OK" : index + 1}</span><span>${slide.section}</span>`;
    button.addEventListener("click", () => {
      current = index;
      render();
    });
    el.stepNav.appendChild(button);
  });
}

function listItems(target, items, ordered) {
  target.innerHTML = "";
  items.forEach((item) => {
    const child = document.createElement("li");
    child.textContent = item;
    target.appendChild(child);
  });
}

function renderFields(fields) {
  el.sampleFields.innerHTML = "";
  fields.forEach(([name, value]) => {
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `<div class="field-name">${name}</div><div class="field-value">${value}</div>`;
    el.sampleFields.appendChild(row);
  });
}

function render() {
  const slide = slides[current];
  const percent = Math.round(((current + 1) / slides.length) * 100);
  el.progressText.textContent = `Step ${current + 1} of ${slides.length}`;
  el.progressPercent.textContent = `${percent}%`;
  el.progressBar.style.width = `${percent}%`;
  el.screenLabel.textContent = slide.section;
  el.screenFile.textContent = slide.image;
  el.screenImage.src = `assets/${slide.image}`;
  el.screenImage.alt = `${slide.section} screenshot`;
  el.hotspot.style.left = `${slide.hotspot[0]}%`;
  el.hotspot.style.top = `${slide.hotspot[1]}%`;
  el.sectionName.textContent = slide.section;
  el.lessonTitle.textContent = slide.title;
  el.lessonSummary.textContent = slide.summary;
  listItems(el.actionList, slide.actions);
  renderFields(slide.fields);
  listItems(el.qualityList, slide.checks);
  el.practicePrompt.textContent = slide.practice;
  el.filledPreview.textContent = slide.filled;
  el.filledPreview.classList.remove("show");
  el.fillButton.textContent = practice ? "Show Filled Example" : "Reveal Practice Answer";
  el.prevButton.disabled = current === 0;
  el.nextButton.disabled = current === slides.length - 1;
  el.completeButton.textContent = completed.has(current) ? "Step Complete" : "Mark Step Complete";
  el.completeButton.disabled = completed.has(current);
  el.guideMode.classList.toggle("active", !practice);
  el.practiceMode.classList.toggle("active", practice);
  document.body.classList.toggle("practice", practice);
  renderNav();
}

el.prevButton.addEventListener("click", () => {
  if (current > 0) {
    current -= 1;
    render();
  }
});

el.nextButton.addEventListener("click", () => {
  if (current < slides.length - 1) {
    current += 1;
    render();
  }
});

el.completeButton.addEventListener("click", () => {
  completed.add(current);
  render();
});

el.fillButton.addEventListener("click", () => {
  el.filledPreview.classList.toggle("show");
});

el.guideMode.addEventListener("click", () => {
  practice = false;
  render();
});

el.practiceMode.addEventListener("click", () => {
  practice = true;
  render();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight" && current < slides.length - 1) {
    current += 1;
    render();
  }
  if (event.key === "ArrowLeft" && current > 0) {
    current -= 1;
    render();
  }
});

render();
