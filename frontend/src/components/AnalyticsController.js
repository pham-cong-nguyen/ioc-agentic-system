/**
 * Analytics Controller - Manage analytics view and visualizations
 */

export class AnalyticsController {
    constructor(api, state, ui, conversationService) {
        this.api = api;
        this.state = state;
        this.ui = ui;
        this.conversationService = conversationService;
        this.chartInstances = {};
        this.refreshInterval = null;
        
        this.init();
    }

    init() {
        console.log('📊 Analytics Controller initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for view changes
        document.addEventListener('viewChanged', (e) => {
            if (e.detail === 'analytics') {
                this.loadAnalytics();
            }
        });

        // Listen for refresh button
        const refreshBtn = document.getElementById('refresh-analytics');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAnalytics());
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }

    /**
     * Load analytics data
     */
    async loadAnalytics() {
        this.ui.showLoading('Loading analytics...');
        
        try {
            // Load data from multiple sources
            const [conversationStats, functionStats, systemStats] = await Promise.all([
                this.loadConversationStats(),
                this.loadFunctionStats(),
                this.loadSystemStats()
            ]);

            // Render analytics
            this.renderOverviewCards(conversationStats, functionStats, systemStats);
            this.renderConversationChart(conversationStats);
            this.renderFunctionUsageChart(functionStats);
            this.renderRecentActivity();
            this.renderInsights(conversationStats, functionStats);

            this.ui.hideLoading();
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.ui.hideLoading();
            this.ui.showToast('Failed to load analytics', 'error');
        }
    }

    /**
     * Load conversation statistics
     */
    async loadConversationStats() {
        const stats = this.conversationService.getStats();
        const conversations = this.state.getState('conversations') || [];
        
        // Calculate time-based stats
        const now = Date.now();
        const dayAgo = now - 24 * 60 * 60 * 1000;
        const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
        
        const last24h = conversations.filter(c => 
            new Date(c.createdAt).getTime() > dayAgo
        ).length;
        
        const last7days = conversations.filter(c => 
            new Date(c.createdAt).getTime() > weekAgo
        ).length;

        // Calculate daily conversation counts for chart
        const dailyCounts = this.calculateDailyCounts(conversations, 7);

        return {
            ...stats,
            last24h,
            last7days,
            dailyCounts
        };
    }

    /**
     * Load function statistics
     */
    async loadFunctionStats() {
        try {
            const response = await this.api.get('/registry/functions');
            const functions = response.functions || [];
            
            // Calculate domain distribution
            const domainCounts = {};
            const methodCounts = {};
            
            functions.forEach(func => {
                domainCounts[func.domain] = (domainCounts[func.domain] || 0) + 1;
                methodCounts[func.method] = (methodCounts[func.method] || 0) + 1;
            });

            return {
                total: functions.length,
                byDomain: domainCounts,
                byMethod: methodCounts,
                functions
            };
        } catch (error) {
            console.error('Error loading function stats:', error);
            return {
                total: 0,
                byDomain: {},
                byMethod: {},
                functions: []
            };
        }
    }

    /**
     * Load system statistics
     */
    async loadSystemStats() {
        try {
            const response = await this.api.get('/analytics/system');
            return response.stats || {
                uptime: 0,
                requestCount: 0,
                avgResponseTime: 0,
                errorRate: 0
            };
        } catch (error) {
            console.warn('System stats not available:', error);
            return {
                uptime: 0,
                requestCount: 0,
                avgResponseTime: 0,
                errorRate: 0
            };
        }
    }

    /**
     * Render overview cards
     */
    renderOverviewCards(conversationStats, functionStats, systemStats) {
        const container = document.getElementById('analytics-overview');
        if (!container) return;

        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${conversationStats.totalConversations}</div>
                        <div class="stat-label">Total Conversations</div>
                        <div class="stat-change positive">
                            <i class="fas fa-arrow-up"></i>
                            ${conversationStats.last24h} in last 24h
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-message"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${conversationStats.totalMessages}</div>
                        <div class="stat-label">Total Messages</div>
                        <div class="stat-change">
                            ${conversationStats.avgMessagesPerConversation} avg per conversation
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-cube"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${functionStats.total}</div>
                        <div class="stat-label">Registered Functions</div>
                        <div class="stat-change">
                            ${Object.keys(functionStats.byDomain).length} domains
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${systemStats.avgResponseTime || 0}ms</div>
                        <div class="stat-label">Avg Response Time</div>
                        <div class="stat-change ${systemStats.errorRate > 5 ? 'negative' : ''}">
                            ${systemStats.errorRate || 0}% error rate
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render conversation chart
     */
    renderConversationChart(stats) {
        const canvas = document.getElementById('conversation-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const labels = stats.dailyCounts.map(d => d.date);
        const data = stats.dailyCounts.map(d => d.count);

        // Simple canvas chart (can be replaced with Chart.js)
        this.drawLineChart(ctx, labels, data, {
            color: '#6366f1',
            gradient: true
        });
    }

    /**
     * Render function usage chart
     */
    renderFunctionUsageChart(stats) {
        const canvas = document.getElementById('function-usage-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const domains = Object.keys(stats.byDomain);
        const counts = Object.values(stats.byDomain);

        // Simple bar chart
        this.drawBarChart(ctx, domains, counts, {
            color: '#8b5cf6'
        });
    }

    /**
     * Render recent activity
     */
    renderRecentActivity() {
        const container = document.getElementById('recent-activity');
        if (!container) return;

        const conversations = this.state.getState('conversations') || [];
        const recent = conversations.slice(0, 10);

        if (recent.length === 0) {
            container.innerHTML = '<div class="empty-state">No recent activity</div>';
            return;
        }

        container.innerHTML = `
            <div class="activity-list">
                ${recent.map(conv => `
                    <div class="activity-item">
                        <div class="activity-icon">
                            <i class="fas fa-comment"></i>
                        </div>
                        <div class="activity-content">
                            <div class="activity-title">${this.ui.escapeHtml(conv.title)}</div>
                            <div class="activity-meta">
                                ${conv.messages.length} messages • ${this.ui.formatRelativeTime(conv.updatedAt)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render insights
     */
    renderInsights(conversationStats, functionStats) {
        const container = document.getElementById('analytics-insights');
        if (!container) return;

        const insights = [];

        // Generate insights based on data
        if (conversationStats.last24h > conversationStats.last7days / 7 * 2) {
            insights.push({
                type: 'trend',
                icon: 'fa-arrow-trend-up',
                title: 'High Activity',
                description: 'Conversation volume is significantly higher than average'
            });
        }

        if (functionStats.total > 0) {
            const mostUsedDomain = Object.entries(functionStats.byDomain)
                .sort((a, b) => b[1] - a[1])[0];
            
            if (mostUsedDomain) {
                insights.push({
                    type: 'info',
                    icon: 'fa-cube',
                    title: 'Top Domain',
                    description: `Most functions are in ${mostUsedDomain[0]} (${mostUsedDomain[1]} functions)`
                });
            }
        }

        if (conversationStats.avgMessagesPerConversation > 10) {
            insights.push({
                type: 'success',
                icon: 'fa-comments',
                title: 'Deep Conversations',
                description: 'Users are having long, detailed conversations'
            });
        }

        container.innerHTML = insights.length > 0 ? `
            <div class="insights-list">
                ${insights.map(insight => `
                    <div class="insight-card ${insight.type}">
                        <i class="fas ${insight.icon}"></i>
                        <div class="insight-content">
                            <h4>${insight.title}</h4>
                            <p>${insight.description}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        ` : '<div class="empty-state">No insights available yet</div>';
    }

    /**
     * Calculate daily conversation counts
     */
    calculateDailyCounts(conversations, days) {
        const counts = [];
        const now = new Date();
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            date.setHours(0, 0, 0, 0);
            
            const nextDate = new Date(date);
            nextDate.setDate(nextDate.getDate() + 1);
            
            const count = conversations.filter(c => {
                const createdAt = new Date(c.createdAt);
                return createdAt >= date && createdAt < nextDate;
            }).length;
            
            counts.push({
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                count
            });
        }
        
        return counts;
    }

    /**
     * Draw simple line chart on canvas
     */
    drawLineChart(ctx, labels, data, options = {}) {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Calculate scales
        const maxValue = Math.max(...data, 1);
        const xStep = (width - padding * 2) / (data.length - 1 || 1);
        const yScale = (height - padding * 2) / maxValue;
        
        // Draw gradient if enabled
        if (options.gradient) {
            const gradient = ctx.createLinearGradient(0, 0, 0, height);
            gradient.addColorStop(0, options.color + '40');
            gradient.addColorStop(1, options.color + '00');
            
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.moveTo(padding, height - padding);
            
            data.forEach((value, i) => {
                const x = padding + i * xStep;
                const y = height - padding - value * yScale;
                ctx.lineTo(x, y);
            });
            
            ctx.lineTo(width - padding, height - padding);
            ctx.closePath();
            ctx.fill();
        }
        
        // Draw line
        ctx.strokeStyle = options.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.forEach((value, i) => {
            const x = padding + i * xStep;
            const y = height - padding - value * yScale;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw points
        data.forEach((value, i) => {
            const x = padding + i * xStep;
            const y = height - padding - value * yScale;
            
            ctx.fillStyle = options.color;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    /**
     * Draw simple bar chart on canvas
     */
    drawBarChart(ctx, labels, data, options = {}) {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Calculate scales
        const maxValue = Math.max(...data, 1);
        const barWidth = (width - padding * 2) / data.length * 0.8;
        const barGap = (width - padding * 2) / data.length * 0.2;
        const yScale = (height - padding * 2) / maxValue;
        
        // Draw bars
        data.forEach((value, i) => {
            const x = padding + i * (barWidth + barGap);
            const barHeight = value * yScale;
            const y = height - padding - barHeight;
            
            // Gradient fill
            const gradient = ctx.createLinearGradient(0, y, 0, height - padding);
            gradient.addColorStop(0, options.color);
            gradient.addColorStop(1, options.color + '80');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);
        });
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh(interval = 30000) {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            this.loadAnalytics();
        }, interval);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.stopAutoRefresh();
        Object.values(this.chartInstances).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
    }
}
