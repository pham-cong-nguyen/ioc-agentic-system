/**
 * Registry Controller - Handle API Registry interface logic
 */

export class RegistryController {
    constructor(api, state, ui) {
        this.api = api;
        this.state = state;
        this.ui = ui;
        
        this.functions = [];
        this.filteredFunctions = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Add function button
        const addBtn = document.getElementById('addFunctionBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showFunctionDialog());
        }

        // Import button
        const importBtn = document.getElementById('importBtn');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importFunctions());
        }

        // Export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportFunctions());
        }

        // Search
        const searchInput = document.getElementById('searchFunctions');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterFunctions(e.target.value);
            });
        }

        // Domain filter
        const domainFilter = document.getElementById('filterDomain');
        if (domainFilter) {
            domainFilter.addEventListener('change', (e) => {
                this.filterByDomain(e.target.value);
            });
        }

        // Method filter
        const methodFilter = document.getElementById('filterMethod');
        if (methodFilter) {
            methodFilter.addEventListener('change', (e) => {
                this.filterByMethod(e.target.value);
            });
        }
    }

    async loadFunctions() {
        try {
            this.ui.showLoading('Loading API functions...');
            const response = await this.api.searchFunctions('', null, 100);
            // Response is a FunctionListResponse with { total, items, limit, offset }
            this.functions = response.items || [];
            this.filteredFunctions = [...this.functions];
            this.renderFunctions();
            this.state.setState({ functions: this.functions });
        } catch (error) {
            console.error('Failed to load functions:', error);
            this.ui.showToast('Failed to load functions', 'error');
        } finally {
            this.ui.hideLoading();
        }
    }

    renderFunctions() {
        const grid = document.getElementById('functionsGrid');
        if (!grid) return;

        if (this.filteredFunctions.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <h3>No functions found</h3>
                    <p>Start by adding your first API function</p>
                    <button class="btn-primary" onclick="window.app.controllers.registry.showFunctionDialog()">
                        <i class="fas fa-plus"></i> Add Function
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.filteredFunctions.map(func => this.createFunctionCard(func)).join('');

        // Add event listeners
        grid.querySelectorAll('.function-card').forEach(card => {
            const functionId = card.dataset.id;
            
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.function-actions')) {
                    this.viewFunction(functionId);
                }
            });

            card.querySelector('[data-action="edit"]')?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editFunction(functionId);
            });

            card.querySelector('[data-action="delete"]')?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteFunction(functionId);
            });

            card.querySelector('[data-action="test"]')?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.testFunction(functionId);
            });
        });
    }

    createFunctionCard(func) {
        return `
            <div class="function-card" data-id="${func.function_id}">
                <div class="function-card-header">
                    <div>
                        <div class="function-title">${func.name}</div>
                        <div class="function-id">${func.function_id}</div>
                    </div>
                    <div class="function-badges">
                        <span class="badge method">${func.method}</span>
                        <span class="badge domain">${func.domain}</span>
                    </div>
                </div>
                <div class="function-description">
                    ${func.description || 'No description'}
                </div>
                <div class="function-endpoint">
                    ${func.endpoint}
                </div>
                <div class="function-card-footer">
                    <div class="function-stats">
                        <div class="stat-item">
                            <i class="fas fa-play"></i>
                            <span>${func.call_count || 0}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-check"></i>
                            <span>${func.success_rate ? func.success_rate.toFixed(1) + '%' : 'N/A'}</span>
                        </div>
                    </div>
                    <div class="function-actions">
                        <button class="btn-icon btn-test" data-action="test" title="Test API">
                            <i class="fas fa-flask"></i>
                        </button>
                        <button class="btn-icon" data-action="edit" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" data-action="delete" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    filterFunctions(query) {
        const lowerQuery = query.toLowerCase();
        this.filteredFunctions = this.functions.filter(func => 
            func.name.toLowerCase().includes(lowerQuery) ||
            func.function_id.toLowerCase().includes(lowerQuery) ||
            (func.description && func.description.toLowerCase().includes(lowerQuery))
        );
        this.renderFunctions();
    }

    filterByDomain(domain) {
        if (!domain) {
            this.filteredFunctions = [...this.functions];
        } else {
            this.filteredFunctions = this.functions.filter(func => func.domain === domain);
        }
        this.renderFunctions();
    }

    filterByMethod(method) {
        if (!method) {
            this.filteredFunctions = [...this.functions];
        } else {
            this.filteredFunctions = this.functions.filter(func => func.method === method);
        }
        this.renderFunctions();
    }

    async showFunctionDialog(functionData = null) {
        const isEdit = !!functionData;
        const title = isEdit ? 'Edit Function' : 'Add New Function';

        const content = `
            <div class="function-form">
                <div class="form-group">
                    <label>Function ID *</label>
                    <input type="text" id="functionId" value="${functionData?.function_id || ''}" ${isEdit ? 'disabled' : ''} required>
                </div>
                <div class="form-group">
                    <label>Name *</label>
                    <input type="text" id="functionName" value="${functionData?.name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="functionDesc" rows="3">${functionData?.description || ''}</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Domain *</label>
                        <select id="functionDomain" required>
                            <option value="">Select domain</option>
                            <option value="energy" ${functionData?.domain === 'energy' ? 'selected' : ''}>Energy</option>
                            <option value="traffic" ${functionData?.domain === 'traffic' ? 'selected' : ''}>Traffic</option>
                            <option value="environment" ${functionData?.domain === 'environment' ? 'selected' : ''}>Environment</option>
                            <option value="health" ${functionData?.domain === 'health' ? 'selected' : ''}>Health</option>
                            <option value="security" ${functionData?.domain === 'security' ? 'selected' : ''}>Security</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Method *</label>
                        <select id="functionMethod" required>
                            <option value="GET" ${functionData?.method === 'GET' ? 'selected' : ''}>GET</option>
                            <option value="POST" ${functionData?.method === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${functionData?.method === 'PUT' ? 'selected' : ''}>PUT</option>
                            <option value="DELETE" ${functionData?.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Endpoint *</label>
                    <input type="url" id="functionEndpoint" value="${functionData?.endpoint || ''}" required>
                </div>
                <div class="form-group">
                    <label>Parameters (JSON)</label>
                    <textarea id="functionParams" rows="5" placeholder='{"param1": {"type": "string", "required": true}}'>${functionData?.parameters ? JSON.stringify(functionData.parameters, null, 2) : ''}</textarea>
                </div>
            </div>
        `;

        const result = await this.ui.showModal(title, content, [
            { label: 'Cancel', action: 'cancel', type: 'secondary' },
            { label: 'Save', action: 'save', type: 'primary', icon: 'fas fa-save' }
        ]);

        if (result === 'save') {
            await this.saveFunctionFromDialog(isEdit);
        }
    }

    async saveFunctionFromDialog(isEdit) {
        try {
            const formData = {
                function_id: document.getElementById('functionId').value,
                name: document.getElementById('functionName').value,
                description: document.getElementById('functionDesc').value,
                domain: document.getElementById('functionDomain').value,
                method: document.getElementById('functionMethod').value,
                endpoint: document.getElementById('functionEndpoint').value,
            };

            // Parse parameters JSON
            const paramsText = document.getElementById('functionParams').value;
            if (paramsText) {
                try {
                    formData.parameters = JSON.parse(paramsText);
                } catch (e) {
                    this.ui.showToast('Invalid JSON in parameters', 'error');
                    return;
                }
            }

            this.ui.showLoading(isEdit ? 'Updating function...' : 'Creating function...');

            if (isEdit) {
                await this.api.updateFunction(formData.function_id, formData);
                this.ui.showToast('Function updated successfully', 'success');
            } else {
                await this.api.createFunction(formData);
                this.ui.showToast('Function created successfully', 'success');
            }

            await this.loadFunctions();

        } catch (error) {
            console.error('Failed to save function:', error);
            this.ui.showToast(`Failed to ${isEdit ? 'update' : 'create'} function: ${error.message}`, 'error');
        } finally {
            this.ui.hideLoading();
        }
    }

    async viewFunction(functionId) {
        const func = this.functions.find(f => f.function_id === functionId);
        if (!func) return;

        const content = `
            <div class="function-details">
                <div class="detail-row">
                    <strong>Function ID:</strong>
                    <code>${func.function_id}</code>
                </div>
                <div class="detail-row">
                    <strong>Name:</strong>
                    <span>${func.name}</span>
                </div>
                <div class="detail-row">
                    <strong>Domain:</strong>
                    <span class="badge domain">${func.domain}</span>
                </div>
                <div class="detail-row">
                    <strong>Method:</strong>
                    <span class="badge method">${func.method}</span>
                </div>
                <div class="detail-row">
                    <strong>Endpoint:</strong>
                    <code>${func.endpoint}</code>
                </div>
                <div class="detail-row">
                    <strong>Description:</strong>
                    <p>${func.description || 'N/A'}</p>
                </div>
                ${func.parameters ? `
                    <div class="detail-row">
                        <strong>Parameters:</strong>
                        <pre>${JSON.stringify(func.parameters, null, 2)}</pre>
                    </div>
                ` : ''}
            </div>
        `;

        await this.ui.showModal(func.name, content, [
            { label: 'Close', action: 'close', type: 'secondary' },
            { label: 'Edit', action: 'edit', type: 'primary', icon: 'fas fa-edit' }
        ]).then(result => {
            if (result === 'edit') {
                this.editFunction(functionId);
            }
        });
    }

    async editFunction(functionId) {
        try {
            const func = await this.api.getFunction(functionId);
            await this.showFunctionDialog(func);
        } catch (error) {
            this.ui.showToast('Failed to load function', 'error');
        }
    }

    async deleteFunction(functionId) {
        const func = this.functions.find(f => f.function_id === functionId);
        const confirmed = await this.ui.showConfirm(
            'Delete Function',
            `Are you sure you want to delete "${func?.name}"? This action cannot be undone.`
        );

        if (confirmed === 'confirm') {
            try {
                this.ui.showLoading('Deleting function...');
                const response = await this.api.deleteFunction(functionId);
                
                // Remove from local arrays
                this.functions = this.functions.filter(f => f.function_id !== functionId);
                this.filteredFunctions = this.filteredFunctions.filter(f => f.function_id !== functionId);
                
                // Remove DOM element immediately
                const card = document.querySelector(`.function-card[data-id="${functionId}"]`);
                if (card) {
                    card.remove();
                }
                
                // Update state
                this.state.setState({ functions: this.functions });
                
                this.ui.showToast('Function deleted successfully', 'success');
                
                // Dispatch event for sync controller
                window.dispatchEvent(new CustomEvent('function-deleted', { 
                    detail: { functionId } 
                }));
                
            } catch (error) {
                console.error('Failed to delete function:', error);
                this.ui.showToast(`Failed to delete function: ${error.message}`, 'error');
            } finally {
                this.ui.hideLoading();
            }
        }
    }

    async importFunctions() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                this.ui.showLoading('Importing functions...');
                const data = await this.ui.readJSONFile(file);
                
                const functions = Array.isArray(data) ? data : [data];
                await this.api.bulkImportFunctions(functions);
                
                this.ui.showToast(`Imported ${functions.length} function(s)`, 'success');
                await this.loadFunctions();
            } catch (error) {
                this.ui.showToast('Failed to import functions', 'error');
            } finally {
                this.ui.hideLoading();
            }
        };

        input.click();
    }

    async exportFunctions() {
        try {
            const data = await this.api.exportFunctions();
            const filename = `ioc-functions-${new Date().toISOString().split('T')[0]}.json`;
            this.ui.downloadJSON(data, filename);
            this.ui.showToast('Functions exported successfully', 'success');
        } catch (error) {
            this.ui.showToast('Failed to export functions', 'error');
        }
    }

    async testFunction(functionId) {
        const func = this.functions.find(f => f.function_id === functionId);
        if (!func) return;

        // Build parameter input fields
        const paramInputs = [];
        if (func.parameters && typeof func.parameters === 'object') {
            for (const [paramName, paramSchema] of Object.entries(func.parameters)) {
                const isRequired = paramSchema.required || false;
                const paramType = paramSchema.type || 'string';
                const description = paramSchema.description || '';
                const defaultVal = paramSchema.default !== undefined ? paramSchema.default : '';
                
                let inputField = '';
                if (paramType === 'boolean') {
                    inputField = `
                        <select id="param_${paramName}" ${isRequired ? 'required' : ''}>
                            <option value="true">true</option>
                            <option value="false" ${!defaultVal ? 'selected' : ''}>false</option>
                        </select>
                    `;
                } else if (paramSchema.enum) {
                    const options = paramSchema.enum.map(val => 
                        `<option value="${val}">${val}</option>`
                    ).join('');
                    inputField = `
                        <select id="param_${paramName}" ${isRequired ? 'required' : ''}>
                            <option value="">-- Select --</option>
                            ${options}
                        </select>
                    `;
                } else if (paramType === 'array' || paramType === 'object') {
                    inputField = `
                        <textarea id="param_${paramName}" 
                                  placeholder='${paramType === 'array' ? '["item1", "item2"]' : '{"key": "value"}'}'
                                  rows="3"
                                  ${isRequired ? 'required' : ''}></textarea>
                    `;
                } else {
                    inputField = `
                        <input type="text" 
                               id="param_${paramName}" 
                               placeholder="${description || paramName}"
                               value="${defaultVal}"
                               ${isRequired ? 'required' : ''}>
                    `;
                }

                paramInputs.push(`
                    <div class="form-group">
                        <label for="param_${paramName}">
                            ${paramName}
                            ${isRequired ? '<span class="required">*</span>' : ''}
                            ${description ? `<span class="param-desc">${description}</span>` : ''}
                        </label>
                        ${inputField}
                    </div>
                `);
            }
        }

        const content = `
            <div class="test-function-dialog">
                <div class="test-info">
                    <div class="test-info-row">
                        <strong>Function:</strong> ${func.name}
                    </div>
                    <div class="test-info-row">
                        <strong>Method:</strong> <span class="badge method">${func.method}</span>
                    </div>
                    <div class="test-info-row">
                        <strong>Endpoint:</strong> <code>${func.endpoint}</code>
                    </div>
                </div>

                <form id="testFunctionForm">
                    ${paramInputs.length > 0 ? `
                        <h4>Parameters</h4>
                        ${paramInputs.join('')}
                    ` : '<p class="text-muted">No parameters required</p>'}

                    <div class="form-actions">
                        <button type="button" class="btn-secondary" onclick="window.app.ui.closeDialog()">
                            Cancel
                        </button>
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-play"></i> Run Test
                        </button>
                    </div>
                </form>

                <div id="testResults" class="test-results" style="display: none;">
                    <h4>Results</h4>
                    <div class="result-status"></div>
                    <div class="result-body"></div>
                </div>
            </div>
        `;

        this.ui.showDialog(`Test API: ${func.name}`, content, 'large');

        // Setup form submission
        const form = document.getElementById('testFunctionForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.executeTest(func, form);
        });
    }

    async executeTest(func, form) {
        const resultsDiv = document.getElementById('testResults');
        const statusDiv = resultsDiv.querySelector('.result-status');
        const bodyDiv = resultsDiv.querySelector('.result-body');

        try {
            // Collect parameters
            const params = {};
            if (func.parameters && typeof func.parameters === 'object') {
                for (const paramName of Object.keys(func.parameters)) {
                    const input = form.querySelector(`#param_${paramName}`);
                    if (input && input.value) {
                        const paramSchema = func.parameters[paramName];
                        let value = input.value;

                        // Parse based on type
                        if (paramSchema.type === 'boolean') {
                            value = value === 'true';
                        } else if (paramSchema.type === 'number' || paramSchema.type === 'integer') {
                            value = Number(value);
                        } else if (paramSchema.type === 'array' || paramSchema.type === 'object') {
                            try {
                                value = JSON.parse(value);
                            } catch (e) {
                                throw new Error(`Invalid JSON for parameter "${paramName}"`);
                            }
                        }

                        params[paramName] = value;
                    }
                }
            }

            // Show loading
            statusDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Testing...</div>';
            resultsDiv.style.display = 'block';
            bodyDiv.innerHTML = '';

            // Make API call
            const startTime = Date.now();
            let response;
            
            if (func.method === 'GET') {
                // For GET, add params as query string
                const queryString = new URLSearchParams(params).toString();
                const url = queryString ? `${func.endpoint}?${queryString}` : func.endpoint;
                response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
            } else {
                // For POST/PUT/PATCH, send params in body
                response = await fetch(func.endpoint, {
                    method: func.method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(params)
                });
            }

            const duration = Date.now() - startTime;
            const responseData = await response.json();

            // Show results
            const statusClass = response.ok ? 'success' : 'error';
            statusDiv.innerHTML = `
                <div class="status-badge ${statusClass}">
                    <i class="fas fa-${response.ok ? 'check-circle' : 'exclamation-circle'}"></i>
                    ${response.status} ${response.statusText}
                    <span class="duration">${duration}ms</span>
                </div>
            `;

            bodyDiv.innerHTML = `
                <div class="response-section">
                    <div class="response-header">
                        <strong>Response Body:</strong>
                        <button class="btn-icon" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.textContent)" title="Copy">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                    <pre class="response-body">${JSON.stringify(responseData, null, 2)}</pre>
                </div>
            `;

        } catch (error) {
            statusDiv.innerHTML = `
                <div class="status-badge error">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error
                </div>
            `;
            bodyDiv.innerHTML = `
                <div class="error-message">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
    }

    search(query) {
        this.filterFunctions(query);
    }
}
