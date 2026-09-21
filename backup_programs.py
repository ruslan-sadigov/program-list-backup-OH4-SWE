import csv
import shutil
import socket
import subprocess
import winreg

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Program:
    name: str
    version: str = ""
    publisher: str = ""
    install_location: str = ""


class WindowsProgramScanner:
    REGISTRY_PATHS = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    ]

    def get_installed_programs(self) -> list[Program]:
        programs = {}

        for root, path in self.REGISTRY_PATHS:
            self._scan_registry_path(root, path, programs)

        return sorted(
            programs.values(),
            key=lambda program: program.name.lower(),
        )

    def _scan_registry_path(
        self,
        root,
        path: str,
        programs: dict,
    ) -> None:
        try:
            with winreg.OpenKey(root, path) as registry_key:
                subkey_count = winreg.QueryInfoKey(registry_key)[0]

                for index in range(subkey_count):
                    self._process_subkey(
                        registry_key,
                        index,
                        programs,
                    )

        except OSError:
            pass

    def _process_subkey(
        self,
        registry_key,
        index: int,
        programs: dict,
    ) -> None:
        try:
            subkey_name = winreg.EnumKey(
                registry_key,
                index,
            )

            with winreg.OpenKey(
                registry_key,
                subkey_name,
            ) as subkey:

                name = self._read_value(
                    subkey,
                    "DisplayName",
                )

                if not name:
                    return

                program = Program(
                    name=name,
                    version=self._read_value(
                        subkey,
                        "DisplayVersion",
                    ),
                    publisher=self._read_value(
                        subkey,
                        "Publisher",
                    ),
                    install_location=self._read_value(
                        subkey,
                        "InstallLocation",
                    ),
                )

                unique_key = (
                    program.name.lower(),
                    program.version.lower(),
                )

                programs[unique_key] = program

        except OSError:
            pass

    @staticmethod
    def _read_value(key, value_name: str) -> str:
        try:
            value, _ = winreg.QueryValueEx(
                key,
                value_name,
            )

            return str(value).strip()

        except OSError:
            return ""


class WingetExporter:
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )

            return result.returncode == 0

        except FileNotFoundError:
            return False

    def export(self, output_path: Path) -> bool:
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                [
                    "winget",
                    "export",
                    "-o",
                    str(output_path),
                    "--accept-source-agreements",
                ],
                check=False,
            )

            return result.returncode == 0

        except OSError:
            return False


class BackupWriter:
    def write_text(
        self,
        programs: list[Program],
        output_path: Path,
    ) -> None:

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            file.write("INSTALLED PROGRAMS BACKUP\n")
            file.write("=" * 70 + "\n\n")

            file.write(
                f"Computer: {socket.gethostname()}\n"
            )

            file.write(
                f"Backup date: "
                f"{datetime.now():%Y-%m-%d %H:%M:%S}\n"
            )

            file.write(
                f"Programs found: {len(programs)}\n\n"
            )

            for number, program in enumerate(
                programs,
                start=1,
            ):
                file.write(
                    f"{number}. {program.name}\n"
                )

                if program.version:
                    file.write(
                        f"   Version: {program.version}\n"
                    )

                if program.publisher:
                    file.write(
                        f"   Publisher: {program.publisher}\n"
                    )

                if program.install_location:
                    file.write(
                        f"   Install location: "
                        f"{program.install_location}\n"
                    )

                file.write("\n")

    def write_csv(
        self,
        programs: list[Program],
        output_path: Path,
    ) -> None:

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "Name",
                    "Version",
                    "Publisher",
                    "Install Location",
                ]
            )

            for program in programs:
                writer.writerow(
                    [
                        program.name,
                        program.version,
                        program.publisher,
                        program.install_location,
                    ]
                )


class BackupArchiver:
    def create_zip(
        self,
        backup_directory: Path,
    ) -> Path:

        zip_base_path = (
            backup_directory.parent
            / backup_directory.name
        )

        zip_path = shutil.make_archive(
            str(zip_base_path),
            "zip",
            root_dir=backup_directory,
        )

        return Path(zip_path)


class ProgramBackupManager:
    def __init__(
        self,
        backup_root: str = "backups",
    ):
        self.backup_root = Path(backup_root)

        self.scanner = WindowsProgramScanner()
        self.winget_exporter = WingetExporter()
        self.writer = BackupWriter()
        self.archiver = BackupArchiver()

    def create_backup(self) -> Path:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        backup_directory = (
            self.backup_root
            / f"PC_Program_Backup_{timestamp}"
        )

        backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        print("Scanning installed programs...")

        programs = (
            self.scanner.get_installed_programs()
        )

        print(
            f"Found {len(programs)} programs."
        )

        text_path = (
            backup_directory
            / "installed_programs.txt"
        )

        csv_path = (
            backup_directory
            / "installed_programs.csv"
        )

        winget_path = (
            backup_directory
            / "winget_programs.json"
        )

        self.writer.write_text(
            programs,
            text_path,
        )

        self.writer.write_csv(
            programs,
            csv_path,
        )

        print("\nCreated program lists:")
        print(f"  {text_path}")
        print(f"  {csv_path}")

        print("\nCreating Winget export...")

        winget_success = (
            self.winget_exporter.export(
                winget_path
            )
        )

        if winget_success:
            print(
                f"Winget export created: "
                f"{winget_path}"
            )
        else:
            print(
                "Winget export could not be created."
            )

        print("\nCreating ZIP archive...")

        zip_path = self.archiver.create_zip(
            backup_directory
        )

        print(f"ZIP created: {zip_path}")

        # IMPORTANT:
        # main.py needs this returned path
        return zip_path