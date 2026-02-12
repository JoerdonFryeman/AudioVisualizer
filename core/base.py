import os
import platform
from json import load, dump, JSONDecodeError
from logging import config, getLogger


class Base:
    __slots__ = (
        'logger', 'preset', 'variables', 'device', 'channels_number',
        'samples_number', 'maxsize', 'bands_levels', 'bands'
    )

    def __init__(self):
        self.logger = getLogger()
        self.preset = {
            "device": None,
            "channels_number": 2,
            "samples_number": 1024,
            "maxsize": 16,
            "bands_levels": [2, 6, 12, 25, 45, 70],
            "bands": [
                [20, 80], [80, 160], [160, 320],
                [320, 640], [640, 1280], [1280, 2560],
                [2560, 5120], [5120, 10240], [10240, 20000]
            ]
        }
        self.variables = self.get_config_data('preset')
        try:
            self.device = self.variables['device']
            self.channels_number = self.variables['channels_number']
            self.samples_number = self.variables['samples_number']
            self.maxsize = self.variables['maxsize']
            self.bands_levels = self.variables['bands_levels']
            self.bands = self.variables['bands']
        except TypeError:
            print('\nTypeError! Переменные не могут быть инициализированы!')

    @staticmethod
    def create_directories() -> None:
        """Создаёт каталоги, игнорируя уже существующие."""
        directories: tuple[str, str, str] = ('config_files', 'config_files/logs', 'icons')
        for directory in directories:
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass

    @staticmethod
    def verify_os() -> str | None:
        """Метод проверяет на какой ОС запускается программа."""
        system: str = platform.system()
        if system == 'Linux':
            return 'Linux'
        if system == 'Darwin':
            return 'macOS'
        if system == 'Windows':
            return 'Windows'
        return None

    @staticmethod
    def get_json_data(directory: str, name: str) -> dict:
        """Возвращает данные в формате json из указанного файла."""
        file_path: str = os.path.join(directory, f'{name}.json')
        try:
            with open(file_path, encoding='UTF-8') as json_file:
                data: dict = load(json_file)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f'Файл не найден: {file_path}')
        except JSONDecodeError:
            raise ValueError(f'Ошибка декодирования JSON в файле: {file_path}')
        except PermissionError:
            raise PermissionError(f'Нет доступа к файлу: {file_path}')
        except Exception as e:
            raise Exception(f'Произошла ошибка: {str(e)}')

    @staticmethod
    def save_json_data(directory: str, name: str, data: list | dict) -> None:
        """Сохраняет файл json."""
        file_path: str = os.path.join(directory, f'{name}.json')
        try:
            with open(file_path, 'w', encoding='UTF-8') as json_file:
                dump(data, json_file, ensure_ascii=False, indent=4)
        except PermissionError:
            raise PermissionError(f'Нет доступа для записи в файл: {file_path}')
        except IOError as e:
            raise IOError(f'Ошибка записи в файл: {file_path}. Причина: {str(e)}')
        except Exception as e:
            raise Exception(f'Произошла ошибка: {str(e)}')

    def get_config_data(self, config_name: str):
        """Метод пробует прочитать файл конфигурации и, если это не удаётся, перезаписывает его."""
        try:
            return self.get_json_data('config_files', config_name)
        except FileNotFoundError:
            self.save_json_data('config_files', config_name, self.preset)
            return self.preset
        except JSONDecodeError:
            print(f'\nJSONDecodeError! Файл «{config_name}.json» поврежден или не является корректным JSON!')
            return None
        except OSError as e:
            print(f'\nOSError! Не удалось прочитать файл «{config_name}.json» из-за {e}')
            return None

    def get_logging_data(self) -> None:
        """Загружает и применяет конфигурацию логирования из JSON-файла."""
        config.dictConfig(self.get_json_data('config_files/logs', 'logging'))

    def log_app_release(self, name: str, version: str, year: int) -> None:
        """Логирует заголовок приложения в один info-вызов."""
        self.logger.info(
            '| ЭЛЕКТРОНИКА 54 | %s (version %s) | '
            'https://github.com/JoerdonFryeman/AudioVisualizer | '
            'MIT License, (c) %d Joerdon Fryeman |',
            name, version, year
        )
