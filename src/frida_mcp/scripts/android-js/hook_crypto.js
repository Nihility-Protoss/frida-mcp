/**
 * Crypto Hooks
 * Hook encryption/decryption operations
 * 
 * Dependencies: android_base_utils.js
 * Usage: frida -Uf com.package.name -l android_base_utils.js -l hook_crypto.js
 * Frida 17 Compatible
 */

// Configuration
var HookCrypto_CONFIG = {
    hookCipher: true,
    hookMessageDigest: true
};

/**
 * Hook Cipher class
 */
function HookCrypto_hookCipher() {
    var Cipher = Java.use("javax.crypto.Cipher");
    
    try {
        var IvParameterSpec = Java.use("javax.crypto.spec.IvParameterSpec");
        
        Cipher.init.overload('int', 'java.security.Key', 'java.security.spec.AlgorithmParameterSpec')
            .implementation = function (mode, key, iv) {
                console.log("\n[Cipher.init]");
                console.log("  Mode:", mode, "(1=Encrypt, 2=Decrypt)");
                
                try {
                    var keyBytes = key.getEncoded();
                    console.log("  Key (hex):", FridaUtils.bytesToHex(keyBytes));
                } catch (e) {}
                
                try {
                    var ivObj = Java.cast(iv, IvParameterSpec);
                    var ivBytes = ivObj.getIV();
                    console.log("  IV (hex):", FridaUtils.bytesToHex(ivBytes));
                } catch (e) {}
                
                this.init(mode, key, iv);
            };
        console.log("[+] Cipher.init hooked");
    } catch (e) {
        console.log("[-] Cipher.init hook failed:", e.message);
    }
    
    try {
        Cipher.doFinal.overload('[B').implementation = function (data) {
            console.log("\n[Cipher.doFinal]");
            try {
                console.log("  Input (hex):", FridaUtils.bytesToHex(data));
                console.log("  Input (UTF8):", Java.use("java.lang.String").$new(data));
            } catch (e) {}
            
            var result = this.doFinal(data);
            console.log("  Output (hex):", FridaUtils.bytesToHex(result));
            return result;
        };
        console.log("[+] Cipher.doFinal hooked");
    } catch (e) {
        console.log("[-] Cipher.doFinal hook failed:", e.message);
    }
}

/**
 * Hook MessageDigest class
 */
function HookCrypto_hookMessageDigest() {
    var MessageDigest = Java.use("java.security.MessageDigest");
    
    try {
        MessageDigest.digest.overload('[B').implementation = function (input) {
            console.log("\n[MessageDigest.digest]");
            console.log("  Algorithm:", this.getAlgorithm());
            try {
                console.log("  Input (UTF8):", Java.use("java.lang.String").$new(input));
            } catch (e) {}
            console.log("  Input (hex):", FridaUtils.bytesToHex(input));
            
            var result = this.digest(input);
            console.log("  Output (hex):", FridaUtils.bytesToHex(result));
            return result;
        };
        console.log("[+] MessageDigest.digest hooked");
    } catch (e) {
        console.log("[-] MessageDigest hook failed:", e.message);
    }
    
    try {
        MessageDigest.update.overload('[B').implementation = function (input) {
            console.log("\n[MessageDigest.update]");
            console.log("  Algorithm:", this.getAlgorithm());
            try {
                console.log("  Input (UTF8):", Java.use("java.lang.String").$new(input));
            } catch (e) {}
            
            this.update(input);
        };
        console.log("[+] MessageDigest.update hooked");
    } catch (e) {
        console.log("[-] MessageDigest.update hook failed:", e.message);
    }
}

/**
 * Main entry point
 */
function HookCrypto_main() {
    Java.perform(function () {
        console.log("[*] Crypto Hooks Started");
        
        if (HookCrypto_CONFIG.hookCipher) {
            HookCrypto_hookCipher();
        }
        
        if (HookCrypto_CONFIG.hookMessageDigest) {
            HookCrypto_hookMessageDigest();
        }
        
        console.log("[*] Crypto hooks installed");
    });
}

setImmediate(HookCrypto_main);
