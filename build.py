import subprocess
import sys
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TARGETS = [
    ("dll_installer_tool", "dll_installer_tool.py", True),
    ("dll_installer", "dll_installer.py", False),
    ("dll_uninstaller", "dll_uninstaller.py", False),
]


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


def run(cmd: list[str]) -> int:
    print(">>>", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def ensure_pyinstaller() -> bool:
    if shutil.which("pyinstaller"):
        return True
    print("[!] PyInstaller не найден, устанавливаю...")
    return run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]) == 0


def clean() -> None:
    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    for spec in ROOT.glob("*.spec"):
        spec.unlink(missing_ok=True)


def build(name: str, src: str, windowed: bool) -> bool:
    if not (ROOT / src).exists():
        print(f"[!] Нет файла {src}, пропускаю {name}")
        return False

    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--name", name,
        "--windowed" if windowed else "--console",
        src,
    ]
    return run(cmd) == 0


def main() -> int:
    print_animated_banner()

    print("=" * 50)
    print(" Сборка DllInstaller (без UAC-манифеста)")
    print("=" * 50)

    if not ensure_pyinstaller():
        print("[ОШИБКА] Не удалось установить PyInstaller")
        return 1

    clean()

    ok_all = True
    for i, (name, src, windowed) in enumerate(TARGETS, 1):
        print(f"\n[{i}/{len(TARGETS)}] Сборка {name}.exe ...")
        if not build(name, src, windowed):
            ok_all = False
            print(f"[ОШИБКА] {name} не собран")

    print("\n" + "=" * 50)
    if ok_all:
        print(" Готово! Файлы в dist\\")
        for f in sorted((ROOT / "dist").glob("*.exe")):
            print("  -", f.name)
        print("\nПоложите dll_installer_tool.exe рядом с dll_installer.exe.")
        return 0
    else:
        print(" Сборка завершилась с ошибками.")
        return 1


if __name__ == "__main__":
    sys.exit(main())