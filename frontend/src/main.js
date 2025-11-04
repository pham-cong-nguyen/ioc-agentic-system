/**
 * IOC Agentic System - Main Application Entry Point
 * Modern module-based architecture
 */

// Debug log ngay đầu file
console.log('%c🚀 main.js LOADING...', 'color: #6366f1; font-size: 16px; font-weight: bold');
console.log('Time:', new Date().toLocaleTimeString());

import { ApiService } from './services/api.js';
import { StateManager } from './services/state.js';
import { WebSocketService } from './services/websocket.js';
import { ConversationService } from './services/conversation.js';
import { ChatController } from './components/ChatController.js';
import { RegistryController } from './components/RegistryController.js';
import { AnalyticsController } from './components/AnalyticsController.js';
import { SettingsController } from './components/SettingsController.js';
import { UIManager } from './utils/ui.js';
import { EventBus } from './utils/eventBus.js';

class App {
    constructor() {
        console.log('%c📦 App constructor called', 'color: #10b981; font-weight: bold');
        this.state = new StateManager();
        this.api = new ApiService();
        this.ui = new UIManager();
        this.eventBus = new EventBus();
        this.ws = null;
        this.conversationService = null;
        
        this.controllers = {
            chat: null,
            registry: null,
            analytics: null,
            settings: null
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 IOC Agentic System initializing...');
        
        // Initialize services
        this.conversationService = new ConversationService(this.api, this.state);
        await this.conversationService.init();
        
        // Initialize controllers
        this.controllers.chat = new ChatController(this.api, this.state, this.ui, this.conversationService);
        this.controllers.registry = new RegistryController(this.api, this.state, this.ui);
        this.controllers.analytics = new AnalyticsController(this.api, this.state, this.ui, this.conversationService);
        this.controllers.settings = new SettingsController(this.api, this.state, this.ui, this.conversationService);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.initializeUI();
        
        // Check authentication
        await this.checkAuth();
        
        // Apply saved settings
        this.controllers.settings.applySettings();
        
        // Initialize WebSocket if authenticated
        const token = localStorage.getItem('access_token');
        if (token) {
            this.initWebSocket(token);
        }
        
        // Load initial data
        await this.loadInitialData();
        
        console.log('✅ Application initialized successfully');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.currentTarget.dataset.view;
                this.navigateTo(view);
            });
        });

        // Menu toggle for mobile
        const menuToggle = document.getElementById('menuToggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                document.querySelector('.sidebar').classList.toggle('open');
            });
        }

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Global search
        const globalSearch = document.getElementById('globalSearch');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => {
                this.handleGlobalSearch(e.target.value);
            });
        }

        // Subscribe to events
        this.eventBus.on('auth:logout', () => this.handleLogout());
        this.eventBus.on('error', (error) => this.handleError(error));
    }

    initializeUI() {
        // Set initial theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.body.className = `${savedTheme}-theme`;
        
        // Update theme toggle icon
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    async checkAuth() {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            // For demo purposes, auto-login
            await this.autoLogin();
        } else {
            try {
                const user = await this.api.getCurrentUser();
                this.state.setState({ user, isAuthenticated: true });
                this.updateUserProfile(user);
            } catch (error) {
                console.error('Auth check failed:', error);
                await this.autoLogin();
            }
        }
    }

    async autoLogin() {
        try {
            const response = await this.api.login('admin', 'password');
            localStorage.setItem('access_token', response.access_token);
            this.state.setState({ user: response.user, isAuthenticated: true });
            this.updateUserProfile(response.user);
        } catch (error) {
            console.error('Auto login failed:', error);
            this.ui.showToast('Authentication failed', 'error');
        }
    }

    initWebSocket(token) {
        try {
            this.ws = new WebSocketService(this.eventBus);
            this.ws.connect(token);
            
            // Setup WebSocket event handlers
            this.eventBus.on('ws:connected', () => {
                console.log('✅ WebSocket connected');
                this.ui.showToast('Real-time connection established', 'success');
            });

            this.eventBus.on('ws:disconnected', () => {
                console.log('🔌 WebSocket disconnected');
            });

            this.eventBus.on('ws:error', (error) => {
                console.error('WebSocket error:', error);
            });

            // Chat stream events
            this.eventBus.on('chat:streamStart', (data) => {
                console.log('Stream started:', data);
            });

            this.eventBus.on('chat:streamChunk', (data) => {
                if (this.controllers.chat.handleStreamChunk) {
                    this.controllers.chat.handleStreamChunk(data);
                }
            });

            this.eventBus.on('chat:streamEnd', (data) => {
                if (this.controllers.chat.handleStreamEnd) {
                    this.controllers.chat.handleStreamEnd(data);
                }
            });

            this.eventBus.on('chat:streamError', (error) => {
                console.error('Stream error:', error);
                this.ui.showToast('Stream error: ' + error.message, 'error');
            });

            // Function execution events
            this.eventBus.on('chat:functionExecution', (data) => {
                console.log('Function executed:', data);
            });

            // Notification events
            this.eventBus.on('notification', (data) => {
                this.handleNotification(data);
            });

        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }

    handleNotification(data) {
        const { type, title, message } = data;
        this.ui.showToast(message || title, type || 'info');
    }

    async loadInitialData() {
        try {
            // Load conversations (already loaded in init)
            // Load API functions
            await this.controllers.registry.loadFunctions();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }

    navigateTo(view) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`)?.classList.add('active');

        // Update views
        document.querySelectorAll('.view').forEach(v => {
            v.classList.remove('active');
        });
        
        const viewMap = {
            chat: 'chatView',
            registry: 'registryView',
            analytics: 'analyticsView',
            settings: 'settingsView'
        };
        
        const viewElement = document.getElementById(viewMap[view]);
        if (viewElement) {
            viewElement.classList.add('active');
        }

        // Update breadcrumb
        const breadcrumb = document.getElementById('currentView');
        if (breadcrumb) {
            const titles = {
                chat: 'Chat Interface',
                registry: 'API Registry',
                analytics: 'Analytics',
                settings: 'Settings'
            };
            breadcrumb.textContent = titles[view] || view;
        }

        // Load view-specific data
        if (view === 'analytics') {
            this.controllers.analytics.loadAnalytics();
        } else if (view === 'settings') {
            this.controllers.settings.renderSettings();
        }

        // Store current view
        this.state.setState({ currentView: view });
    }

    toggleTheme() {
        const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.body.className = `${newTheme}-theme`;
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    handleGlobalSearch(query) {
        const currentView = this.state.getState().currentView;
        
        if (currentView === 'registry') {
            this.controllers.registry.search(query);
        } else if (currentView === 'chat') {
            this.controllers.chat.searchHistory(query);
        }
    }

    updateUserProfile(user) {
        const userName = document.querySelector('.user-name');
        const userRole = document.querySelector('.user-role');
        
        if (userName) userName.textContent = user.username || 'Admin User';
        if (userRole) userRole.textContent = user.roles?.[0] || 'Administrator';
    }

    handleLogout() {
        localStorage.removeItem('access_token');
        this.state.setState({ user: null, isAuthenticated: false });
        this.ui.showToast('Logged out successfully', 'success');
        setTimeout(() => window.location.reload(), 1000);
    }

    handleError(error) {
        console.error('Application error:', error);
        this.ui.showToast(error.message || 'An error occurred', 'error');
    }
}

// Initialize app when DOM is ready
console.log('%c⏳ Waiting for DOMContentLoaded...', 'color: #f59e0b; font-weight: bold');

document.addEventListener('DOMContentLoaded', () => {
    console.log('%c✅ DOMContentLoaded fired!', 'color: #10b981; font-size: 14px; font-weight: bold');
    console.log('Creating App instance...');
    window.app = new App();
    console.log('%c✅ App instance created', 'color: #10b981; font-weight: bold');
});

// Handle errors globally
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});
