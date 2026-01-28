import os


class Base:

    @staticmethod
    def create_directories() -> None:
        """Создаёт каталоги, игнорируя уже существующие."""
        directories: tuple[str, str] = ('config_files', 'icons')
        for directory in directories:
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass
