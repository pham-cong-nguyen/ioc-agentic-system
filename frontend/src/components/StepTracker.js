/**
 * Step Tracker Component - Display agent reasoning steps (OpenAI-style)
 */

export class StepTracker {
    constructor() {
        this.steps = [];
        this.apiCalls = [];
    }

    /**
     * Create step tracker UI element
     */
    createStepTrackerUI(container, steps, apiCalls) {
        const trackerHTML = `
            <div class="step-tracker">
                <div class="step-tracker-header">
                    <button class="step-tracker-toggle">
                        <i class="fas fa-chevron-down"></i>
                        <span class="step-count">${steps.length} reasoning steps</span>
                    </button>
                </div>
                <div class="step-tracker-content" style="display: none;">
                    ${this.renderSteps(steps)}
                    ${apiCalls.length > 0 ? this.renderAPICalls(apiCalls) : ''}
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = trackerHTML;
        const trackerEl = tempDiv.firstElementChild;

        // Add toggle functionality
        const toggle = trackerEl.querySelector('.step-tracker-toggle');
        const content = trackerEl.querySelector('.step-tracker-content');
        const icon = toggle.querySelector('i');

        toggle.addEventListener('click', () => {
            const isHidden = content.style.display === 'none';
            content.style.display = isHidden ? 'block' : 'none';
            icon.classList.toggle('fa-chevron-down', !isHidden);
            icon.classList.toggle('fa-chevron-up', isHidden);
        });

        return trackerEl;
    }

    /**
     * Render reasoning steps
     */
    renderSteps(steps) {
        if (!steps || steps.length === 0) return '';

        return `
            <div class="reasoning-steps">
                <h4><i class="fas fa-brain"></i> Reasoning Process</h4>
                ${steps.map(step => this.renderStep(step)).join('')}
            </div>
        `;
    }

    /**
     * Render a single step
     */
    renderStep(step) {
        const icons = {
            thought: 'fa-lightbulb',
            action: 'fa-bolt',
            observation: 'fa-eye',
            final: 'fa-check-circle'
        };

        const colors = {
            thought: '#3b82f6',  // blue
            action: '#f59e0b',   // amber
            observation: '#8b5cf6', // purple
            final: '#10b981'     // green
        };

        const icon = icons[step.step_type] || 'fa-circle';
        const color = colors[step.step_type] || '#6b7280';

        return `
            <div class="step-item" data-step-type="${step.step_type}">
                <div class="step-icon" style="background-color: ${color}20; color: ${color};">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="step-content">
                    <div class="step-header">
                        <span class="step-type">${this.formatStepType(step.step_type)}</span>
                        <span class="step-number">#${step.step_number}</span>
                    </div>
                    <div class="step-text">${this.formatStepContent(step.content, step.step_type)}</div>
                    ${step.details ? this.renderStepDetails(step.details, step.step_type) : ''}
                </div>
            </div>
        `;
    }

    /**
     * Format step type for display
     */
    formatStepType(type) {
        const types = {
            thought: '💭 Thought',
            action: '⚡ Action',
            observation: '👁️ Observation',
            final: 'Final Answer'
        };
        return types[type] || type;
    }

    /**
     * Format step content
     */
    formatStepContent(content, type) {
        if (type === 'action') {
            // Highlight function names
            return content.replace(/Execute function: (.+)/, 
                'Execute function: <code class="function-name">$1</code>');
        }
        return content;
    }

    /**
     * Render step details
     */
    renderStepDetails(details, stepType) {
        if (stepType === 'action' && details.parameters) {
            return `
                <div class="step-details">
                    <button class="details-toggle">
                        <i class="fas fa-chevron-right"></i>
                        Show parameters
                    </button>
                    <div class="details-content" style="display: none;">
                        <pre class="json-display">${JSON.stringify(details.parameters, null, 2)}</pre>
                    </div>
                </div>
            `;
        }
        return '';
    }

    /**
     * Render API calls section
     */
    renderAPICalls(apiCalls) {
        return `
            <div class="api-calls-section">
                <h4><i class="fas fa-plug"></i> API Calls (${apiCalls.length})</h4>
                ${apiCalls.map((call, index) => this.renderAPICall(call, index)).join('')}
            </div>
        `;
    }

    /**
     * Render a single API call
     */
    renderAPICall(call, index) {
        const statusIcon = call.status === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        const statusColor = call.status === 'success' ? '#10b981' : '#ef4444';
        const methodColor = {
            'GET': '#3b82f6',
            'POST': '#10b981',
            'PUT': '#f59e0b',
            'DELETE': '#ef4444'
        }[call.method] || '#6b7280';

        return `
            <div class="api-call-item" data-status="${call.status}">
                <div class="api-call-header">
                    <div class="api-call-title">
                        <span class="api-call-method" style="background-color: ${methodColor};">
                            ${call.method}
                        </span>
                        <span class="api-call-name">${call.function_name}</span>
                        <span class="api-call-status" style="color: ${statusColor};">
                            <i class="fas ${statusIcon}"></i>
                            ${call.status}
                        </span>
                    </div>
                    <span class="api-call-time">${call.execution_time_ms.toFixed(0)}ms</span>
                </div>
                
                <div class="api-call-endpoint">
                    <code>${call.endpoint}</code>
                </div>

                <div class="api-call-details">
                    <button class="api-details-toggle">
                        <i class="fas fa-chevron-right"></i>
                        View details
                    </button>
                    <div class="api-details-content" style="display: none;">
                        <!-- Parameters -->
                        <div class="api-detail-section">
                            <h5>📥 Parameters</h5>
                            <pre class="json-display">${JSON.stringify(call.parameters, null, 2)}</pre>
                        </div>
                        
                        <!-- Response -->
                        ${call.response ? `
                            <div class="api-detail-section">
                                <h5>📤 Response</h5>
                                <pre class="json-display">${JSON.stringify(call.response, null, 2)}</pre>
                            </div>
                        ` : ''}
                        
                        <!-- Error -->
                        ${call.error ? `
                            <div class="api-detail-section error">
                                <h5>❌ Error</h5>
                                <pre class="error-display">${call.error}</pre>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Setup event listeners for expandable sections
     */
    setupEventListeners(container) {
        // Toggle step details
        container.querySelectorAll('.details-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const content = toggle.nextElementSibling;
                const icon = toggle.querySelector('i');
                const isHidden = content.style.display === 'none';
                
                content.style.display = isHidden ? 'block' : 'none';
                icon.classList.toggle('fa-chevron-right', !isHidden);
                icon.classList.toggle('fa-chevron-down', isHidden);
                toggle.innerHTML = `<i class="fas ${isHidden ? 'fa-chevron-down' : 'fa-chevron-right'}"></i> ${isHidden ? 'Hide' : 'Show'} parameters`;
            });
        });

        // Toggle API call details
        container.querySelectorAll('.api-details-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const content = toggle.nextElementSibling;
                const icon = toggle.querySelector('i');
                const isHidden = content.style.display === 'none';
                
                content.style.display = isHidden ? 'block' : 'none';
                icon.classList.toggle('fa-chevron-right', !isHidden);
                icon.classList.toggle('fa-chevron-down', isHidden);
                toggle.innerHTML = `<i class="fas ${isHidden ? 'fa-chevron-down' : 'fa-chevron-right'}"></i> ${isHidden ? 'Hide' : 'View'} details`;
            });
        });
    }
}
