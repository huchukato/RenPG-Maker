"""Gestione download, estrazione e build dell'SDK Ren'Py."""

import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path

RENPV_VERSION = "8.5.3"
BASE_URL = "https://www.renpy.org/dl/{version}"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sdk_dir() -> Path:
    """Cartella dove risiede (o verrà scaricato) l'SDK Ren'Py."""
    return _project_root() / "renpy-sdk"


def version_file() -> Path:
    return sdk_dir() / "version.txt"


def is_sdk_present() -> bool:
    """True se l'SDK è presente e alla versione attesa."""
    vf = version_file()
    if not sdk_dir().is_dir() or not vf.exists():
        return False
    return vf.read_text(encoding="utf-8").strip() == RENPV_VERSION


def _archive_name() -> str:
    if platform.system() == "Windows":
        return f"renpy-{RENPV_VERSION}-sdk.zip"
    return f"renpy-{RENPV_VERSION}-sdk.tar.bz2"


def _archive_url() -> str:
    return f"{BASE_URL.format(version=RENPV_VERSION)}/{_archive_name()}"


def _download_file(url: str, dest: Path, progress_callback=None):
    """Scarica un file da url salvandolo in dest, opzionalmente invocando progress_callback(bytes, total)."""
    req = urllib.request.Request(url, headers={"User-Agent": "RenPGMaker"})
    with urllib.request.urlopen(req, timeout=30) as response:
        total = int(response.headers.get("Content-Length", 0))
        block = 8192
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(block)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    progress_callback(downloaded, total)


def _extract(archive: Path, dest: Path):
    """Estrae un archivio .zip o .tar.bz2 in dest."""
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(dest)
    else:
        with tarfile.open(archive, "r:bz2") as tf:
            tf.extractall(dest)


def _flatten_extracted_dir(dest: Path):
    """Se l'estrazione ha creato una sottocartella tipo renpy-8.5.3-sdk, sposta il contenuto su dest."""
    inner = dest / f"renpy-{RENPV_VERSION}-sdk"
    if inner.is_dir():
        for item in inner.iterdir():
            target = dest / item.name
            if target.exists():
                if item.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(target))
        inner.rmdir()


def download_sdk(progress_callback=None) -> None:
    """Scarica ed estrae l'SDK Ren'Py nella cartella del progetto."""
    dest = sdk_dir()
    archive_name = _archive_name()
    archive_url = _archive_url()
    temp = _project_root() / ".download"
    temp.mkdir(exist_ok=True)
    archive_path = temp / archive_name
    try:
        if progress_callback:
            progress_callback(0, 0)
        _download_file(archive_url, archive_path, progress_callback)
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        _extract(archive_path, dest)
        _flatten_extracted_dir(dest)
        version_file().write_text(RENPV_VERSION, encoding="utf-8")
    finally:
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
        try:
            temp.rmdir()
        except OSError:
            pass


def renpy_command() -> list[str]:
    """Restituisce la lista di argomenti per lanciare Ren'Py dall'SDK."""
    root = sdk_dir()
    if platform.system() == "Windows":
        exe = root / "renpy.exe"
        if exe.exists():
            return [str(exe)]
        py = root / "lib" / "py3-windows-x86_64" / "python.exe"
        return [str(py), str(root / "renpy.py")]

    sh = root / "renpy.sh"
    if sh.exists():
        return [str(sh)]

    # Fallback: trova l'interprete Python incluso
    machine = platform.machine().lower()
    candidates = [
        root / "lib" / f"py3-linux-{machine}" / "python",
        root / "lib" / f"py3-mac-{machine}" / "python",
        root / "lib" / "py3-linux-x86_64" / "python",
        root / "lib" / "py3-mac-x86_64" / "python",
    ]
    for py in candidates:
        if py.exists():
            return [str(py), str(root / "renpy.py")]
    raise FileNotFoundError("Impossibile trovare l'eseguibile Ren'Py nell'SDK")


def build_project(
    project_dir: str | Path,
    target: str = "all",
    destination: str | Path | None = None,
    log_callback=None,
    cancel_event=None,
) -> tuple[int, str]:
    """Lancia la build del progetto Ren'Py con il target richiesto.

    target può essere: all, win, mac, linux.
    Il comando viene eseguito dalla cartella SDK usando 'launcher' come basedir.
    """
    sdk = sdk_dir()
    cmd = renpy_command() + ["launcher", "distribute", str(project_dir)]
    if destination:
        cmd += ["--destination", str(destination)]

    if target != "all":
        mapping = {"win": "win", "mac": "mac", "linux": "linux"}
        pkg = mapping.get(target)
        if pkg:
            cmd += ["--package", pkg]

    env = os.environ.copy()
    env["RENPY_NO_STEAM"] = "1"

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=str(sdk),
    )
    lines = []
    if process.stdout:
        for line in process.stdout:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                process.wait()
                return 1, "\n".join(lines) + "\nBuild cancelled by user."
            line = line.rstrip()
            lines.append(line)
            if log_callback:
                log_callback(line)
    returncode = process.wait()

    # Estrae automaticamente l'.app macOS dallo zip e rimuove lo zip.
    if returncode == 0 and destination and target in ("mac", "all"):
        dest_path = Path(destination)
        for zip_path in dest_path.glob("*-mac.zip"):
            try:
                subprocess.run(
                    ["unzip", "-q", "-o", str(zip_path)],
                    cwd=str(dest_path),
                    check=True,
                )
                zip_path.unlink()
            except Exception:
                # Se unzip non e disponibile o fallisce, lascia lo zip.
                pass
            break

    return returncode, "\n".join(lines)
