/**
 * WebSocket Service - Real-time communication with backend
 * Handles streaming responses and live updates
 */

export class WebSocketService {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isIntentionallyClosed = false;
        this.messageHandlers = new Map();
        this.connectionPromise = null;
    }

    /**
     * Connect to WebSocket server
     */
    connect(token) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return Promise.resolve();
        }

        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        this.connectionPromise = new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;
            
            console.log('🔌 Connecting to WebSocket:', wsUrl);
            
            try {
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('✅ WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.isIntentionallyClosed = false;
                    this.eventBus.emit('ws:connected');
                    this.connectionPromise = null;
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.ws.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.eventBus.emit('ws:error', error);
                    this.connectionPromise = null;
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    console.log('🔌 WebSocket closed:', event.code, event.reason);
                    this.eventBus.emit('ws:disconnected', { code: event.code, reason: event.reason });
                    this.connectionPromise = null;
                    
                    // Attempt to reconnect if not intentionally closed
                    if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnect(token);
                    }
                };
            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                this.connectionPromise = null;
                reject(error);
            }
        });

        return this.connectionPromise;
    }

    /**
     * Reconnect with exponential backoff
     */
    reconnect(token) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(token).catch(error => {
                console.error('Reconnection failed:', error);
            });
        }, delay);
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);

            const { type, payload, messageId } = data;

            // Call specific handler if registered
            if (messageId && this.messageHandlers.has(messageId)) {
                this.messageHandlers.get(messageId)(payload);
            }

            // Emit event for general listeners
            this.eventBus.emit(`ws:${type}`, payload);
            
            // Handle specific message types
            switch (type) {
                case 'stream_start':
                    this.eventBus.emit('chat:streamStart', payload);
                    break;
                case 'stream_chunk':
                    this.eventBus.emit('chat:streamChunk', payload);
                    break;
                case 'stream_end':
                    this.eventBus.emit('chat:streamEnd', payload);
                    // Clean up handler
                    if (messageId) {
                        this.messageHandlers.delete(messageId);
                    }
                    break;
                case 'stream_error':
                    this.eventBus.emit('chat:streamError', payload);
                    if (messageId) {
                        this.messageHandlers.delete(messageId);
                    }
                    break;
                case 'function_execution':
                    this.eventBus.emit('chat:functionExecution', payload);
                    break;
                case 'notification':
                    this.eventBus.emit('notification', payload);
                    break;
                default:
                    console.warn('Unknown message type:', type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }

    /**
     * Send a message through WebSocket
     */
    send(type, payload, messageId = null) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }

        const message = {
            type,
            payload,
            messageId: messageId || this.generateMessageId(),
            timestamp: new Date().toISOString()
        };

        try {
            this.ws.send(JSON.stringify(message));
            return message.messageId;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }

    /**
     * Register a handler for a specific message
     */
    registerMessageHandler(messageId, handler) {
        this.messageHandlers.set(messageId, handler);
    }

    /**
     * Send a chat query with streaming support
     */
    sendQuery(query, conversationId = null) {
        const messageId = this.generateMessageId();
        
        const sent = this.send('query', {
            query,
            conversationId,
            stream: true
        }, messageId);

        return sent ? messageId : null;
    }

    /**
     * Generate a unique message ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Check if WebSocket is connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Close WebSocket connection
     */
    disconnect() {
        if (this.ws) {
            this.isIntentionallyClosed = true;
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
            console.log('WebSocket disconnected');
        }
    }

    /**
     * Get connection state
     */
    getState() {
        if (!this.ws) return 'DISCONNECTED';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'CONNECTED';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'DISCONNECTED';
            default: return 'UNKNOWN';
        }
    }
}
