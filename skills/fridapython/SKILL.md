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

## 5. Execution Phase

Only after:

-   Version read
-   Config loaded/initialized
-   Frida server verified
-   Device selected and saved

The AI may proceed with:

-   Process enumeration
-   Process attachment
-   Script injection
-   Custom Frida functionality

(Details to be extended.)

------------------------------------------------------------------------

## Operational Principles

-   Strictly follow ordered workflow.
-   Never skip initialization.
-   Never execute Frida operations without verified server state.
-   Persist configuration changes before execution.
