from time import sleep
from threading import Thread, Lock

from random import uniform

from .visualisation import Visualisation


class RunProgram(Visualisation):
    __slots__ = ('locker', 'running', 'variables', 'bands')

    def __init__(self):
        super().__init__()
        self.locker = Lock()
        self.running: bool = True
        self.variables: dict = self.get_config_data('audio_visualizer_config')
        self.bands = self.variables['bands']

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
