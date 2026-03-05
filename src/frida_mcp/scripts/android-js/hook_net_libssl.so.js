function showStacks(str_tag) {
    var Exception = Java.use("java.lang.Exception");
    var ins = Exception.$new("Exception");
    var straces = ins.getStackTrace();
 
    if (undefined == straces || null == straces) {
        return;
    }
    // var all_string = straces.toString();
    // if (all_string.indexOf('com.adjust.sdk.sig.NativeLibHelper.nSign') < 0) {
    //     return;
    // }
    console.log("=============================" + str_tag + " Stack strat=======================");
 
 
    for (var i = 0; i < straces.length; i++) {
        var str = "   " + straces[i].toString();
        console.log(str);
    }
 
    console.log("=============================" + str_tag + " Stack end=======================\r\n");
    Exception.$dispose();
}
 
function getStacksInfo() {
    var Exception = Java.use("java.lang.Exception");
    var ins = Exception.$new("Exception");
    var straces = ins.getStackTrace();
    var result = ""; // 用于存储拼接后的调用栈信息
    if (undefined == straces || null == straces) {
        return;
    }
 
    for (var i = 0; i < straces.length; i++) {
        var str = "   " + straces[i].toString();
        // console.log(str);
        result += str + "\n"; // 将每一行调用栈信息拼接到结果字符串中
    }
 
    Exception.$dispose();
    return result; // 返回拼接后的调用栈信息
}
 
function getSocketData(fd) {
    if (false) return "";
    console.log("fd:", fd);
    var socketType = Socket.type(fd)
    if (socketType != null) {
        var res = "type:" + socketType + ",loadAddress:" + JSON.stringify(Socket.localAddress(fd)) + ",peerAddress" + JSON.stringify(Socket.peerAddress(fd));
        return res;
    } else {
        return "type:" + socketType;
    }
}
 
function getSocketData2(stream) {
    var data0 = stream.this$0.value;
    var sockdata = data0.socket.value;
    return sockdata;
}
 
function bytesToHex(bytes) {
    var hexString = '';
    var arr = new Uint8Array(bytes);
    for (var i = 0; i < arr.length; i++) {
        hexString += ('0' + arr[i].toString(16)).slice(-2);
    }
    return hexString;
}
 
function getContentLength(responseHeaders) {
    // 使用正则表达式获取 Content-Length 的值
    const regex = /Content-Length:\s*(\d+)/i;
    const match = responseHeaders.match(regex);
 
    if (match && match[1]) {
        return parseInt(match[1], 10); // 转换为整数
    } else {
        return null; // 如果未找到 Content-Length，返回 null
    }
}
 
function hasTransferEncodingChunked(responseHeaders) {
    // 将响应头分成每一行
    var headers = responseHeaders.split('\r\n');
    // 遍历每一行，检查是否包含 Transfer-Encoding: chunked
    for (var i = 0; i < headers.length; i++) {
        if (headers[i].toLowerCase().startsWith('transfer-encoding:')) {
            // 检查该行是否包含 'chunked'
            return headers[i].toLowerCase().includes('chunked');
        }
    }
 
    // 如果没有找到，返回 false
    return false;
}
 
function get_content(r, size) {
    // 使用readUtf8String读取有时候会有错误，采用反射java代码
    var StringClass = Java.use('java.lang.String');
    var CharsetClass = Java.use('java.nio.charset.Charset');
    var bytes2 = r.readByteArray(size);
    // 将 byte[] 转换为 Java 字符串
    var byteArray = Java.array('byte', new Uint8Array(bytes2));
    var stringData = StringClass.$new(byteArray, CharsetClass.forName('UTF-8'));
    return stringData;
}
 
function isTargetRequest(key, myMap, tag) {
    var value = myMap.get(key);
    if (value != null) {
        return (value.indexOf(tag) >= 0);
    } else {
        return false;
    }
}
 
function print_finish_result(myMap, chunkMap, key) {
    var request_value = myMap.get(key);
    if (request_value != null) {
        console.log(key + " 请求:");
        console.log(request_value);
        console.log("\n");
        myMap.delete(key);
    }
 
    var last_content = chunkMap.get(key);
    console.log("\n" + key + " 响应:");
    console.log(last_content);
    chunkMap.delete(key);
}
 
//jni的ssl的加密数据hook
function hook_jni_ssl_enc() {
    // var writePtr = Module.getExportByName("libc.so", "write");
    // var readPtr = Module.getExportByName("libc.so", "read");
    var writePtr = Process.getModuleByName('libc.so').getExportByName('write')
    var readPtr = Process.getModuleByName('libc.so').getExportByName('read')
    console.log("write:", writePtr, ",read:", readPtr);
    Interceptor.attach(writePtr, {
        onEnter: function (args) {
            var fd = args[0];
            var buff = args[1];
            var size = args[2];
            if (size > 20) {
                var sockdata = getSocketData(fd.toInt32());
                if (sockdata.indexOf("tcp")) {
                    console.log(sockdata);
                    // console.log(hexdump(buff, { length: size.toInt32() }));
                }
            }
 
        },
        onLeave: function (retval) {
 
        }
    });
    Interceptor.attach(readPtr, {
        onEnter: function (args) {
            this.fd = args[0];
            this.buff = args[1];
            this.size = args[2];
        },
        onLeave: function (retval) {
            if (this.size > 20) {
                var sockdata = getSocketData(this.fd.toInt32());
                if (sockdata.indexOf("tcp")) {
                    console.log(sockdata);
                    // console.log(hexdump(this.buff, { length: this.size.toInt32() }));
                }
            }
 
        }
    });
}
 
//处理https请求
function hook_jni_ssl() {
 
    Java.perform(function () {
        // Process.getModuleByName('libc.so').getExportByName('recvfrom')
        var sslWritePtr = Process.getModuleByName('libssl.so').getExportByName('SSL_write')
        var sslReadPtr = Process.getModuleByName('libssl.so').getExportByName('SSL_read')
        console.log("sslWrite:", sslWritePtr, ",sslRead:", sslReadPtr);
        var sslGetFdPtr = Process.getModuleByName('libssl.so').getExportByName('SSL_get_rfd')
        var sslGetFdFunc = new NativeFunction(sslGetFdPtr, 'int', ['pointer']);
 
        // 创建一个 Map
        var myMap = new Map();
        var chunkMap = new Map();
        //int SSL_write(SSL *ssl, const void *buf, int num)
        Interceptor.attach(sslWritePtr, {
            onEnter: function (args) {
                this.sslPtr = args[0];
                this.buff = args[1];
                this.size = args[2];
            },
            onLeave: function (retval) {
                var headerInfo = ptr(this.buff).readByteArray(4);
                var hexHeaderInfo = bytesToHex(headerInfo).toLowerCase();
                // if (!hexHeaderInfo.startsWith('00000000')) {
                if (hexHeaderInfo.startsWith('504f5354')//各种请求，如POST，GET等
                    || hexHeaderInfo.startsWith('474554')
                    || hexHeaderInfo.startsWith('505554')
                    || hexHeaderInfo.startsWith('44454c455445')
                    || hexHeaderInfo.startsWith('48454144')
                    || hexHeaderInfo.startsWith('4f5054494f4e53')
                    || hexHeaderInfo.startsWith('5041544348')
                    || hexHeaderInfo.startsWith('434f4e4e454354')
                    || hexHeaderInfo.startsWith('505249')
                ) {
                    var bytes = ptr(this.buff).readByteArray(this.size.toInt32());
                    var arr = new Uint8Array(bytes);
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i] == 0x0d && arr[i + 1] == 0x0a && arr[i + 2] == 0x0d && arr[i + 3] == 0x0a) {
                            var buffer = ptr(this.buff).readUtf8String(i);
                            var content_length = getContentLength(buffer);
                            var real_len = this.size.toInt32();
                            if (content_length == null) {
                                real_len = i;
                            } else {
                                real_len = i + 4 + content_length;
                            }
                            var stringData = get_content(ptr(this.buff), real_len);
                            myMap.set(this.sslPtr.toString(), stringData);
                            console.log("请求数量:" + this.sslPtr.toString() + "=" + stringData.substring(0, stringData.indexOf('\n')))
                            break;
                        }
                    }
                }
            }
        });
 
        //int SSL_read(SSL *ssl, void *buf, int num)
        Interceptor.attach(sslReadPtr, {
            onEnter: function (args) {
                this.sslPtr = args[0];
                this.buff = args[1];
                this.size = args[2];
                // var buffer  =  ptr(args[1]).readUtf8String(args[2].toInt32());
                // console.log(buffer);
            },
            onLeave: function (retval) {
                var headerInfo = ptr(this.buff).readByteArray(4);
                var hexHeaderInfo = bytesToHex(headerInfo).toLowerCase();
 
                var fd_str = this.sslPtr.toString();
 
                // if (isTargetRequest(fd_str, myMap, "/api/interface/version1.2/customer")) {
                //     console.log(fd_str + " retval:" + retval.toInt32())
                // }
 
                if (chunkMap.get(fd_str) != null) {//处理块
                    if (retval.toInt32() > 0) {
                        var chunkedContent = get_content(ptr(this.buff), retval.toInt32());
                        var new_content = chunkMap.get(fd_str) + chunkedContent;
                        chunkMap.set(fd_str, new_content);
                        // console.log(hexdump(ptr(this.buff).add( retval.toInt32()-4), { length: 4 }));
                        if (retval.toInt32() >= 5) {
                            var bytes = ptr(this.buff).add(retval.toInt32() - 5).readByteArray(5);
                            var arr = new Uint8Array(bytes);
                            if (arr[0] == 0x30 && arr[1] == 0x0d && arr[2] == 0x0a && arr[3] == 0x0d && arr[4] == 0x0a) {
                                print_finish_result(myMap, chunkMap, fd_str);
                            }
                        } else {//正常不回出现这种情况
                            print_finish_result(myMap, chunkMap, fd_str);
                        }
 
                    } else {
                        print_finish_result(myMap, chunkMap, fd_str);
                    }
 
                }
                var head_end = 0;
                // if (!hexHeaderInfo.startsWith('00000000')) {
                if (hexHeaderInfo.startsWith('48545450')) {
 
                    var bytes = ptr(this.buff).readByteArray(this.size.toInt32());
                    var arr = new Uint8Array(bytes);
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i] == 0x0d && arr[i + 1] == 0x0a && arr[i + 2] == 0x0d && arr[i + 3] == 0x0a) {
                            head_end = i;
                            try {
                                var buffer = ptr(this.buff).readUtf8String(i);//这里使用readUtf8String ，因为已经确定了响应头不会出现乱七八糟的字符
                                console.log("响应数量:" + this.sslPtr.toString() + "=" + buffer.substring(0, buffer.indexOf('\n')))
                                var hasChunked = hasTransferEncodingChunked(buffer);
                                console.log("hasChunked = " + hasChunked + "," + this.sslPtr.toString() + " retval:", retval.toInt32());
                                // console.log(fd_str + " retval:", retval.toInt32());
                                // console.log(fd_str + " size:", this.size.toInt32());
 
                                if (hasChunked) {
                                    // console.log(hexdump(this.buff, { length: retval.toInt32() }));
                                    var stringData = get_content(ptr(this.buff), retval.toInt32());
                                    chunkMap.set(fd_str, stringData);
                                    // if (isTargetRequest(this.sslPtr.toString(), myMap, "/api/interface/version1.2/customer")) {
                                    //     console.log(this.sslPtr.toString() + ":" + stringData)
                                    //     console.log(hexdump(this.buff, { length: retval.toInt32() + 5 }));
                                    // }
                                    if (retval.toInt32() >= 5) {
                                        var end_bytes = ptr(this.buff).add(retval.toInt32() - 5).readByteArray(5);
                                        var end_arr = new Uint8Array(end_bytes);
                                        if (end_arr[0] == 0x30 && end_arr[1] == 0x0d && end_arr[2] == 0x0a && end_arr[3] == 0x0d && end_arr[4] == 0x0a) {
                                            print_finish_result(myMap, chunkMap, fd_str);
                                        } else {
                                            print_finish_result(myMap, chunkMap, fd_str);
                                        }
                                    }
                                    // console.log(hexdump(ptr(this.buff).add(retval.toInt32()-10), { length: 20 }));
                                } else {//没有分块，直接读取全部
                                    // var chunkedContent = ptr(this.buff).readUtf8String(retval.toInt32());
                                    var chunkedContent = get_content(ptr(this.buff), retval.toInt32());
                                    chunkMap.set(fd_str, stringData);
                                    print_finish_result(myMap, chunkMap, fd_str);
                                }
 
                            } catch (error) {
                                var tmp_size = this.size.toInt32();
                                if (tmp_size < 30000) {
                                    // console.log(hexdump(this.buff, { length: this.size.toInt32() }));
                                }
                                console.log("捕获到错误 retval:", retval.toInt32());
                                console.log("捕获到错误 size:", this.size.toInt32());
                                console.log("捕获到错误:", error.stack);
                                var content = ptr(this.buff).readUtf8String(head_end);
                                // console.log(hexdump(this.buff, { length: retval.toInt32() }));
                                console.log(content);
 
 
                            } finally {
                                // 可选的代码，无论是否发生异常都会执行
                            }
                            break;
                        }
                    }
                }
            }
        });
 
    });
 
 
}
 
//处理http请求
function hook_jni_tcp() {
 
    Java.perform(function () {
        // var sendtoPtr = Module.getExportByName("libc.so", "sendto");
        // var recvfromPtr = Module.getExportByName("libc.so", "recvfrom");
 
        var sendtoPtr = Process.getModuleByName('libc.so').getExportByName('sendto')
        var recvfromPtr = Process.getModuleByName('libc.so').getExportByName('recvfrom')
        console.log("sendto:", sendtoPtr, ",recvfrom:", recvfromPtr);
 
        // 创建一个 Map
        var myMap = new Map();
        var chunkMap = new Map();
        //sendto(int fd, const void *buf, size_t n, int flags, const struct sockaddr *addr, socklen_t addr_len)
        Interceptor.attach(sendtoPtr, {
            onEnter: function (args) {
                this.sslPtr = args[0];
                this.buff = args[1];
                this.size = args[2];
            },
            onLeave: function (retval) {
                var headerInfo = ptr(this.buff).readByteArray(4);
                var hexHeaderInfo = bytesToHex(headerInfo).toLowerCase();
                // if (!hexHeaderInfo.startsWith('00000000')) {
                if (hexHeaderInfo.startsWith('504f5354')
                    || hexHeaderInfo.startsWith('474554')
                    || hexHeaderInfo.startsWith('505554')
                    || hexHeaderInfo.startsWith('44454c455445')
                    || hexHeaderInfo.startsWith('48454144')
                    || hexHeaderInfo.startsWith('4f5054494f4e53')
                    || hexHeaderInfo.startsWith('5041544348')
                    || hexHeaderInfo.startsWith('434f4e4e454354')
                    || hexHeaderInfo.startsWith('505249')
                ) {
                    var bytes = ptr(this.buff).readByteArray(this.size.toInt32());
                    var arr = new Uint8Array(bytes);
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i] == 0x0d && arr[i + 1] == 0x0a && arr[i + 2] == 0x0d && arr[i + 3] == 0x0a) {
                            var buffer = ptr(this.buff).readUtf8String(i);
                            var content_length = getContentLength(buffer);
                            var real_len = this.size.toInt32();
                            if (content_length == null) {
                                real_len = i;
                            } else {
                                real_len = i + 4 + content_length;
                            }
                            var stringData = get_content(ptr(this.buff), real_len);
                            // console.log(stringData.toString());
                            myMap.set(this.sslPtr.toString(), stringData);
                            break;
                        }
                    }
                }
            }
        });
        //recvfrom(int fd, void *buf, size_t n, int flags, struct sockaddr *addr, socklen_t *addr_len)
        Interceptor.attach(recvfromPtr, {
            onEnter: function (args) {
                this.sslPtr = args[0];
                this.buff = args[1];
                this.size = args[2];
            },
            onLeave: function (retval) {
                var headerInfo = ptr(this.buff).readByteArray(4);
                var hexHeaderInfo = bytesToHex(headerInfo).toLowerCase();
 
                var fd_str = this.sslPtr.toString();
                if (chunkMap.get(fd_str) != null) {//处理块
                    if (retval.toInt32() > 0) {
                        var chunkedContent = get_content(ptr(this.buff), retval.toInt32());
                        var new_content = chunkMap.get(fd_str) + chunkedContent;
                        chunkMap.set(fd_str, new_content);
                        // console.log(hexdump(ptr(this.buff).add( retval.toInt32()-4), { length: 4 }));
                        if (retval.toInt32() >= 5) {
                            var bytes = ptr(this.buff).add(retval.toInt32() - 5).readByteArray(5);
                            var arr = new Uint8Array(bytes);
                            if (arr[0] == 0x30 && arr[1] == 0x0d && arr[2] == 0x0a && arr[3] == 0x0d && arr[4] == 0x0a) {
                                print_finish_result(myMap, chunkMap, fd_str);
                            }
                        } else {//正常不回出现这种情况
                            print_finish_result(myMap, chunkMap, fd_str);
                        }
 
                    } else {//正常不回出现这种情况
                        print_finish_result(myMap, chunkMap, fd_str);
                    }
 
                }
                var head_end = 0;
                // if (!hexHeaderInfo.startsWith('00000000')) {
                if (hexHeaderInfo.startsWith('48545450')) {
                    var bytes = ptr(this.buff).readByteArray(this.size.toInt32());
                    var arr = new Uint8Array(bytes);
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i] == 0x0d && arr[i + 1] == 0x0a && arr[i + 2] == 0x0d && arr[i + 3] == 0x0a) {
                            head_end = i;
                            try {
                                var buffer = ptr(this.buff).readUtf8String(i);//这里使用readUtf8String ，因为已经确定了响应头不会出现乱七八糟的字符
 
                                var hasChunked = hasTransferEncodingChunked(buffer);
                                console.log("hasChunked = ", hasChunked);
                                // console.log(fd_str + " retval:", retval.toInt32());
                                // console.log(fd_str + " size:", this.size.toInt32());
 
                                if (hasChunked) {
                                    var stringData = get_content(ptr(this.buff), retval.toInt32());
                                    chunkMap.set(fd_str, stringData);
                                    if (retval.toInt32() >= 5) {
                                        var end_bytes = ptr(this.buff).add(retval.toInt32() - 5).readByteArray(5);
                                        var end_arr = new Uint8Array(end_bytes);
                                        if (end_arr[0] == 0x30 && end_arr[1] == 0x0d && end_arr[2] == 0x0a && end_arr[3] == 0x0d && end_arr[4] == 0x0a) {
                                            print_finish_result(myMap, chunkMap, fd_str);
                                        }
                                    } else {//正常不回出现这种情况
                                        print_finish_result(myMap, chunkMap, fd_str);
                                    }
                                    // console.log(hexdump(ptr(this.buff).add(retval.toInt32()-10), { length: 20 }));
                                } else {
                                    var chunkedContent = get_content(ptr(this.buff), retval.toInt32());
                                    chunkMap.set(fd_str, chunkedContent);
                                    print_finish_result(myMap, chunkMap, fd_str);
                                }
 
                            } catch (error) {
                                var tmp_size = this.size.toInt32();
                                if (tmp_size < 30000) {
                                    // console.log(hexdump(this.buff, { length: this.size.toInt32() }));
                                }
                                console.log("捕获到错误 retval:", retval.toInt32());
                                console.log("捕获到错误 size:", this.size.toInt32());
                                console.log("捕获到错误:", error.stack);
                                var content = ptr(this.buff).readUtf8String(head_end);
                                // console.log(hexdump(this.buff, { length: retval.toInt32() }));
                                console.log(content);
 
 
                            } finally {
                                // 可选的代码，无论是否发生异常都会执行
                            }
                            break;
                        }
                    }
                }
            }
        });
    });
 
}
 
 
function hook_java_net() {
    hook_jni_ssl();
    hook_jni_tcp();
    // hook_jni_ssl_enc();
}
 
setImmediate(hook_java_net);