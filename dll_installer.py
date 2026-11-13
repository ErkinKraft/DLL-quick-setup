import os
import sys
import ctypes
import winreg
import shutil
import subprocess
import time
from pathlib import Path

APP_NAME = "DllInstaller"
APP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / APP_NAME


def print_animated_banner():
    banner = r"""
oooooooooooo oooo    oooo 
`888'     `8 `888   .8P'  
 888          888  d8'    
 888oooo8     88888[      
 888    "     888`88b.    
 888       o  888  `88b.  
o888ooooood8 o888o  o888o 
                          
                          
                          
"""
    signature = "        2009-2026 ErkinKraft"

    for line in banner.split('\n'):
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.0015)
        sys.stdout.write('\n')

    time.sleep(0.3)

    for char in signature:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.04)
    sys.stdout.write('\n\n')


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    if is_admin():
        return
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit(0)


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_tool() -> Path:
    base = get_app_dir()
    candidates = [
        base / "dll_installer_tool.exe",
        base / "dll_installer_tool.py",
        base / "dll_installer_tool" / "dll_installer_tool.exe",
    ]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).resolve().parent / "dll_installer_tool.exe")

    for c in candidates:
        if c.exists():
            return c

    tried = "\n".join(f"  - {c}" for c in candidates)
    raise FileNotFoundError(
        "Не найден dll_installer_tool.exe.\n"
        "Положите его рядом с dll_installer.exe.\n"
        f"Искали в:\n{tried}"
    )


def copy_payload() -> Path:
    src = find_tool()
    APP_DIR.mkdir(parents=True, exist_ok=True)
    dst_name = "dll_installer_tool.exe" if src.suffix == ".exe" else "dll_installer_tool.py"
    dst = APP_DIR / dst_name
    shutil.copy2(src, dst)
    return dst


def add_context_menu(exe_path: Path):
    key_path = r"Software\Classes\*\shell\DllInstaller"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Установить DLL")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, str(exe_path))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')


def register_scheduled_task(exe_path: Path):
    task_name = "DllInstallerRunAsAdmin"
    cmd = [
        "schtasks", "/Create", "/F",
        "/SC", "ONCE", "/ST", "00:00",
        "/TN", task_name,
        "/TR", f'"{exe_path}" "%1"',
        "/RL", "HIGHEST",
    ]
    subprocess.run(cmd, check=False, capture_output=True)


def main():
    print_animated_banner()

    relaunch_as_admin()
    print("Установка DllInstaller...")

    try:
        exe = copy_payload()
    except FileNotFoundError as e:
        print("[ОШИБКА]", e)
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    print(f"Скопировано в: {exe}")

    add_context_menu(exe)
    print("Пункт контекстного меню добавлен (HKCU).")

    register_scheduled_task(exe)
    print("Задача 'DllInstallerRunAsAdmin' создана (запуск от админа).")

    print("Готово.")
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()