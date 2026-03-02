// ==========================================
// INSIGHTS PAGE FUNCTIONALITY
// ==========================================

// DOM Elements
const themeToggle = document.getElementById('themeToggle');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const previousReportBtn = document.getElementById('previousReportBtn');
const printBtn = document.getElementById('printBtn');
const saveReportBtn = document.getElementById('saveReportBtn');

// Container for dynamic insights
const parameterDetailsContainer = document.getElementById('parameterDetails');

// ==========================================
// DARK MODE
// ==========================================

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme');
let isDarkMode = savedTheme === 'dark';

// Apply saved theme on load
if (isDarkMode) {
    document.documentElement.classList.add('dark');
}

themeToggle.addEventListener('click', () => {
    isDarkMode = !isDarkMode;

    if (isDarkMode) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
});

// ==========================================
// NEW ANALYSIS BUTTON
// ==========================================

if (newAnalysisBtn) {
    newAnalysisBtn.addEventListener('click', () => {
        // Clear session data
        sessionStorage.clear();

        // Show notification and redirect
        showNotification('Starting new analysis...', 'info');

        setTimeout(() => {
            window.location.href = 'upload_ui.html';
        }, 500);
    });
}

// ==========================================
// PREVIOUS REPORT BUTTON
// ==========================================

// ==========================================
// PREVIOUS REPORT / COMPARISON LOGIC
// ==========================================

const compareBtn = document.getElementById('compareBtn');
const comparisonModal = document.getElementById('comparisonModal');
const comparisonHeader = document.getElementById('comparisonHeader');
const exitComparisonBtn = document.getElementById('exitComparisonBtn');

if (compareBtn) {
    compareBtn.addEventListener('click', () => {
        loadHistory();
        comparisonModal.classList.remove('hidden');
    });
}

if (exitComparisonBtn) {
    exitComparisonBtn.addEventListener('click', () => {
        exitComparisonMode();
    });
}

async function loadHistory() {
    const listContainer = document.getElementById('historyList');
    listContainer.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/history`, { credentials: 'include' });
        if (!response.ok) throw new Error('Failed to fetch history');

        const history = await response.json();

        if (history.length === 0) {
            listContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-8 text-center">
                    <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                        <span class="material-icons-round text-3xl text-slate-400 dark:text-slate-500">history_toggle_off</span>
                    </div>
                    <p class="text-slate-600 dark:text-slate-300 font-semibold mb-1">No Previous Reports</p>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Upload more reports to see comparisons.</p>
                </div>
            `;
            return;
        }

        let html = '';
        history.forEach(report => {
            html += `
                <div class="p-4 border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors flex justify-between items-center group"
                     onclick="compareWithReport(${report.id}, this.dataset.filename, '${report.timestamp}')"
                     data-filename="${report.filename ? report.filename.replace(/"/g, '&quot;') : 'Report'}">
                    <div>
                        <div class="font-semibold text-slate-800 dark:text-white">${report.filename}</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2 mt-1">
                            <span class="material-icons-round text-[10px]">calendar_today</span>
                            ${new Date(report.timestamp).toLocaleDateString()}
                            <span class="w-1 h-1 rounded-full bg-slate-300"></span>
                            <span>${report.status || 'Processed'}</span>
                        </div>
                    </div>
                    <span class="material-icons-round text-teal-500 opacity-0 group-hover:opacity-100 transition-opacity">arrow_forward</span>
                </div>
            `;
        });
        listContainer.innerHTML = html;

    } catch (error) {
        console.error('Error fetching history:', error);
        listContainer.innerHTML = '<p class="text-center text-red-500 py-4">Failed to load history.</p>';
    }
}

let comparisonData = null;

async function compareWithReport(reportId, filename, date) {
    try {
        const response = await fetch(`${API_BASE_URL}/report/${reportId}`, { credentials: 'include' });
        if (!response.ok) throw new Error('Failed to fetch report details');

        const reportData = await response.json();

        // Convert parameters array to a name-indexed dictionary
        comparisonData = {};
        if (reportData.parameters && Array.isArray(reportData.parameters)) {
            reportData.parameters.forEach(p => {
                comparisonData[p.name] = p;
            });
        } else if (Array.isArray(reportData)) {
            // Just in case the endpoint returns an array directly
            reportData.forEach(p => {
                comparisonData[p.name] = p;
            });
        }

        // Update UI for comparison mode
        comparisonModal.classList.add('hidden');
        comparisonHeader.classList.remove('hidden');
        comparisonHeader.classList.remove('translate-y-[-100%]');
        document.getElementById('comparingWithName').textContent = `${filename} (${new Date(date).toLocaleDateString()})`;

        // Re-render insights with comparison data
        const currentParams = JSON.parse(sessionStorage.getItem('analysisResults') || '[]');
        const currentInsights = JSON.parse(sessionStorage.getItem('analysisInsights') || '{}');

        renderDynamicInsights(currentParams, currentInsights, comparisonData);

        showNotification(`Comparing with ${filename}`, 'success');

    } catch (error) {
        console.error('Comparison error:', error);
        showNotification('Failed to load comparison data', 'error');
    }
}

function exitComparisonMode() {
    comparisonData = null;
    comparisonHeader.classList.add('translate-y-[-100%]');
    setTimeout(() => {
        comparisonHeader.classList.add('hidden');
    }, 300);

    // Re-render without comparison
    const currentParams = JSON.parse(sessionStorage.getItem('analysisResults') || '[]');
    const currentInsights = JSON.parse(sessionStorage.getItem('analysisInsights') || '{}');
    renderDynamicInsights(currentParams, currentInsights);
}

// ==========================================
// PRINT SUMMARY BUTTON
// ==========================================

if (printBtn) {
    printBtn.addEventListener('click', () => {
        window.print();
    });
}

// ==========================================
// SAVE REPORT BUTTON
// ==========================================

// const saveReportBtn = document.getElementById('saveReportBtn'); // Already declared at top

if (saveReportBtn) {
    saveReportBtn.addEventListener('click', async () => {
        saveReportBtn.disabled = true;
        const originalContent = saveReportBtn.innerHTML;
        saveReportBtn.innerHTML = '<span class="animate-spin w-5 h-5 border-2 border-primary border-t-transparent rounded-full"></span> Saving...';

        try {
            const reportId = sessionStorage.getItem('currentReportId');
            if (!reportId) {
                throw new Error("Report ID not found. Cannot save insights.");
            }

            const analysisInsights = JSON.parse(sessionStorage.getItem('analysisInsights') || '{}');
            const analysisSummary = JSON.parse(sessionStorage.getItem('analysisSummary') || '{}');
            const systemsImpact = JSON.parse(sessionStorage.getItem('systemsImpact') || '{}');
            const uploadedFile = JSON.parse(sessionStorage.getItem('uploadedFile') || '{}');

            const payload = {
                insights: analysisInsights,
                summary: analysisSummary,
                systems_impact: systemsImpact,
                filename: uploadedFile.name || 'document'
            };

            const response = await fetch(`${API_BASE_URL}/report/${reportId}/save-insights`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to save report: ${response.statusText}`);
            }

            showNotification('Report insights saved successfully!', 'success');

            // Change button visual to saved state
            saveReportBtn.innerHTML = '<span class="material-icons-round text-xl relative top-[1px]">bookmark</span> Saved';
            saveReportBtn.classList.add('bg-teal-50', 'dark:bg-teal-900/40', 'border-transparent');
            saveReportBtn.classList.remove('hover:bg-teal-50', 'dark:hover:bg-teal-900/20');

        } catch (error) {
            console.error('Save report error:', error);
            showNotification(error.message || 'Failed to save report', 'error');
            saveReportBtn.disabled = false;
            saveReportBtn.innerHTML = originalContent;
        }
    });
}

// ==========================================
// EXPORT BUTTONS
// ==========================================

const exportPdfBtn = document.getElementById('exportPdfBtn');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');

async function exportReport(format) {
    try {
        const analysisResults = sessionStorage.getItem('analysisResults');
        const analysisSummary = sessionStorage.getItem('analysisSummary');

        if (!analysisResults) {
            showNotification('No data to export', 'error');
            return;
        }

        const parameters = JSON.parse(analysisResults);
        const summary = JSON.parse(analysisSummary || '{}');

        // Reconstruct analysis object for backend
        const analysis = {};
        parameters.forEach(p => {
            analysis[p.name] = {
                value: p.value,
                unit: p.unit,
                range: p.range,
                status: p.status
            };
        });

        // Get systems impact and insights from sessionStorage
        const systemsImpactStr = sessionStorage.getItem('systemsImpact');
        const insightsStr = sessionStorage.getItem('analysisInsights');
        const uploadedFileStr = sessionStorage.getItem('uploadedFile');

        const systemsImpact = systemsImpactStr ? JSON.parse(systemsImpactStr) : {};
        const insights = insightsStr ? JSON.parse(insightsStr) : { summary: summary };
        const uploadedFile = uploadedFileStr ? JSON.parse(uploadedFileStr) : {};

        const payload = {
            analysis: analysis,
            insights: insights,
            systems_impact: systemsImpact,
            filename: uploadedFile.name || 'Uploaded Report'
        };

        const response = await fetch(`${API_BASE_URL}/api/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        if (!response.ok) throw new Error(`${format.toUpperCase()} generation failed`);

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `lab-summary-report.${format === 'excel' ? 'xlsx' : format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match) filename = match[1];
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification(`${format.toUpperCase()} exported successfully!`, 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification(`Failed to export ${format.toUpperCase()}`, 'error');
    }
}

if (exportPdfBtn) exportPdfBtn.addEventListener('click', () => exportReport('pdf'));
if (exportExcelBtn) exportExcelBtn.addEventListener('click', () => exportReport('excel'));
if (exportCsvBtn) exportCsvBtn.addEventListener('click', () => exportReport('csv'));

// ==========================================
// CIRCULAR PROGRESS ANIMATION
// ==========================================

function animateCircularProgress() {
    const circles = document.querySelectorAll('[id^="circle"]');

    circles.forEach(circle => {
        const dashOffset = parseFloat(circle.getAttribute('stroke-dashoffset'));
        let currentOffset = 251; // Full circle

        const animate = () => {
            if (currentOffset > dashOffset) {
                currentOffset -= 2;
                circle.setAttribute('stroke-dashoffset', currentOffset);
                requestAnimationFrame(animate);
            }
        };

        // Start animation after a short delay
        setTimeout(animate, 300);
    });
}

// ==========================================
// INITIALIZE PAGE
// ==========================================

function initializePage() {
    // Inject Skeletons for a "Juicy" UX
    const container = document.getElementById('parameterDetails');
    if (container) {
        container.innerHTML = Array(3).fill(`
            <div class="bg-white dark:bg-slate-900/60 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700/30 mb-6 cursor-wait">
                <div class="flex flex-col md:flex-row gap-6">
                    <div class="md:w-1/3 flex items-start gap-4">
                        <div class="w-12 h-12 rounded-xl skeleton-loading shrink-0"></div>
                        <div class="w-full space-y-3 mt-1">
                            <div class="h-4 skeleton-loading w-3/4 rounded"></div>
                            <div class="h-3 skeleton-loading w-1/2 rounded mt-2"></div>
                        </div>
                    </div>
                    <div class="md:w-2/3 space-y-3 mt-1">
                        <div class="h-4 skeleton-loading w-full rounded"></div>
                        <div class="h-4 skeleton-loading w-5/6 rounded mt-2"></div>
                        <div class="h-4 skeleton-loading w-4/6 rounded mt-2"></div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Artificial wait for anticipatory UX
    setTimeout(() => {
        // Check sessionStorage for data
        const summaryData = sessionStorage.getItem('analysisSummary');
        const paramsDataStr = sessionStorage.getItem('analysisResults');
        const systemsImpactStr = sessionStorage.getItem('systemsImpact');
        let paramsData = [];

        if (paramsDataStr) {
            try {
                paramsData = JSON.parse(paramsDataStr);
                // Load backend insights
                const insightsDataStr = sessionStorage.getItem('analysisInsights');
                let insightsData = { detailed_insights: [] };
                if (insightsDataStr) {
                    insightsData = JSON.parse(insightsDataStr);
                }
                console.log("Loaded params for insights", paramsData);
                console.log("Loaded backend insights", insightsData);
                renderDynamicInsights(paramsData, insightsData);
            } catch (e) { console.error(e); }
        }

        // Load and render systems impact
        if (systemsImpactStr) {
            try {
                const systemsImpact = JSON.parse(systemsImpactStr);
                console.log("Loaded systems impact", systemsImpact);
                renderSystemsImpact(systemsImpact);
                renderBodyFigure(systemsImpact);
            } catch (e) { console.error('Error parsing systems impact', e); }
        }

        if (summaryData) {
            try {
                const summary = JSON.parse(summaryData);

                // Update Stats Cards
                // Card 1: Total
                document.querySelector('.neon-glow-blue + div h3').textContent = 'TOTAL EXTRACTED'; // Keep label
                document.querySelector('.neon-glow-blue span').textContent = summary.total_extracted || 0;

                // Card 2: Optimal
                document.querySelector('.neon-glow-green span').textContent = summary.optimal_count || 0;

                // Card 3: Attention
                document.querySelector('.neon-glow-coral span').textContent = summary.attention_count || 0;

                // Wellness Score
                const max = summary.total_extracted || 1;
                const optimal = summary.optimal_count || 0;
                const score = Math.round((optimal / max) * 100);

                const wellnessText = document.getElementById('wellnessScoreText');
                const wellnessLabel = document.getElementById('wellnessScoreLabel');
                const wellnessCircle = document.getElementById('circleWellness');

                if (wellnessText) {
                    wellnessText.textContent = score;
                    let label = "Needs Attention";
                    if (score >= 90) label = "Excellent";
                    else if (score >= 70) label = "Good";
                    else if (score >= 50) label = "Fair";

                    if (wellnessLabel) wellnessLabel.textContent = label;

                    if (wellnessCircle) {
                        const offset = 264 * (1 - (score / 100));
                        wellnessCircle.setAttribute('stroke-dashoffset', offset);
                    }
                }

                // Update Progress Circles (Calculate dash offsets)
                // Circumference is approx 264

                const optimalPct = (summary.optimal_count / max);
                const attentionPct = (summary.attention_count / max);

                const circle2 = document.getElementById('circle2');
                if (circle2) {
                    // Invert logic: stroke-dashoffset = circumference * (1 - percentage)
                    // Actually existing CSS seems to just act as a loader, we should maintain the animation 
                    // but strictly speaking we should set the final values here if we want accuracy.
                    // For now, let's keep the visual "alive" but update the text.
                }

                // Analysis Depth
                const depthBar = document.querySelector('.text-teal-600');
                if (depthBar) depthBar.textContent = summary.analysis_depth || '100%';

            } catch (e) {
                console.error('Error parsing summary data', e);
            }
        }

        // ── Critical Value Alert ─────────────────────────────────────────────────
        // If any parameters are Critical severity, show blocking modal AFTER render
        try {
            const criticalParams = (Array.isArray(paramsData) ? paramsData : []).filter(
                p => p.status === 'Critical' || (p.severity || '').toUpperCase() === 'CRITICAL'
            );
            if (criticalParams.length > 0 && typeof window.showCriticalAlert === 'function') {
                // Small delay so the page has rendered behind the modal
                setTimeout(() => {
                    window.showCriticalAlert(criticalParams.map(p => ({ name: p.name, value: p.value, unit: p.unit || '' })));
                }, 400);
            }
        } catch (critErr) {
            console.warn('Critical alert check failed:', critErr);
        }

        // Generate Natural Language AI Summary
        if (summaryData) {
            try {
                generateAndDisplayAISummary(JSON.parse(summaryData), paramsData);
            } catch (e) { console.error('Error generating AI Summary', e); }
        }

        // Animate progress circles
        animateCircularProgress();
    }, 600); // 600ms artificial wait for juicy UX
}

// ==========================================
// AI NATURAL LANGUAGE SUMMARY
// ==========================================

function generateAndDisplayAISummary(summary, paramsData) {
    const container = document.getElementById('aiSummaryContainer');
    const textContainer = document.getElementById('aiSummaryText');
    if (!container || !textContainer || !paramsData || !paramsData.length) return;

    container.classList.remove('hidden');

    const max = summary.total_extracted || 1;
    const optimal = summary.optimal_count || 0;
    const score = Math.round((optimal / max) * 100);

    let overachingHealth = "Your biomarkers are largely balanced.";
    if (score >= 90) overachingHealth = "Your results are absolutely excellent, showing strong baseline health.";
    else if (score >= 70) overachingHealth = "Your results look generally good, though a few metrics require some fine-tuning.";
    else if (score >= 50) overachingHealth = "Your profile shows several key areas that need attention and lifestyle adjustment.";
    else overachingHealth = "Your blood work indicates significant clinical deviations that strongly recommend medical consultation.";

    const criticalParams = paramsData.filter(p => p.status === 'Critical' || (p.severity || '').toUpperCase() === 'CRITICAL');
    const highLowParams = paramsData.filter(p => !criticalParams.includes(p) && (p.status === 'High' || p.status === 'Low' || p.status === 'Review'));

    let details = "";
    if (criticalParams.length > 0) {
        const names = criticalParams.map(p => `<strong>${p.name}</strong>`).join(', ');
        details += `Critically, you have urgent alerts for ${names} that require immediate clinical review. `;
    }

    if (highLowParams.length > 0) {
        const top3 = highLowParams.slice(0, 3).map(p => `<strong>${p.name}</strong> (${p.status})`).join(', ');
        details += `Additionally, keep an eye on ${top3}${highLowParams.length > 3 ? ` and ${highLowParams.length - 3} others` : ''}. `;
    } else if (criticalParams.length === 0) {
        details += "All extracted parameters fall within their optimal or normal physiological ranges! Keep up the good work.";
    }

    const htmlContent = `
        <p>${overachingHealth} ${details}</p>
        <p class="mt-2 text-sm text-indigo-500/80 dark:text-indigo-400/80 italic">This AI summary is generated from your data but is not a medical diagnosis.</p>
    `;

    textContainer.classList.add('opacity-0', 'transition-opacity', 'duration-700');

    // Slight delay for "typing" effect simulation
    setTimeout(() => {
        textContainer.innerHTML = htmlContent;
        requestAnimationFrame(() => {
            textContainer.classList.remove('opacity-0');
        });
    }, 400);
}

// ==========================================
// RENDER BODY FIGURE (Dynamic Markers)
// ==========================================

// Severity to visual mapping (non-diagnostic)
const SEVERITY_COLORS = {
    none: { fill: '#94a3b8', stroke: '#64748b', pulse: false },    // Slate/muted
    mild: { fill: '#f59e0b', stroke: '#d97706', pulse: true },     // Amber
    moderate: { fill: '#f97316', stroke: '#ea580c', pulse: true }, // Orange
    high: { fill: '#ef4444', stroke: '#dc2626', pulse: true }      // Red (but NOT called "critical")
};

function renderBodyFigure(systemsData) {
    const markersGroup = document.getElementById('bodyMarkers');
    const labelsContainer = document.getElementById('bodyLabels');

    if (!markersGroup || !labelsContainer) return;

    // Clear existing markers and labels
    markersGroup.innerHTML = '';
    labelsContainer.innerHTML = '';

    const allSystems = Object.entries(systemsData);

    if (allSystems.length === 0) {
        return;
    }

    let markersSvg = '';
    let labelsHtml = '';
    let relationshipsSvg = '';

    // First, render relationships as curved lines
    allSystems.forEach(([systemName, data]) => {
        const relatedSystems = data.related_systems || [];
        if (relatedSystems.length > 0) {
            const sourceRegion = data.body_region || { x: 50, y: 100 };

            relatedSystems.forEach(rel => {
                const targetData = systemsData[rel.target];
                if (targetData) {
                    const targetRegion = targetData.body_region || { x: 50, y: 100 };

                    // Calculate control point for curved line (bezier curve)
                    const midX = (sourceRegion.x + targetRegion.x) / 2;
                    const midY = (sourceRegion.y + targetRegion.y) / 2;
                    const offsetX = (targetRegion.y - sourceRegion.y) * 0.2; // Perpendicular offset
                    const controlX = midX + offsetX;
                    const controlY = midY;

                    // Color based on relationship type
                    let strokeColor = '#94a3b8'; // default slate
                    let strokeOpacity = 0.2;
                    if (rel.type === 'regulatory') {
                        strokeColor = '#3b82f6'; // blue
                        strokeOpacity = 0.3;
                    } else if (rel.type === 'hormonal') {
                        strokeColor = '#8b5cf6'; // purple
                        strokeOpacity = 0.3;
                    } else if (rel.type === 'metabolic') {
                        strokeColor = '#f59e0b'; // amber
                        strokeOpacity = 0.3;
                    }

                    relationshipsSvg += `
        < path d = "M ${sourceRegion.x},${sourceRegion.y} Q ${controlX},${controlY} ${targetRegion.x},${targetRegion.y}"
    fill = "none" stroke = "${strokeColor}" stroke - width="0.8"
    stroke - opacity="${strokeOpacity}" stroke - dasharray="2,2"
    class="hover:stroke-opacity-60 transition-all" />
        `;
                }
            });
        }
    });

    // Render all systems (both normal and abnormal)
    allSystems.forEach(([systemName, data], index) => {
        const region = data.body_region || { x: 50, y: 100 };
        const healthScore = data.health_score || 100;

        // Determine color based on health score
        let colors;
        if (healthScore >= 90) {
            colors = { fill: '#10b981', stroke: '#059669', pulse: false }; // Emerald
        } else if (healthScore >= 70) {
            colors = { fill: '#f59e0b', stroke: '#d97706', pulse: true }; // Amber
        } else if (healthScore >= 50) {
            colors = { fill: '#f97316', stroke: '#ea580c', pulse: true }; // Orange
        } else {
            colors = { fill: '#ef4444', stroke: '#dc2626', pulse: true }; // Red
        }

        const markerId = `marker - ${systemName.replace(/\s+/g, '-').toLowerCase()} `;

        // Create SVG marker with click handler
        markersSvg += `
        < g class="body-marker cursor-pointer hover:opacity-80 transition-opacity" data - system="${systemName}" onclick = "showSystemDetail('${systemName}')" >
                < !--Outer pulse ring(only for abnormal) -->
        ${colors.pulse ? `
                <circle cx="${region.x}" cy="${region.y}" r="8" 
                    fill="none" stroke="${colors.stroke}" stroke-opacity="0.3" stroke-width="1.5">
                    <animate attributeName="r" dur="2.5s" repeatCount="indefinite" values="6;10;6"/>
                    <animate attributeName="stroke-opacity" dur="2.5s" repeatCount="indefinite" values="0.4;0.1;0.4"/>
                </circle>
                ` : ''
            }
                < !--Central marker-- >
        <circle cx="${region.x}" cy="${region.y}" r="4"
            fill="${colors.fill}" stroke="${colors.stroke}" stroke-width="1"
            class="cursor-pointer" style="filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2))" />
            </g >
        `;

        // Create HTML label with health score
        const labelSide = region.x > 50 ? 'left' : 'right';
        const labelX = labelSide === 'left' ? '5%' : '55%';
        const labelY = `${(region.y / 240) * 100}% `;

        const abnormalCount = data.abnormal_count || 0;
        const showHealthScore = abnormalCount > 0;

        labelsHtml += `
        < div class="absolute pointer-events-auto group/label cursor-pointer"
    style = "top: ${labelY}; ${labelSide}: 2px; transform: translateY(-50%);"
    onclick = "showSystemDetail('${systemName}')" >
                <div class="px-2 py-1 rounded-md text-[9px] font-bold shadow-md whitespace-nowrap
                    ${healthScore >= 90 ? 'bg-emerald-500 text-white' :
                healthScore >= 70 ? 'bg-amber-500 text-white' :
                    healthScore >= 50 ? 'bg-orange-500 text-white' :
                        'bg-red-500 text-white'}
                    ${healthScore >= 90 ? 'opacity-50' : ''}">
                    ${systemName.toUpperCase().slice(0, 12)}${showHealthScore ? ` ${healthScore}` : ''}
                </div>
                <!--Tooltip on hover-- >
        <div class="absolute ${labelSide === 'left' ? 'left-full ml-2' : 'right-full mr-2'} top-1/2 -translate-y-1/2 
                     opacity-0 group-hover/label:opacity-100 transition-opacity z-50 pointer-events-none">
            <div class="bg-slate-900 dark:bg-slate-800 text-white text-[10px] px-3 py-2 rounded-lg shadow-xl whitespace-nowrap">
                <div class="font-bold mb-1">${systemName}</div>
                <div class="text-slate-300">Health Score: ${healthScore}/100</div>
                <div class="text-slate-400 mt-1">${data.status}</div>
                ${abnormalCount > 0 ? `<div class="text-rose-400 mt-1">${abnormalCount} abnormal</div>` : ''}
                <div class="text-cyan-400 mt-2 text-[9px]">Click for details →</div>
            </div>
        </div>
            </div >
        `;
    });

    // Inject relationships first (so they appear below markers)
    const relationshipsGroup = document.getElementById('systemRelationships');
    if (relationshipsGroup) {
        relationshipsGroup.innerHTML = relationshipsSvg;
    }

    markersGroup.innerHTML = markersSvg;
    labelsContainer.innerHTML = labelsHtml;
}

// ==========================================
// RENDER SYSTEMS IMPACT
// ==========================================

function renderSystemsImpact(systemsData) {
    // Store globally for interactive body map
    globalSystemsData = systemsData;

    const container = document.getElementById('systemsImpactContainer');
    if (!container) return;

    const systemNames = Object.keys(systemsData);

    if (systemNames.length === 0) {
        container.innerHTML = `
        < div class="flex flex-col items-center justify-center py-6 text-center bg-emerald-50/50 dark:bg-emerald-900/10 rounded-2xl border border-emerald-100 dark:border-emerald-800/30" >
                <div class="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/40 rounded-full flex items-center justify-center mb-3">
                    <span class="material-icons-round text-2xl text-emerald-500">health_and_safety</span>
                </div>
                <p class="text-slate-800 dark:text-emerald-50 font-semibold mb-1">Optimal System Health</p>
                <p class="text-xs text-slate-500 dark:text-emerald-200/60 max-w-[200px]">No significant systemic impacts detected from current values.</p>
            </div >
        `;
        return;
    }

    // Sort systems: critical first, then by abnormal count
    const sortedSystems = systemNames.sort((a, b) => {
        const sysA = systemsData[a];
        const sysB = systemsData[b];
        if (sysA.critical && !sysB.critical) return -1;
        if (!sysA.critical && sysB.critical) return 1;
        return sysB.abnormal_count - sysA.abnormal_count;
    });

    let html = '';

    sortedSystems.forEach(systemName => {
        const system = systemsData[systemName];

        // Determine colors based on health score (new weighted approach)
        const healthScore = system.health_score || 0;
        let bgColor, borderColor, iconBg, iconText, statusColor, scoreColor;

        if (healthScore >= 90) {
            // Excellent health
            bgColor = 'bg-emerald-50 dark:bg-emerald-900/10';
            borderColor = 'border-emerald-200 dark:border-emerald-800/30';
            iconBg = 'bg-emerald-100 dark:bg-emerald-500/10';
            iconText = 'text-emerald-600 dark:text-emerald-400';
            statusColor = 'text-emerald-600 dark:text-emerald-400';
            scoreColor = 'text-emerald-600';
        } else if (healthScore >= 70) {
            // Good health
            bgColor = 'bg-amber-50 dark:bg-amber-900/10';
            borderColor = 'border-amber-200 dark:border-amber-800/30';
            iconBg = 'bg-amber-100 dark:bg-amber-500/10';
            iconText = 'text-amber-600 dark:text-amber-400';
            statusColor = 'text-amber-600 dark:text-amber-400';
            scoreColor = 'text-amber-600';
        } else if (healthScore >= 50) {
            // Fair health
            bgColor = 'bg-orange-50 dark:bg-orange-900/10';
            borderColor = 'border-orange-200 dark:border-orange-800/30';
            iconBg = 'bg-orange-100 dark:bg-orange-500/10';
            iconText = 'text-orange-600 dark:text-orange-400';
            statusColor = 'text-orange-600 dark:text-orange-400';
            scoreColor = 'text-orange-600';
        } else {
            // Poor health
            bgColor = 'bg-rose-50 dark:bg-rose-900/10';
            borderColor = 'border-rose-200 dark:border-rose-800/30';
            iconBg = 'bg-rose-100 dark:bg-rose-500/10';
            iconText = 'text-rose-600 dark:text-rose-400';
            statusColor = 'text-rose-600 dark:text-rose-400';
            scoreColor = 'text-rose-600';
        }

        // Build parameter list tooltip
        const abnormalList = system.abnormal_parameters.map(p =>
            `${p.name}: ${p.value} (${p.status})`
        ).join(', ') || 'All within range';

        // Calculate progress percentage for score circle
        const scorePercentage = healthScore;
        const circumference = 2 * Math.PI * 16; // r=16
        const dashOffset = circumference * (1 - scorePercentage / 100);

        html += `
        < div class="flex items-start gap-3 p-3 ${bgColor} rounded-xl border ${borderColor} transition-all hover:shadow-md group cursor-pointer"
    onclick = "showSystemDetail('${systemName}')"
    title = "${abnormalList}" >
                <div class="w-9 h-9 ${iconBg} rounded-lg flex items-center justify-center ${iconText} border dark:border-current/20 flex-shrink-0">
                    <span class="material-icons-round text-lg">${system.icon}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between gap-2 mb-1">
                        <p class="text-xs font-bold text-slate-900 dark:text-white truncate">${systemName}</p>
                        <span class="text-[9px] ${statusColor} font-bold whitespace-nowrap">${system.abnormal_count}/${system.total_count}</span>
                    </div>
                    
                    <!-- Health Score Display -->
                    <div class="flex items-center gap-2 mb-1">
                        <div class="relative w-8 h-8 flex-shrink-0">
                            <svg class="w-full h-full -rotate-90" viewBox="0 0 36 36">
                                <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" 
                                    class="text-slate-200 dark:text-slate-700" stroke-width="3"></circle>
                                <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" 
                                    class="${scoreColor}" stroke-width="3" 
                                    stroke-dasharray="${circumference}" 
                                    stroke-dashoffset="${dashOffset}"
                                    stroke-linecap="round"></circle>
                            </svg>
                            <span class="absolute inset-0 flex items-center justify-center text-[9px] font-bold ${scoreColor}">${healthScore}</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-[10px] ${statusColor} font-medium truncate">${system.status}</p>
                            <p class="text-[8px] text-slate-400 dark:text-slate-500">Health Score</p>
                        </div>
                    </div>
                    
                    ${system.abnormal_parameters.length > 0 ? `
                        <div class="mt-1 flex flex-wrap gap-1">
                            ${system.abnormal_parameters.slice(0, 2).map(p => `
                                <span class="inline-block px-1.5 py-0.5 text-[8px] font-bold uppercase rounded 
                                    ${p.status === 'Critical' ? 'bg-rose-200 dark:bg-rose-800 text-rose-700 dark:text-rose-300' :
                p.status === 'High' ? 'bg-orange-200 dark:bg-orange-800 text-orange-700 dark:text-orange-300' :
                    'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300'}">${p.name}</span>
                            `).join('')}
                            ${system.abnormal_parameters.length > 2 ? `<span class="text-[8px] text-slate-400">+${system.abnormal_parameters.length - 2} more</span>` : ''}
                        </div>
                    ` : ''}
                </div>
            </div >
        `;
    });

    container.innerHTML = html;
}

function renderDynamicInsights(parameters, insightsData = { detailed_insights: [] }, comparisonReport = null) {
    if (!parameterDetailsContainer) return;

    // Trend Celebrations
    if (comparisonReport) {
        let celebrations = [];
        parameters.forEach(param => {
            const prev = comparisonReport[param.name];
            if (prev && ['High', 'Low', 'Critical'].includes(prev.status) && param.status === 'Normal') {
                const prevVal = parseFloat(prev.value);
                const currVal = parseFloat(param.value);
                if (!isNaN(prevVal) && !isNaN(currVal)) {
                    const diff = currVal - prevVal;
                    const percent = Math.abs((diff / prevVal) * 100).toFixed(1);
                    celebrations.push({ name: param.name, percent });
                }
            }
        });

        if (celebrations.length > 0) {
            setTimeout(() => {
                if (typeof confetti === 'function') confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 }, zIndex: 10000 });
                const msg = celebrations.length === 1
                    ? `🎉 Great job! Your ${celebrations[0].name} improved by ${celebrations[0].percent}% to Normal.`
                    : `🎉 Great job! ${celebrations.length} metrics improved to Normal since your last test.`;
                showNotification(msg, 'success');
            }, 1000);
        }
    }

    // Filter for abnormal items: High, Low, Critical
    const abnormalItems = parameters.filter(p => ['High', 'Low', 'Critical'].includes(p.status));

    if (abnormalItems.length === 0) {
        parameterDetailsContainer.innerHTML = `
        < div class="p-8 text-center card-light rounded-2xl" >
                <span class="material-icons-round text-5xl text-emerald-500 mb-4">check_circle</span>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white">All Results Normal</h3>
                <p class="text-slate-500">No parameters flagged for attention.</p>
            </div >
        `;
        return;
    }

    let html = `
        < div class="flex items-center gap-4 mb-8" >
            <h2 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <span class="w-1 h-8 bg-cyan-500 rounded-full"></span>
                Attention Required
            </h2>
            <div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
            <span class="text-sm font-bold text-rose-500 bg-rose-50 dark:bg-rose-900/20 px-3 py-1 rounded-full border border-rose-100 dark:border-rose-900/30 flex items-center gap-2">
                <span class="material-icons-round text-sm">warning</span>
                ${abnormalItems.length} Issues Found
            </span>
        </div >
        <div class="space-y-6">
            `;

    abnormalItems.forEach(param => {
        // Get backend insight data
        let backendInsight = null;
        if (insightsData && insightsData.detailed_insights) {
            backendInsight = insightsData.detailed_insights.find(
                i => i.parameter === param.name && i.status.toUpperCase() === param.status.toUpperCase()
            );
        }

        // Severity mapping
        const severityCode = param.severity || backendInsight?.severity || 'MEDIUM';
        const severityLabel = param.severity_label || backendInsight?.severity_label || 'Moderate Deviation';
        const severityClass = {
            'LOW': 'severity-badge-mild',
            'MEDIUM': 'severity-badge-moderate',
            'HIGH': 'severity-badge-moderate',
            'CRITICAL': 'severity-badge-critical'
        }[severityCode] || 'severity-badge-moderate';

        // COMPARISON LOGIC
        let comparisonHTML = '';
        if (comparisonReport && comparisonReport[param.name]) {
            const prev = comparisonReport[param.name];
            const prevVal = parseFloat(prev.value);
            const currVal = parseFloat(param.value);

            if (!isNaN(prevVal) && !isNaN(currVal)) {
                const diff = currVal - prevVal;
                const percentChange = (diff / prevVal) * 100;
                const arrow = diff > 0 ? 'arrow_upward' : (diff < 0 ? 'arrow_downward' : 'remove');
                const color = diff > 0 ? 'text-rose-500' : 'text-emerald-500'; // Context dependent, keeping simple for now

                comparisonHTML = `
            <div class="mt-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg flex justify-between items-center text-xs">
                <span class="text-indigo-600 dark:text-indigo-300 font-medium">Previous: ${prevVal} ${prev.unit}</span>
                <div class="flex items-center gap-1 ${color} font-bold">
                    <span class="material-icons-round text-xs">${arrow}</span>
                    <span>${Math.abs(percentChange).toFixed(1)}%</span>
                </div>
            </div>
            `;
            }
        }

        // Confidence data
        const confidenceScore = backendInsight?.confidence_score || 60;
        const confidenceRationale = backendInsight?.confidence_rationale || 'Limited contextual data';
        const confidenceClass = confidenceScore >= 75 ? 'confidence-high' : (confidenceScore >= 50 ? 'confidence-medium' : 'confidence-low');

        // Audit trail
        const auditTrail = backendInsight?.audit_trail;

        // Insight text
        const rawInsightText = backendInsight?.insight || generateInsightText(param, insightsData);
        const insightText = enrichInsightText(rawInsightText);

        // Supporting parameters
        const supportingParams = backendInsight?.supporting_params || [];

        // Color scheme
        let statusColor = "amber";
        if (param.status === 'Critical') statusColor = "rose";
        else if (param.status === 'Low') statusColor = "blue";

        const rangeStr = param.range ? `Reference: ${param.range}` : 'No reference range';

        html += `
            <!-- Parameter Card with Enhanced Phase 2-4 Features -->
            <div class="card-light rounded-[2rem] p-8 hover:shadow-lg dark:hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] transition-all duration-300 border border-slate-100 dark:border-slate-800 group relative overflow-hidden">

                <!-- Status Line -->
                <div class="absolute left-0 top-0 bottom-0 w-1 bg-${statusColor}-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

                <div class="flex flex-col gap-6">
                    <!-- Header with Severity Badge -->
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-3 mb-2">
                                <h3 class="text-lg font-bold text-slate-800 dark:text-white">${param.name}</h3>
                                <span class="severity-badge ${severityClass}">
                                    <span class="severity-dot severity-dot-${severityCode.toLowerCase()}"></span>
                                    ${severityLabel}
                                </span>
                            </div>
                            ${supportingParams.length > 0 ? `
                        <div class="flex flex-wrap gap-1 mt-2">
                            <span class="text-xs text-slate-500">Related:</span>
                            ${supportingParams.map(sp => `<span class="text-xs px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-600 dark:text-slate-400">${sp}</span>`).join('')}
                        </div>
                        ` : ''}
                        </div>
                        <div class="text-right">
                            <div class="text-3xl font-bold text-slate-800 dark:text-white font-mono tracking-tight">${param.value}</div>
                            <div class="text-sm font-bold text-slate-400">${param.unit}</div>
                        </div>
                    </div>

                    <!-- Confidence Indicator (Phase 3) -->
                    <div class="confidence-indicator">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">System Confidence</span>
                            <span class="text-xs font-bold text-slate-700 dark:text-slate-300">${confidenceScore}%</span>
                        </div>
                        <div class="confidence-bar-container">
                            <div class="confidence-bar ${confidenceClass}" style="width: ${confidenceScore}%"></div>
                        </div>
                        <details class="mt-2">
                            <summary class="text-xs text-slate-500 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">View rationale</summary>
                            <p class="text-xs text-slate-600 dark:text-slate-400 mt-1 pl-4">${confidenceRationale}</p>
                        </details>
                    </div>

                    <!-- Range Visualization -->
                    <div class="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div class="absolute top-0 bottom-0 left-1/4 right-1/4 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                        <div class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-${statusColor}-500 rounded-full ring-4 ring-white dark:ring-slate-900 shadow-lg left-[${param.status === 'Low' ? '15%' : '85%'}]">
                            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                                ${param.value}
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-between mt-2 text-xs font-medium text-slate-400">
                        <span>Low</span>
                        <span class="text-slate-500">${rangeStr}</span>
                        <span>High</span>
                    </div>

                    ${comparisonHTML}

                    <!-- Historical Trend (Phase 6) -->
                    <div class="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                        <details class="mt-2" ontoggle="if(this.open) fetchAndRenderTrend('${param.name}')">
                            <summary class="text-xs font-semibold text-slate-600 dark:text-slate-400 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">
                                Historical Trend
                                <span id="trend-badge-${param.name.replace(/\s+/g, '-')}" class="ml-2 inline-block"></span>
                            </summary>
                            <div class="mt-3 pl-4">
                                <div style="position: relative; height: 150px; width: 100%;">
                                    <canvas id="trend-chart-${param.name.replace(/\s+/g, '-')}"></canvas>
                                </div>
                                <div id="trend-message-${param.name.replace(/\s+/g, '-')}" class="text-xs text-slate-500 dark:text-slate-400 mt-2">Loading trend data...</div>
                            </div>
                        </details>
                    </div>

                    <!-- Insight -->
                    <div class="bg-slate-50 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-100 dark:border-slate-800 relative">
                        <div class="absolute -top-3 -left-3 w-8 h-8 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700 flex items-center justify-center">
                            <span class="material-icons-round text-sm text-${statusColor}-500">smart_toy</span>
                        </div>
                        <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pt-2">
                            ${insightText}
                        </p>
                    </div>

                    ${auditTrail ? `
                <!-- Audit Trail (Phase 4) -->
                <details class="audit-trail-section">
                    <summary class="text-xs font-semibold text-slate-500 hover:text-teal-500 transition-colors">
                        <span class="material-icons-round text-sm align-middle mr-1">info</span>
                        Why was this flagged?
                    </summary>
                    <div class="mt-3 space-y-2 text-xs bg-slate-50 dark:bg-slate-900/20 rounded-lg p-4">
                        <div class="audit-field">
                            <span class="audit-label">Rule ID:</span>
                            <span class="audit-value"><code>${auditTrail.rule_id}</code></span>
                        </div>
                        <div class="audit-field">
                            <span class="audit-label">Rule:</span>
                            <span class="audit-value">${auditTrail.rule_name}</span>
                        </div>
                        <div class="audit-field">
                            <span class="audit-label">Trigger:</span>
                            <span class="audit-value">${auditTrail.trigger_condition}</span>
                        </div>
                        ${auditTrail.deviation_percentage ? `
                        <div class="audit-field">
                            <span class="audit-label">Deviation:</span>
                            <span class="audit-value">${auditTrail.deviation_percentage.toFixed(1)}% from reference</span>
                        </div>
                        ` : ''}
                        <div class="audit-field">
                            <span class="audit-label">Timestamp:</span>
                            <span class="audit-value">${new Date(auditTrail.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="audit-field">
                            <span class="audit-label">Audit Hash:</span>
                            <span class="audit-value"><code class="text-[10px]">${auditTrail.audit_hash}</code></span>
                        </div>
                    </div>
                </details>
                ` : ''}
                </div>
            </div>`;
    });

    html += `</div>`;

    // Add Follow-Up Recommendations Section (Phase 2)
    if (insightsData.followup_recommendations && insightsData.followup_recommendations.length > 0) {
        html += `
                < div class="mt-12" >
            <div class="flex items-center gap-4 mb-6">
                <h2 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <span class="w-1 h-8 bg-blue-500 rounded-full"></span>
                    Suggested Follow-Up Tests
                </h2>
                <div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
                <button onclick="downloadCalendarReminder()" class="flex items-center gap-2 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800/60 transition-colors text-sm font-semibold border border-indigo-200 dark:border-indigo-800 shadow-sm">
                    <span class="material-icons-round text-sm">event</span>
                    Remind in 3 Months
                </button>
            </div>
            <div class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-xl p-4 mb-6">
                <div class="flex items-start gap-3">
                    <span class="material-icons-round text-amber-600 dark:text-amber-400">info</span>
                    <div class="text-sm text-amber-800 dark:text-amber-300">
                        <p class="font-semibold mb-1">Educational Recommendations</p>
                        <p class="text-xs">These are guideline-based test suggestions. Always consult your healthcare provider for personalized medical advice.</p>
                    </div>
                </div>
            </div>
            <div class="space-y-4">
        `;

        insightsData.followup_recommendations.forEach(rec => {
            const priorityClass = {
                'high': 'priority-high',
                'medium': 'priority-medium',
                'low': 'priority-low'
            }[rec.priority] || 'priority-medium';

            html += `
            <details class="card-light rounded-xl p-6 border border-slate-100 dark:border-slate-800">
                <summary class="cursor-pointer flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <span class="material-icons-round text-blue-500">science</span>
                        <span class="font-semibold text-slate-800 dark:text-white">For ${rec.parameter}</span>
                        <span class="priority-badge ${priorityClass}">${rec.priority}</span>
                    </div>
                    <span class="material-icons-round text-slate-400">expand_more</span>
                </summary>
                <div class="mt-4 pl-9">
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-3">${rec.rationale}</p>
                    <div class="space-y-2">
                        <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">Suggested Tests:</p>
                        <ul class="space-y-1">
                            ${rec.tests.map(test => `<li class="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2"><span class="material-icons-round text-xs text-teal-500 mt-0.5">check_circle</span>${test}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </details>
            `;
        });

        html += `</div></div > `;
    }

    // Explainability Panel (Phase 4)
    html += `
        < div class="mt-12 card-light rounded-2xl p-8 border border-slate-100 dark:border-slate-800" >
        <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
            <span class="material-icons-round text-cyan-500">psychology</span>
            How Insights Are Generated
        </h3>
        <div class="space-y-6">
            <div class="explainability-step">
                <div class="flex items-start gap-4">
                    <div class="step-number">1</div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-slate-800 dark:text-white mb-1">Raw Data Extraction</h4>
                        <p class="text-sm text-slate-600 dark:text-slate-400">Lab report is processed using OCR and NLP to extract parameter values, units, and reference ranges with no interpretation applied.</p>
                    </div>
                </div>
            </div>
            <div class="explainability-step">
                <div class="flex items-start gap-4">
                    <div class="step-number">2</div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-slate-800 dark:text-white mb-1">Rule-Based Classification</h4>
                        <p class="text-sm text-slate-600 dark:text-slate-400">Values are compared against reference ranges using deterministic rules. Deviations calculate severity based on percentage distance from boundaries.</p>
                    </div>
                </div>
            </div>
            <div class="explainability-step">
                <div class="flex items-start gap-4">
                    <div class="step-number">3</div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-slate-800 dark:text-white mb-1">Insight Generation</h4>
                        <p class="text-sm text-slate-600 dark:text-slate-400">Pre-written, clinically-reviewed interpretations are retrieved based on triggered rules and parameter relationships. No black-box AI prediction involved.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-6 p-4 bg-slate-50 dark:bg-slate-900/20 rounded-lg border border-slate-200 dark:border-slate-700">
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                <strong>Transparency Note:</strong> All insights are generated through explicit, traceable rules. This system does not use machine learning predictions or black-box algorithms for clinical interpretation.
            </p>
        </div>
    </div >
        `;

    // Inject
    parameterDetailsContainer.innerHTML = html;

    // Fetch and render trend data for all abnormal parameters
    abnormalItems.forEach(param => {
        fetchAndRenderTrend(param.name);
    });
}

function generateInsightText(param, insightsData) {
    // Try to find specific backend insight first
    if (insightsData && insightsData.detailed_insights) {
        const backendInsight = insightsData.detailed_insights.find(
            i => i.parameter === param.name && i.status === param.status
        );
        if (backendInsight) {
            return backendInsight.insight;
        }
    }

    // Fallback to generic text
    if (param.status === 'Critical') return `Critical value detected.Immediate medical attention may be required.`;
    if (param.status === 'High') return `Elevated ${param.name} can be associated with various conditions.Clinical correlation recommended.`;
    if (param.status === 'Low') return `Lower than normal ${param.name} detected.Discuss dietary or medical interventions with your doctor.`;
    return `Value is outside standard reference range.`;
}

const MEDICAL_TERMS = {
    'Cholesterol': '🥩 A type of fat found in your blood.',
    'LDL': '🍔 "Bad" cholesterol that builds up in arteries.',
    'HDL': '🥑 "Good" cholesterol that removes bad cholesterol.',
    'Triglycerides': '🧈 A type of fat from unused calories.',
    'Hemoglobin': '🩸 Protein in red blood cells that carries oxygen.',
    'Glucose': "🍬 Blood sugar, your body's main source of energy.",
    'Creatinine': '🧹 Waste product filtered by kidneys.',
    'Bilirubin': '🟡 Substance made during normal breakdown of red blood cells.',
    'Platelets': '🩹 Blood cells that help form clots and stop bleeding.',
    'Erythrocytes': '🔴 Red blood cells.'
};

function enrichInsightText(text) {
    if (!text) return text;
    let enriched = text;
    Object.keys(MEDICAL_TERMS).forEach(term => {
        const regex = new RegExp(`\\\\b(${term}) \\\\b`, 'gi');
        enriched = enriched.replace(regex, `< span class="relative group inline-block cursor-help border-b-2 border-dashed border-indigo-300 dark:border-indigo-600 text-indigo-700 dark:text-indigo-300 font-medium pb-0.5" > $1 < span class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 pointer-events-none text-center leading-tight" > ${MEDICAL_TERMS[term]} <svg class="absolute text-slate-800 h-2 w-full left-0 top-full" x="0px" y="0px" viewBox="0 0 255 255"><polygon class="fill-current" points="0,0 127.5,127.5 255,0" /></svg></span ></span > `);
    });
    return enriched;
}

// ==========================================
// INTERACTIVE BODY MAP - SYSTEM DETAIL MODAL
// ==========================================

// Global storage for systems data
let globalSystemsData = {};

function showSystemDetail(systemName) {
    const systemData = globalSystemsData[systemName];
    if (!systemData) {
        console.error('System data not found:', systemName);
        return;
    }

    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 animate-fadeIn';
    modal.id = 'systemDetailModal';

    // Modal content
    const abnormalParams = systemData.abnormal_parameters || [];
    const normalParams = systemData.normal_parameters || [];

    modal.innerHTML = `
        < div class="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden animate-slideUp" >
            <div class="p-6 border-b border-slate-200 dark:border-slate-700">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <span class="material-icons-round text-3xl text-cyan-500">${systemData.icon || 'science'}</span>
                        <div>
                            <h2 class="text-2xl font-bold text-slate-800 dark:text-white">${systemName}</h2>
                            <p class="text-sm text-slate-500 dark:text-slate-400">${systemData.status}</p>
                        </div>
                    </div>
                    <button onclick="closeSystemDetail()" class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <span class="material-icons-round text-slate-400">close</span>
                    </button>
                </div>
            </div>
            
            <div class="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
                <div class="space-y-6">
                    <!-- Health Score Display -->
                    <div class="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-cyan-200 dark:border-cyan-800/30">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <p class="text-xs text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1">System Health Score</p>
                                <div class="flex items-baseline gap-2">
                                    <span class="text-4xl font-bold ${systemData.health_score >= 90 ? 'text-emerald-600' :
            systemData.health_score >= 70 ? 'text-amber-600' :
                systemData.health_score >= 50 ? 'text-orange-600' :
                    'text-rose-600'
        }">${systemData.health_score || 0}</span>
                                    <span class="text-lg text-slate-500">/100</span>
                                </div>
                                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${systemData.status}</p>
                            </div>
                            <div class="relative w-24 h-24">
                                <svg class="w-full h-full -rotate-90" viewBox="0 0 100 100">
                                    <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" 
                                        class="text-slate-200 dark:text-slate-700" stroke-width="8"></circle>
                                    <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" 
                                        class="${systemData.health_score >= 90 ? 'text-emerald-600' :
            systemData.health_score >= 70 ? 'text-amber-600' :
                systemData.health_score >= 50 ? 'text-orange-600' :
                    'text-rose-600'
        }" stroke-width="8" 
                                        stroke-dasharray="${2 * Math.PI * 42}" 
                                        stroke-dashoffset="${2 * Math.PI * 42 * (1 - systemData.health_score / 100)}"
                                        stroke-linecap="round"></circle>
                                </svg>
                            </div>
                        </div>
                        <div class="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-cyan-200 dark:border-cyan-800/30">
                            <div>
                                <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Parameters</p>
                                <p class="text-xl font-bold text-slate-800 dark:text-white">${systemData.total_count}</p>
                            </div>
                            <div>
                                <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">Attention Needed</p>
                                <p class="text-xl font-bold text-rose-500">${systemData.abnormal_count}</p>
                            </div>
                        </div>
                    </div>

                    ${abnormalParams.length > 0 ? `
                    <!-- Abnormal Parameters -->
                    <div>
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                            <span class="w-1.5 h-6 bg-rose-500 rounded-full"></span>
                            Parameters Requiring Attention
                        </h3>
                        <div class="space-y-3">
                            ${abnormalParams.map(param => `
                            <div class="bg-rose-50 dark:bg-rose-900/10 border border-rose-200 dark:border-rose-800/30 rounded-xl p-4">
                                <div class="flex justify-between items-start mb-2">
                                    <h4 class="font-semibold text-slate-800 dark:text-white">${param.name}</h4>
                                    <span class="severity-badge severity-badge-${param.severity || 'moderate'}">
                                        ${param.status}
                                    </span>
                                </div>
                                <div class="grid grid-cols-2 gap-3 text-sm">
                                    <div>
                                        <span class="text-slate-500 dark:text-slate-400">Value:</span>
                                        <span class="font-mono font-bold text-slate-800 dark:text-white ml-1">${param.value}</span>
                                    </div>
                                    ${param.range ? `
                                    <div>
                                        <span class="text-slate-500 dark:text-slate-400">Range:</span>
                                        <span class="font-mono text-slate-600 dark:text-slate-300 ml-1">${param.range}</span>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}

                    ${(systemData.parameters || []).filter(p => p.status === 'Normal').length > 0 ? `
                    <!-- Normal Parameters -->\r
                    <details class="group">
                        <summary class="cursor-pointer text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-cyan-500 transition-colors flex items-center gap-1">
                            <span class="material-icons-round text-sm">expand_more</span>
                            View ${(systemData.parameters || []).filter(p => p.status === 'Normal').length} Parameters Within Range
                        </summary>
                        <div class="mt-3 grid grid-cols-2 gap-2">
                            ${(systemData.parameters || []).filter(p => p.status === 'Normal').map(p => `
                            <div class="text-sm text-slate-600 dark:text-slate-400 bg-emerald-50 dark:bg-emerald-900/10 px-3 py-2 rounded-lg border border-emerald-200 dark:border-emerald-800/30 flex items-center gap-2">
                                <span class="material-icons-round text-xs text-emerald-500">check_circle</span>
                                <span><span class="font-semibold">${p.name}</span>: ${p.value} ${p.unit}</span>
                            </div>
                            `).join('')}
                        </div>
                    </details>
                    ` : ''}
                    
                    ${systemData.related_systems && systemData.related_systems.length > 0 ? `
                    <!-- Related Systems -->
                    <div>
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                            <span class="material-icons-round text-purple-500">hub</span>
                            Related Systems
                        </h3>
                        <div class="space-y-2">
                            ${systemData.related_systems.map(rel => `
                                <div class="bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-800/30 rounded-lg p-3">
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="material-icons-round text-sm text-purple-600 dark:text-purple-400">arrow_forward</span>
                                        <span class="font-semibold text-slate-800 dark:text-white">${rel.target}</span>
                                        <span class="text-xs px-2 py-0.5 rounded-full bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-300">${rel.type}</span>
                                    </div>
                                    <p class="text-xs text-slate-600 dark:text-slate-400 ml-6">${rel.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${systemData.score_breakdown && systemData.score_breakdown.deductions && systemData.score_breakdown.deductions.length > 0 ? `
                    <!-- Score Breakdown -->
                    <div>
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                            <span class="material-icons-round text-blue-500">analytics</span>
                            Score Breakdown
                        </h3>
                        <div class="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-4 space-y-2">
                            <div class="flex justify-between text-sm">
                                <span class="text-slate-600 dark:text-slate-400">Base Score</span>
                                <span class="font-bold text-slate-800 dark:text-white">${systemData.score_breakdown.base}</span>
                            </div>
                            ${systemData.score_breakdown.deductions.map(d => `
                                <div class="flex justify-between text-sm">
                                    <span class="text-slate-600 dark:text-slate-400">${d.parameter}</span>
                                    <span class="font-bold text-rose-600">-${d.deduction}</span>
                                </div>
                            `).join('')}
                            <div class="flex justify-between text-sm pt-2 border-t border-slate-200 dark:border-slate-700">
                                <span class="font-bold text-slate-800 dark:text-white">Final Score</span>
                                <span class="font-bold text-cyan-600">${systemData.score_breakdown.score}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="p-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700">
                <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    <strong>Note:</strong> This grouping is for organizational purposes only. Consult your healthcare provider for medical interpretation.
                </p>
            </div>
        </div >
        `;

    // Add click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSystemDetail();
        }
    });

    document.body.appendChild(modal);

    // Load trend data for abnormal parameters
    if (abnormalParams.length > 0) {
        abnormalParams.forEach(param => fetchAndRenderTrend(param.name));
    }
}

// ==========================================
// TREND VISUALIZATION (Phase 6)
// ==========================================

async function fetchParameterHistory(parameterName) {
    /**
     * Fetch historical data for a parameter from the backend
     */
    try {
        const response = await fetch(`${API_BASE_URL} /api/tracking / parameter / ${encodeURIComponent(parameterName)}?limit = 10`, {
            credentials: 'include'
        });
        if (!response.ok) {
            console.warn(`No historical data for ${parameterName}`);
            return null;
        }
        const data = await response.json();
        return data.history && data.history.length > 0 ? data.history : null;
    } catch (error) {
        console.error(`Error fetching history for ${parameterName}: `, error);
        return null;
    }
}

async function fetchAndRenderTrend(parameterName) {
    /**
     * Fetch and render trend visualization for a parameter
     */
    const history = await fetchParameterHistory(parameterName);
    const chartId = `trend - chart - ${parameterName.replace(/\s+/g, '-')} `;
    const badgeId = `trend - badge - ${parameterName.replace(/\s+/g, '-')} `;
    const messageId = `trend - message - ${parameterName.replace(/\s+/g, '-')} `;

    const canvas = document.getElementById(chartId);
    const badgeEl = document.getElementById(badgeId);
    const messageEl = document.getElementById(messageId);

    if (!canvas || !badgeEl || !messageEl) return;

    if (!history || history.length < 2) {
        // Show "no data" message
        badgeEl.innerHTML = '<span class="text-slate-400 text-xs">Insufficient Data</span>';
        messageEl.innerHTML = 'Upload more reports to see trends';
        canvas.style.display = 'none';
        return;
    }

    // Analyze trend direction
    const values = history.map(h => h.value).reverse(); // Oldest to newest
    const dates = history.map(h => new Date(h.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })).reverse();

    // Calculate trend
    const firstValue = values[0];
    const lastValue = values[values.length - 1];
    const change = lastValue - firstValue;
    const changePercent = ((change / firstValue) * 100).toFixed(1);

    // Determine trend direction
    let trendDirection = 'stable';
    let trendColor = '#94a3b8'; // Slate
    let trendIcon = '→';

    if (Math.abs(changePercent) > 5) {
        if (change > 0) {
            trendDirection = 'increasing';
            trendColor = '#ef4444'; // Red (could be good or bad depending on parameter)
            trendIcon = '↗';
        } else {
            trendDirection = 'decreasing';
            trendColor = '#3b82f6'; // Blue
            trendIcon = '↘';
        }
    }

    // Update badge
    badgeEl.innerHTML = `
        < span class="px-2 py-1 rounded-full text-xs font-bold" style = "background-color: ${trendColor}20; color: ${trendColor}" >
            ${trendIcon} ${trendDirection.toUpperCase()} ${Math.abs(changePercent)}%
        </span >
        `;

    // Update message
    messageEl.innerHTML = `Based on ${values.length} previous measurements`;

    // Render sparkline chart
    renderTrendChart(chartId, dates, values, trendColor);
}

function renderTrendChart(chartId, labels, data, color) {
    /**
     * Render a sparkline chart using Chart.js
     */
    const canvas = document.getElementById(chartId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destroy existing chart if any
    const existingChart = Chart.getChart(chartId);
    if (existingChart) {
        existingChart.destroy();
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Value',
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 1,
                pointHoverRadius: 5,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 8,
                    displayColors: false,
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (item) => `Value: ${item.raw} `
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: { display: false },
                    ticks: {
                        font: { size: 9 },
                        color: '#94a3b8'
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 9 },
                        color: '#94a3b8',
                        maxTicksLimit: 4
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function closeSystemDetail() {
    const modal = document.getElementById('systemDetailModal');
    if (modal) {
        modal.classList.add('animate-fadeOut');
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 200);
    }
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

// showNotification is provided by utils.js

// ==========================================
// PAGE LOAD
// ==========================================

document.addEventListener('DOMContentLoaded', initializePage);

console.log('MedLab Analyzer Insights UI (Tailwind) initialized successfully');
