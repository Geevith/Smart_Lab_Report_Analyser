// ==========================================
// FILE UPLOAD FUNCTIONALITY - ENHANCED
// ==========================================

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileMeta = document.getElementById('fileMeta');
const removeBtn = document.getElementById('removeBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const darkModeToggle = document.getElementById('darkModeToggle');

// Preview Modal Elements
const previewModal = document.getElementById('previewModal');
const closePreviewBtn = document.getElementById('closePreviewBtn');
const reUploadBtn = document.getElementById('reUploadBtn');
const continueAnalysisBtn = document.getElementById('continueAnalysisBtn');
const extractedText = document.getElementById('extractedText');
const textLength = document.getElementById('textLength');
const overallQuality = document.getElementById('overallQuality');
const resolutionScore = document.getElementById('resolutionScore');
const contrastScore = document.getElementById('contrastScore');
const pageCount = document.getElementById('pageCount');
const ocrConfidence = document.getElementById('ocrConfidence');
const suggestions = document.getElementById('suggestions');
const suggestionsList = document.getElementById('suggestionsList');
const rotationControls = document.getElementById('rotationControls');

let selectedFile = null;
let currentRotation = 0;
let previewData = null;

// ==========================================
// DARK MODE
// ==========================================

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
}

darkModeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
});

// ==========================================
// EVENT LISTENERS
// ==========================================

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

uploadArea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
    }
});

browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files[0]);
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('border-primary', 'dark:border-primary');
});

uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('border-primary', 'dark:border-primary');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('border-primary', 'dark:border-primary');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    removeFile();
});

analyzeBtn.addEventListener('click', () => {
    if (selectedFile) {
        handlePreview();
    }
});

// Preview Modal Events
closePreviewBtn.addEventListener('click', closePreview);
reUploadBtn.addEventListener('click', () => {
    closePreview();
    removeFile();
});
continueAnalysisBtn.addEventListener('click', handleAnalyze);

// Rotation buttons
document.querySelectorAll('.rotation-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        const rotation = parseInt(e.target.dataset.rotation);
        await applyRotation(rotation);
    });
});

fileInput.addEventListener('click', (e) => {
    e.stopPropagation();
});

// ==========================================
// ENHANCED FILE VALIDATION
// ==========================================

function handleFileSelect(file) {
    if (!file) return;

    // Validate file type (MIME type AND extension)
    const allowedMimeTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];

    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

    if (!allowedMimeTypes.includes(file.type) || !allowedExtensions.includes(fileExtension)) {
        showNotification('Please upload a PDF, JPG, or PNG file only', 'error');
        return;
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit. Please use a smaller file.', 'error');
        return;
    }

    // For images, validate dimensions (minimum 300x300px)
    if (file.type.startsWith('image/')) {
        validateImageDimensions(file, (isValid, width, height) => {
            if (!isValid) {
                showNotification(`Image resolution too low (${width}x${height}). Minimum 300x300px required.`, 'error');
                return;
            }
            proceedWithFile(file);
        });
    } else {
        proceedWithFile(file);
    }
}

function validateImageDimensions(file, callback) {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = function () {
        URL.revokeObjectURL(url);
        const isValid = this.width >= 300 && this.height >= 300;
        callback(isValid, this.width, this.height);
    };

    img.onerror = function () {
        URL.revokeObjectURL(url);
        callback(false, 0, 0);
    };

    img.src = url;
}

function proceedWithFile(file) {
    selectedFile = file;
    currentRotation = 0;
    displayFilePreview(file);
}

function displayFilePreview(file) {
    fileName.textContent = file.name;

    const fileSize = formatFileSize(file.size);
    const fileType = getFileType(file.type);
    fileMeta.textContent = `${fileSize} • ${fileType}`;

    uploadArea.style.display = 'none';
    filePreview.classList.remove('hidden');

    analyzeBtn.disabled = false;
}

function removeFile() {
    selectedFile = null;
    currentRotation = 0;
    previewData = null;
    fileInput.value = '';

    filePreview.classList.add('hidden');
    uploadArea.style.display = 'block';

    analyzeBtn.disabled = true;
}

// ==========================================
// PREVIEW & QUALITY ASSESSMENT
// ==========================================

async function handlePreview() {
    // Show modal with loading state
    showPreviewModal();

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (currentRotation > 0) {
            formData.append('rotation', currentRotation);
        }

        const response = await fetch(`${API_BASE_URL}/preview`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`Preview failed: ${response.statusText}`);
        }

        previewData = await response.json();
        displayPreviewData(previewData);

    } catch (error) {
        console.error('Preview error:', error);

        // Fallback: show basic preview without backend
        const fallbackData = {
            text: "Preview not available. Click 'Continue to Analysis' to proceed.",
            quality: {
                overall_score: 0.7,
                resolution_score: 0.75,
                contrast_score: 0.7,
                ocr_confidence: 0.7
            },
            pages: 1,
            suggestions: ["Backend preview endpoint not available. Analysis will proceed with full extraction."]
        };

        displayPreviewData(fallbackData);
    }
}

function showPreviewModal() {
    previewModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    // Reset to loading state with medical heartbeat SVG
    extractedText.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12 gap-4">
            <svg class="w-16 h-16 text-primary" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M 0 50 h 30 l 10 -30 l 20 60 l 10 -30 h 30" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" values="300;0;-300" dur="1.5s" repeatCount="indefinite" />
                </path>
            </svg>
            <p class="text-sm font-medium text-gray-500 dark:text-gray-400 animate-pulse">Extracting Clinical Data...</p>
        </div>
    `;
}

function displayPreviewData(data) {
    // Display extracted text
    const text = data.text || "No text extracted";
    extractedText.innerHTML = `<pre class="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-mono">${escapeHtml(text)}</pre>`;
    textLength.textContent = `${text.length} characters`;

    // Display quality scores
    const quality = data.quality || {};
    const overallScore = quality.overall_score || 0.7;

    // Overall quality badge
    let qualityLabel = 'Good';
    let qualityColor = 'bg-green-500';

    if (overallScore >= 0.8) {
        qualityLabel = 'Excellent';
        qualityColor = 'bg-green-500';
    } else if (overallScore >= 0.6) {
        qualityLabel = 'Good';
        qualityColor = 'bg-blue-500';
    } else if (overallScore >= 0.4) {
        qualityLabel = 'Fair';
        qualityColor = 'bg-yellow-500';
    } else {
        qualityLabel = 'Poor';
        qualityColor = 'bg-red-500';
    }

    overallQuality.textContent = qualityLabel;
    overallQuality.className = `px-4 py-2 ${qualityColor} text-white text-sm font-bold rounded-lg`;

    // Individual scores
    resolutionScore.textContent = formatScore(quality.resolution_score || 0.75);
    contrastScore.textContent = formatScore(quality.contrast_score || 0.7);
    pageCount.textContent = data.pages || 1;
    ocrConfidence.textContent = formatScore(quality.ocr_confidence || 0.7);

    // Suggestions
    if (data.suggestions && data.suggestions.length > 0) {
        suggestions.classList.remove('hidden');
        suggestionsList.innerHTML = data.suggestions.map(s =>
            `<div class="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400">
                <span class="material-icons-round text-sm text-yellow-500">lightbulb</span>
                <span>${escapeHtml(s)}</span>
            </div>`
        ).join('');
    } else {
        suggestions.classList.add('hidden');
    }

    // Show rotation controls for images
    if (selectedFile.type.startsWith('image/')) {
        rotationControls.classList.remove('hidden');
    } else {
        rotationControls.classList.add('hidden');
    }
}

function closePreview() {
    previewModal.classList.add('hidden');
    document.body.style.overflow = '';
}

async function applyRotation(degrees) {
    currentRotation = (currentRotation + degrees) % 360;
    showNotification(`Rotating image ${degrees}°...`, 'info');

    // Re-fetch preview with rotation
    await handlePreview();
}

// ==========================================
// FINAL ANALYSIS & PROGRESS BAR
// ==========================================

async function handleAnalyze() {
    closePreview();

    // Show Progress Overlay instead of button spinner
    const progressOverlay = document.getElementById('progressOverlay');
    const progressBar = document.getElementById('progressBar');
    const progressTitle = document.getElementById('progressTitle');
    const progressStatus = document.getElementById('progressStatus');

    // Steps
    const step1 = document.getElementById('step1Icon');  // Text Extraction
    const step2 = document.getElementById('step2');      // Parsing
    const step2Icon = document.getElementById('step2Icon');
    const step3 = document.getElementById('step3');      // Analysis
    const step3Icon = document.getElementById('step3Icon');

    progressOverlay.classList.remove('hidden');

    // reset
    progressBar.style.width = '0%';
    step2.classList.add('opacity-50');
    step3.classList.add('opacity-50');

    // Start Simulation
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            // Variable speed
            const increment = progress < 30 ? 2 : (progress < 60 ? 1 : 0.5);
            progress += increment;
            progressBar.style.width = `${progress}%`;

            // Update stages
            if (progress > 30 && progress < 60) {
                // Stage 2: Parsing
                step1.innerHTML = '<span class="material-icons-round text-xs">check</span>';
                step2.classList.remove('opacity-50');
                step2Icon.className = "w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center text-[10px]";
                step2Icon.innerHTML = `<span class="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>`;
                progressStatus.textContent = "Parsing clinical data structures...";
            } else if (progress > 60) {
                // Stage 3: Analysis
                step2Icon.innerHTML = '<span class="material-icons-round text-xs">check</span>';
                step3.classList.remove('opacity-50');
                step3Icon.className = "w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center text-[10px]";
                step3Icon.innerHTML = `<span class="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>`;
                progressStatus.textContent = "Running AI analysis models...";
            }
        }
    }, 100);

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (currentRotation > 0) {
            formData.append('rotation', currentRotation);
        }

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Analysis result:', data);

        // Store real API data
        sessionStorage.setItem('uploadedFile', JSON.stringify({
            name: selectedFile.name,
            size: selectedFile.size,
            type: selectedFile.type,
            timestamp: Date.now()
        }));

        sessionStorage.setItem('analysisResults', JSON.stringify(data.parameters));
        sessionStorage.setItem('analysisSummary', JSON.stringify(data.summary));
        sessionStorage.setItem('analysisInsights', JSON.stringify(data.insights));
        sessionStorage.setItem('systemsImpact', JSON.stringify(data.systems_impact));

        if (data.report_id) {
            sessionStorage.setItem('currentReportId', data.report_id);
        }

        sessionStorage.setItem('currentStep', 'verify');

        // Complete Progress
        clearInterval(progressInterval);
        progressBar.style.width = '100%';

        step3Icon.innerHTML = '<span class="material-icons-round text-xs">check</span>';
        progressTitle.textContent = "Analysis Complete!";
        progressStatus.textContent = "Redirecting to validation...";

        // Success animation pause
        setTimeout(() => {
            window.location.href = 'verify_ui.html';
        }, 800);

    } catch (error) {
        clearInterval(progressInterval);
        console.error('Error:', error);
        progressOverlay.classList.add('hidden'); // Hide overlay on error

        if (error.message.includes('Not authenticated') || error.message.includes('401')) {
            if (confirm("You need to be logged in to analyze reports. Go to login page?")) {
                window.location.href = 'login.html?redirect=upload_ui.html';
            }
        } else {
            showNotification(error.message || 'Analysis failed. Please try again.', 'error');
        }
    }
}

// ==========================================
// UTILITY FUNCTIONS
// (showNotification, formatFileSize, escapeHtml are in utils.js)
// ==========================================

function getFileType(mimeType) {
    const types = {
        'application/pdf': 'PDF',
        'image/jpeg': 'JPG',
        'image/jpg': 'JPG',
        'image/png': 'PNG'
    };
    return types[mimeType] || 'Unknown';
}

function formatScore(score) {
    return `${Math.round(score * 100)}%`;
}

// ==========================================
// ONBOARDING TOUR
// ==========================================

const tourSteps = [
    {
        element: '#uploadArea',
        title: 'Upload Your Report',
        text: 'Drag and drop your PDF or image file here. We support common formats like PDF, JPG, and PNG.',
        position: 'center'
    },
    {
        element: 'a[download]',
        title: 'Try a Sample',
        text: 'Don\'t have a report handy? Download our sample report to test the analysis features.',
        position: 'top'
    },
    {
        element: '#progressSteps',
        title: '3-Step Process',
        text: 'We upload, verify, and then analyze your data to give you personalized health insights.',
        position: 'right'
    }
];

let currentTourStep = 0;

function startTour() {
    const overlay = document.getElementById('tourOverlay');
    overlay.classList.remove('hidden');
    currentTourStep = 0;
    showTourStep(currentTourStep);
}

function showTourStep(index) {
    if (index >= tourSteps.length) {
        endTour();
        return;
    }

    const step = tourSteps[index];
    const target = document.querySelector(step.element);
    if (!target) {
        // Skip if element not found
        showTourStep(index + 1);
        return;
    }

    const rect = target.getBoundingClientRect();
    const highlight = document.getElementById('tourHighlight');
    const card = document.getElementById('tourCard');
    const title = document.getElementById('tourTitle');
    const text = document.getElementById('tourText');
    const indicator = document.getElementById('tourStepIndicator');

    // Position Highlight
    highlight.style.top = `${rect.top - 4}px`;
    highlight.style.left = `${rect.left - 4}px`;
    highlight.style.width = `${rect.width + 8}px`;
    highlight.style.height = `${rect.height + 8}px`;

    // Update Content
    title.textContent = step.title;
    text.textContent = step.text;
    indicator.textContent = `${index + 1}/${tourSteps.length}`;

    // Position Card (Basic logic - improve for edge cases)
    const cardRect = card.getBoundingClientRect();
    let top = rect.bottom + 20;
    let left = rect.left;

    // Adjust if goes off screen
    if (top + cardRect.height > window.innerHeight) {
        top = rect.top - cardRect.height - 20; // Show above
    }
    if (left + cardRect.width > window.innerWidth) {
        left = window.innerWidth - cardRect.width - 20;
    }

    card.style.top = `${top}px`;
    card.style.left = `${left}px`;
}

function endTour() {
    const overlay = document.getElementById('tourOverlay');
    overlay.classList.add('hidden');
    localStorage.setItem('hasSeenTour', 'true');
}

// Tour Events
document.getElementById('startTourBtn').addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent triggering file browser from parent uploadArea
    startTour();
});

// Prevent download sample report link from triggering file browser
const downloadSampleLink = document.querySelector('a[href="assets/sample_report.pdf"]');
if (downloadSampleLink) {
    downloadSampleLink.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent triggering file browser from parent uploadArea
    });
}

document.getElementById('skipTourBtn').addEventListener('click', endTour);
document.getElementById('nextTourBtn').addEventListener('click', () => {
    currentTourStep++;
    showTourStep(currentTourStep);
});

// Auto-start check
window.addEventListener('load', () => {
    if (!localStorage.getItem('hasSeenTour')) {
        setTimeout(startTour, 1000);
    }
});

console.log('MedLab Analyzer Upload UI (Enhanced) initialized successfully');

// ==========================================
// AUTHENTICATION
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize authentication (check user status but don't force redirect)
    if (typeof initAuth === 'function') {
        try {
            const user = await initAuth({
                requireAuthentication: false, // Allow guests to see landing/upload
                displayUser: true,
                navElementId: 'navActions'
            });

            if (!user) {
                // Show guest banner
                const bannerContainer = document.createElement('div');
                bannerContainer.className = 'w-full max-w-4xl mx-auto mb-6 px-4 shrink-0 relative z-10';
                bannerContainer.innerHTML = `
                    <div class="bg-blue-50 border-l-4 border-primary p-4 rounded-r-lg shadow-sm flex items-start gap-4">
                        <span class="material-icons-round text-primary mt-0.5">info</span>
                        <div>
                            <h3 class="text-sm font-bold text-blue-900">Demo Mode Active</h3>
                            <p class="text-sm text-blue-700 mt-1">You are viewing the application as a guest. You can upload and preview reports, but <a href="login.html?redirect=upload_ui.html" class="font-bold underline hover:text-blue-900">logging in</a> is required to run AI analysis.</p>
                        </div>
                    </div>
                `;
                const mainEl = document.querySelector('main');
                if (mainEl && mainEl.firstChild) {
                    mainEl.insertBefore(bannerContainer, mainEl.firstChild);
                }
            }
        } catch (error) {
            console.error('Auth initialization failed:', error);
        }
    } else {
        console.warn('Auth module not loaded');
    }
});
