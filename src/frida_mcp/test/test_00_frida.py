# Baseline Test @test

import frida

target = "1"
device_id = "local"

device = frida.get_device(device_id)


def main():
    # Determine PID
    if target.isdigit():
        pid = int(target)
        app_name = target
        print(pid)
    else:
        applications = device.enumerate_applications()
        target_app = None

        for app in applications:
            if app.identifier == target and app.pid and app.pid > 0:
                target_app = app
                break

        if not target_app:
            print({
                "status": "error",
                "message": f"Unable to find running app: {target}"
            })


def test_func():
    applications = device.enumerate_applications()
    for app in applications:
        print(app.pid, app.identifier)


if __name__ == '__main__':
    test_func()
