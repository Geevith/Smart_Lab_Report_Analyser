// ==========================================
// VALIDATION SUMMARY PAGE - CLINICAL UI
// ==========================================

// DOM Elements
const categorizedParams = document.getElementById('categorizedParams');
const discardBtn = document.getElementById('discardBtn');
const confirmBtn = document.getElementById('confirmBtn');
const darkModeToggle = document.getElementById('darkModeToggle');
const searchInput = document.getElementById('searchInput');

// Stat elements
const statusLabel = document.getElementById('statusLabel');
const progressBar = document.getElementById('progressBar');
const progressPercent = document.getElementById('progressPercent');
const validatedCount = document.getElementById('validatedCount');
const autoResolvedCount = document.getElementById('autoResolvedCount');
const pendingCount = document.getElementById('pendingCount');
const totalBadge = document.getElementById('totalBadge');
const integrityIndicator = document.getElementById('integrityIndicator');

// Data container
let parametersData = [];

// Category definitions for grouping
const categories = {
    'Blood Panel (CBC)': {
        subtitle: 'Hematology Analysis',
        keywords: ['hemoglobin', 'hgb', 'wbc', 'rbc', 'platelet', 'hematocrit', 'mcv', 'mch', 'mchc', 'rdw', 'mpv', 'neutrophil', 'lymphocyte', 'monocyte', 'eosinophil', 'basophil']
    },
    'Renal Function': {
        subtitle: 'Kidney Performance Markers',
        keywords: ['creatinine', 'bun', 'urea', 'egfr', 'gfr', 'uric acid']
    },
    'Liver Function': {
        subtitle: 'Hepatic Performance Markers',
        keywords: ['alt', 'ast', 'sgpt', 'sgot', 'bilirubin', 'albumin', 'globulin', 'alkaline', 'alp', 'ggt', 'ggtp']
    },
    'Lipid Profile': {
        subtitle: 'Cardiovascular Risk Markers',
        keywords: ['cholesterol', 'hdl', 'ldl', 'triglyceride', 'vldl']
    },
    'Electrolytes & Metabolic': {
        subtitle: 'Ion Balance & Energy',
        keywords: ['sodium', 'potassium', 'chloride', 'calcium', 'magnesium', 'phosphorus', 'bicarbonate', 'glucose', 'sugar', 'hba1c']
    },
    'Thyroid Panel': {
        subtitle: 'Thyroid Function Markers',
        keywords: ['tsh', 't3', 't4', 'thyroid']
    },
    'Other Parameters': {
        subtitle: 'Additional Markers',
        keywords: []
    }
};

// Protocol descriptions for parameter display
const protocolDescriptions = [
    'Unit Standardization',
    'Ontology Normalization',
    'Range Verification',
    'Plausibility Check',
    'Cross-ref Validation',
    'Biological Analysis'
];

// ==========================================
// NEW: State for verification features
// ==========================================

// Cache for historical data
const historicalDataCache = {};

// Track flagged parameters
const flaggedParameters = new Set();

// Currently editing parameter
let currentlyEditing = null;

// Missing tests suggestions
let missingTestsSuggestions = [];

// ==========================================
// DARK MODE
// ==========================================

const savedTheme = localStorage.getItem('theme');
// Default to dark mode if no preference is saved
if (savedTheme === 'light') {
    document.documentElement.classList.remove('dark');
} else {
    document.documentElement.classList.add('dark');
}

// Update icon based on current theme on load
function updateDarkModeIcon() {
    const isDark = document.documentElement.classList.contains('dark');
    const icon = darkModeToggle.querySelector('.material-symbols-outlined');
    if (icon) {
        icon.textContent = isDark ? 'dark_mode' : 'light_mode';
    }
}

// Set initial icon state
updateDarkModeIcon();

darkModeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateDarkModeIcon();
});

// ==========================================
// INITIALIZE PAGE
// ==========================================

function initializePage() {
    const storedResults = sessionStorage.getItem('analysisResults');

    if (storedResults) {
        try {
            parametersData = JSON.parse(storedResults);
            console.log('Loaded parameters:', parametersData);
        } catch (e) {
            console.error('Failed to parse analysis results', e);
            showNotification('Error loading analysis data', 'error');
        }
    } else {
        console.log('No analysis data found, using demo data');
        // Demo data for testing
        parametersData = generateDemoData();
    }

    // Calculate stats
    updateStats();

    // Render categorized parameters
    renderCategorizedParameters();

    // Animate progress bar
    animateProgress();

    // NEW: Fetch missing tests suggestions
    fetchMissingTestsSuggestions();
}

function generateDemoData() {
    return [
        { name: 'Hemoglobin', value: '13.80', unit: 'g/dL', confidence: 'high', notes: [] },
        { name: 'WBC Count', value: '6.20', unit: 'x10³/µL', confidence: 'high', notes: ['normalization'] },
        { name: 'Platelets', value: '210.00', unit: 'x10³/µL', confidence: 'high', notes: [] },
        { name: 'RBC Count', value: '4.85', unit: 'x10⁶/µL', confidence: 'high', notes: [] },
        { name: 'Creatinine', value: '0.90', unit: 'mg/dL', confidence: 'high', notes: [] },
        { name: 'BUN', value: '14.00', unit: 'mg/dL', confidence: 'high', notes: [] },
        { name: 'eGFR', value: '>90', unit: 'mL/min', confidence: 'high', notes: ['calculated'] },
        { name: 'Glucose, Fasting', value: '94.00', unit: 'mg/dL', confidence: 'high', notes: ['standardized'] },
        { name: 'Potassium', value: '4.10', unit: 'mmol/L', confidence: 'high', notes: [] },
        { name: 'Sodium', value: '139.00', unit: 'mmol/L', confidence: 'high', notes: [] },
        { name: 'ALT (SGPT)', value: '28.00', unit: 'U/L', confidence: 'medium', notes: ['normalization'] },
        { name: 'AST (SGOT)', value: '24.00', unit: 'U/L', confidence: 'high', notes: [] },
        { name: 'Total Cholesterol', value: '185.00', unit: 'mg/dL', confidence: 'high', notes: [] },
        { name: 'HDL Cholesterol', value: '52.00', unit: 'mg/dL', confidence: 'high', notes: [] },
        { name: 'LDL Cholesterol', value: '110.00', unit: 'mg/dL', confidence: 'high', notes: ['calculated'] },
        { name: 'TSH', value: '2.45', unit: 'mIU/L', confidence: 'high', notes: [] }
    ];
}

function updateStats() {
    const total = parametersData.length;
    const high = parametersData.filter(p => p.confidence && p.confidence.toLowerCase() === 'high').length;
    const medium = parametersData.filter(p => p.confidence && p.confidence.toLowerCase() === 'medium').length;
    const low = parametersData.filter(p => p.confidence && p.confidence.toLowerCase() === 'low').length;

    validatedCount.textContent = high;
    autoResolvedCount.textContent = medium;
    pendingCount.textContent = low;
    totalBadge.textContent = `${total} ENTRIES`;

    // Update status based on validation state
    if (low === 0 && total > 0) {
        statusLabel.textContent = 'SYSTEM STATUS: VERIFIED';
        integrityIndicator.innerHTML = `
            <div class="size-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <div class="flex-1">
                <p class="text-emerald-400 text-xs font-bold uppercase tracking-wider">Integrity Passed</p>
            </div>
        `;
    } else if (low > 0) {
        statusLabel.textContent = 'SYSTEM STATUS: REVIEW REQUIRED';
        integrityIndicator.classList.remove('bg-emerald-500/5', 'border-emerald-500/20');
        integrityIndicator.classList.add('bg-amber-500/5', 'border-amber-500/20');
        integrityIndicator.innerHTML = `
            <div class="size-2 rounded-full bg-amber-500 animate-pulse"></div>
            <div class="flex-1">
                <p class="text-amber-400 text-xs font-bold uppercase tracking-wider">Review Recommended</p>
            </div>
        `;
    }
}

function animateProgress() {
    const total = parametersData.length;
    const high = parametersData.filter(p => p.confidence && p.confidence.toLowerCase() === 'high').length;
    const medium = parametersData.filter(p => p.confidence && p.confidence.toLowerCase() === 'medium').length;

    const verified = high + medium;
    const percent = total > 0 ? Math.round((verified / total) * 100) : 0;

    setTimeout(() => {
        progressBar.style.width = `${percent}%`;
        progressPercent.textContent = `${percent.toFixed(2)}%`;
    }, 300);
}

// ==========================================
// CATEGORIZE & RENDER PARAMETERS
// ==========================================

function categorizeParameters(params) {
    const categorized = {};

    // Initialize categories
    Object.keys(categories).forEach(cat => {
        categorized[cat] = [];
    });

    params.forEach(param => {
        const paramLower = param.name.toLowerCase();
        let found = false;

        for (const [catName, catDef] of Object.entries(categories)) {
            if (catName === 'Other Parameters') continue;

            for (const keyword of catDef.keywords) {
                if (paramLower.includes(keyword)) {
                    categorized[catName].push(param);
                    found = true;
                    break;
                }
            }
            if (found) break;
        }

        if (!found) {
            categorized['Other Parameters'].push(param);
        }
    });

    // Remove empty categories
    Object.keys(categorized).forEach(cat => {
        if (categorized[cat].length === 0) {
            delete categorized[cat];
        }
    });

    return categorized;
}

function renderCategorizedParameters() {
    const categorized = categorizeParameters(parametersData);
    categorizedParams.innerHTML = '';

    Object.entries(categorized).forEach(([catName, params]) => {
        const catDef = categories[catName];
        const okCount = params.filter(p => p.confidence === 'high').length;
        const warnCount = params.filter(p => p.confidence !== 'high').length;

        const section = document.createElement('details');
        section.className = 'group/section';
        section.open = true;

        section.innerHTML = `
            <summary class="flex items-center justify-between glass-header px-6 py-4 rounded-xl cursor-pointer hover:bg-primary/5 transition-colors mb-4 select-none">
                <div class="flex items-center gap-4">
                    <span class="material-symbols-outlined text-slate-400 group-open/section:rotate-90 transition-transform">chevron_right</span>
                    <div class="flex flex-col">
                        <span class="text-slate-900 dark:text-white font-bold text-sm uppercase tracking-wider">${catName}</span>
                        <span class="text-slate-500 text-[10px]">${catDef.subtitle}</span>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    ${okCount > 0 ? `<span class="px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold tracking-wider">${okCount} OK</span>` : ''}
                    ${warnCount > 0 ? `<span class="px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 text-amber-700 dark:text-amber-400 text-[10px] font-bold tracking-wider">${warnCount} ATTN</span>` : ''}
                </div>
            </summary>
            <table class="w-full border-separate border-spacing-y-2 pl-4">
                <tbody class="text-sm">
                    <tr class="text-left opacity-60">
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Parameter Label</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Protocol</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2 text-right">Value</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Reference Range</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2 text-right">Status</th>
                    </tr>
                    ${params.map((param, idx) => createParameterRow(param, idx)).join('')}
                </tbody>
            </table>
        `;

        categorizedParams.appendChild(section);
    });

    // Add end marker
    const endMarker = document.createElement('div');
    endMarker.className = 'mt-8 flex flex-col items-center pb-8 opacity-60 hover:opacity-100 transition-opacity';
    endMarker.innerHTML = `<p class="text-slate-500 text-[10px] uppercase tracking-widest font-bold">End of categorized list</p>`;
    categorizedParams.appendChild(endMarker);
}

function createParameterRow(param, index) {
    const confidence = (param.confidence || 'low').toLowerCase();
    const isHigh = confidence === 'high';
    const isMedium = confidence === 'medium';
    // const isLow = confidence === 'low'; // implied

    const hasNotes = param.notes && param.notes.length > 0;

    // Random protocol for display purposes
    const protocol = protocolDescriptions[index % protocolDescriptions.length];

    // Fetch historical data asynchronously (cached after first fetch)
    if (!historicalDataCache[param.name]) {
        fetchHistoricalData(param.name);
    }

    // Status Logic
    let statusText = 'Review Required';
    let statusColorClass = 'text-amber-600 dark:text-amber-400';
    let dotColorClass = 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]';

    if (isHigh) {
        statusText = 'Verified';
        statusColorClass = 'text-emerald-600 dark:text-emerald-400';
        dotColorClass = 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    } else if (isMedium) {
        statusText = 'Auto-Resolved';
        statusColorClass = 'text-blue-600 dark:text-blue-400';
        dotColorClass = 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]';
    }



    // Calculate actual position based on value and reference range
    let positionPercent = 50; // Default to middle if no range
    if (param.range && param.value) {
        // Parse range like "13.0 - 17.0" or "70 - 100"
        const rangeMatch = param.range.match(/([\d.]+)\s*[-–]\s*([\d.]+)/);
        if (rangeMatch) {
            const minVal = parseFloat(rangeMatch[1]);
            const maxVal = parseFloat(rangeMatch[2]);
            const value = parseFloat(param.value);

            if (!isNaN(minVal) && !isNaN(maxVal) && !isNaN(value) && maxVal > minVal) {
                // Calculate where value falls. 25% = min, 75% = max (center is normal zone)
                // Values outside range: <25% for low, >75% for high
                const rangeSpan = maxVal - minVal;
                const normalizedPos = (value - minVal) / rangeSpan;
                // Map to 25%-75% visual range (normal zone)
                positionPercent = 25 + (normalizedPos * 50);
                // Clamp between 5% and 95% for visibility
                positionPercent = Math.max(5, Math.min(95, positionPercent));
            }
        }
    }

    // Historical comparison (will be populated after data loads)
    const history = historicalDataCache[param.name] || [];
    let historicalHTML = '';
    if (history.length > 0) {
        const mostRecent = history[0];
        const trend = calculateTrend(parseFloat(param.value), parseFloat(mostRecent.value));

        if (trend !== null) {
            const trendIcon = trend > 0 ? '↑' : '↓';
            const trendColor = Math.abs(trend) > 40 ? 'text-red-500' : trend > 0 ? 'text-emerald-500' : 'text-blue-500';
            const warningBadge = Math.abs(trend) > 40 ? '<span class="ml-2 px-2 py-0.5 bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-[9px] font-bold rounded-full">ALERT</span>' : '';

            historicalHTML = `
                <div class="flex items-center gap-2 text-[10px] mt-1">
                    <span class="${trendColor} font-bold">${trendIcon} ${Math.abs(trend).toFixed(1)}%</span>
                    <span class="text-slate-400">vs ${new Date(mostRecent.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                    ${warningBadge}
                </div>
            `;
        }
    }

    return `
        <tr class="glass-pill group hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-all" data-param-name="${param.name}">
            <td class="px-6 py-4 rounded-l-lg">
                <div class="flex items-center gap-2">
                    <span class="text-slate-900 dark:text-white font-medium">${param.name}</span>
                    <button class="info-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-primary/10 rounded" 
                        onclick="showHistoricalTooltip('${param.name.replace(/'/g, "\\'")}', '${param.value}', event)"
                        title="View information">
                        <span class="material-symbols-outlined text-primary text-sm">info</span>
                    </button>
                </div>
                ${historicalHTML}
            </td>
            <td class="px-6 py-4">
                <span class="text-xs text-slate-500 dark:text-slate-400 font-light">${hasNotes ? 'Normalization Applied' : protocol}</span>
            </td>
            <td class="px-6 py-4 text-right param-value-cell">
                <div class="flex items-center justify-end gap-2">
                    <span class="text-precision text-slate-900 dark:text-white font-medium">${param.value} ${param.unit}</span>
                    <button class="edit-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-emerald-500/10 rounded" 
                        onclick="editParameter('${param.name.replace(/'/g, "\\'")}', '${param.value}', '${param.unit}')"
                        title="Edit value">
                        <span class="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-sm">edit</span>
                    </button>
                </div>
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                    <span class="text-[9px] text-slate-400 dark:text-slate-600 font-mono">L</span>
                    <div class="relative w-28 h-1 bg-slate-200 dark:bg-slate-800 rounded-full">
                        <div class="absolute inset-y-0 left-[25%] right-[25%] bg-emerald-500/30 rounded-full"></div>
                        <div class="absolute top-1/2 -translate-y-1/2 size-2 bg-white dark:bg-white rounded-full shadow border border-slate-300 dark:border-slate-900" style="left: ${positionPercent}%"></div>
                    </div>
                    <span class="text-[9px] text-slate-400 dark:text-slate-600 font-mono">H</span>
                </div>
            </td>
            <td class="px-6 py-4 text-right rounded-r-lg">
                <div class="flex items-center justify-end gap-3">
                    <div class="inline-flex items-center gap-2 ${statusColorClass} text-[10px] font-bold uppercase tracking-wider">
                        <span class="size-1.5 rounded-full ${dotColorClass}"></span>
                        <span>${statusText}</span>
                    </div>
                    <button class="flag-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-amber-500/10 rounded" 
                        onclick="flagParameter('${param.name.replace(/'/g, "\\'")}', '${param.value} ${param.unit}')"
                        title="Report issue">
                        <span class="material-symbols-outlined text-amber-600 dark:text-amber-400 text-sm">flag</span>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// ==========================================
// SEARCH FILTER
// ==========================================

searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();

    if (query === '') {
        renderCategorizedParameters();
        return;
    }

    const filtered = parametersData.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.unit.toLowerCase().includes(query)
    );

    const categorized = categorizeParameters(filtered);
    categorizedParams.innerHTML = '';

    Object.entries(categorized).forEach(([catName, params]) => {
        const catDef = categories[catName];
        const okCount = params.filter(p => p.confidence === 'high').length;
        const warnCount = params.filter(p => p.confidence !== 'high').length;

        const section = document.createElement('details');
        section.className = 'group/section';
        section.open = true;

        section.innerHTML = `
            <summary class="flex items-center justify-between glass-header px-6 py-4 rounded-xl cursor-pointer hover:bg-primary/10 transition-colors mb-4 select-none">
                <div class="flex items-center gap-4">
                    <span class="material-symbols-outlined text-slate-400 group-open/section:rotate-90 transition-transform">chevron_right</span>
                    <div class="flex flex-col">
                        <span class="text-white font-bold text-sm uppercase tracking-wider">${catName}</span>
                        <span class="text-slate-500 text-[10px]">${catDef.subtitle}</span>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    ${okCount > 0 ? `<span class="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold tracking-wider">${okCount} OK</span>` : ''}
                    ${warnCount > 0 ? `<span class="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-bold tracking-wider">${warnCount} WARN</span>` : ''}
                </div>
            </summary>
            <table class="w-full border-separate border-spacing-y-2 pl-4">
                <tbody class="text-sm">
                    <tr class="text-left opacity-60">
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Parameter Label</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Protocol</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2 text-right">Value</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2">Reference Range</th>
                        <th class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em] px-6 pb-2 text-right">Status</th>
                    </tr>
                    ${params.map((param, idx) => createParameterRow(param, idx)).join('')}
                </tbody>
            </table>
        `;

        categorizedParams.appendChild(section);
    });
});

// ==========================================
// ACTION BUTTONS
// ==========================================

discardBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to start over?')) {
        sessionStorage.clear();
        showNotification('Starting over...', 'info');
        setTimeout(() => {
            window.location.href = 'upload_ui.html';
        }, 1000);
    }
});

confirmBtn.addEventListener('click', () => {
    sessionStorage.setItem('verifiedParameters', JSON.stringify(parametersData));
    sessionStorage.setItem('currentStep', 'insights');

    showNotification('Validation complete. Proceeding to insights...', 'success');

    setTimeout(() => {
        window.location.href = 'insights_ui.html';
    }, 1500);
});

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

// showNotification is provided by utils.js

// ==========================================
// NEW: VERIFICATION HELPER FUNCTIONS
// ==========================================

// Fetch historical data for a parameter
async function fetchHistoricalData(parameterName) {
    // Check cache first
    if (historicalDataCache[parameterName]) {
        return historicalDataCache[parameterName];
    }

    try {
        const response = await fetch(`/parameter_history/${encodeURIComponent(parameterName)}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            historicalDataCache[parameterName] = data.history || [];
            return data.history || [];
        }
    } catch (error) {
        console.error(`Failed to fetch history for ${parameterName}:`, error);
    }

    return [];
}

// Calculate trend percentage
function calculateTrend(current, previous) {
    if (!previous || previous === 0) return null;
    return ((current - previous) / previous) * 100;
}

// Inline edit parameter
async function editParameter(paramName, currentValue, currentUnit) {
    if (currentlyEditing) {
        showNotification('Please finish editing the current parameter first', 'error');
        return;
    }

    const row = document.querySelector(`tr[data-param-name="${paramName}"]`);
    if (!row) return;

    currentlyEditing = paramName;
    const valueCell = row.querySelector('.param-value-cell');
    const originalHTML = valueCell.innerHTML;

    // Create inline edit UI
    valueCell.innerHTML = `
        <div class="flex items-center gap-2">
            <input type="text" value="${currentValue}" 
                class="edit-value-input bg-white dark:bg-slate-800 border border-primary/30 rounded px-2 py-1 text-sm w-20 text-slate-900 dark:text-white"
                placeholder="Value">
            <input type="text" value="${currentUnit}" 
                class="edit-unit-input bg-white dark:bg-slate-800 border border-primary/30 rounded px-2 py-1 text-sm w-16 text-slate-900 dark:text-white"
                placeholder="Unit">
            <button class="save-edit-btn px-3 py-1 bg-emerald-500 hover:bg-emerald-600 text-white rounded text-xs font-bold transition-colors">
                SAVE
            </button>
            <button class="cancel-edit-btn px-3 py-1 bg-slate-500 hover:bg-slate-600 text-white rounded text-xs font-bold transition-colors">
                CANCEL
            </button>
        </div>
    `;

    const valueInput = valueCell.querySelector('.edit-value-input');
    const unitInput = valueCell.querySelector('.edit-unit-input');
    const saveBtn = valueCell.querySelector('.save-edit-btn');
    const cancelBtn = valueCell.querySelector('.cancel-edit-btn');

    valueInput.focus();
    valueInput.select();

    // Cancel handler
    const cancelEdit = () => {
        valueCell.innerHTML = originalHTML;
        currentlyEditing = null;
    };

    cancelBtn.addEventListener('click', cancelEdit);

    // Save handler
    saveBtn.addEventListener('click', async () => {
        const newValue = valueInput.value.trim();
        const newUnit = unitInput.value.trim();

        if (!newValue) {
            showNotification('Value cannot be empty', 'error');
            return;
        }

        try {
            const response = await fetch('/api/verify/update_parameter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    parameter_name: paramName,
                    new_value: newValue,
                    new_unit: newUnit
                })
            });

            if (response.ok) {
                const result = await response.json();

                // Update local data
                const param = parametersData.find(p => p.name === paramName);
                if (param) {
                    param.value = newValue;
                    param.unit = newUnit;
                }

                // Restore with new values
                valueCell.innerHTML = `<span class="text-precision text-slate-900 dark:text-white font-medium">${newValue} ${newUnit}</span>`;
                currentlyEditing = null;

                showNotification(`Parameter updated successfully!`, 'success');

                // Add visual feedback
                row.classList.add('bg-emerald-100', 'dark:bg-emerald-500/10');
                setTimeout(() => {
                    row.classList.remove('bg-emerald-100', 'dark:bg-emerald-500/10');
                }, 2000);
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Failed to update parameter', 'error');
                cancelEdit();
            }
        } catch (error) {
            console.error('Error updating parameter:', error);
            showNotification('Network error. Please try again.', 'error');
            cancelEdit();
        }
    });

    // Enter to save, Esc to cancel
    valueInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') saveBtn.click();
        if (e.key === 'Escape') cancelEdit();
    });
    unitInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') saveBtn.click();
        if (e.key === 'Escape') cancelEdit();
    });
}

// Flag parameter as incorrect
async function flagParameter(paramName, originalValue) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4';
    modal.innerHTML = `
        <div class="glass-panel rounded-2xl p-8 max-w-md w-full space-y-6 animate-in">
            <div class="flex items-center gap-3 mb-4">
                <span class="material-symbols-outlined text-amber-500 text-3xl">flag</span>
                <h3 class="text-xl font-bold text-slate-900 dark:text-white">Report Issue</h3>
            </div>
            
            <div class="space-y-4">
                <div>
                    <label class="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Parameter</label>
                    <div class="glass-pill rounded-lg px-4 py-2">
                        <span class="text-slate-900 dark:text-white font-medium">${paramName}</span>
                    </div>
                </div>
                
                <div>
                    <label class="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Issue Type</label>
                    <select class="flag-issue-type w-full glass-pill rounded-lg px-4 py-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700">
                        <option value="misread">Value Misread</option>
                        <option value="incorrect_unit">Incorrect Unit</option>
                        <option value="missing">Missing Parameter</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div>
                    <label class="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Corrected Value (optional)</label>
                    <input type="text" class="flag-corrected-value w-full glass-pill rounded-lg px-4 py-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700" placeholder="e.g., 12.5">
                </div>
                
                <div>
                    <label class="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Additional Notes (optional)</label>
                    <textarea class="flag-notes w-full glass-pill rounded-lg px-4 py-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 h-24 resize-none" placeholder="Any additional information..."></textarea>
                </div>
            </div>
            
            <div class="flex gap-3">
                <button class="flag-submit-btn flex-1 bg-amber-500 hover:bg-amber-600 text-white font-bold py-3 px-6 rounded-xl transition-colors">
                    Submit Report
                </button>
                <button class="flag-cancel-btn px-6 bg-slate-500 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-colors">
                    Cancel
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const issueTypeSelect = modal.querySelector('.flag-issue-type');
    const correctedValueInput = modal.querySelector('.flag-corrected-value');
    const notesTextarea = modal.querySelector('.flag-notes');
    const submitBtn = modal.querySelector('.flag-submit-btn');
    const cancelBtn = modal.querySelector('.flag-cancel-btn');

    const closeModal = () => document.body.removeChild(modal);

    cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    submitBtn.addEventListener('click', async () => {
        const issueType = issueTypeSelect.value;
        const correctedValue = correctedValueInput.value.trim();
        const notes = notesTextarea.value.trim();

        try {
            const response = await fetch('/api/verify/flag_parameter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    parameter_name: paramName,
                    original_value: originalValue,
                    corrected_value: correctedValue,
                    issue_type: issueType,
                    notes: notes
                })
            });

            if (response.ok) {
                const result = await response.json();
                flaggedParameters.add(paramName);
                closeModal();
                showNotification('Thank you for the feedback! This helps improve our system.', 'success');

                // Mark parameter as flagged in UI
                const row = document.querySelector(`tr[data-param-name="${paramName}"]`);
                if (row) {
                    const flagBtn = row.querySelector('.flag-btn');
                    if (flagBtn) {
                        flagBtn.classList.add('text-amber-500');
                        flagBtn.innerHTML = '<span class="material-symbols-outlined" style="font-variation-settings: \'FILL\' 1">flag</span>';
                    }
                }
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Failed to submit flag', 'error');
            }
        } catch (error) {
            console.error('Error flagging parameter:', error);
            showNotification('Network error. Please try again.', 'error');
        }
    });
}

// Show historical comparison tooltip
function showHistoricalTooltip(paramName, currentValue, event) {
    // Remove any existing tooltips
    const existing = document.querySelector('.historical-tooltip');
    if (existing) existing.remove();

    const history = historicalDataCache[paramName];
    if (!history || history.length === 0) {
        showTooltip(paramName, event);
        return;
    }

    const mostRecent = history[0];
    const trend = calculateTrend(parseFloat(currentValue), parseFloat(mostRecent.value));

    const tooltip = document.createElement('div');
    tooltip.className = 'historical-tooltip fixed z-50 glass-panel rounded-xl p-4 shadow-2xl max-w-xs';

    let trendHTML = '';
    if (trend !== null) {
        const trendIcon = trend > 0 ? '↑' : '↓';
        const trendColor = Math.abs(trend) > 40 ? 'text-red-500' : trend > 0 ? 'text-emerald-500' : 'text-blue-500';
        trendHTML = `
            <div class="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <span class="${trendColor} font-bold text-sm">${trendIcon} ${Math.abs(trend).toFixed(1)}%</span>
                <span class="text-slate-500 text-xs ml-2">vs. last result</span>
            </div>
        `;
    }

    tooltip.innerHTML = `
        <div class="space-y-2">
            <div class="flex items-center gap-2 mb-2">
                <span class="material-symbols-outlined text-primary text-sm">history</span>
                <span class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Historical Data</span>
            </div>
            <div>
                <p class="text-xs text-slate-500">Previous Value</p>
                <p class="text-sm font-bold text-slate-900 dark:text-white">${mostRecent.value} ${mostRecent.unit}</p>
                <p class="text-[10px] text-slate-400 mt-1">${new Date(mostRecent.date).toLocaleDateString()}</p>
            </div>
            ${trendHTML}
        </div>
    `;

    document.body.appendChild(tooltip);

    // Position tooltip
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`;

    // Auto-remove on click outside
    const removeHandler = (e) => {
        if (!tooltip.contains(e.target)) {
            tooltip.remove();
            document.removeEventListener('click', removeHandler);
        }
    };
    setTimeout(() => document.addEventListener('click', removeHandler), 100);
}

// Show generic tooltip with parameter info
function showTooltip(paramName, event) {
    const existing = document.querySelector('.param-tooltip');
    if (existing) existing.remove();

    const tooltip = document.createElement('div');
    tooltip.className = 'param-tooltip fixed z-50 glass-panel rounded-xl p-4 shadow-2xl max-w-sm';

    tooltip.innerHTML = `
        <div class="space-y-2">
            <div class="flex items-center gap-2 mb-2">
                <span class="material-symbols-outlined text-primary text-sm">info</span>
                <span class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">${paramName}</span>
            </div>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                This parameter measures ${paramName.toLowerCase()} levels in your blood. Normal ranges may vary based on age, gender, and laboratory standards.
            </p>
            <div class="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <p class="text-[10px] text-slate-500 uppercase tracking-wider">Learn More</p>
                <p class="text-xs text-primary cursor-pointer hover:underline mt-1">View detailed information →</p>
            </div>
        </div>
    `;

    document.body.appendChild(tooltip);

    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`;

    const removeHandler = (e) => {
        if (!tooltip.contains(e.target)) {
            tooltip.remove();
            document.removeEventListener('click', removeHandler);
        }
    };
    setTimeout(() => document.addEventListener('click', removeHandler), 100);
}

// Fetch missing test suggestions
async function fetchMissingTestsSuggestions() {
    try {
        const response = await fetch('/api/verify/suggest_missing_tests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ parameters: parametersData })
        });

        if (response.ok) {
            const data = await response.json();
            missingTestsSuggestions = data.suggestions || [];
            renderMissingTestsSuggestions();
        }
    } catch (error) {
        console.error('Error fetching test suggestions:', error);
    }
}

// Render missing tests suggestions in sidebar
function renderMissingTestsSuggestions() {
    if (missingTestsSuggestions.length === 0) return;

    // Find sidebar content area
    const sidebar = document.querySelector('aside .flex-1');
    if (!sidebar) return;

    // Create suggestions section
    const suggestionsSection = document.createElement('div');
    suggestionsSection.className = 'mt-8 space-y-4';
    suggestionsSection.innerHTML = `
        <h3 class="text-slate-500 text-[10px] font-bold uppercase tracking-[0.25em]">Suggested Follow-up Tests</h3>
        <div class="space-y-3" id="suggestionsList"></div>
    `;

    sidebar.appendChild(suggestionsSection);

    const suggestionsList = suggestionsSection.querySelector('#suggestionsList');

    missingTestsSuggestions.forEach(suggestion => {
        const priorityColors = {
            'High': 'text-red-500',
            'Medium': 'text-amber-500',
            'Low': 'text-blue-500'
        };

        const item = document.createElement('div');
        item.className = 'glass-pill rounded-xl p-4 space-y-2';
        item.innerHTML = `
            <div class="flex items-start justify-between gap-2">
                <p class="text-sm text-slate-900 dark:text-white font-medium">${suggestion.test_name}</p>
                <span class="${priorityColors[suggestion.priority]} text-[9px] font-bold uppercase tracking-wider">${suggestion.priority}</span>
            </div>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">${suggestion.rationale}</p>
        `;

        suggestionsList.appendChild(item);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializePage);

console.log('MedLab Analyzer Validation Summary (Clinical UI) initialized successfully');
