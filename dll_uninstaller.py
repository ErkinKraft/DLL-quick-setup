import os
import sys
import ctypes
import shutil
import winreg
import subprocess
import time
from pathlib import Path

APP_NAME = "DllInstaller"
APP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Programs" / APP_NAME
TASK_NAME = "DllInstallerRunAsAdmin"


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


def remove_context_menu():
    key_path = r"Software\Classes\*\shell\DllInstaller"
    try:
        subprocess.run(["reg", "delete", f"HKCU\\{key_path}", "/f"],
                       capture_output=True, check=False)
    except Exception:
        pass


def remove_task():
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME],
                   capture_output=True, check=False)


def remove_files():
    if APP_DIR.exists():
        try:
            shutil.rmtree(APP_DIR, ignore_errors=True)
        except Exception:
            pass


def remove_self():
    exe = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    cmd = f'timeout /t 2 >nul & del /f /q "{exe}" & rmdir "{exe.parent}"'
    subprocess.Popen(["cmd", "/c", cmd], shell=False,
                     creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    print_animated_banner()

    relaunch_as_admin()
    print("Удаление DllInstaller...")

    remove_context_menu()
    print("Пункт контекстного меню удалён.")

    remove_task()
    print("Задача планировщика удалена (если была).")

    remove_files()
    print(f"Папка программы удалена: {APP_DIR}")

    print("Готово.")
    try:
        input("Нажмите Enter для выхода...")
    except EOFError:
        pass

    if getattr(sys, "frozen", False) and APP_DIR in Path(sys.executable).parents:
        remove_self()


if __name__ == "__main__":
    main()