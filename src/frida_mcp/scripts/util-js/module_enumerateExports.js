async function frida_Module_enumerateExports() {
    const moduleName = "{{module_name}}";

    try {
        // 使用现代Frida 17 API - Process.getModuleByName
        const module = await Process.getModuleByName(moduleName);

        // 枚举导出函数
        const exports = await module.enumerateExports();

        console.log(`[+] Found ${exports.length} exports in module: ${moduleName}`);
        console.log('='.repeat(60));

        // 使用现代for...of循环
        for (const exp of exports) {
            console.log(`Type: ${exp.type.padEnd(10)} | Name: ${exp.name.padEnd(30)} | Address: ${exp.address}`);
        }

        console.log('='.repeat(60));
        console.log(`[+] Enumeration completed for ${moduleName}`);

    } catch (error) {
        console.error(`[-] Error enumerating exports: ${error.message}`);
        console.error(`[-] Make sure the module '${moduleName}' is loaded`);
    }
}

// 使用现代Frida 17的异步执行方式
if (Java.available) {
    Java.perform(() => {
        frida_Module_enumerateExports().catch(err => {
            console.error('[-] Failed to execute enumeration:', err);
        });
    });
} else {
    // 非Android环境直接执行
    frida_Module_enumerateExports().catch(err => {
        console.error('[-] Failed to execute enumeration:', err);
    });
}