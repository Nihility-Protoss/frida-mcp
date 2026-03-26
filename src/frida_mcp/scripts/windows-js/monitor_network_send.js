// Windows network API monitor
// Depends on helpers from windows_base_utils.js:
//   - monitorApi
//   - safeArg
//   - safeReadString
//   - safeToUInt32
//   - formatHandle

const winhttpSessions = new Map();      // hSession -> {agent, accessType, proxy, bypass, flags}
const winhttpConnections = new Map();   // hConnect -> {session, host, port}
const winhttpRequests = new Map();      // hRequest -> {connect, method, path, version, referrer, acceptTypes, flags}
const winhttpHeaderStore = new Map();   // hRequest -> [headerLine, ...]
const wininetHeaderStore = new Map();   // hRequest -> [headerLine, ...]
const highLevelCallDepth = new Map();   // tid -> depth

const ENABLE_SOCKET_FALLBACK_LOG = true;

function parseAcceptTypes(ppAcceptTypes) {
    return readWideStringList(ppAcceptTypes, 32);
}

// Mark current thread as being in a high-level HTTP call chain.
function enterHighLevelNetworkCall() {
    const tid = Process.getCurrentThreadId();
    const depth = highLevelCallDepth.get(tid) || 0;
    highLevelCallDepth.set(tid, depth + 1);
}

// Leave high-level HTTP call chain for current thread.
function leaveHighLevelNetworkCall() {
    const tid = Process.getCurrentThreadId();
    const depth = highLevelCallDepth.get(tid) || 0;
    if (depth <= 1) highLevelCallDepth.delete(tid);
    else highLevelCallDepth.set(tid, depth - 1);
}

// Suppress ws2_32 fallback logs when current call stack already has WinINet/WinHTTP context.
function shouldSuppressSocketFallback() {
    const tid = Process.getCurrentThreadId();
    return (highLevelCallDepth.get(tid) || 0) > 0;
}

function getWinHttpRequestContext(hRequest) {
    const req = winhttpRequests.get(hRequest);
    if (!req) return {};
    const conn = winhttpConnections.get(req.connect) || {};
    const session = winhttpSessions.get(conn.session) || {};
    return {
        method: req.method || "",
        path: req.path || "",
        version: req.version || "",
        referrer: req.referrer || "",
        acceptTypes: req.acceptTypes || [],
        host: conn.host || "",
        port: conn.port || 0,
        agent: session.agent || ""
    };
}

function normalizeHeaderLines(rawHeaders) {
    if (!rawHeaders) return [];
    return String(rawHeaders)
        .split(/\r?\n/)
        .map(function (s) { return s.trim(); })
        .filter(function (s) { return s.length > 0; });
}

function appendHeaderLines(store, key, rawHeaders) {
    if (!key) return;
    const lines = normalizeHeaderLines(rawHeaders);
    if (lines.length === 0) return;
    const prev = store.get(key) || [];
    store.set(key, prev.concat(lines));
}

function dedupeHeaderLines(lines) {
    const out = [];
    const seen = new Set();
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const k = line.toLowerCase();
        if (seen.has(k)) continue;
        seen.add(k);
        out.push(line);
    }
    return out;
}

function buildRequestHead(method, path, version, host, agent, headersText) {
    const ver = version && version.length > 0 ? version : "HTTP/1.1";
    const p = path && path.length > 0 ? path : "/";
    const startLine = `${method || "GET"} ${p} ${ver}`;
    const lines = normalizeHeaderLines(headersText);
    if (host) {
        const hasHost = lines.some(function (x) { return x.toLowerCase().startsWith("host:"); });
        if (!hasHost) lines.unshift(`Host: ${host}`);
    }
    if (agent) {
        const hasUA = lines.some(function (x) { return x.toLowerCase().startsWith("user-agent:"); });
        if (!hasUA) lines.unshift(`User-Agent: ${agent}`);
    }
    const merged = dedupeHeaderLines(lines);
    return `${startLine}\n${merged.join("\n")}`;
}

function extractHeaderValue(requestHead, headerName) {
    if (!requestHead) return "";
    const target = `${String(headerName || "").toLowerCase()}:`;
    const lines = String(requestHead).split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
        const raw = lines[i] || "";
        const line = raw.trim();
        if (line.toLowerCase().startsWith(target)) {
            return line.slice(target.length).trim();
        }
    }
    return "";
}

function buildHeadersDumpContent(meta, requestHead) {
    const m = meta || {};
    const connectHost = String(m.host || "");
    const connectPort = Number(m.port || 0);
    const connectDst = connectHost && connectPort ? `${connectHost}:${connectPort}` : (connectHost || "unknown");
    const hostHeader = extractHeaderValue(requestHead, "Host");
    const mismatch = Boolean(connectHost && hostHeader && connectHost.toLowerCase() !== hostHeader.toLowerCase());
    const method = String(m.method || "");
    const path = String(m.path || "");

    // Keep a compact analysis prelude in file; no extra console noise.
    return [
        `# api=${String(m.api || "UNKNOWN")}`,
        `# dst=${connectDst}`,
        `# host_header=${hostHeader || "unknown"}`,
        `# host_mismatch=${mismatch}`,
        `# request_line=${method} ${path}`.trim(),
        "",
        String(requestHead || "[no headers captured]"),
        ""
    ].join("\n");
}

function compactInfoForLog(obj) {
    const src = obj || {};
    const out = {};
    const keys = Object.keys(src);
    for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        const v = src[k];
        if (v === null || v === undefined) continue;
        if (typeof v === "string" && v.trim() === "") continue;
        if (Array.isArray(v) && v.length === 0) continue;
        if (typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0) continue;
        out[k] = v;
    }
    return out;
}

function hasMeaningfulParsedUrl(parsed) {
    if (!parsed) return false;
    const keys = Object.keys(parsed);
    for (let i = 0; i < keys.length; i++) {
        const v = parsed[keys[i]];
        if (v === null || v === undefined) continue;
        if (typeof v === "string" && v.trim() === "") continue;
        if (typeof v === "number" && v === 0) continue;
        return true;
    }
    return false;
}

function resultArrow(ok) {
    return ok ? "✔=>" : "X=>";
}

function logRequestHeadersOnly(tag, meta, requestHead) {
    const head = requestHead && requestHead.length > 0 ? requestHead : "[no headers captured]";
    const ts = Date.now();
    const filename = makeHeadersDumpFilename(meta || {}, ts, head);
    const payloadText = buildHeadersDumpContent(meta || {}, head);
    const bytes = stringToUtf8Bytes(payloadText);
    send({
        type: "headers_dump",
        filename: filename,
        pid: Process.id,
        api: String((meta && meta.api) || "UNKNOWN"),
        destination: buildDestination(meta || {}),
        timestamp: ts
    }, bytes.buffer);
    console.log(`[${tag}] REQUEST headers_dump=${filename}`);
}

function logSocketSummary(tag, meta) {
    if (!ENABLE_SOCKET_FALLBACK_LOG) return;
    if (shouldSuppressSocketFallback()) return;
    console.log(`[${tag}] SOCKET meta=${JSON.stringify(meta || {})}`);
}

function getUrlComponentsLayout() {
    // URL_COMPONENTS layout for Windows default packing.
    // x86:
    //   dwStructSize(0) lpszScheme(4) dwSchemeLength(8) nScheme(12) ...
    // x64:
    //   dwStructSize(0) pad(4) lpszScheme(8) dwSchemeLength(16) nScheme(20) ...
    const p = Process.pointerSize;
    if (p === 8) {
        return {
            schemePtr: 8, schemeLen: 16,
            hostPtr: 24, hostLen: 32, port: 36,
            userPtr: 40, userLen: 48,
            passPtr: 56, passLen: 64,
            pathPtr: 72, pathLen: 80,
            extraPtr: 88, extraLen: 96
        };
    }
    return {
        schemePtr: 4, schemeLen: 8,
        hostPtr: 16, hostLen: 20, port: 24,
        userPtr: 28, userLen: 32,
        passPtr: 36, passLen: 40,
        pathPtr: 44, pathLen: 48,
        extraPtr: 52, extraLen: 56
    };
}

// Parse URL_COMPONENTS from WinINet/WinHTTP URL cracking APIs.
function parseUrlComponents(urlComponentsPtr, isWide) {
    if (!urlComponentsPtr || urlComponentsPtr.isNull()) return {};
    try {
        const o = getUrlComponentsLayout();
        const readByLen = isWide ? readWideByLength : readAnsiByLength;
        const schemePtr = Memory.readPointer(urlComponentsPtr.add(o.schemePtr));
        const schemeLen = Memory.readU32(urlComponentsPtr.add(o.schemeLen));
        const hostPtr = Memory.readPointer(urlComponentsPtr.add(o.hostPtr));
        const hostLen = Memory.readU32(urlComponentsPtr.add(o.hostLen));
        const port = Memory.readU32(urlComponentsPtr.add(o.port));
        const userPtr = Memory.readPointer(urlComponentsPtr.add(o.userPtr));
        const userLen = Memory.readU32(urlComponentsPtr.add(o.userLen));
        const passPtr = Memory.readPointer(urlComponentsPtr.add(o.passPtr));
        const passLen = Memory.readU32(urlComponentsPtr.add(o.passLen));
        const pathPtr = Memory.readPointer(urlComponentsPtr.add(o.pathPtr));
        const pathLen = Memory.readU32(urlComponentsPtr.add(o.pathLen));
        const extraPtr = Memory.readPointer(urlComponentsPtr.add(o.extraPtr));
        const extraLen = Memory.readU32(urlComponentsPtr.add(o.extraLen));
        return {
            scheme: readByLen(schemePtr, schemeLen),
            host: readByLen(hostPtr, hostLen),
            port: port >>> 0,
            username: readByLen(userPtr, userLen),
            password: readByLen(passPtr, passLen),
            path: readByLen(pathPtr, pathLen),
            extra: readByLen(extraPtr, extraLen)
        };
    } catch (e) {
        return {};
    }
}

function sanitizeFileToken(value) {
    if (!value) return "unknown";
    return String(value).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function buildDestination(meta) {
    if (!meta) return "unknown";
    const host = meta.host || "";
    const port = meta.port || 0;
    if (host && port) return `${host}_${port}`;
    if (host) return String(host);
    if (meta.handle) return String(meta.handle);
    return "unknown";
}

function makeHeadersDumpFilename(meta, ts, requestHead) {
    const api = sanitizeFileToken((meta && meta.api) || "UNKNOWN");
    const destination = sanitizeFileToken(buildDestination(meta || {}));
    const hostHeader = sanitizeFileToken(extractHeaderValue(requestHead, "Host") || "unknown");
    return `${api}_${destination}_host_${hostHeader}_${ts}.txt`;
}

function stringToUtf8Bytes(text) {
    const s = String(text || "");
    try {
        if (typeof TextEncoder !== "undefined") {
            return new TextEncoder().encode(s);
        }
    } catch (e) {
        // fallback below
    }
    // Frida-safe fallback without TextEncoder.
    const encoded = unescape(encodeURIComponent(s));
    const out = new Uint8Array(encoded.length);
    for (let i = 0; i < encoded.length; i++) {
        out[i] = encoded.charCodeAt(i);
    }
    return out;
}

function monitorSend() {
    monitorApi("ws2_32.dll", "send", function (args) {
        const sock = safeArg(args, 0);
        const buf = safeArg(args, 1);
        const len = safeToUInt32(safeArg(args, 2));
        const flags = safeToUInt32(safeArg(args, 3));
        this._netSendInfo = {sock, len, flags};
    }, function (retval) {
        const sent = retval ? retval.toInt32() : -1;
        const info = this._netSendInfo || {};
        const meta = {
            api: "send",
            socket: formatHandle(info.sock),
            requested_len: info.len || 0,
            sent_len: sent,
            flags: info.flags || 0
        };
        logSocketSummary("WS2_32", meta);
    });
}

function monitorWSASend() {
    monitorApi("ws2_32.dll", "WSASend", function (args) {
        const sock = safeArg(args, 0);
        const lpBuffers = safeArg(args, 1);
        const bufCount = safeToUInt32(safeArg(args, 2));
        const lpNumberOfBytesSent = safeArg(args, 3);
        const flags = safeToUInt32(safeArg(args, 4));

        this._wsaSendInfo = {sock, bufCount, flags, lpNumberOfBytesSent};
    }, function (retval) {
        const status = retval ? retval.toInt32() : -1;
        const info = this._wsaSendInfo || {};
        let bytesSent = 0;
        try {
            if (info.lpNumberOfBytesSent && !info.lpNumberOfBytesSent.isNull()) {
                bytesSent = Memory.readU32(info.lpNumberOfBytesSent);
            }
        } catch (e) {
            bytesSent = 0;
        }
        const meta = {
            api: "WSASend",
            socket: formatHandle(info.sock),
            buffer_count: info.bufCount || 0,
            status,
            flags: info.flags || 0,
            bytes_sent: bytesSent
        };
        logSocketSummary("WS2_32", meta);
    });
}

function monitorInternetOpenA() {
    monitorApi("wininet.dll", "InternetOpenA", function (args) {
        this._internetOpen = {
            agent: safeReadString(safeArg(args, 0), false),
            accessType: safeToUInt32(safeArg(args, 1)),
            proxy: safeReadString(safeArg(args, 2), false),
            proxyBypass: safeReadString(safeArg(args, 3), false),
            flags: safeToUInt32(safeArg(args, 4))
        };
    }, function (retval) {
        const hInternet = retval;
        const ok = hInternet && !hInternet.isNull();
        const info = this._internetOpen || {};
        console.log(`[WININET] InternetOpenA => handle=${formatHandle(hInternet)} ok=${ok} info=${JSON.stringify(info)}`);
    });
}

// Capture request headers from WinINet high-level API.
// Uses thread-depth guard so nested ws2_32 logs can be suppressed in same call chain.
function monitorHttpSendRequestA() {
    monitorApi("wininet.dll", "HttpSendRequestA", function (args) {
        enterHighLevelNetworkCall();
        try {
            const hRequest = safeArg(args, 0);
            const headersPtr = safeArg(args, 1);
            const headersLen = safeToUInt32(safeArg(args, 2));
            const reqKey = hRequest ? hRequest.toString() : "";
            const extraHeaders = readAnsiByLength(headersPtr, headersLen);
            appendHeaderLines(wininetHeaderStore, reqKey, extraHeaders);

            this._httpSendReq = {
                hRequest,
                reqKey
            };
        } catch (e) {
            // Ensure depth is not leaked when onEnter parsing fails.
            leaveHighLevelNetworkCall();
            throw e;
        }
    }, function (retval) {
        try {
            const ok = retval && retval.toInt32() !== 0;
            const info = this._httpSendReq || {};
            const lines = dedupeHeaderLines(wininetHeaderStore.get(info.reqKey || "") || []);
            const requestHead = lines.join("\n");
            const meta = {
                api: "HttpSendRequestA",
                handle: formatHandle(info.hRequest),
                result: ok
            };
            logRequestHeadersOnly("WININET", meta, requestHead);
        } finally {
            leaveHighLevelNetworkCall();
        }
    });
}

function monitorHttpAddRequestHeadersA() {
    monitorApi("wininet.dll", "HttpAddRequestHeadersA", function (args) {
        const hRequest = safeArg(args, 0);
        const reqKey = hRequest ? hRequest.toString() : "";
        const headers = readAnsiByLength(safeArg(args, 1), safeToUInt32(safeArg(args, 2)));
        this._httpAddHeaders = { reqKey, headers };
    }, function (retval) {
        const ok = retval && retval.toInt32() !== 0;
        const info = this._httpAddHeaders || {};
        if (ok) appendHeaderLines(wininetHeaderStore, info.reqKey || "", info.headers || "");
    });
}

function monitorWinHttpOpen() {
    monitorApi("winhttp.dll", "WinHttpOpen", function (args) {
        this._winHttpOpen = {
            agent: safeReadString(safeArg(args, 0), true),
            accessType: safeToUInt32(safeArg(args, 1)),
            proxy: safeReadString(safeArg(args, 2), true),
            proxyBypass: safeReadString(safeArg(args, 3), true),
            flags: safeToUInt32(safeArg(args, 4))
        };
    }, function (retval) {
        const hSession = retval;
        const ok = hSession && !hSession.isNull();
        const info = this._winHttpOpen || {};
        if (ok) {
            winhttpSessions.set(hSession.toString(), info);
        }
        const compactInfo = compactInfoForLog(info);
        console.log(`[WINHTTP] WinHttpOpen ${resultArrow(ok)} info=${JSON.stringify(compactInfo)}`);
    });
}

function monitorWinHttpConnect() {
    monitorApi("winhttp.dll", "WinHttpConnect", function (args) {
        this._winHttpConnect = {
            session: safeArg(args, 0),
            host: safeReadString(safeArg(args, 1), true),
            port: safeToUInt32(safeArg(args, 2))
        };
    }, function (retval) {
        const hConnect = retval;
        const ok = hConnect && !hConnect.isNull();
        const info = this._winHttpConnect || {};
        if (ok) {
            winhttpConnections.set(hConnect.toString(), {
                session: info.session ? info.session.toString() : "",
                host: info.host || "",
                port: info.port || 0
            });
        }
        console.log(`[WINHTTP] WinHttpConnect ${resultArrow(ok)} host=${info.host || ""} port=${info.port || 0}`);
    });
}

function monitorWinHttpOpenRequest() {
    monitorApi("winhttp.dll", "WinHttpOpenRequest", function (args) {
        this._winHttpOpenReq = {
            connect: safeArg(args, 0),
            method: safeReadString(safeArg(args, 1), true),
            path: safeReadString(safeArg(args, 2), true),
            version: safeReadString(safeArg(args, 3), true),
            referrer: safeReadString(safeArg(args, 4), true),
            acceptTypes: parseAcceptTypes(safeArg(args, 5)),
            flags: safeToUInt32(safeArg(args, 6))
        };
    }, function (retval) {
        const hRequest = retval;
        const ok = hRequest && !hRequest.isNull();
        const info = this._winHttpOpenReq || {};
        if (ok) {
            winhttpRequests.set(hRequest.toString(), {
                connect: info.connect ? info.connect.toString() : "",
                method: info.method || "",
                path: info.path || "",
                version: info.version || "",
                referrer: info.referrer || "",
                acceptTypes: info.acceptTypes || [],
                flags: info.flags || 0
            });
        }
        console.log(`[WINHTTP] WinHttpOpenRequest ${resultArrow(ok)} method=${info.method || ""} path=${info.path || ""}`);
    });
}

function monitorWinHttpSendRequest() {
    monitorApi("winhttp.dll", "WinHttpSendRequest", function (args) {
        enterHighLevelNetworkCall();
        try {
            const hRequest = safeArg(args, 0);
            const headersPtr = safeArg(args, 1);
            const headersLen = safeToUInt32(safeArg(args, 2));
            const reqKey = hRequest ? hRequest.toString() : "";
            const extraHeaders = readWideByLength(headersPtr, headersLen);
            appendHeaderLines(winhttpHeaderStore, reqKey, extraHeaders);

            this._winHttpSendReq = {
                hRequest,
                reqKey
            };
        } catch (e) {
            // Ensure depth is not leaked when onEnter parsing fails.
            leaveHighLevelNetworkCall();
            throw e;
        }
    }, function (retval) {
        try {
            const ok = retval && retval.toInt32() !== 0;
            const info = this._winHttpSendReq || {};
            const reqKey = info.hRequest ? info.hRequest.toString() : "";
            const ctx = getWinHttpRequestContext(reqKey);
            const stored = winhttpHeaderStore.get(info.reqKey || "") || [];
            const mergedHeaders = dedupeHeaderLines(stored).join("\n");
            const requestHead = buildRequestHead(
                ctx.method || "GET",
                ctx.path || "/",
                ctx.version || "HTTP/1.1",
                ctx.host || "",
                ctx.agent || "",
                mergedHeaders
            );

            const meta = {
                api: "WinHttpSendRequest",
                handle: formatHandle(info.hRequest),
                result: ok,
                host: ctx.host || "",
                port: ctx.port || 0,
                method: ctx.method || "",
                path: ctx.path || "",
                version: ctx.version || "",
                referrer: ctx.referrer || "",
                acceptTypes: ctx.acceptTypes || [],
                agent: ctx.agent || ""
            };

            logRequestHeadersOnly("WINHTTP", meta, requestHead);
        } finally {
            leaveHighLevelNetworkCall();
        }
    });
}

// Shared hook builder for URL parsing APIs.
function monitorCrackUrl(moduleName, apiName, isWide, tag) {
    monitorApi(moduleName, apiName, function (args) {
        const urlPtr = safeArg(args, 0);
        const urlLen = safeToUInt32(safeArg(args, 1));
        this._crackInfo = {
            url: isWide ? readWideByLength(urlPtr, urlLen) : readAnsiByLength(urlPtr, urlLen),
            compPtr: safeArg(args, 3)
        };
    }, function (retval) {
        const ok = retval && retval.toInt32() !== 0;
        const info = this._crackInfo || {};
        const parsed = ok ? parseUrlComponents(info.compPtr, isWide) : {};
        if (!ok) return;
        if ((!info.url || String(info.url).trim() === "") && !hasMeaningfulParsedUrl(parsed)) return;
        // Avoid leaking clear-text credentials in logs.
        if (parsed && parsed.password) parsed.password = "***";
        console.log(`[${tag}] ${apiName} ${resultArrow(ok)} url=${JSON.stringify(info.url || "")} parsed=${JSON.stringify(parsed)}`);
    });
}

function monitorWinHttpAddRequestHeaders() {
    monitorApi("winhttp.dll", "WinHttpAddRequestHeaders", function (args) {
        const hRequest = safeArg(args, 0);
        const reqKey = hRequest ? hRequest.toString() : "";
        const headers = readWideByLength(safeArg(args, 1), safeToUInt32(safeArg(args, 2)));
        this._winHttpAddHeaders = { reqKey, headers };
    }, function (retval) {
        const ok = retval && retval.toInt32() !== 0;
        const info = this._winHttpAddHeaders || {};
        if (ok) appendHeaderLines(winhttpHeaderStore, info.reqKey || "", info.headers || "");
    });
}

function monitorNetworkApis() {
    monitorSend();
    monitorWSASend();
    monitorInternetOpenA();
    monitorCrackUrl("wininet.dll", "InternetCrackUrlA", false, "WININET");
    monitorCrackUrl("wininet.dll", "InternetCrackUrlW", true, "WININET");
    monitorHttpAddRequestHeadersA();
    monitorHttpSendRequestA();
    monitorWinHttpOpen();
    monitorWinHttpConnect();
    monitorWinHttpOpenRequest();
    monitorCrackUrl("winhttp.dll", "WinHttpCrackUrl", true, "WINHTTP");
    monitorWinHttpAddRequestHeaders();
    monitorWinHttpSendRequest();
    console.log("[+] [NET] Network API monitor initialized");
}

monitorNetworkApis();
