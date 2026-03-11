# Frida MCP Skill Specification

## Purpose

This skill defines the required operational workflow for interacting
with the Frida MCP implementation.\
The AI MUST follow the defined sequence to ensure deterministic and
stable behavior.

------------------------------------------------------------------------

## 1. Initialization (MANDATORY)

At the beginning of every session, the AI MUST read:

-   `frida://version`
-   `frida://config`

These resources are required to:

-   Confirm MCP version compatibility
-   Load current configuration state
-   Determine operating system and execution context

No Frida operation should begin before both resources are read.

------------------------------------------------------------------------

## 2. Configuration Management

### 2.1 New Project Initialization

For every new Frida project, the AI SHOULD:

1.  Call `config_init` to create a project-specific configuration.
2.  Use `config_set` to modify required fields.
3.  After bulk updates, call `config_save` to persist configuration to
    disk.

### 2.2 Configuration Rules

-   All environment-dependent parameters MUST be stored in config.
-   `config_set` modifies in-memory config only.
-   `config_save` MUST be called to persist changes.

------------------------------------------------------------------------

## 3. Frida Server Management (Precondition)

Before executing any Frida functionality, the AI MUST ensure the correct
frida-server is running.

### Android (requires `config.os=Android`)

-   `start_android_frida_server`
-   `stop_android_frida_server`
-   `check_android_frida_status`

### Windows (requires `config.os=Windows`)

-   `start_windows_frida_server`
-   `stop_windows_frida_server`
-   `check_windows_frida_status`

### Cross-Platform

-   `check_frida_status` (auto-detect based on config.os)

The AI MUST:

1.  Verify current OS from config.
2.  Check server status.
3.  Start server if not running.

------------------------------------------------------------------------

## 4. Device Discovery

The AI MUST interact with the user to identify the target device.

Steps:

1.  Call `enumerate_devices`
2.  Determine correct `device_id`
3.  Store device_id using `config_set`
4.  Persist using `config_save`

All subsequent operations MUST use the configured device_id.

------------------------------------------------------------------------

## 5. Target Process Control

Before script injection the AI MUST connect to or start the target process.

Two possible methods exist:

- `attach(target: str)` – attach to a running process
- `spawn(package_name: str)` – start the target process in suspended state

Parameters:

- `target`: running process name
- `package_name`: package or executable name

Script injection is only allowed after one of these calls succeeds.

------------------------------------------------------------------------

## 6. Script Construction and Injection

After attaching to the process the AI may construct the script to be injected.

### Script Management

- `get_script_list`
- `get_script_now`
- `reset_script_now`
- `inject_user_script_run`
- `inject_user_script_run_all`

### Android Script Tools

- `android_load_script_anti_DexHelper_hook_clone`
- `android_load_script_anti_DexHelper_hook_pthread`
- `android_load_script_anti_DexHelper`
- `android_load_hook_net_libssl`
- `android_load_hook_clone`
- `android_load_hook_activity`

### General Script Tools

- `util_load_module_enumerateExports`

### Windows Script Tools

- `windows_load_monitor_api`
- `windows_load_monitor_registry`
- `windows_load_monitor_file`
- `windows_fast_load_all_monitor_file`
- `windows_fast_load_monitor_memory_alloc`

### Script Execution Behavior

All script tool functions (except the two user injection functions) include:

`run_script_bool: bool = False`

Meaning:

- `False` → only append the script to the current injector script
- `True` → append and immediately execute

Special behavior:

- `inject_user_script_run`
- `inject_user_script_run_all`

These functions execute immediately and do not use `run_script_bool`.

### Script Composition Rules

- Multiple script tool calls concatenate into **the current injector script**
- Executing a script will:
  1. unload previously injected scripts
  2. inject the newly constructed script
  3. execute it immediately

------------------------------------------------------------------------

# 7. Message and Log Handling

After script injection, runtime output must be retrieved using:

- get_messages
- get_new_messages

Definitions:

get_messages  
Returns the full global log buffer snapshot.

get_new_messages  
Returns only messages produced since the last retrieval.

The AI must determine when to retrieve logs:

Possible strategies:

- Wait an appropriate amount of time for hooks to trigger
- Ask the user to perform actions in the target application
- Wait until the user confirms the action is finished

Only then fetch logs to obtain hook results.

------------------------------------------------------------------------

# 8. Session Management

At the end of a single task, the AI may call:

- detach
- get_session_info

Purpose:

- Safely terminate the session
- Check if a session is still active

------------------------------------------------------------------------

# 9. Multi-Target Workflow

After finishing work on one program:

If steps 1-4 remain unchanged, the AI may start directly from:

Step 5 (Process Connection)

This allows efficient processing of multiple targets using the same environment.

------------------------------------------------------------------------

## Operational Principles

-   Strictly follow ordered workflow.
-   Never skip initialization.
-   Never execute Frida operations without verified server state.
-   Persist configuration changes before execution.
