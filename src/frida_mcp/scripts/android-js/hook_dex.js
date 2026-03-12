/**
 * DEX Loading Hooks
 * Hook DexClassLoader and FART dump
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_dex.js
 * Frida 17 Compatible
 */

// Configuration
var HookDex_CONFIG = {
    hookDexClassLoader: true,
    triggerFart: true,
    logPathList: true
};

/**
 * Hook DexClassLoader
 */
function HookDex_hookClassLoader() {
    var DexClassLoader = Java.use("dalvik.system.DexClassLoader");
    
    DexClassLoader.$init.implementation = function (dexPath, optimizedDir, libraryPath, parent) {
        console.log("\n[DexClassLoader]");
        console.log("  Dex Path:     ", dexPath);
        console.log("  Optimized Dir:", optimizedDir);
        console.log("  Library Path: ", libraryPath);
        
        if (HookDex_CONFIG.logPathList) {
            try {
                var pathListField = this.getClass().getSuperclass().getSuperclass()
                    .getDeclaredField("pathList");
                pathListField.setAccessible(true);
                var pathList = pathListField.get(this);
                
                var dexPathList = Java.use("dalvik.system.DexPathList");
                var elementsField = dexPathList.class.getDeclaredField("dexElements");
                elementsField.setAccessible(true);
                var elements = elementsField.get(pathList);
                
                console.log("  Dex Elements: ", elements);
            } catch (e) {}
        }
        
        this.$init(dexPath, optimizedDir, libraryPath, parent);
        
        if (HookDex_CONFIG.triggerFart) {
            try {
                var ActivityThread = Java.use("android.app.ActivityThread");
                ActivityThread.fartwithClassloader(this);
                console.log("  [+] FART dump triggered");
            } catch (e) {}
        }
    };
    
    console.log("[+] DexClassLoader hooked");
}

/**
 * Hook PathClassLoader
 */
function HookDex_hookPathLoader() {
    try {
        var PathClassLoader = Java.use("dalvik.system.PathClassLoader");
        
        PathClassLoader.$init.overload('java.lang.String', 'java.lang.ClassLoader').implementation = function(path, parent) {
            console.log("\n[PathClassLoader]");
            console.log("  Path: ", path);
            this.$init(path, parent);
        };
        
        console.log("[+] PathClassLoader hooked");
    } catch (e) {
        console.log("[-] PathClassLoader hook failed:", e.message);
    }
}

/**
 * Hook InMemoryClassLoader
 */
function HookDex_hookMemoryLoader() {
    try {
        var InMemoryClassLoader = Java.use("dalvik.system.InMemoryClassLoader");
        
        InMemoryClassLoader.$init.implementation = function(dexBuffer, parent) {
            console.log("\n[InMemoryClassLoader]");
            console.log("  Buffer capacity:", dexBuffer.capacity());
            this.$init(dexBuffer, parent);
        };
        
        console.log("[+] InMemoryClassLoader hooked");
    } catch (e) {
        console.log("[-] InMemoryClassLoader not available (Android 8+)");
    }
}

/**
 * Main entry point
 */
function HookDex_main() {
    Java.perform(function () {
        console.log("[*] DEX Hooks Started");
        
        if (HookDex_CONFIG.hookDexClassLoader) {
            HookDex_hookClassLoader();
            HookDex_hookPathLoader();
            HookDex_hookMemoryLoader();
        }
        
        console.log("[*] DEX hooks installed");
    });
}

setImmediate(HookDex_main);
