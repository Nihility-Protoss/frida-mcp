// Common utility functions
function printStackTrace() {
    Java.perform(function () {
        var Log = Java.use("android.util.Log");
        var Exception = Java.use("java.lang.Exception");
        console.log("[+] Stack trace:");
        console.log(Log.getStackTraceString(Exception.$new()));
    });
}

function bytesToHex(bytes) {
    var hex = [];
    for (var i = 0; i < bytes.length; i++) {
        hex.push((bytes[i] >>> 4).toString(16));
        hex.push((bytes[i] & 0xF).toString(16));
    }
    return hex.join('');
}

function hexToBytes(hex) {
    var bytes = [];
    for (var i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    return bytes;
}