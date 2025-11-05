/**
 * Markdown Utility - Character-level streaming with markdown rendering
 * Like ChatGPT/Claude
 */

export class MarkdownRenderer {
    constructor() {
        // Configure marked with syntax highlighting
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                highlight: function(code, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (err) {
                            console.error('Highlight error:', err);
                        }
                    }
                    return hljs.highlightAuto(code).value;
                },
                breaks: true,
                gfm: true,
                pedantic: false,
                sanitize: false,
                smartLists: true,
                smartypants: true
            });
        }
    }

    /**
     * Render markdown to HTML
     */
    render(markdown) {
        if (typeof marked === 'undefined') {
            console.warn('Marked.js not loaded, returning plain text');
            return this.escapeHtml(markdown);
        }
        
        try {
            return marked.parse(markdown);
        } catch (error) {
            console.error('Markdown parse error:', error);
            return this.escapeHtml(markdown);
        }
    }

    /**
     * Render markdown incrementally (for streaming)
     * Handles partial markdown gracefully
     */
    renderIncremental(markdown) {
        if (typeof marked === 'undefined') {
            return this.escapeHtml(markdown);
        }

        try {
            // For incomplete markdown, try to render what we have
            // If it fails, return as plain text with preserving line breaks
            return marked.parse(markdown);
        } catch (error) {
            // If markdown is incomplete, show as formatted text
            return `<p>${this.escapeHtml(markdown).replace(/\n/g, '<br>')}</p>`;
        }
    }

    /**
     * Escape HTML for safety
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Apply syntax highlighting to code blocks after rendering
     */
    highlightCodeBlocks(container) {
        if (typeof hljs === 'undefined') return;
        
        const codeBlocks = container.querySelectorAll('pre code');
        codeBlocks.forEach((block) => {
            if (!block.classList.contains('hljs')) {
                hljs.highlightElement(block);
            }
        });
    }
}

/**
 * Character-level streaming text renderer
 * Streams text character by character like ChatGPT
 */
export class CharacterStreamRenderer {
    constructor(container, markdownRenderer, options = {}) {
        this.container = container;
        this.markdownRenderer = markdownRenderer;
        this.buffer = '';
        this.isStreaming = false;
        
        // Options
        this.charsPerFrame = options.charsPerFrame || 2; // Characters per animation frame
        this.minDelay = options.minDelay || 10; // Minimum delay between frames (ms)
        this.maxDelay = options.maxDelay || 30; // Maximum delay between frames (ms)
        
        // Internal state
        this.currentIndex = 0;
        this.fullText = '';
        this.animationFrame = null;
        this.lastFrameTime = 0;
    }

    /**
     * Start streaming text character by character
     */
    async streamText(text, isMarkdown = true) {
        this.fullText = text;
        this.currentIndex = 0;
        this.isStreaming = true;
        this.lastFrameTime = performance.now();
        this.scrollAttempts = 0; // Track scroll attempts

        return new Promise((resolve) => {
            const animate = (currentTime) => {
                if (!this.isStreaming || this.currentIndex >= this.fullText.length) {
                    this.isStreaming = false;
                    
                    // Final render with complete markdown
                    if (isMarkdown) {
                        this.container.innerHTML = this.markdownRenderer.render(this.fullText);
                        this.markdownRenderer.highlightCodeBlocks(this.container);
                    }
                    
                    // Final scroll to ensure visibility
                    setTimeout(() => {
                        this.forceScrollToBottom();
                    }, 100);
                    
                    resolve();
                    return;
                }

                // Calculate delay with some randomness for natural feel
                const elapsed = currentTime - this.lastFrameTime;
                const delay = this.minDelay + Math.random() * (this.maxDelay - this.minDelay);

                if (elapsed >= delay) {
                    // Add characters
                    this.currentIndex = Math.min(
                        this.currentIndex + this.charsPerFrame,
                        this.fullText.length
                    );
                    
                    const currentText = this.fullText.substring(0, this.currentIndex);
                    
                    // Render incrementally
                    if (isMarkdown) {
                        this.container.innerHTML = this.markdownRenderer.renderIncremental(currentText);
                    } else {
                        this.container.textContent = currentText;
                    }
                    
                    this.lastFrameTime = currentTime;
                    
                    // Auto-scroll every few frames
                    this.scrollAttempts++;
                    if (this.scrollAttempts % 3 === 0) { // Scroll every 3 frames
                        this.autoScroll();
                    }
                }

                this.animationFrame = requestAnimationFrame(animate);
            };

            this.animationFrame = requestAnimationFrame(animate);
        });
    }

    /**
     * Add chunk of text to stream (for SSE)
     */
    addChunk(chunk) {
        this.fullText += chunk;
    }

    /**
     * Stop streaming immediately and show full text
     */
    stopStreaming() {
        this.isStreaming = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        // Show complete text
        this.container.innerHTML = this.markdownRenderer.render(this.fullText);
        this.markdownRenderer.highlightCodeBlocks(this.container);
    }

    /**
     * Auto-scroll to keep streaming text visible
     */
    autoScroll() {
        try {
            // Try to find scrollable parent
            const scrollParent = this.findScrollParent(this.container);
            
            if (scrollParent) {
                // Scroll parent container
                const isNearBottom = scrollParent.scrollHeight - scrollParent.scrollTop - scrollParent.clientHeight < 150;
                if (isNearBottom) {
                    scrollParent.scrollTop = scrollParent.scrollHeight;
                }
            } else {
                // No scrollable parent found, scroll window
                const docHeight = Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight,
                    document.body.clientHeight,
                    document.documentElement.clientHeight
                );
                
                const windowBottom = window.innerHeight + window.scrollY;
                const isNearBottom = docHeight - windowBottom < 150;
                
                if (isNearBottom) {
                    // Smooth scroll to bottom
                    window.scrollTo({
                        top: docHeight,
                        behavior: 'smooth'
                    });
                }
            }
            
            // Always scroll container into view if it's not fully visible
            const rect = this.container.getBoundingClientRect();
            const isVisible = (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
            
            if (!isVisible) {
                this.container.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest',
                    inline: 'nearest'
                });
            }
        } catch (error) {
            console.warn('Auto-scroll error:', error);
        }
    }

    /**
     * Find scrollable parent element
     */
    findScrollParent(element) {
        let parent = element.parentElement;
        while (parent && parent !== document.body) {
            const style = window.getComputedStyle(parent);
            const overflowY = style.overflowY;
            const overflowX = style.overflowX;
            
            // Check if this element is scrollable
            if ((overflowY === 'auto' || overflowY === 'scroll' || overflowX === 'auto' || overflowX === 'scroll') &&
                parent.scrollHeight > parent.clientHeight) {
                return parent;
            }
            
            parent = parent.parentElement;
        }
        return null;
    }

    /**
     * Clear the container
     */
    clear() {
        this.container.innerHTML = '';
        this.buffer = '';
        this.fullText = '';
        this.currentIndex = 0;
        this.isStreaming = false;
    }
}
