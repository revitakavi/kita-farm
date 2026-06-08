// KITA FARM Dashboard - Application Core Logic

// 1. Database of 14 Zones (24 Tables total - โรงเรือน 1 เดิม)
// Total Holes: 5,520 (โต๊ะละ 230 หลุม)
const ZONES_DATA = {
    1: { name: "โซน 1 (บ่อปุ๋ย 1 - ผักน้ำหนักน้อย)", tables: "โต๊ะ 1, 2", holes: 460, type: "lightweight" },
    2: { name: "โซน 2 (บ่อปุ๋ย 1 - ผักน้ำหนักน้อย)", tables: "โต๊ะ 3, 4", holes: 460, type: "lightweight" },
    3: { name: "โซน 3 (บ่อปุ๋ย 2 - ผักหลัก)", tables: "โต๊ะ 5, 6", holes: 460, type: "main" },
    4: { name: "โซน 4 (บ่อปุ๋ย 2 - ผักหลัก)", tables: "โต๊ะ 7, 8", holes: 460, type: "main" },
    5: { name: "โซน 5 (บ่อปุ๋ย 3 - ผักหลัก)", tables: "โต๊ะ 9, 10", holes: 460, type: "main" },
    6: { name: "โซน 6 (บ่อปุ๋ย 3 - ผักหลัก)", tables: "โต๊ะ 11, 12", holes: 460, type: "main" },
    7: { name: "โซน 7 (บ่อปุ๋ย 4 - ผักหลัก)", tables: "โต๊ะ 13, 14", holes: 460, type: "main" },
    8: { name: "โซน 8 (บ่อปุ๋ย 4 - ผักหลัก)", tables: "โต๊ะ 15, 16", holes: 460, type: "main" },
    9: { name: "โซน 9 (บ่อปุ๋ย 5 - ผักหลัก)", tables: "โต๊ะ 17, 18", holes: 460, type: "main" },
    10: { name: "โซน 10 (บ่อปุ๋ย 5 - ผักหลัก)", tables: "โต๊ะ 19, 20", holes: 460, type: "main" },
    11: { name: "โซน 11 (บ่อปุ๋ย 6 - ผักหลัก)", tables: "โต๊ะ 21", holes: 230, type: "main" },
    12: { name: "โซน 12 (บ่อปุ๋ย 6 - ผักหลัก)", tables: "โต๊ะ 22", holes: 230, type: "main" },
    13: { name: "โซน 13 (บ่อปุ๋ย 6 - ผักหลัก)", tables: "โต๊ะ 23", holes: 230, type: "main" },
    14: { name: "โซน 14 (บ่อปุ๋ย 6 - ผักหลัก)", tables: "โต๊ะ 24", holes: 230, type: "main" }
};

const FIXED_COST_24_TABLES = 32824; // 26,000 wages (2 people) + 6,824 electricity
const VARIABLE_COST_PER_KG = 12;

// Initialize System on load
document.addEventListener("DOMContentLoaded", () => {
    // Set default date to today
    const today = new Date();
    const formattedDate = today.toISOString().substring(0, 10);
    document.getElementById("start-date-input").value = formattedDate;
    document.getElementById("live-date").innerText = formatDateThai(today);

    // Build zone selection options
    const zoneSelect = document.getElementById("zone-select");
    for (let i = 1; i <= 14; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.innerText = `โซนที่ ${i} - ${ZONES_DATA[i].name} (${ZONES_DATA[i].holes} หลุม)`;
        zoneSelect.appendChild(opt);
    }

    // Run calculations
    generateCalendar();
    calculateSeeds();
    updateSalesMix();
});

// Tab Switcher
function switchTab(tabId) {
    const tabs = document.querySelectorAll(".tab-content");
    const buttons = document.querySelectorAll(".tab-btn");

    tabs.forEach(t => t.classList.remove("active"));
    buttons.forEach(b => b.classList.remove("active"));

    document.getElementById(tabId).classList.add("active");
    
    // Find matching button
    for (let btn of buttons) {
        if (
            (tabId === 'overview' && btn.innerText.includes('แดชบอร์ด')) ||
            (tabId === 'content-studio' && btn.innerText.includes('จีจี้')) ||
            (tabId === 'employee-portal' && btn.innerText.includes('น้องกิ๊ก')) ||
            (tabId === 'coordination' && btn.innerText.includes('ประสานงาน')) ||
            (tabId === 'calendar' && btn.innerText.includes('ปฏิทิน')) ||
            (tabId === 'inventory' && btn.innerText.includes('ควบคุม')) ||
            (tabId === 'sales' && btn.innerText.includes('จำลอง')) ||
            (tabId === 'guide' && btn.innerText.includes('Google Sheets'))
        ) {
            btn.classList.add("active");
            break;
        }
    }
}

// Format Date to Thai Language Format
function formatDateThai(dateObj) {
    const months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ];
    return `${dateObj.getDate()} ${months[dateObj.getMonth()]} ${dateObj.getFullYear() + 543}`;
}

// Generate the 14-zone crop calendar loop
function generateCalendar() {
    const startInput = document.getElementById("start-date-input").value;
    if (!startInput) return;

    const tableBody = document.getElementById("calendar-table-body");
    tableBody.innerHTML = "";

    let currentDate = new Date(startInput);

    // Generate 15 rows (covering 30 days, every 2 days step)
    for (let i = 0; i < 15; i++) {
        // Zone index loops from 1 to 14
        const zoneIndex = (i % 14) + 1;
        const zone = ZONES_DATA[zoneIndex];
        
        // Date math
        const rowDate = new Date(currentDate);
        rowDate.setDate(currentDate.getDate() + (i * 2));

        const tr = document.createElement("tr");

        // Format dates
        const dateStr = formatDateThai(rowDate);
        const transplantSowDate = new Date(rowDate);
        transplantSowDate.setDate(rowDate.getDate() - 14);
        const sowStr = formatDateThai(transplantSowDate);

        // Highlight lightweight zone
        const badgeClass = zone.type === 'lightweight' ? 'badge-light' : 'badge-main';
        const typeLabel = zone.type === 'lightweight' ? 'ผักน้ำหนักน้อย' : 'ผักหลัก';

        tr.innerHTML = `
            <td><strong>${dateStr}</strong></td>
            <td>
                <span class="badge ${badgeClass}">${typeLabel}</span><br>
                <strong>${zone.name}</strong><br>
                <small style="color: var(--text-secondary);">${zone.tables}</small>
            </td>
            <td>${zone.holes} หลุม</td>
            <td>💚 ตัดผักขายได้สุทธิ: <strong>${Math.round(zone.holes * 0.9)} ต้น</strong> (≈ ${Math.round(zone.holes * 0.09)} กก.)</td>
            <td>🧹 ล้างโต๊ะขจัดคราบปุ๋ย</td>
            <td>🌱 ย้ายกล้าลงรางใหญ่<br><small style="color: var(--text-secondary);">*เพาะแตะฟองน้ำเมื่อ: ${sowStr}</small></td>
        `;

        tableBody.appendChild(tr);
    }
}

// Copy calendar data formatted for Telegram
function copyCalendarToTelegram() {
    const startInput = document.getElementById("start-date-input").value;
    if (!startInput) return;

    let currentDate = new Date(startInput);
    let output = "📋 *ตารางการปฏิบัติงาน KITA FARM (อัปเดตคนงาน)*\n\n";

    for (let i = 0; i < 5; i++) {
        const zoneIndex = (i % 14) + 1;
        const zone = ZONES_DATA[zoneIndex];
        const rowDate = new Date(currentDate);
        rowDate.setDate(currentDate.getDate() + (i * 2));
        
        const dateStr = formatDateThai(rowDate);
        const expectedYield = Math.round(zone.holes * 0.9);

        output += `📅 *วันที่:* ${dateStr}\n`;
        output += `📍 *จุดงาน:* ${zone.name} (${zone.tables})\n`;
        output += `👨‍🌾 *งานที่ต้องทำ:*\n`;
        output += `  1. ตัดผักขาย [เป้าหมาย: ${expectedYield} ต้น / ${expectedYield / 10} กิโล]\n`;
        output += `  2. ล้างรางทำความสะอาด\n`;
        output += `  3. ย้ายกล้าใหม่ลงแทนทันที\n`;
        output += `--------------------------------\n`;
    }

    const preview = document.getElementById("calendar-clipboard-preview");
    preview.innerText = output;
    navigator.clipboard.writeText(output);
    alert("คัดลอกตารางงานสำหรับส่ง LINE/Telegram เรียบร้อยแล้วครับ!");
}

// Copy calendar data formatted for Notion table
function copyCalendarToNotion() {
    const startInput = document.getElementById("start-date-input").value;
    if (!startInput) return;

    let currentDate = new Date(startInput);
    let output = "| วันที่ปฏิบัติงาน | โซน | งานที่ทำ | เป้าตัดผัก (ต้น) |\n|---|---|---|---|\n";

    for (let i = 0; i < 14; i++) {
        const zoneIndex = (i % 14) + 1;
        const zone = ZONES_DATA[zoneIndex];
        const rowDate = new Date(currentDate);
        rowDate.setDate(currentDate.getDate() + (i * 2));
        
        const dateStr = formatDateThai(rowDate);
        const expectedYield = Math.round(zone.holes * 0.9);

        output += `| ${dateStr} | ${zone.name} | ตัดผัก + ล้างโต๊ะ + ลงกล้าใหม่ | ${expectedYield} |\n`;
    }

    const preview = document.getElementById("calendar-clipboard-preview");
    preview.innerText = output;
    navigator.clipboard.writeText(output);
    alert("คัดลอกตารางตาราง Markdown สำหรับ Notion เรียบร้อยแล้ว!");
}

// Seed calculator logic
function calculateSeeds() {
    const zoneVal = document.getElementById("zone-select").value;
    const zone = ZONES_DATA[zoneVal];

    const totalHoles = zone.holes;
    const marketYield = Math.round(totalHoles * 0.90);
    // Formula: (Holes * 1.10) for 90% survival rate and up to 5% safe backup buffer.
    const targetSeeds = Math.round(totalHoles * 1.10); 
    const expectedWeight = (marketYield * 0.1).toFixed(1); // 1 plant = 1ขีด = 0.1kg

    document.getElementById("lbl-total-holes").innerText = `${totalHoles.toLocaleString()} หลุม`;
    document.getElementById("lbl-market-yield").innerText = `${marketYield.toLocaleString()} ต้น`;
    document.getElementById("lbl-target-seeds").innerText = `${targetSeeds.toLocaleString()} เมล็ด`;
    document.getElementById("lbl-expected-weight").innerText = `${expectedWeight} กิโลกรัม`;

    // Populate actual yield input dynamically
    document.getElementById("actual-yield-input").value = expectedWeight;

    // Render info box about zone
    const infoBox = document.getElementById("zone-info-card");
    const badgeClass = zone.type === 'lightweight' ? 'badge-light' : 'badge-main';
    const typeLabel = zone.type === 'lightweight' ? 'ผักน้ำหนักน้อย' : 'ผักหลัก';
    infoBox.innerHTML = `
        <h4 style="margin-bottom: 5px;">📍 ข้อมูลจุดงาน: ${zone.name}</h4>
        <p><strong>โต๊ะที่ประกอบการ:</strong> ${zone.tables}</p>
        <p><strong>ประเภทบ่อปุ๋ย:</strong> <span class="badge ${badgeClass}">${typeLabel}</span></p>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 5px;">
            *บ่อปุ๋ยของโซนนี้ได้รับการตั้งค่าสภาพตามชนิดพืชเพื่อความคุมอุณหภูมิและ EC/pH ที่สมบูรณ์
        </p>
    `;
}

// Copy seed calculation to sheets format (TSV)
function copySeedDataToSheets() {
    const zoneVal = document.getElementById("zone-select").value;
    const zone = ZONES_DATA[zoneVal];
    const totalHoles = zone.holes;
    const targetSeeds = Math.round(totalHoles * 1.10);
    const actualCut = document.getElementById("actual-yield-input").value;
    const today = formatDateThai(new Date());

    // TSV format for simple spreadsheet copy-paste
    const headers = "วันที่บันทึก\tโซน\tชนิดโต๊ะปุ๋ย\tความจุ (หลุม)\tเป้าเมล็ดเพาะ\tน้ำหนักตัดจริง (กก.)\n";
    const dataRow = `${today}\t${zone.name}\t${zone.type === 'lightweight' ? 'ผักน้ำหนักน้อย' : 'ผักหลัก'}\t${totalHoles}\t${targetSeeds}\t${actualCut}\n`;
    
    const output = headers + dataRow;

    const preview = document.getElementById("seed-clipboard-preview");
    preview.innerText = output;
    navigator.clipboard.writeText(output);
    alert("คัดลอกข้อมูลเรียบร้อย! สามารถนำไปกดวาง (Ctrl+V) ใน Google Sheets ได้ทันที");
}

// Sales Mix Simulator Logic
function updateSalesMix() {
    const wholesaleVal = parseInt(document.getElementById("wholesale-ratio-slider").value);
    const retailVal = 100 - wholesaleVal;

    // Display ratio labels
    document.getElementById("lbl-wholesale-ratio").innerText = `${wholesaleVal}%`;
    document.getElementById("lbl-retail-ratio").innerText = `${retailVal}%`;

    // Auto update retail slider (disabled but showing current state)
    document.getElementById("retail-ratio-slider").value = retailVal;

    // Yield loss slider
    const yieldLossVal = parseInt(document.getElementById("yield-loss-slider").value);
    document.getElementById("lbl-yield-loss").innerText = `${yieldLossVal}%`;

    // Financial Calculation based on 24 tables and 5,322 marketable plants / month
    const baseMonthlyPlants = 5322; 
    // Standard weight per plant is 0.1 kg (1ขีด). Yield loss directly reduces weight efficiency.
    const averageWeightKg = 0.1 * (1 - (yieldLossVal - 10) / 100); // 10% is default. If it is 10%, weight is 0.1 kg.
    const totalWeightKg = baseMonthlyPlants * averageWeightKg;

    // Split weights
    const wholesaleWeight = totalWeightKg * (wholesaleVal / 100);
    const retailWeight = totalWeightKg * (retailVal / 100);

    // Revenues
    const wholesaleRevenue = wholesaleWeight * 65;
    const retailRevenue = retailWeight * 100;
    const totalRevenue = wholesaleRevenue + retailRevenue;

    // Weighted average price
    const weightedAvgPrice = totalWeightKg > 0 ? (totalRevenue / totalWeightKg) : 0;

    // Expenses
    const variableExpenses = totalWeightKg * VARIABLE_COST_PER_KG;
    const totalExpenses = FIXED_COST_24_TABLES + variableExpenses;

    // Net Profit
    const netProfit = totalRevenue - totalExpenses;

    // Render outcomes
    document.getElementById("sim-net-weight").innerText = `${totalWeightKg.toFixed(1)} กก./เดือน`;
    document.getElementById("sim-avg-price").innerText = `฿${weightedAvgPrice.toFixed(2)} / กก.`;
    document.getElementById("sim-revenue").innerText = `฿${Math.round(totalRevenue).toLocaleString()} / เดือน`;
    document.getElementById("sim-expense").innerText = `฿${Math.round(totalExpenses).toLocaleString()} / เดือน`;
    
    const profitEl = document.getElementById("sim-net-profit");
    profitEl.innerText = `฿${Math.round(netProfit).toLocaleString()} / เดือน`;

    if (netProfit < 0) {
        profitEl.style.color = "var(--danger)";
    } else {
        profitEl.style.color = "var(--primary-color)";
    }

    // Sync back to Overview Tab profit KPI
    const kpiProfit = document.getElementById("kpi-profit");
    const kpiProfitDesc = document.getElementById("kpi-profit-desc");
    const kpiCard = document.getElementById("kpi-profit-card");

    kpiProfit.innerText = `฿${Math.round(netProfit).toLocaleString()} / เดือน`;
    kpiProfitDesc.innerText = `อัตราส่วนค้าส่ง ${wholesaleVal}% / ค้าปลีก ${retailVal}% (Yield Loss: ${yieldLossVal}%)`;

    if (netProfit < 0) {
        kpiCard.className = "stat-card danger";
    } else {
        kpiCard.className = "stat-card success";
    }
}

// Copy Headers for Google Sheets guide
function copyHeaders(sheetNum) {
    let headers = "";
    if (sheetNum === 1) {
        headers = "วันที่บันทึก\tรอบโซน\tชนิดผัก\tจำนวนเมล็ดเพาะ (Seeds)\tน้ำหนักผักตัดได้จริง (กก.)\tพนักงานผู้บันทึก";
    } else {
        headers = "วันที่\tหมวดหมู่\tรายละเอียด\tจำนวนเงิน (บาท)";
    }

    navigator.clipboard.writeText(headers);
    alert(`คัดลอกหัวตารางแผ่นที่ ${sheetNum} ลงบอร์ดแล้ว! สามารถนำไปวางลงแถวแรกใน Google Sheets ได้เลยครับ`);
}

// -------------------------------------------------------------
// Interactive Functions for Web App (Jeejee Content Studio & Employee Portal)
// -------------------------------------------------------------

// Sample Database of script themes & research fact-checks
const REELS_THEMES = [
    {
        title: "ทำไมกรีนโอ๊คเชียงใหม่ของคีตะฟาร์มถึงหวานกรอบกว่าทั่วไป?",
        factCheck: "🧪 ข้อมูลวิจัย: เนื่องจากคีตะฟาร์มใช้น้ำจากหุบเขาธรรมชาติเชียงใหม่ซึ่งมีแร่ธาตุอุดมสมบูรณ์ และอากาศยามค่ำคืนที่เย็นตัวลง ช่วยเร่งการสะสมน้ำตาลในท่อน้ำเลี้ยง (EC 1.4-1.6 ms/cm) ทำให้ผักไม่ขม ไม่มีปลายใบไหม้ (Tip burn) ปลอดภัย 100%",
        script: "🎬 [ซีน 1 - หิ้วตะกร้าผักสลัด] (พูดน้ำเสียงร่าเริง)\n\"รู้ไหมคะว่าผักสลัดกรีนโอ๊คที่เชียงใหม่ของเรา...ทำไมถึงเคี้ยวแล้วกร๊อบบ! หวานฉ่ำ ไม่ขมเลย!\"\n\n🎬 [ซีน 2 - แชะกล้องไปที่บ่อปุ๋ยโซน 3]\n\"เคล็ดลับคือ เราคุมบ่อปุ๋ยมาตรฐานแบบเจาะจงโซน 4 โต๊ะต่อ 1 บ่อค่ะ ล็อกค่าปุ๋ยแม่นยำ ผักได้สารอาหารเต็มคำ!\"\n\n🎬 [ซีน 3 - น้องกิ๊กกัดผักโชว์กล้อง]\n\"สดใหม่จากฟาร์มเชียงใหม่ ส่งตรงถึงบ้านทุกสัปดาห์ สนใจผักกล่องสลัดทักแชทจีจี้มาได้เลยนะค๊าา! 🥬✨\""
    },
    {
        title: "ผักไฮโดรฯ ทนร้อนได้จริงไหม? เผยสูตรลับ 'กรีนคอส' โตไวสู้แดด",
        factCheck: "🧪 ข้อมูลวิจัย: กรีนคอสเป็นผักที่ทนอุณหภูมิได้สูงถึง 35-38 องศาเซลเซียส แต่ต้องการการควบคุมออกซิเจนในรากอย่างเสถียร ระบบบ่อปุ๋ยรวมแยก 4 โต๊ะ ช่วยป้องกันการสะสมความร้อนในน้ำปุ๋ยและช่วยเพิ่มอัตราการรอดปลอดภัยเป็น 90%",
        script: "🎬 [ซีน 1 - เอานิ้วจิ้มน้ำในแปลงปลูก]\n\"แดดเชียงใหม่ร้อนขนาดนี้...แต่ดู 'กรีนคอส' แปลงนี้สิคะ! ใบยังเด้งสู้แดด สดชื่นไม่มีเหี่ยวเลย!\"\n\n🎬 [ซีน 2 - ซูมให้เห็นรากผักสีขาวสะอาด]\n\"เคล็ดลับของคีตะฟาร์มคือ บ่อปุ๋ยแยกช่วยคุมอุณหภูมิรากให้เย็นและมีออกซิเจนไหลเวียนตลอดเวลาค่ะ\"\n\n🎬 [ซีน 3 - โลโก้แบรนด์ Kita's Farm ท้ายคลิป]\n\"อยากทานผักสลัดเกรดพรีเมียม สด สะอาด ปลอดสารเคมี ทักข้อความหาแอดมินจีจี้เพื่อจองสิทธิ์กล่องสลัดสัปดาห์นี้ด่วนเลยค่ะ!\""
    },
    {
        title: "พาส่องงานย้ายกล้าผัก 14 โซน ปลูกวนรอบทุก 2 วันของคีตะฟาร์ม",
        factCheck: "🧪 ข้อมูลวิจัย: การทำเกษตรหมุนเวียน 14 โซน (โซนละ 1-2 โต๊ะ) ช่วยเฉลี่ยภาระงานของพนักงาน ลดการใช้แรงงานเหลือเพียง 2 คน และทำให้มีผลผลิตออกสู่ตลาดอย่างสม่ำเสมอเฉลี่ย 394 ต้นต่อรอบ ไม่ล้นไม่ขาดตลาด",
        script: "🎬 [ซีน 1 - น้องกิ๊กกำลังย้ายต้นกล้าลงช่องปลูก]\n\"พาทุกคนมาดูเบื้องหลังความเหนื่อยที่แสนสนุก! วันนี้ถึงรอบคิว โซนปฏิบัติงานย้ายกล้าลงแปลงใหญ่แล้วค่ะ!\"\n\n🎬 [ซีน 2 - แพนกล้องดูโต๊ะปลูกเรียงรายสุดลูกหูลูกตา]\n\"เราแบ่งแปลงปลูกเป็น 14 โซนย่อย เพื่อคอยย้ายกล้าและล้างแปลงทุกๆ 2 วันแบบไม่หยุดพักค่ะ\"\n\n🎬 [ซีน 3 - โชว์ผักกล่องบรรจุถุงส่งของ]\n\"ระบบนี้ทำให้คีตะฟาร์มมีผักสดส่งตรงถึงร้านอาหารคาเฟ่เชียงใหม่ทุกเช้าค่ะ สนใจราคาส่งทักแชทเลยนะค๊า!\""
    }
];

let currentActiveScriptIndex = 0;

// Random Daily Reels Script and Fact-check Report
function generateDailyContent() {
    const randomIndex = Math.floor(Math.random() * REELS_THEMES.length);
    currentActiveScriptIndex = randomIndex;
    const theme = REELS_THEMES[randomIndex];
    
    // Display Script
    const scriptDiv = document.getElementById("reels-script");
    scriptDiv.innerText = `หัวข้อ: ${theme.title}\n\n${theme.script}`;
    document.getElementById("daily-script-container").style.display = "block";
    
    // Display Fact Check
    const factCheckDiv = document.getElementById("fact-check-box");
    factCheckDiv.innerHTML = `
        <h4 style="color: var(--secondary-color); margin-bottom: 10px;">📋 ผลการวิเคราะห์ข้อมูลความจริง:</h4>
        <p style="font-size: 0.95rem; line-height: 1.5; color: var(--text-secondary);">${theme.factCheck}</p>
        <span class="badge badge-main" style="margin-top: 10px; display: inline-block;">Verified by DeepSeek-R1</span>
    `;
}

// Approve script
function approveDailyContent() {
    alert("อนุมัติสคริปต์เรียบร้อย! ส่งตารางเข้าท่อการผลิดภาพดิบวิดีโอแล้ว");
    addCoordinationMessage("คุณพ่อเลี้ยง", `อนุมัติสคริปต์หัวข้อ "${REELS_THEMES[currentActiveScriptIndex].title}" เรียบร้อยแล้วนะจีจี้ ผลิตต่อได้เลย!`);
}

// Simulated Video Build
function renderApprovedVideo() {
    alert("กำลังเรียกใช้ Higgsfield / Remotion Engine เพื่อวาดเฟรมวิดีโอ...\nสคริปต์นี้จะใช้พรีเซนเตอร์คีตะฟาร์ม [Soul ID: KitaPresenter]");
    setTimeout(() => {
        alert("ประกอบวิดีโอเสร็จสมบูรณ์! ได้ไฟล์คลิปสั้น Reels สำหรับวันนี้แล้ว\n(เซฟลงโฟลเดอร์ /Raw/ เพื่อตรวจเตรียมโพสต์)");
        addCoordinationMessage("จีจี้", `ประกอบวิดีโอ Reels สำหรับหัวข้อวันนี้เสร็จแล้วค่ะคุณป๊า! คลิปสั้นอยู่ในระบบคลังรอโพสต์เย็นนี้ค่ะ 🎬🥬`);
    }, 1500);
}

// Simulated File Upload for Kik
function handleFileUpload() {
    const input = document.getElementById("media-file-input");
    const status = document.getElementById("upload-status");
    if (input.files.length > 0) {
        const file = input.files[0];
        status.innerText = `⏳ กำลังอัปโหลด: ${file.name} (ขนาด ${(file.size / (1024 * 1024)).toFixed(2)} MB)...`;
        
        setTimeout(() => {
            status.innerText = `✅ อัปโหลดสำเร็จ! ไฟล์ ${file.name} ถูกย้ายไปยังโฟลเดอร์ /Raw/ เรียบร้อยแล้ว (จีจี้พร้อมนำไปประกอบสคริปต์แล้ว)`;
            addCoordinationMessage("กิ๊ก (พนักงานแปลงผัก)", `ส่งภาพถ่ายยอดผักจากโซนที่คิวตัดวันนี้เข้าห้องระบบดิบแล้วค่ะพี่กร พี่จีจี้ เอาไปลงคลิปได้เลยน๊า 📸🥬`);
        }, 1200);
    }
}

// Coordination Chat Logic
const INITIAL_MESSAGES = [
    { sender: "พี่กร", text: "จีจี้ วันนี้ถึงคิวล้างแปลงและตัดผักของโซนที่ 1 (บ่อปุ๋ย 1 - บัตเตอร์เฮด เรดโอ๊ค ฟินเล่) นะ อย่าลืมคุมค่า EC ของโซนนี้ให้อ่อนกว่าปกติด้วยล่ะ" },
    { sender: "จีจี้", text: "รับทราบค่ะพี่กร! เดี๋ยวจีจี้เตรียมเขียนบท Reels โปรโมทบัตเตอร์เฮดเช้าวันนี้เลย ผักกำลังกรอบได้ที่เลยค่ะ" },
    { sender: "กิ๊ก (พนักงานแปลงผัก)", text: "ผักโซน 1 ตัดเสร็จเรียบร้อย ชั่งน้ำหนักจริงได้ 42.5 กิโลกรัม ส่งเข้าตาราง Sheets และส่งรูปเข้าแอปแล้วนะคะ" }
];

// Load initial chat messages
document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-messages");
    if (chatContainer) {
        INITIAL_MESSAGES.forEach(msg => {
            appendMessageHTML(msg.sender, msg.text);
        });
    }
});

function appendMessageHTML(sender, text) {
    const chatContainer = document.getElementById("chat-messages");
    if (!chatContainer) return;
    
    const messageDiv = document.createElement("div");
    messageDiv.style.marginBottom = "10px";
    messageDiv.style.padding = "10px 14px";
    messageDiv.style.borderRadius = "8px";
    messageDiv.style.maxWidth = "80%";
    
    if (sender === "จีจี้") {
        messageDiv.style.alignSelf = "flex-start";
        messageDiv.style.backgroundColor = "rgba(16, 185, 129, 0.15)";
        messageDiv.style.border = "1px solid rgba(16, 185, 129, 0.3)";
    } else if (sender === "พี่กร") {
        messageDiv.style.alignSelf = "flex-end";
        messageDiv.style.backgroundColor = "rgba(59, 130, 246, 0.15)";
        messageDiv.style.border = "1px solid rgba(59, 130, 246, 0.3)";
    } else if (sender.includes("คุณพ่อเลี้ยง")) {
        messageDiv.style.alignSelf = "center";
        messageDiv.style.backgroundColor = "rgba(245, 158, 11, 0.15)";
        messageDiv.style.border = "1px solid rgba(245, 158, 11, 0.3)";
        messageDiv.style.textAlign = "center";
    } else {
        messageDiv.style.alignSelf = "flex-start";
        messageDiv.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
        messageDiv.style.border = "1px solid var(--border-color)";
    }

    messageDiv.innerHTML = `
        <strong style="color: var(--secondary-color); font-size: 0.85rem;">${sender}</strong>
        <p style="margin-top: 4px; font-size: 0.9rem; line-height: 1.4;">${text}</p>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const sender = document.getElementById("chat-sender").value;
    const text = input.value.trim();
    
    if (text) {
        appendMessageHTML(sender, text);
        input.value = "";
    }
}

function addCoordinationMessage(sender, text) {
    appendMessageHTML(sender, text);
}
