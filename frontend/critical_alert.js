/**
 * critical_alert.js
 *
 * Displays a blocking full-screen modal whenever a Critical-severity
 * lab value is detected. The user must explicitly acknowledge the alert
 * before the main dashboard renders.
 *
 * Usage:
 *   import { showCriticalAlert } from './critical_alert.js';
 *
 *   if (data.has_critical && data.critical_parameters?.length) {
 *     await showCriticalAlert(data.critical_parameters);
 *   }
 *   // Dashboard renders here, after user acknowledges
 */

/**
 * Returns a Promise that resolves when the user clicks "I Understand".
 *
 * @param {Array<{name: string, value: string|number, unit: string}>} criticalParams
 * @returns {Promise<void>}
 */
export function showCriticalAlert(criticalParams) {
    return new Promise((resolve) => {
        // Prevent body scroll while modal is open
        document.body.style.overflow = 'hidden';

        const overlay = document.createElement('div');
        overlay.className = 'critical-alert-overlay';
        overlay.setAttribute('role', 'alertdialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'critical-alert-title');
        overlay.setAttribute('aria-describedby', 'critical-alert-desc');

        overlay.innerHTML = `
      <div class="critical-alert-box" tabindex="-1">
        <div class="critical-alert-header">
          <span class="critical-alert-icon" aria-hidden="true">⚠️</span>
          <h2 class="critical-alert-title" id="critical-alert-title">
            Critical Values Detected
          </h2>
        </div>

        <p class="critical-alert-subtitle" id="critical-alert-desc">
          The following lab results are outside critical limits and may require
          <strong>immediate medical attention</strong>. Please contact your
          healthcare provider or emergency services if you are experiencing symptoms.
        </p>

        <div class="critical-params-list" role="list">
          ${(criticalParams || []).map(p => `
            <div class="critical-param-item" role="listitem">
              <span class="critical-param-name">${escapeHtml(p.name || p.parameter || '')}</span>
              <span class="critical-param-value">
                ${escapeHtml(String(p.value || ''))}
                <span class="critical-param-unit">${escapeHtml(p.unit || '')}</span>
              </span>
              <span class="critical-param-badge" aria-label="Critical severity">CRITICAL</span>
            </div>
          `).join('')}
        </div>

        <div class="critical-alert-emergency">
          <span class="critical-alert-emergency-icon" aria-hidden="true">🏥</span>
          <span>
            If you feel unwell, call emergency services immediately.
            <strong>Do not wait</strong> for your next scheduled appointment.
          </span>
        </div>

        <p class="critical-alert-disclaimer">
          This analysis is for informational purposes only and does not constitute
          medical advice, diagnosis, or treatment. Always consult a qualified
          healthcare professional for medical decisions.
        </p>

        <div class="critical-alert-actions">
          <button class="critical-alert-acknowledge" id="critical-alert-confirm">
            I understand — Show full results
          </button>
        </div>
      </div>
    `;

        document.body.appendChild(overlay);

        // Focus the modal box for screen reader announcement
        const box = overlay.querySelector('.critical-alert-box');
        box.focus();

        // Trap focus inside modal
        overlay.addEventListener('keydown', (e) => {
            const focusable = overlay.querySelectorAll('button, [tabindex]:not([tabindex="-1"])');
            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (e.key === 'Tab') {
                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
            // Block Escape — user must explicitly acknowledge
            if (e.key === 'Escape') e.preventDefault();
        });

        overlay.querySelector('#critical-alert-confirm').addEventListener('click', () => {
            overlay.classList.add('critical-alert-closing');
            document.body.style.overflow = '';

            setTimeout(() => {
                overlay.remove();
                resolve();
            }, 300);
        });
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
}
