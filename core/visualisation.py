try:
    from curses import (
        wrapper, error, curs_set, start_color, init_pair, use_default_colors, color_pair, has_colors,
        COLOR_MAGENTA, COLOR_BLUE, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
    )
except ModuleNotFoundError:
    print('\nДля работы программы необходимо установить модуль curses!\n')

from .base import Base


class Visualisation(Base):

    @staticmethod
    def init_colors() -> None:
        """Инициализирует 6 цветовых пар."""
        color_map: dict = {
            1: COLOR_RED, 2: COLOR_YELLOW, 3: COLOR_GREEN,
            4: COLOR_CYAN, 5: COLOR_BLUE, 6: COLOR_MAGENTA
        }
        [init_pair(i + 1, color_map[i + 1], 1) for i in range(6)]

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

    def init_curses(self, stdscr) -> None:
        """Инициализирует экран curses"""
        stdscr.clear()
        stdscr.refresh()
        curs_set(False)
        if has_colors():
            use_default_colors()
            start_color()
            self.init_colors()
