try:
    from curses import (
        wrapper, error, curs_set, start_color, init_pair, use_default_colors, color_pair, has_colors,
        COLOR_MAGENTA, COLOR_BLUE, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
    )
except ModuleNotFoundError:
    print('\nFor the program to work, you need to install the curses module!\n')

from .base import Base


class Visualisation(Base):
    __slots__ = ('band_levels_visualisation', 'y', 'x')

    def __init__(self):
        super().__init__()
        self.create_directories()
        self.get_logging_data()
        self.band_levels_visualisation: list[tuple[int, None, int]] = [
            (-10, None, 0), (-8, None, 0), (-6, None, 0),
            (-4, None, 0), (-2, None, 0), (0, None, 0)
        ]
        self.y: int = 11
        self.x: int = 2

    @staticmethod
    def init_colors() -> None:
        color_map = {1: COLOR_RED, 2: COLOR_YELLOW, 3: COLOR_GREEN, 4: COLOR_CYAN, 5: COLOR_BLUE, 6: COLOR_MAGENTA}
        [init_pair(i + 1, color_map[i + 1], 1) for i in range(6)]

    @staticmethod
    def safe_wrapper(function, *args) -> None:
        try:
            if any(args):
                wrapper(function, *args)
            else:
                wrapper(function)
        except error:
            pass

    def init_curses(self, stdscr):
        stdscr.clear()
        stdscr.refresh()
        curs_set(False)
        if has_colors():
            use_default_colors()
            start_color()
            self.init_colors()

    def verify_band_level(self, band_level):
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

    def create_band(self, stdscr, band_level, x):
        for i, (off, _, _) in enumerate(self.band_levels_visualisation):
            color = self.verify_band_level(band_level)[i]
            y = self.y + off
            if color == 0:
                stdscr.addstr(y, x, '      ')
            else:
                stdscr.addstr(y, x, '██████', color_pair(color))
