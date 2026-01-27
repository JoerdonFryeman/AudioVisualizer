import os

try:
    from curses import (
        wrapper, error, curs_set, start_color, init_pair, use_default_colors, color_pair, has_colors,
        COLOR_MAGENTA, COLOR_BLUE, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
    )
except ModuleNotFoundError:
    print('\nFor the program to work, you need to install the curses module!\n')

directories: tuple[str, str] = ('config_files', 'icons')
for directory in directories:
    try:
        os.mkdir(directory)
    except FileExistsError:
        pass


class Base:

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
