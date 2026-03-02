# Frida MCP 技能规范

## 目标

本技能定义与 Frida MCP 交互时必须遵循的操作流程。\
AI 必须按照顺序执行，以保证行为稳定、可预测。

------------------------------------------------------------------------

## 1. 初始化（强制）

在每次会话开始时，AI 必须读取：

-   `frida://version`
-   `frida://config`

目的：

-   确认 MCP 版本兼容性
-   加载当前配置状态
-   确定操作系统与运行环境

在读取完成之前，不得执行任何 Frida 操作。

------------------------------------------------------------------------

## 2. 配置管理

### 2.1 新项目初始化

每个新的 Frida 项目开始时，AI 应当：

1.  调用 `config_init` 创建项目配置文件
2.  使用 `config_set` 设置所需参数
3.  在批量修改后调用 `config_save` 将内存配置写入文件

### 2.2 配置规则

-   所有与环境相关的参数必须写入 config
-   `config_set` 仅修改内存中的配置
-   必须调用 `config_save` 才能持久化

------------------------------------------------------------------------

## 3. Frida Server 管理（前置条件）

在执行任何 Frida 功能前，必须确认对应平台的 frida-server 已正确运行。

### Android（需 `config.os=Android`）

-   `start_android_frida_server`
-   `stop_android_frida_server`
-   `check_android_frida_status`

### Windows（需 `config.os=Windows`）

-   `start_windows_frida_server`
-   `stop_windows_frida_server`
-   `check_windows_frida_status`

### 跨平台

-   `check_frida_status`（根据 config.os 自动判断）

AI 必须：

1.  从 config 读取当前 OS
2.  检查 server 状态
3.  若未运行则启动

------------------------------------------------------------------------

## 4. 设备发现

AI 必须通过与用户交互确定目标设备。

步骤：

1.  调用 `enumerate_devices`
2.  确认目标 `device_id`
3.  使用 `config_set` 写入 device_id
4.  使用 `config_save` 持久化

后续所有操作必须基于已配置的 device_id。

------------------------------------------------------------------------

## 5. 执行阶段

仅在以下步骤完成后：

-   读取 version
-   加载/初始化 config
-   验证 frida-server 状态
-   设备选择并保存

才可以执行：

-   进程枚举
-   进程附加
-   脚本注入
-   自定义 Frida 功能

（细节后续完善）

------------------------------------------------------------------------

## 操作原则

-   严格按顺序执行
-   不得跳过初始化
-   未验证 server 状态不得执行
-   执行前必须持久化配置
