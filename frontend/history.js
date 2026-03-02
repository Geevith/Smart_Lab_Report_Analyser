// ============================================================================
// History Page — Full Interactive Controller
// ============================================================================

// API_BASE_URL is now loaded from config.js
let currentFilter = 'all';
let currentSort = 'newest';
let searchTimeout = null;
let pendingDeleteId = null;
let pendingNotesId = null;
let pendingNotesFilename = '';

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initAuth();
    loadStats();
    loadHistory();
    setupEventListeners();
});

// ---- Dark Mode ----
function initDarkMode() {
    const saved = localStorage.getItem('darkMode');
    if (saved === 'true') {
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
    }
    const toggle = document.getElementById('darkModeToggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            document.documentElement.classList.toggle('light');
            localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
        });
    }
}

// ---- Event Listeners ----
function setupEventListeners() {
    // Search with debounce
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => loadHistory(), 350);
        });
    }

    // Sort
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            loadHistory();
        });
    }

    // Filter pills
    document.querySelectorAll('.filter-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentFilter = pill.dataset.filter;
            loadHistory();
        });
    });

    // Delete modal
    document.getElementById('cancelDeleteBtn')?.addEventListener('click', closeDeleteModal);
    document.getElementById('confirmDeleteBtn')?.addEventListener('click', confirmDelete);
    document.getElementById('deleteModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'deleteModal') closeDeleteModal();
    });

    // Notes modal
    document.getElementById('closeNotesBtn')?.addEventListener('click', closeNotesModal);
    document.getElementById('cancelNotesBtn')?.addEventListener('click', closeNotesModal);
    document.getElementById('saveNotesBtn')?.addEventListener('click', saveNotes);
    document.getElementById('notesModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'notesModal') closeNotesModal();
    });
}

// ---- Load Stats ----
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE_URL}/history/stats`, { credentials: 'include' });
        if (!res.ok) return;
        const stats = await res.json();
        document.getElementById('statTotal').textContent = stats.total || 0;
        document.getElementById('statFavorites').textContent = stats.favorites || 0;
        document.getElementById('statFlagged').textContent = stats.flagged || 0;
    } catch (e) {
        console.error('Stats load error:', e);
    }
}

// ---- Load History ----
async function loadHistory() {
    const listContainer = document.getElementById('historyList');
    const loadingState = document.getElementById('loading');
    const emptyState = document.getElementById('emptyState');
    if (!listContainer) return;

    loadingState?.classList.remove('hidden');
    listContainer.innerHTML = '';
    emptyState?.classList.add('hidden');

    try {
        const searchVal = document.getElementById('searchInput')?.value?.trim() || '';
        const params = new URLSearchParams();
        if (searchVal) params.set('search', searchVal);
        if (currentFilter === 'favorites') params.set('favorite', 'true');
        if (currentFilter === 'attention') params.set('status', 'attention');
        if (currentFilter === 'normal') params.set('status', 'normal');
        params.set('sort', currentSort);

        // Use API_BASE_URL from config.js
        const res = await fetch(`${API_BASE_URL}/history?${params.toString()}`, { credentials: 'include' });

        if (!res.ok) {
            if (res.status === 401) { window.location.href = 'login.html'; return; }
            throw new Error('Failed to fetch history');
        }

        const history = await res.json();
        loadingState?.classList.add('hidden');

        // Render Milestones based on history
        renderMilestones(history);

        if (history.length === 0) {
            emptyState?.classList.remove('hidden');
            return;
        }

        listContainer.innerHTML = history.map((report, idx) => buildReportCard(report, idx)).join('');

    } catch (error) {
        console.error('Error fetching history:', error);
        loadingState?.classList.add('hidden');
        listContainer.innerHTML = `
            <div class="text-center py-12 bg-white dark:bg-slate-900/60 rounded-2xl border border-gray-100 dark:border-slate-700/30">
                <span class="material-icons-round text-4xl text-rose-400 mb-3 block">error_outline</span>
                <p class="text-gray-600 dark:text-gray-400 mb-3">Failed to load history.</p>
                <button onclick="loadHistory()" class="text-primary font-semibold text-sm hover:underline">Try Again</button>
            </div>
        `;
    }
}

// ---- Build Report Card ----
function buildReportCard(report, index) {
    const date = new Date(report.timestamp).toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric'
    });
    const time = new Date(report.timestamp).toLocaleTimeString(undefined, {
        hour: '2-digit', minute: '2-digit'
    });

    // Parse status
    const statusText = report.status || 'Processed';
    const isAttention = statusText.includes('issue') && statusText !== '0 issues';
    const statusColor = isAttention
        ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
        : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
    const statusIcon = isAttention ? 'warning' : 'check_circle';
    const displayStatus = isAttention ? statusText : 'Normal';

    const isFav = report.is_favorite;
    const hasNotes = report.notes && report.notes.trim().length > 0;
    const escapedFilename = (report.filename || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const escapedNotes = (report.notes || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');

    return `
        <div class="report-card juicy-hover fade-in bg-white dark:bg-slate-900/60 border border-gray-100 dark:border-slate-700/30 rounded-2xl p-5 shadow-sm transition-all"
             style="animation-delay: ${index * 50}ms" id="report-${report.id}">
            <div class="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                <!-- Left: Info -->
                <div class="flex items-start gap-4 flex-grow cursor-pointer min-w-0" onclick="openReport(${report.id}, '${escapedFilename}')">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 flex items-center justify-center text-primary shrink-0">
                        <span class="material-icons-round text-2xl">description</span>
                    </div>
                    <div class="min-w-0">
                        <h3 class="font-semibold text-gray-900 dark:text-white truncate hover:text-primary transition-colors">
                            ${report.filename}
                        </h3>
                        <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                            <span class="flex items-center gap-1">
                                <span class="material-icons-round text-[14px]">calendar_today</span>
                                ${date} · ${time}
                            </span>
                            ${report.lab_name ? `<span class="flex items-center gap-1"><span class="material-icons-round text-[14px]">local_hospital</span>${report.lab_name}</span>` : ''}
                        </div>
                        ${hasNotes ? `<p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5 truncate max-w-sm italic">📝 ${report.notes}</p>` : ''}
                    </div>
                </div>

                <!-- Right: Actions -->
                <div class="flex items-center gap-2 shrink-0">
                    <span class="px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${statusColor}">
                        <span class="material-icons-round text-sm">${statusIcon}</span>
                        ${displayStatus}
                    </span>

                    <button class="favorite-btn ${isFav ? 'active' : ''} w-9 h-9 rounded-lg hover:bg-amber-50 dark:hover:bg-amber-900/20 flex items-center justify-center transition-all"
                            onclick="event.stopPropagation(); toggleFavorite(${report.id}, this)"
                            title="${isFav ? 'Remove from favorites' : 'Add to favorites'}">
                        <span class="material-icons-round text-lg ${isFav ? 'text-amber-500' : 'text-gray-300 dark:text-gray-600'}">${isFav ? 'star' : 'star_border'}</span>
                    </button>

                    <button class="w-9 h-9 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center justify-center transition-all text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400"
                            onclick="event.stopPropagation(); openNotesModal(${report.id}, '${escapedFilename}', '${escapedNotes}')"
                            title="Add notes">
                        <span class="material-icons-round text-lg">${hasNotes ? 'edit_note' : 'note_add'}</span>
                    </button>

                    <button class="w-9 h-9 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20 flex items-center justify-center transition-all text-gray-400 dark:text-gray-500 hover:text-rose-500"
                            onclick="event.stopPropagation(); openDeleteModal(${report.id})"
                            title="Delete report">
                        <span class="material-icons-round text-lg">delete_outline</span>
                    </button>

                    <div class="w-9 h-9 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 flex items-center justify-center cursor-pointer text-gray-400 hover:text-primary transition-all"
                         onclick="openReport(${report.id}, '${escapedFilename}')">
                        <span class="material-icons-round text-lg">chevron_right</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ---- Toggle Favorite ----
async function toggleFavorite(reportId, btn) {
    try {
        const res = await fetch(`${API_BASE_URL}/report/${reportId}/favorite`, {
            method: 'PUT',
            credentials: 'include'
        });
        if (!res.ok) throw new Error('Failed to toggle favorite');
        const data = await res.json();

        // Update button UI
        const icon = btn.querySelector('.material-icons-round');
        if (data.is_favorite) {
            btn.classList.add('active');
            icon.textContent = 'star';
            icon.className = 'material-icons-round text-lg text-amber-500';
            showNotification('Added to favorites', 'success');
        } else {
            btn.classList.remove('active');
            icon.textContent = 'star_border';
            icon.className = 'material-icons-round text-lg text-gray-300 dark:text-gray-600';
            showNotification('Removed from favorites', 'info');
        }

        // Refresh stats
        loadStats();

        // If we're filtering by favorites, reload the list
        if (currentFilter === 'favorites') loadHistory();

    } catch (e) {
        console.error('Favorite error:', e);
        showNotification('Failed to update favorite', 'error');
    }
}

// ---- Delete ----
function openDeleteModal(reportId) {
    pendingDeleteId = reportId;
    document.getElementById('deleteModal')?.classList.remove('hidden');
}

function closeDeleteModal() {
    pendingDeleteId = null;
    document.getElementById('deleteModal')?.classList.add('hidden');
}

async function confirmDelete() {
    if (!pendingDeleteId) return;
    const reportId = pendingDeleteId;
    const btn = document.getElementById('confirmDeleteBtn');

    try {
        btn.innerHTML = '<div class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>';
        btn.disabled = true;

        const res = await fetch(`${API_BASE_URL}/report/${reportId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!res.ok) throw new Error('Failed to delete report');

        closeDeleteModal();

        // Remove card with animation
        const card = document.getElementById(`report-${reportId}`);
        if (card) {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '0';
            card.style.transform = 'translateX(20px)';
            setTimeout(() => card.remove(), 300);
        }

        showNotification('Report deleted successfully', 'success');
        loadStats();

        // Check if empty
        setTimeout(() => {
            const historyList = document.getElementById('historyList');
            if (historyList && historyList.children.length === 0) {
                document.getElementById('emptyState')?.classList.remove('hidden');
            }
        }, 400);

    } catch (e) {
        console.error('Delete error:', e);
        showNotification('Failed to delete report', 'error');
    } finally {
        btn.innerHTML = '<span class="material-icons-round text-lg">delete</span> Delete';
        btn.disabled = false;
    }
}

// ---- Notes ----
function openNotesModal(reportId, filename, notes) {
    pendingNotesId = reportId;
    pendingNotesFilename = filename;
    document.getElementById('notesReportName').textContent = filename;
    document.getElementById('notesTextarea').value = notes || '';
    document.getElementById('notesModal')?.classList.remove('hidden');
    setTimeout(() => document.getElementById('notesTextarea')?.focus(), 100);
}

function closeNotesModal() {
    pendingNotesId = null;
    document.getElementById('notesModal')?.classList.add('hidden');
}

async function saveNotes() {
    if (!pendingNotesId) return;
    const reportId = pendingNotesId;
    const notes = document.getElementById('notesTextarea')?.value || '';
    const btn = document.getElementById('saveNotesBtn');

    try {
        btn.innerHTML = '<div class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>';
        btn.disabled = true;

        const res = await fetch(`${API_BASE_URL}/report/${reportId}/notes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes }),
            credentials: 'include'
        });

        if (!res.ok) throw new Error('Failed to save notes');

        closeNotesModal();
        showNotification('Notes saved', 'success');
        loadHistory(); // Reload to reflect notes in cards

    } catch (e) {
        console.error('Notes error:', e);
        showNotification('Failed to save notes', 'error');
    } finally {
        btn.innerHTML = '<span class="material-icons-round text-lg">save</span> Save Notes';
        btn.disabled = false;
    }
}

// ---- Open Report (navigate to insights) ----
async function openReport(reportId, filename) {
    showNotification('Loading report...', 'info');

    try {
        const res = await fetch(`${API_BASE_URL}/report/${reportId}`, { credentials: 'include' });
        if (!res.ok) throw new Error('Failed to fetch report');
        const data = await res.json();

        // Save to sessionStorage for insights page
        sessionStorage.setItem('analysisResults', JSON.stringify(data.parameters));

        if (data.summary) {
            sessionStorage.setItem('analysisSummary', JSON.stringify(data.summary));
        } else {
            sessionStorage.setItem('analysisSummary', JSON.stringify({
                total_extracted: data.parameters.length,
                optimal_count: data.parameters.filter(p => !['High', 'Low', 'Critical'].includes(p.status)).length,
                attention_count: data.parameters.filter(p => ['High', 'Low', 'Critical'].includes(p.status)).length
            }));
        }

        if (data.insights) sessionStorage.setItem('analysisInsights', JSON.stringify(data.insights));
        if (data.systems_impact) sessionStorage.setItem('systemsImpact', JSON.stringify(data.systems_impact));

        sessionStorage.setItem('uploadedFile', JSON.stringify({
            name: filename, type: 'application/pdf', size: 0
        }));

        window.location.href = 'insights_ui.html';

    } catch (e) {
        console.error('Open report error:', e);
        showNotification('Failed to open report', 'error');
    }
}

// ---- Toast Notification ----
// showToast is replaced by showNotification from utils.js

function renderMilestones(history) {
    const container = document.getElementById('milestonesContainer');
    if (!container) return;

    // Calculate full history count without filters
    const statTotalEl = document.getElementById('statTotal');
    const count = statTotalEl && statTotalEl.textContent !== '-' ? parseInt(statTotalEl.textContent, 10) : history.length;

    const milestones = [
        { id: 'first', title: 'First Upload', desc: 'Started your journey', req: 1, icon: 'emoji_events', color: 'emerald' },
        { id: 'consistent', title: 'Consistent Tracker', desc: '3+ reports analyzed', req: 3, icon: 'military_tech', color: 'blue' },
        { id: 'advocate', title: 'Health Advocate', desc: '5+ reports analyzed', req: 5, icon: 'workspace_premium', color: 'purple' },
        { id: 'proactive', title: 'Proactive', desc: '10+ reports analyzed', req: 10, icon: 'diamond', color: 'amber' }
    ];

    const styles = {
        emerald: { active: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800/30 text-emerald-500' },
        blue: { active: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/30 text-blue-500' },
        purple: { active: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800/30 text-purple-500' },
        amber: { active: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/30 text-amber-500' }
    };

    let html = '';
    milestones.forEach(m => {
        const achieved = count >= m.req;
        const opacity = achieved ? 'opacity-100' : 'opacity-40 grayscale';
        const s = styles[m.color];
        const achievedClass = achieved ? s.active : 'bg-gray-50 dark:bg-slate-800/50 border-gray-200 dark:border-slate-700/50 text-gray-400';

        html += `
            <div class="flex-shrink-0 flex items-center gap-3 p-4 rounded-xl border transition-all ${achievedClass} ${opacity} min-w-[220px]">
                <div class="w-10 h-10 rounded-full flex items-center justify-center bg-white/50 dark:bg-black/20 shrink-0 shadow-sm">
                    <span class="material-icons-round text-2xl">${m.icon}</span>
                </div>
                <div>
                    <h4 class="font-bold text-sm text-gray-900 dark:text-white">${m.title}</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400 font-medium">${m.desc}</p>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}
