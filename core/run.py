from time import sleep
from threading import Thread, Lock

from random import uniform

from .base import Base
from .visualizer import Visualizer


class RunProgram(Visualizer, Base):
    __slots__ = ('locker', 'running')

    def __init__(self):
        super().__init__()
        self.locker = Lock()
        self.running: bool = True
        self.bands = [
            [20, 80], [80, 160], [160, 320],
            [320, 640], [640, 1280], [1280, 2560],
            [2560, 5120], [5120, 10240], [10240, 20000]
        ]

    def wait_for_enter(self, stdscr) -> None:
        stdscr.getch()
        self.running: bool = False

    def create_main_loop(self, stdscr) -> None:
        while self.running:
            with self.locker:
                counter = 0
                band_levels: list[float] = [uniform(0, 100) for _ in range(len(self.bands))]  # заглушка
                for i in range(len(band_levels)):
                    Thread(target=self.safe_wrapper, args=(self.create_band, band_levels[i], self.x + counter)).start()
                    counter += len(band_levels) - 1
                stdscr.refresh()
            sleep(0.1)

    def create_wrapped_threads(self):
        self.safe_wrapper(self.init_curses, None)
        Thread(target=self.safe_wrapper, args=(self.wait_for_enter, None)).start()
        self.safe_wrapper(self.create_main_loop, None)
