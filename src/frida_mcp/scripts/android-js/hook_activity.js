/**
 * Activity Lifecycle Hook
 * Hook Android Activity lifecycle methods
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_activity.js
 * Frida 17 Compatible
 */

// Configuration
var HookActivity_CONFIG = {
    packageName: "{{package_name}}",
    activityName: "{{activity_name}}"
};

/**
 * Hook Activity lifecycle methods
 */
function HookActivity_lifecycle() {
    var fullClassName = HookActivity_CONFIG.packageName + "." + HookActivity_CONFIG.activityName;
    console.log("[*] Hooking Activity:", fullClassName);
    
    try {
        var Activity = Java.use(fullClassName);
        
        Activity.onCreate.overload('android.os.Bundle').implementation = function(savedInstanceState) {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onCreate() called");
            FridaUtils.showStacks("onCreate");
            this.onCreate(savedInstanceState);
        };
        
        Activity.onStart.implementation = function() {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onStart() called");
            this.onStart();
        };
        
        Activity.onResume.implementation = function() {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onResume() called");
            this.onResume();
        };
        
        Activity.onPause.implementation = function() {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onPause() called");
            this.onPause();
        };
        
        Activity.onStop.implementation = function() {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onStop() called");
            this.onStop();
        };
        
        Activity.onDestroy.implementation = function() {
            console.log("[Activity] " + HookActivity_CONFIG.activityName + ".onDestroy() called");
            this.onDestroy();
        };
        
        console.log("[+] Activity lifecycle hooks installed");
    } catch (e) {
        console.log("[-] Failed to hook Activity:", e.message);
    }
}

/**
 * Main entry point
 */
function HookActivity_main() {
    Java.perform(function() {
        console.log("[*] Activity Hook Started");
        HookActivity_lifecycle();
    });
}

setImmediate(HookActivity_main);
