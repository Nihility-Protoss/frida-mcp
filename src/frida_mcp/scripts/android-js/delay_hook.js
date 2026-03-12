/**
 * Delay Hook Template
 * Execute hook after SO load or time delay
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l delay_hook.js
 * Frida 17 Compatible
 */

// Configuration
var DelayHook_CONFIG = {
    targetSo: "{{target_so}}",
    delayMs: {{delay_ms}},
    targetFunction: "{{target_function}}",
    targetClass: "{{target_class}}",
    targetMethod: "{{target_method}}"
};

/**
 * Custom hook logic
 */
function DelayHook_installHooks() {
    console.log("[*] Installing custom hooks...");
    
    if (DelayHook_CONFIG.targetSo && !DelayHook_CONFIG.targetSo.includes("{{")) {
        FridaUtils.safeHook(DelayHook_CONFIG.targetSo, DelayHook_CONFIG.targetFunction, {
            onEnter: function (args) {
                console.log("[Hook]", DelayHook_CONFIG.targetFunction, "called");
            },
            onLeave: function (retval) {
                console.log("[Hook]", DelayHook_CONFIG.targetFunction, "returned:", retval);
            }
        });
    }
    
    if (DelayHook_CONFIG.targetClass && !DelayHook_CONFIG.targetClass.includes("{{")) {
        FridaUtils.hookJavaMethod(DelayHook_CONFIG.targetClass, DelayHook_CONFIG.targetMethod, null, function () {
            console.log("[Hook]", DelayHook_CONFIG.targetMethod, "called");
            return this[DelayHook_CONFIG.targetMethod].apply(this, arguments);
        });
    }
    
    // Add your custom hook logic here
    // ========================================
    
    
    
    // ========================================
}

/**
 * Main entry point
 */
function DelayHook_main() {
    if (DelayHook_CONFIG.targetSo && !DelayHook_CONFIG.targetSo.includes("{{")) {
        console.log("[*] Waiting for SO:", DelayHook_CONFIG.targetSo);
        FridaUtils.delayHookBySoLoad(DelayHook_CONFIG.targetSo, DelayHook_installHooks);
    } else {
        console.log("[*] Delaying for", DelayHook_CONFIG.delayMs, "ms");
        FridaUtils.delayHookByTime(DelayHook_installHooks, DelayHook_CONFIG.delayMs);
    }
}

setImmediate(DelayHook_main);
