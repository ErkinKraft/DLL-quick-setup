import os
import sys
import ctypes
import struct
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path


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


def get_pe_machine(path: Path) -> str:
    try:
        with open(path, "rb") as f:
            if f.read(2) != b"MZ":
                return "unknown"
            f.seek(0x3C)
            pe_off = struct.unpack("<I", f.read(4))[0]
            f.seek(pe_off)
            if f.read(4) != b"PE\0\0":
                return "unknown"
            machine = struct.unpack("<H", f.read(2))[0]
            return {0x14c: "x86", 0x8664: "x64"}.get(machine, "unknown")
    except Exception:
        return "unknown"


def install_dll(src: Path) -> tuple[bool, str]:
    windir = Path(os.environ["WINDIR"])
    sys32 = windir / "System32"
    syswow = windir / "SysWOW64"

    machine = get_pe_machine(src)
    msgs = []

    if machine == "x64":
        targets = [sys32]
    elif machine == "x86":
        targets = [syswow] if syswow.exists() else [sys32]
    else:
        targets = [sys32] + ([syswow] if syswow.exists() else [])

    copied_any = False
    for tgt in targets:
        try:
            dst = tgt / src.name
 
            if dst.exists():
                subprocess.run(["takeown", "/F", str(dst)], capture_output=True, check=False)
                subprocess.run(["icacls", str(dst), "/grant", "administrators:F"],
                               capture_output=True, check=False)
            import shutil
            shutil.copy2(src, dst)
            copied_any = True
            msgs.append(f"Скопировано: {dst} ({machine})")
        except Exception as e:
            msgs.append(f"ОШИБКА копирования в {tgt}: {e}")

    if not copied_any:
        return False, "\n".join(msgs)


    reg_target = (syswow / src.name) if (machine == "x86" and syswow.exists()) else (sys32 / src.name)
    reg_msg = ""
    try:
        r = subprocess.run(
            ["regsvr32", "/s", str(reg_target)],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            reg_msg = "DLL установлена и зарегистрирована."
        else:
            reg_msg = ("DLL установлена, но не зарегистрирована "
                       "(DllRegisterServer вернул ошибку или отсутствует - "
                       "возможно, регистрация не требуется).")
    except Exception as e:
        reg_msg = f"DLL установлена, регистрация не выполнена: {e}"

    return True, "\n".join(msgs) + "\n\n" + reg_msg


def show_result(ok: bool, text: str, title: str):
    root = tk.Tk()
    root.withdraw()
    if ok:
        messagebox.showinfo(title, text)
    else:
        messagebox.showerror(title, text)
    root.destroy()


def find_dll_arg() -> Path | None:

    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.suffix.lower() == ".dll" and p.exists():
            return p
    return None

def main():
    relaunch_as_admin()

    src = find_dll_arg()

    if src is None:
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Выберите DLL для установки",
            filetypes=[("DLL files", "*.dll")]
        )
        root.destroy()
        
        if not file_path:
            sys.exit(0)
        src = Path(file_path)

    ok, msg = install_dll(src)
    show_result(ok, msg, "DllInstaller")

if __name__ == "__main__":
    main()