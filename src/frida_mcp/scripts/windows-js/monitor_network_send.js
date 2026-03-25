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

function logRequestPacket(tag, meta, headers, bodyBytes) {
    const bodyText = bytesToText(bodyBytes);
    const metaStr = JSON.stringify(meta || {});
    const oneLineSummary = `[NET][${tag}] REQUEST meta=${metaStr} body_len=${bodyBytes.length}`;
    const oneLinePayload = `headers=${JSON.stringify(headers || "")} body_text=${JSON.stringify(bodyText)}`;
    console.log(`${oneLineSummary}\n${oneLinePayload}`);
}

function monitorSend() {
    monitorApi("ws2_32.dll", "send", function (args) {
        const sock = safeArg(args, 0);
        const buf = safeArg(args, 1);
        const len = safeToUInt32(safeArg(args, 2));
        const flags = safeToUInt32(safeArg(args, 3));
        const payload = readBytesSafe(buf, len);
        this._netSendInfo = {sock, len, flags, payload};
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
        logRequestPacket("WS2_32", meta, "", info.payload || new Uint8Array(0));
    });
}

function monitorWSASend() {
    monitorApi("ws2_32.dll", "WSASend", function (args) {
        const sock = safeArg(args, 0);
        const lpBuffers = safeArg(args, 1);
        const bufCount = safeToUInt32(safeArg(args, 2));
        const lpNumberOfBytesSent = safeArg(args, 3);
        const flags = safeToUInt32(safeArg(args, 4));

        const chunks = [];
        const stride = Process.pointerSize === 8 ? 16 : 8;
        let firstBufPtr = ptr(0);

        for (let i = 0; i < bufCount; i++) {
            try {
                const wsabuf = lpBuffers.add(i * stride);
                // WSABUF (official):
                //   ULONG len;
                //   CHAR *buf;
                // x86: [len:4][buf:4]
                // x64: [len:4][pad:4][buf:8]
                let chunkLen = Memory.readU32(wsabuf);
                let chunkPtr = Memory.readPointer(wsabuf.add(Process.pointerSize === 8 ? 8 : 4));
                // Fallback for non-standard packing
                if ((!chunkPtr || chunkPtr.isNull()) && Process.pointerSize === 8) {
                    chunkPtr = Memory.readPointer(wsabuf.add(4));
                }
                const chunk = readBytesSafe(chunkPtr, chunkLen);
                if (i === 0) firstBufPtr = chunkPtr || ptr(0);
                chunks.push(chunk);
            } catch (e) {
                // ignore bad entries
            }
        }

        let total = 0;
        for (const c of chunks) total += c.length;
        const merged = new Uint8Array(total);
        let off = 0;
        for (const c of chunks) {
            merged.set(c, off);
            off += c.length;
        }

        this._wsaSendInfo = {sock, bufCount, flags, payload: merged, firstBufPtr, lpNumberOfBytesSent};
    }, function (retval) {
        const status = retval ? retval.toInt32() : -1;
        const info = this._wsaSendInfo || {};
        let payload = info.payload || new Uint8Array(0);
        let bytesSent = 0;
        try {
            if (info.lpNumberOfBytesSent && !info.lpNumberOfBytesSent.isNull()) {
                bytesSent = Memory.readU32(info.lpNumberOfBytesSent);
            }
        } catch (e) {
            bytesSent = 0;
        }
        // Fallback: if WSABUF parse returns empty but API reports sent bytes, read from first buffer.
        if (payload.length === 0 && bytesSent > 0 && info.firstBufPtr && !info.firstBufPtr.isNull()) {
            payload = readBytesSafe(info.firstBufPtr, bytesSent);
        }
        const meta = {
            api: "WSASend",
            socket: formatHandle(info.sock),
            buffer_count: info.bufCount || 0,
            status,
            flags: info.flags || 0,
            bytes_sent: bytesSent
        };
        logRequestPacket("WS2_32", meta, "", payload);
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
        const bodyPtr = safeArg(args, 3);
        const bodyLen = safeToUInt32(safeArg(args, 4));

        this._httpSendReq = {
            hRequest,
            headers: readAnsiByLength(headersPtr, headersLen),
            payload: readBytesSafe(bodyPtr, bodyLen)
        };
    }, function (retval) {
        const ok = retval && retval.toInt32() !== 0;
        const info = this._httpSendReq || {};
        const meta = {
            api: "HttpSendRequestA",
            handle: formatHandle(info.hRequest),
            result: ok
        };
        logRequestPacket("WININET", meta, info.headers || "", info.payload || new Uint8Array(0));
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
        const bodyPtr = safeArg(args, 3);
        const bodyLen = safeToUInt32(safeArg(args, 4));

        this._winHttpSendReq = {
            hRequest,
            headers: readWideByLength(headersPtr, headersLen),
            payload: readBytesSafe(bodyPtr, bodyLen)
        };
    }, function (retval) {
        const ok = retval && retval.toInt32() !== 0;
        const info = this._winHttpSendReq || {};
        const reqKey = info.hRequest ? info.hRequest.toString() : "";
        const ctx = getWinHttpRequestContext(reqKey);

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

        logRequestPacket("WINHTTP", meta, info.headers || "", info.payload || new Uint8Array(0));
    });
}

function monitorNetworkApis() {
    monitorSend();
    monitorWSASend();
    monitorInternetOpenA();
    monitorHttpSendRequestA();
    monitorWinHttpOpen();
    monitorWinHttpConnect();
    monitorWinHttpOpenRequest();
    monitorWinHttpSendRequest();
    console.log("[+] [NET] Network API monitor initialized");
}

monitorNetworkApis();
