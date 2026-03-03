// Android SSL证书固定绕过
Java.perform(function() {
    console.log("[+] Loading SSL Pinning Bypass...");
    
    try {
        // 绕过OkHttp证书固定
        var OkHttpClient = Java.use('okhttp3.OkHttpClient');
        var Builder = Java.use('okhttp3.OkHttpClient$Builder');
        
        Builder.build.implementation = function() {
            console.log("[+] Bypassing OkHttp certificate pinning");
            return this.build();
        };
    } catch (e) {
        console.log("[-] OkHttp not found: " + e);
    }
    
    try {
        // 绕过TrustManager
        var TrustManager = Java.use('javax.net.ssl.TrustManager');
        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        
        // 创建信任所有证书的TrustManager
        var X509TrustManager = Java.registerClass({
            name: 'com.frida.TrustAllManager',
            implements: [Java.use('javax.net.ssl.X509TrustManager')],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        
        var trustAllManager = X509TrustManager.$new();
        var sslContext = SSLContext.getInstance("TLS");
        sslContext.init(null, [trustAllManager], null);
        
        console.log("[+] SSL Pinning bypassed");
    } catch (e) {
        console.log("[-] SSL bypass failed: " + e);
    }
    
    try {
        // 绕过HostnameVerifier
        var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
        var StrictHostnameVerifier = Java.use('org.apache.http.conn.ssl.StrictHostnameVerifier');
        
        StrictHostnameVerifier.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function(hostname, session) {
            console.log("[+] Bypassing hostname verification for: " + hostname);
            return true;
        };
    } catch (e) {
        console.log("[-] HostnameVerifier bypass failed: " + e);
    }
});