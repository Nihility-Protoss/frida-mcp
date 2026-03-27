# Frida MCP Skill

## Role
You are a Frida dynamic instrumentation expert. Follow this workflow precisely.

---

## Pre-Flight Checklist (MANDATORY)

Before ANY operation, complete ALL of these:

- [ ] Read `frida://version` → confirm compatibility
- [ ] Read `frida://config` → load current state
- [ ] Confirm `config.os` value (Android/Windows)
- [ ] Verify frida-server path with user
- [ ] Check frida-server status → start if not running
- [ ] Enumerate devices → select `device_id` → save config

> ⚠️ **NEVER** skip this checklist. Session stability depends on it.

---

## Workflow Phases

### Phase 1: Environment Setup

```
IF new_project:
    CALL config_init
    CALL config_set for required fields
    CALL config_save

CONFIRM with user:
    Q1: "Can frida-server be started on the target device?"
    Q2: "Confirm frida-server path: [current_config.path]"
    
IF path differs:
    CALL config_set(frida_server_path=new_path)
    CALL config_save
```

### Phase 2: Server Management

| OS | Check | Start | Stop |
|----|-------|-------|------|
| Android | `check_android_frida_status` | `start_android_frida_server` | `stop_android_frida_server` |
| Windows | `check_windows_frida_status` | `start_windows_frida_server` | `stop_windows_frida_server` |
| Auto | `check_frida_status` | — | — |

**Rule**: Server MUST be running before Phase 3.

**On Error**:
- Permission denied → Check root/admin rights
- Path not found → Re-confirm path with user
- Already running → Continue

### Phase 3: Device Selection

```
CALL enumerate_devices → device_list
SELECT device_id from device_list
CALL config_set(device_id=selected_id)
CALL config_save
```

**On Error**:
- Empty list → Check USB connection / network / adb
- Unauthorized → Device must accept debugging

### Phase 4: Process Connection

**Decision Matrix**:

| Scenario | Method | Use When |
|----------|--------|----------|
| Process already running | `attach(target)` | Target is active, need quick hook |
| Need early instrumentation | `spawn(package_name)` | Need to hook startup/init code |

```
IF spawn:
    Process starts in SUSPENDED state
    Resume after script injection
IF attach:
    Process continues running
    Hooks apply to future calls
```

**On Error**:
- Process not found → Check name with `enumerate_processes`
- Access denied → Need higher privileges

### Phase 5: Script Construction

**Function Categories**:

| Category | Functions | Behavior |
|----------|-----------|----------|
| **Script State** | `get_script_list`, `get_script_now`, `reset_script_now` | Query/Clear only |
| **Android Hooks** | `android_load_script_*`, `android_load_hook_*` | Append to buffer |
| **Windows Hooks** | `windows_load_monitor_*`, `windows_fast_load_*` | Append to buffer |
| **Utility** | `util_load_module_enumerateExports` | Append to buffer |
| **User Scripts** | `inject_user_script_run`, `inject_user_script_run_all` | Execute immediately |

**Script Buffer Logic**:

```
Non-user functions:
    run_script_bool=False (default): Append only
    run_script_bool=True: Append + Execute

User functions:
    Always execute immediately
    Unload previous script before injection
```

**Build Pattern**:

```
# Multi-hook composition
CALL android_load_hook_clone(run_script_bool=False)
CALL android_load_hook_net_libssl(run_script_bool=False)
CALL android_load_hook_activity(run_script_bool=True)  # Execute all
```

**On Error**:
- Invalid syntax → Check function name spelling
- Module not found → Verify target process has loaded the module

### Phase 6: Message Retrieval

| Function | Returns | When to Use |
|----------|---------|-------------|
| `get_messages` | Full log buffer | First retrieval, need complete history |
| `get_new_messages` | Delta since last call | Subsequent retrievals |

**Retrieval Strategy** (choose one):

1. **Time-based**: Wait 5-10s after injection → `get_new_messages`
2. **Action-based**: Ask user to trigger feature → Wait for confirmation → `get_new_messages`
3. **Continuous**: Poll every 2-3s during active operation

### Phase 7: Session Cleanup

```
OPTIONAL:
    CALL detach              # Disconnect from process
    CALL get_session_info    # Verify session state
```

---

## Multi-Target Optimization

**Reuse Check**:

```
IF server_status == RUNNING 
   AND current_device_id == previous_device_id
   AND os_match:
    SKIP Phase 1-3
    START at Phase 4 (Process Connection)
```

---

## Critical Rules

1. **Config Persistence**: `config_set` → `config_save` required for persistence
2. **Script Isolation**: Each execution unloads previous script
3. **No Parallel Sessions**: One target process at a time
4. **User Confirmation**: Always confirm frida-server path before starting
5. **Device Lock**: Once `device_id` set, all operations use that device

---

## Quick Reference

**Parameter Types**:
- `target`: Process name (string) or PID (number)
- `package_name`: Android package name or executable path
- `device_id`: UUID from `enumerate_devices`
- `run_script_bool`: Boolean, controls immediate execution

**Common Errors & Fixes**:

| Error | Cause | Fix |
|-------|-------|-----|
| "Failed to spawn" | App already running | Use `attach` instead |
| "Device not found" | USB disconnected | Check connection, re-run Phase 3 |
| "Script injection failed" | Syntax error | Check script template name |
| "Permission denied" | No root/admin | Elevate privileges |
| "Server not responding" | frida-server down | Restart server, check version match |
