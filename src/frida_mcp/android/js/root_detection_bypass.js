// Android Root检测绕过
Java.perform(function() {
    console.log("[+] Loading Root Detection Bypass...");
    
    // 绕过Root检测 - 检查su文件
    var File = Java.use('java.io.File');
    File.exists.implementation = function() {
        var path = this.getPath();
        var rootPaths = ['/sbin/su', '/system/bin/su', '/system/xbin/su', 
                        '/data/local/xbin/su', '/data/local/bin/su', 
                        '/system/sd/xbin/su', '/system/bin/failsafe/su',
                        '/data/local/su'];
        
        if (rootPaths.includes(path)) {
            console.log("[+] Bypassing root check for: " + path);
            return false;
        }
        return this.exists();
    };
    
    // 绕过Root检测 - Build.TAGS检查
    var Build = Java.use('android.os.Build');
    var originalTags = Build.TAGS.value;
    Build.TAGS.value = 'release-keys';
    console.log("[+] Build.TAGS set to: release-keys");
    
    // 绕过Root检测 - 检查test-keys
    var String = Java.use('java.lang.String');
    String.contains.implementation = function(s) {
        if (s === 'test-keys') {
            console.log("[+] Bypassing test-keys check");
            return false;
        }
        return this.contains(s);
    };
    
    // 绕过RootBeer检测
    try {
        var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
        RootBeer.isRooted.implementation = function() {
            console.log("[+] Bypassing RootBeer detection");
            return false;
        };
    } catch (e) {
        console.log("[-] RootBeer not found: " + e);
    }
    
    // 绕过SafetyNet
    try {
        var SafetyNet = Java.use('com.google.android.gms.safetynet.SafetyNet');
        SafetyNet.attest.implementation = function(nonce, apiKey) {
            console.log("[+] Bypassing SafetyNet attest");
            return null;
        };
    } catch (e) {
        console.log("[-] SafetyNet not found: " + e);
    }
});