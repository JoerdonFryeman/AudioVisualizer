try:
    from curses import (
        wrapper, error, curs_set, start_color, init_pair, use_default_colors, color_pair, has_colors,
        COLOR_MAGENTA, COLOR_BLUE, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
    )
except ModuleNotFoundError:
    print('\nДля работы программы необходимо установить модуль curses!\n')

from .base import Base


class Visualisation(Base):
    __slots__ = ('band_levels_visualisation', 'y', 'x')

    def __init__(self):
        super().__init__()
        self.band_levels_visualisation = [
            (-10, None, 0), (-8, None, 0), (-6, None, 0),
            (-4, None, 0), (-2, None, 0), (0, None, 0)
        ]
        self.y = 11
        self.x = 2

    @staticmethod
    def safe_wrapper(function, *args) -> None:
        """Оборачивает вызов wrapper в try/except и подавляет исключения curses.error."""
        try:
            if any(args):
                wrapper(function, *args)
            else:
                wrapper(function)
        except error:
            pass

    @staticmethod
    def init_colors() -> None:
        """Инициализирует 6 цветовых пар."""
        palette: tuple = (COLOR_RED, COLOR_YELLOW, COLOR_GREEN, COLOR_CYAN, COLOR_BLUE, COLOR_MAGENTA)
        i = 1
        for fg in palette:
            init_pair(i, fg, 1)
            i += 1

    def init_curses(self, stdscr) -> None:
        """Инициализирует экран curses"""
        stdscr.clear()
        stdscr.refresh()
        curs_set(0)
        if has_colors():
            use_default_colors()
            start_color()
            self.init_colors()

    def verify_band_level(self, band_level: int) -> tuple[int, int, int, int, int, int]:
        """Возвращает кортеж из 6 целых чисел, представляющих уровни для 6 полос."""
        if band_level >= self.bands_levels[5]:
            return 1, 2, 3, 4, 5, 6
        elif band_level >= self.bands_levels[4]:
            return 0, 2, 3, 4, 5, 6
        elif band_level >= self.bands_levels[3]:
            return 0, 0, 3, 4, 5, 6
        elif band_level >= self.bands_levels[2]:
            return 0, 0, 0, 4, 5, 6
        elif band_level >= self.bands_levels[1]:
            return 0, 0, 0, 0, 5, 6
        elif band_level > self.bands_levels[0]:
            return 0, 0, 0, 0, 0, 6
        return 0, 0, 0, 0, 0, 0

    def create_band(self, stdscr, band_level: int, x: int):
        """Создаёт и отображает одну полосу визуализации для заданного уровня и позиции."""
        for i, (off, _, _) in enumerate(self.band_levels_visualisation):
            color: int = self.verify_band_level(band_level)[i]
            y: int = self.y + off
            if color == 0:
                stdscr.addstr(y, x, '      ')
            else:
                stdscr.addstr(y, x, '██████', color_pair(color))
