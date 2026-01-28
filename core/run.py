from time import sleep
from threading import Thread, Lock

from .audio_processor import Analyzer


class RunProgram(Analyzer):
    __slots__ = ('locker', 'running')

    def __init__(self):
        super().__init__()
        self.locker = Lock()
        self.running: bool = True

    def wait_for_enter(self, stdscr) -> None:
        stdscr.getch()
        self.running: bool = False

    def create_main_loop(self, stdscr) -> None:
        while self.running:
            with self.locker:
                counter = 0
                band_levels: list[float] = self.get_band_levels()
                for i in range(len(band_levels)):
                    Thread(target=self.safe_wrapper, args=(self.create_band, band_levels[i], self.x + counter)).start()
                    counter += len(band_levels) - 1
                stdscr.refresh()
            sleep(0.1)

    def create_wrapped_threads(self):
        self.safe_wrapper(self.init_curses, None)
        Thread(target=self.safe_wrapper, args=(self.wait_for_enter, None)).start()
        self.safe_wrapper(self.create_main_loop, None)
