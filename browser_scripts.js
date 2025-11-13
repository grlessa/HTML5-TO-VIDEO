/**
 * Browser-side JavaScript for HTML5 animation control and capture
 * 
 * These scripts are injected into the rendered HTML page to:
 * - Detect and extract background colors
 * - Apply proportional scaling with viewport forcing
 * - Trigger and control animations (CSS, CreateJS, GSAP)
 * - Enable frame-by-frame animation capture
 */

// ==============================================================================
// BACKGROUND COLOR DETECTION
// ==============================================================================

(function(global) {
    if (global.__html5VideoHelpersLoaded) {
        return;
    }
    global.__html5VideoHelpersLoaded = true;

/**
 * Extracts the predominant background color from the page.
 * Checks in order: body background, html background, first content container.
 * 
 * @returns {string} RGB color string (e.g., "rgb(0, 0, 0)")
 */
global.getPredominantBackgroundColor = function() {
    // Try body background color first
    let bodyBg = window.getComputedStyle(document.body).backgroundColor;
    if (bodyBg && bodyBg !== 'rgba(0, 0, 0, 0)' && bodyBg !== 'transparent') {
        return bodyBg;
    }

    // Try html background color
    let htmlBg = window.getComputedStyle(document.documentElement).backgroundColor;
    if (htmlBg && htmlBg !== 'rgba(0, 0, 0, 0)' && htmlBg !== 'transparent') {
        return htmlBg;
    }

    // Try first div or main content container
    let containers = document.querySelectorAll('div, main, section, #banner, .frame');
    for (let el of containers) {
        let bg = window.getComputedStyle(el).backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
            return bg;
        }
    }

    // Default to black
    return 'rgb(0, 0, 0)';
};


// ==============================================================================
// PROPORTIONAL SCALING WITH FORCED VIEWPORT
// ==============================================================================

/**
 * Applies proportional scaling to content within a forced viewport size.
 * 
 * This function:
 * 1. Forces the viewport to exact target dimensions
 * 2. Creates a wrapper for the original content
 * 3. Positions wrapper with calculated offset for centering
 * 4. Applies proportional scale transform
 * 5. Scales canvas internal buffers for sharp rendering
 * 
 * @param {number} targetWidth - Target frame width
 * @param {number} targetHeight - Target frame height
 * @param {number} sourceWidth - Original content width
 * @param {number} sourceHeight - Original content height
 * @param {number} scaleFactor - Proportional scale factor
 * @param {number} padX - Horizontal padding offset for centering
 * @param {number} padY - Vertical padding offset for centering
 * @param {string} bgColor - Background color for padding areas
 */
global.applyProportionalScaling = function(
    targetWidth,
    targetHeight,
    sourceWidth,
    sourceHeight,
    scaleFactor,
    padX,
    padY,
    bgColor
) {
    console.log('Applying proportional scaling with forced viewport centering');

    // Force viewport to exact target frame size
    document.documentElement.style.margin = '0';
    document.documentElement.style.padding = '0';
    document.documentElement.style.width = targetWidth + 'px';
    document.documentElement.style.height = targetHeight + 'px';
    document.documentElement.style.minHeight = targetHeight + 'px';
    document.documentElement.style.maxHeight = targetHeight + 'px';
    document.documentElement.style.overflow = 'hidden';
    document.documentElement.style.background = bgColor;

    // Force body to exact target frame size (critical for centering)
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.width = targetWidth + 'px';
    document.body.style.height = targetHeight + 'px';
    document.body.style.minHeight = targetHeight + 'px';
    document.body.style.maxHeight = targetHeight + 'px';
    document.body.style.overflow = 'hidden';
    document.body.style.background = bgColor;
    document.body.style.position = 'relative';  // For absolute positioning context

    // Create wrapper for scaled content
    var wrapper = document.createElement('div');
    wrapper.id = 'content-wrapper';

    // Position wrapper at calculated offset for perfect centering
    wrapper.style.position = 'absolute';
    wrapper.style.left = padX + 'px';
    wrapper.style.top = padY + 'px';
    wrapper.style.width = sourceWidth + 'px';
    wrapper.style.height = sourceHeight + 'px';

    // Apply proportional scale from top-left origin
    wrapper.style.transform = 'scale(' + scaleFactor + ')';
    wrapper.style.transformOrigin = 'top left';

    // Move all body children into wrapper
    while (document.body.firstChild) {
        wrapper.appendChild(document.body.firstChild);
    }
    document.body.appendChild(wrapper);

    // Scale canvas internal buffers for sharp rendering
    var canvases = wrapper.getElementsByTagName('canvas');
    for (var i = 0; i < canvases.length; i++) {
        var canvas = canvases[i];
        var origWidth = canvas.width;
        var origHeight = canvas.height;

        // Scale internal buffer to high resolution
        canvas.width = Math.floor(origWidth * scaleFactor);
        canvas.height = Math.floor(origHeight * scaleFactor);

        // Set CSS size to match original layout
        canvas.style.width = origWidth + 'px';
        canvas.style.height = origHeight + 'px';

        console.log('Scaled canvas buffer:', origWidth + 'x' + origHeight,
                    '→', canvas.width + 'x' + canvas.height);

        // Try to trigger redraw if available
        if (window.render) window.render();
        if (canvas.render) canvas.render();
    }

    console.log('Forced viewport centering complete');
    console.log('Viewport forced to:', targetWidth + 'x' + targetHeight);
    console.log('Wrapper position: absolute, left:' + padX + 'px, top:' + padY + 'px');
    console.log('Transform: scale(' + scaleFactor + ') from top-left');
};


// ==============================================================================
// ANIMATION TRIGGERING AND CONTROL
// ==============================================================================

/**
 * Triggers all animations and prepares them for frame-by-frame capture.
 * 
 * This function:
 * 1. Forces all CSS animations to run
 * 2. Triggers common animation start functions
 * 3. Initializes animation libraries (CreateJS, GSAP)
 * 4. Simulates user interactions (hover, click)
 * 5. Starts any embedded videos
 */
global.triggerAnimations = function() {
    console.log('Triggering animations...');

    // Force all CSS animations to run
    var style = document.createElement('style');
    style.innerHTML = `
        * {
            animation-play-state: running !important;
            animation-delay: 0s !important;
        }
    `;
    document.head.appendChild(style);

    // Simulate hover on interactive elements
    var interactiveElements = document.querySelectorAll(
        'a, button, [class*="hover"], [class*="interactive"]'
    );
    interactiveElements.forEach(function(el) {
        el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true}));
        el.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true, cancelable: true}));
    });

    // Click the body to trigger any click-based animations
    document.body.click();
    document.body.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));

    // Trigger common animation start functions
    if (typeof startAnimation === 'function') startAnimation();
    if (typeof start === 'function') start();
    if (typeof init === 'function') init();
    if (typeof play === 'function') play();
    if (typeof animate === 'function') animate();

    // CreateJS/EaselJS support (common in HTML5 ads)
    if (typeof createjs !== 'undefined' && createjs.Ticker) {
        console.log('CreateJS detected, setting up ticker');
        window.__createJSActive = true;
        if (!createjs.Ticker.hasEventListener('tick')) {
            console.log('CreateJS ticker not started, starting now');
            createjs.Ticker.framerate = 30;
            createjs.Ticker.timingMode = createjs.Ticker.RAF;
        }
    }

    // GSAP support
    if (typeof gsap !== 'undefined') {
        console.log('GSAP detected');
        window.__gsapActive = true;
    }

    // For canvas/WebGL animations
    window.animationStartTime = Date.now();
    window.animationEnabled = true;

    // Start any paused videos
    var videos = document.getElementsByTagName('video');
    for (var i = 0; i < videos.length; i++) {
        videos[i].play();
    }

    // Log canvas elements found
    var canvases = document.getElementsByTagName('canvas');
    console.log('Found ' + canvases.length + ' canvas elements');
    for (var i = 0; i < canvases.length; i++) {
        console.log('Canvas ' + i + ': ' + canvases[i].width + 'x' + canvases[i].height);
    }
};


/**
 * Pauses all CSS animations for frame-by-frame control.
 * Uses the Web Animations API to gain precise control over animation timing.
 * 
 * @returns {number} Count of animations paused
 */
global.pauseAnimationsForControl = function() {
    // Store all CSS animations using Web Animations API
    window.__animationElements = [];

    document.querySelectorAll('*').forEach(function(el) {
        var animations = el.getAnimations();
        if (animations.length > 0) {
            animations.forEach(function(anim) {
                // Pause the animation at its current state
                anim.pause();
                window.__animationElements.push(anim);
            });
        }
    });

    console.log('Paused ' + window.__animationElements.length + ' animations');

    // Store animation start time for precise control
    window.__animationStartTime = performance.now();
    
    return window.__animationElements ? window.__animationElements.length : 0;
};


/**
 * Sets all animations to a specific time for frame capture.
 * 
 * This function provides frame-perfect animation control by:
 * 1. Updating CSS animations via Web Animations API
 * 2. Controlling CreateJS timeline
 * 3. Seeking GSAP global timeline
 * 4. Updating requestAnimationFrame-based animations
 * 
 * @param {number} elapsedMs - Elapsed time in milliseconds
 */
global.setAnimationTime = function(elapsedMs) {
    var elapsedSeconds = elapsedMs / 1000.0;

    // Update all paused CSS animations to exact time
    if (window.__animationElements) {
        window.__animationElements.forEach(function(anim) {
            anim.currentTime = elapsedMs;
        });
    }

    // Update CreateJS animations (seek to specific time)
    if (typeof createjs !== 'undefined' && createjs.Ticker) {
        var tickEvent = new createjs.Event("tick");
        tickEvent.delta = 16.67; // Simulate 60fps tick
        tickEvent.time = elapsedMs;
        tickEvent.runTime = elapsedMs;
        createjs.Ticker._listeners.forEach(function(listener) {
            if (listener && listener.handleEvent) {
                listener.handleEvent(tickEvent);
            }
        });
    }

    // Update GSAP global timeline to exact time
    if (typeof gsap !== 'undefined') {
        // Seek GSAP global timeline to specific time
        if (gsap.globalTimeline) {
            gsap.globalTimeline.time(elapsedSeconds);
        }
        // Also update any explicit timelines
        if (gsap.exportRoot) {
            var root = gsap.exportRoot();
            root.time(elapsedSeconds);
        }
    }

    // Update canvas animations that use requestAnimationFrame
    if (window.animationStartTime) {
        window.animationStartTime = Date.now() - elapsedMs;
    }

    // Force reflow to ensure all changes take effect
    document.body.offsetHeight;
};


// ==============================================================================
// ANIMATION INFORMATION GATHERING
// ==============================================================================

/**
 * Gathers information about CSS animations in the page.
 * 
 * @returns {Object} Object with animation counts and details
 */
global.gatherAnimationInfo = function() {
    var info = {
        stylesheets: document.styleSheets.length,
        animations: []
    };

    // Try to find @keyframes rules
    try {
        for (var i = 0; i < document.styleSheets.length; i++) {
            var sheet = document.styleSheets[i];
            try {
                var rules = sheet.cssRules || sheet.rules;
                for (var j = 0; j < rules.length; j++) {
                    if (rules[j].type === CSSRule.KEYFRAMES_RULE) {
                        info.animations.push(rules[j].name);
};

})(typeof window !== 'undefined' ? window : this);
            } catch(e) {
                // CORS or access issues
            }
        }
    } catch(e) {}

    // Check computed styles on elements
    var elements = document.querySelectorAll('*');
    info.animated_elements = 0;
    for (var i = 0; i < elements.length; i++) {
        var style = window.getComputedStyle(elements[i]);
        if (style.animationName && style.animationName !== 'none') {
            info.animated_elements++;
        }
    }

    return info;
};

})(typeof window !== 'undefined' ? window : this);
