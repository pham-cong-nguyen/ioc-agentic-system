/**
 * State Manager - Centralized state management
 * Simple reactive state management without external dependencies
 */

export class StateManager {
    constructor() {
        this.state = {
            user: null,
            isAuthenticated: false,
            currentView: 'chat',
            currentConversation: null,
            conversations: [],
            functions: [],
            messages: [],
            isLoading: false,
            error: null
        };
        
        this.listeners = new Map();
    }

    /**
     * Get current state or specific key
     */
    getState(key = null) {
        if (key) {
            return this.state[key];
        }
        return { ...this.state };
    }

    /**
     * Update state and notify listeners
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = { ...this.state, ...updates };
        
        // Notify listeners
        Object.keys(updates).forEach(key => {
            if (this.listeners.has(key)) {
                this.listeners.get(key).forEach(callback => {
                    callback(this.state[key], oldState[key]);
                });
            }
        });

        // Notify global listeners
        if (this.listeners.has('*')) {
            this.listeners.get('*').forEach(callback => {
                callback(this.state, oldState);
            });
        }
    }

    /**
     * Subscribe to state changes
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(key);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        };
    }

    /**
     * Clear specific state key
     */
    clearState(key) {
        if (key in this.state) {
            this.setState({ [key]: null });
        }
    }

    /**
     * Reset entire state
     */
    resetState() {
        this.state = {
            user: null,
            isAuthenticated: false,
            currentView: 'chat',
            currentConversation: null,
            conversations: [],
            functions: [],
            messages: [],
            isLoading: false,
            error: null
        };
        
        // Notify all listeners
        this.listeners.forEach((callbacks, key) => {
            callbacks.forEach(callback => callback(null, null));
        });
    }
}
