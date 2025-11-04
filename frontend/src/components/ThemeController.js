/**
 * ThemeController - Manages light/dark theme switching
 */
export class ThemeController {
    constructor() {
        this.STORAGE_KEY = 'ioc-theme';
        this.currentTheme = this.loadTheme();
        this.themeToggleBtn = null;
        
        console.log('🎨 ThemeController initialized, current theme:', this.currentTheme);
    }

    /**
     * Initialize theme controller
     */
    init() {
        // Apply saved theme
        this.applyTheme(this.currentTheme);
        
        // Setup toggle button
        this.themeToggleBtn = document.getElementById('themeToggle');
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
            this.updateToggleIcon();
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.hasUserPreference()) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
        
        console.log('✅ ThemeController ready');
    }

    /**
     * Load theme from localStorage or system preference
     */
    loadTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        if (savedTheme) {
            return savedTheme;
        }
        
        // Fall back to system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'dark'; // Default to dark
    }

    /**
     * Check if user has set a preference
     */
    hasUserPreference() {
        return localStorage.getItem(this.STORAGE_KEY) !== null;
    }

    /**
     * Apply theme to body
     */
    applyTheme(theme) {
        const body = document.body;
        
        // Remove old theme classes
        body.classList.remove('light-theme', 'dark-theme');
        
        // Add new theme class
        body.classList.add(`${theme}-theme`);
        
        // Update current theme
        this.currentTheme = theme;
        
        // Save to localStorage
        localStorage.setItem(this.STORAGE_KEY, theme);
        
        // Update toggle icon
        this.updateToggleIcon();
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme } 
        }));
        
        console.log(`🎨 Theme changed to: ${theme}`);
    }

    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        
        // Add animation effect
        if (this.themeToggleBtn) {
            this.themeToggleBtn.classList.add('animate-spin');
            setTimeout(() => {
                this.themeToggleBtn.classList.remove('animate-spin');
            }, 300);
        }
    }

    /**
     * Update toggle button icon
     */
    updateToggleIcon() {
        if (!this.themeToggleBtn) return;
        
        const icon = this.themeToggleBtn.querySelector('i');
        if (!icon) return;
        
        // Remove old classes
        icon.classList.remove('fa-moon', 'fa-sun');
        
        // Add new class based on current theme
        if (this.currentTheme === 'dark') {
            icon.classList.add('fa-sun'); // Show sun icon in dark mode (to switch to light)
        } else {
            icon.classList.add('fa-moon'); // Show moon icon in light mode (to switch to dark)
        }
    }

    /**
     * Get current theme
     */
    getTheme() {
        return this.currentTheme;
    }

    /**
     * Set theme programmatically
     */
    setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') {
            console.warn('Invalid theme:', theme);
            return;
        }
        this.applyTheme(theme);
    }
}
