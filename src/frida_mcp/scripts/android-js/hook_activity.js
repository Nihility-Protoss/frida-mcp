// Android Activity生命周期Hook
Java.perform(function() {
    var packageName = "{{package_name}}";
    var activityName = "{{activity_name}}";
    
    console.log("[+] Hooking Activity: " + packageName + "." + activityName);
    
    var Activity = Java.use(packageName + "." + activityName);
    
    // Hook onCreate
    Activity.onCreate.overload('android.os.Bundle').implementation = function(savedInstanceState) {
        console.log("[+] " + activityName + ".onCreate() called");
        this.onCreate(savedInstanceState);
    };
    
    // Hook onStart
    Activity.onStart.implementation = function() {
        console.log("[+] " + activityName + ".onStart() called");
        this.onStart();
    };
    
    // Hook onResume
    Activity.onResume.implementation = function() {
        console.log("[+] " + activityName + ".onResume() called");
        this.onResume();
    };
    
    // Hook onPause
    Activity.onPause.implementation = function() {
        console.log("[+] " + activityName + ".onPause() called");
        this.onPause();
    };
    
    // Hook onStop
    Activity.onStop.implementation = function() {
        console.log("[+] " + activityName + ".onStop() called");
        this.onStop();
    };
    
    // Hook onDestroy
    Activity.onDestroy.implementation = function() {
        console.log("[+] " + activityName + ".onDestroy() called");
        this.onDestroy();
    };
});