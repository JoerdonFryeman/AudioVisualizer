from .base import color_pair


class Visualisation:
    __slots__ = ('y', 'x', 'band_levels_visualisation', 'preset')

    def __init__(self):
        self.band_levels_visualisation: list[tuple[int, None, int]] = [
            (-10, None, 0), (-8, None, 0), (-6, None, 0),
            (-4, None, 0), (-2, None, 0), (0, None, 0)
        ]
        self.y: int = 11
        self.x: int = 2
        self.preset = [2, 6, 12, 25, 45, 70]

    def verify_band_level(self, band_level):
        if band_level >= self.preset[5]:
            return 1, 2, 3, 4, 5, 6
        elif band_level >= self.preset[4]:
            return 0, 2, 3, 4, 5, 6
        elif band_level >= self.preset[3]:
            return 0, 0, 3, 4, 5, 6
        elif band_level >= self.preset[2]:
            return 0, 0, 0, 4, 5, 6
        elif band_level >= self.preset[1]:
            return 0, 0, 0, 0, 5, 6
        elif band_level > self.preset[0]:
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
