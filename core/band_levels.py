from .visualisation import color_pair, Visualisation


class BandLevels(Visualisation):
    __slots__ = ('band_levels_visualisation', 'y', 'x')

    def __init__(self):
        super().__init__()
        self.band_levels_visualisation = [
            (-10, None, 0), (-8, None, 0), (-6, None, 0),
            (-4, None, 0), (-2, None, 0), (0, None, 0)
        ]
        self.y = 11
        self.x = 2

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
