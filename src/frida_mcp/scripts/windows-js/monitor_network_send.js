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
const wininetSessions = new Map();      // hInternet -> {agent, accessType, proxy, bypass, flags}
const winhttpHeaderStore = new Map();   // hRequest -> [headerLine, ...]
const wininetHeaderStore = new Map();   // hRequest -> [headerLine, ...]

const ENABLE_SOCKET_FALLBACK_LOG = false;

function parseAcceptTypes(ppAcceptTypes) {
    return readWideStringList(ppAcceptTypes, 32);
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

function logRequestHeadersOnly(tag, meta, requestHead) {
    const head = requestHead && requestHead.length > 0 ? requestHead : "[no headers captured]";
    const filename = makeHeadersDumpFilename(meta || {});
    // Keep dump file content clean: headers only, no log-style prefix.
    const payloadText = `${head}\n`;
    const bytes = stringToUtf8Bytes(payloadText);
    send({
        type: "headers_dump",
        filename: filename,
        pid: Process.id,
        api: String((meta && meta.api) || "UNKNOWN"),
        destination: buildDestination(meta || {}),
        timestamp: Date.now()
    }, bytes.buffer);
    console.log(`[NET][${tag}] REQUEST headers_dump=${filename}`);
}

function logSocketSummary(tag, meta) {
    if (!ENABLE_SOCKET_FALLBACK_LOG) return;
    console.log(`[NET][${tag}] SOCKET meta=${JSON.stringify(meta || {})}`);
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

function makeHeadersDumpFilename(meta) {
    const api = sanitizeFileToken((meta && meta.api) || "UNKNOWN");
    const destination = sanitizeFileToken(buildDestination(meta || {}));
    const ts = Date.now();
    return `${api}_${destination}_${ts}.txt`;
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
        if (ok) {
            wininetSessions.set(hInternet.toString(), info);
        }
        console.log(`[NET][WININET] InternetOpenA => handle=${formatHandle(hInternet)} ok=${ok} info=${JSON.stringify(info)}`);
    });
}

function monitorHttpSendRequestA() {
    monitorApi("wininet.dll", "HttpSendRequestA", function (args) {
        const hRequest = safeArg(args, 0);
        const headersPtr = safeArg(args, 1);
        const headersLen = safeToUInt32(safeArg(args, 2));
        const reqKey = hRequest ? hRequest.toString() : "";
        const extraHeaders = readAnsiByLength(headersPtr, headersLen);
        appendHeaderLines(wininetHeaderStore, reqKey, extraHeaders);

        this._httpSendReq = {
            hRequest,
            reqKey,
            headers: extraHeaders
        };
    }, function (retval) {
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
        console.log(`[NET][WINHTTP] WinHttpOpen => handle=${formatHandle(hSession)} ok=${ok} info=${JSON.stringify(info)}`);
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
        console.log(`[NET][WINHTTP] WinHttpConnect => handle=${formatHandle(hConnect)} ok=${ok} host=${info.host || ""} port=${info.port || 0}`);
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
        console.log(`[NET][WINHTTP] WinHttpOpenRequest => handle=${formatHandle(hRequest)} ok=${ok} method=${info.method || ""} path=${info.path || ""}`);
    });
}

function monitorWinHttpSendRequest() {
    monitorApi("winhttp.dll", "WinHttpSendRequest", function (args) {
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
    }, function (retval) {
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
    monitorHttpAddRequestHeadersA();
    monitorHttpSendRequestA();
    monitorWinHttpOpen();
    monitorWinHttpConnect();
    monitorWinHttpOpenRequest();
    monitorWinHttpAddRequestHeaders();
    monitorWinHttpSendRequest();
    console.log("[+] [NET] Network API monitor initialized");
}

monitorNetworkApis();
