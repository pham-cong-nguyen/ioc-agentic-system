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
                await this.api.deleteFunction(functionId);
                this.ui.showToast('Function deleted successfully', 'success');
                await this.loadFunctions();
            } catch (error) {
                this.ui.showToast('Failed to delete function', 'error');
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

    search(query) {
        this.filterFunctions(query);
    }
}
