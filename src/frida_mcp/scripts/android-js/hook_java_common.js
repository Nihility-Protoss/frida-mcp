/**
 * Common Java Layer Hooks
 * Hook common Java classes: Map, StringBuilder, Base64, Dialog, Toast
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_java_common.js
 * Frida 17 Compatible
 */

// Configuration
var HookJava_CONFIG = {
    hookMap: true,
    mapTargetKey: "{{target_key}}",
    hookStringBuilder: true,
    hookBase64: true,
    hookDialog: true,
    hookToast: true,
    hookSnackbar: true
};

/**
 * Hook Map operations
 */
function HookJava_mapOperations() {
    try {
        var TreeMap = Java.use('java.util.TreeMap');
        TreeMap.put.implementation = function (key, value) {
            if (!HookJava_CONFIG.mapTargetKey.includes("{{")) {
                if (key == HookJava_CONFIG.mapTargetKey) {
                    console.log("[Map.put] Key=" + key + ", Value=" + value);
                    FridaUtils.showStacks("Map.put");
                }
            } else {
                console.log("[Map.put] Key=" + key + ", Value=" + value);
            }
            return this.put(key, value);
        };
        console.log("[+] TreeMap.put hooked");
    } catch (e) {
        console.log("[-] TreeMap hook failed:", e.message);
    }
    
    try {
        var HashMap = Java.use('java.util.HashMap');
        HashMap.put.implementation = function (key, value) {
            if (!HookJava_CONFIG.mapTargetKey.includes("{{")) {
                if (key == HookJava_CONFIG.mapTargetKey) {
                    console.log("[HashMap.put] Key=" + key + ", Value=" + value);
                }
            }
            return this.put(key, value);
        };
        console.log("[+] HashMap.put hooked");
    } catch (e) {}
}

/**
 * Hook StringBuilder
 */
function HookJava_stringBuilder() {
    try {
        var StringBuilder = Java.use("java.lang.StringBuilder");
        StringBuilder.toString.implementation = function () {
            var result = this.toString();
            if (result.length > 0) {
                console.log("[StringBuilder] Result:", result.substring(0, 200));
            }
            return result;
        };
        console.log("[+] StringBuilder.toString hooked");
    } catch (e) {
        console.log("[-] StringBuilder hook failed:", e.message);
    }
    
    try {
        var StringBuffer = Java.use("java.lang.StringBuffer");
        StringBuffer.toString.implementation = function () {
            var result = this.toString();
            if (result.length > 0) {
                console.log("[StringBuffer] Result:", result.substring(0, 200));
            }
            return result;
        };
        console.log("[+] StringBuffer.toString hooked");
    } catch (e) {}
}

/**
 * Hook Base64
 */
function HookJava_base64() {
    try {
        var Base64 = Java.use("android.util.Base64");
        
        Base64.encodeToString.overload('[B', 'int').implementation = function (data, flags) {
            var result = this.encodeToString(data, flags);
            console.log("[Base64] Encoded:", result.substring(0, 100));
            return result;
        };
        console.log("[+] Base64.encodeToString hooked");
    } catch (e) {
        console.log("[-] Base64 hook failed:", e.message);
    }
}

/**
 * Hook Dialog
 */
function HookJava_dialog() {
    try {
        var AlertDialogBuilder = Java.use("android.app.AlertDialog$Builder");
        AlertDialogBuilder.show.implementation = function () {
            console.log("\n[AlertDialog.show]");
            FridaUtils.showStacks("AlertDialog.show");
            return this.show.apply(this, arguments);
        };
        console.log("[+] AlertDialog.Builder.show hooked");
    } catch (e) {}
    
    try {
        var Dialog = Java.use("android.app.Dialog");
        Dialog.show.implementation = function () {
            var className = this.getClass().getName();
            if (!className.startsWith("android.") && !className.startsWith("com.android.")) {
                console.log("\n[Dialog.show] Class:", className);
                FridaUtils.showStacks("Dialog.show: " + className);
            }
            return this.show.apply(this, arguments);
        };
        console.log("[+] Dialog.show hooked");
    } catch (e) {}
}

/**
 * Hook Toast
 */
function HookJava_toast() {
    try {
        var Toast = Java.use("android.widget.Toast");
        
        Toast.show.implementation = function () {
            try {
                var text = this.getText() ? this.getText().toString() : "N/A";
                console.log("\n[Toast] Content:", text);
                FridaUtils.showStacks("Toast.show");
            } catch (e) {}
            return this.show.apply(this, arguments);
        };
        console.log("[+] Toast.show hooked");
    } catch (e) {}
}

/**
 * Hook Snackbar
 */
function HookJava_snackbar() {
    try {
        var Snackbar = Java.use("com.google.android.material.snackbar.Snackbar");
        Snackbar.show.implementation = function () {
            console.log("\n[Snackbar.show]");
            FridaUtils.showStacks("Snackbar.show");
            return this.show.apply(this, arguments);
        };
        console.log("[+] Snackbar.show hooked");
    } catch (e) {
        console.log("[-] Snackbar not available (Material Components not used)");
    }
}

/**
 * Main entry point
 */
function HookJava_main() {
    Java.perform(function () {
        console.log("[*] Common Java Hooks Started");
        
        if (HookJava_CONFIG.hookMap) {
            HookJava_mapOperations();
        }
        
        if (HookJava_CONFIG.hookStringBuilder) {
            HookJava_stringBuilder();
        }
        
        if (HookJava_CONFIG.hookBase64) {
            HookJava_base64();
        }
        
        if (HookJava_CONFIG.hookDialog) {
            HookJava_dialog();
        }
        
        if (HookJava_CONFIG.hookToast) {
            HookJava_toast();
        }
        
        if (HookJava_CONFIG.hookSnackbar) {
            HookJava_snackbar();
        }
        
        console.log("[*] All Java hooks installed");
    });
}

setImmediate(HookJava_main);
