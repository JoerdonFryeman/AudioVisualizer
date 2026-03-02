from time import sleep
from threading import Thread, Lock

from .audio_processor import Analyzer


class RunProgram(Analyzer):
    __slots__ = ('locker', 'running', 'fps')

    def __init__(self):
        super().__init__()
        self.locker = Lock()
        self.running = True
        self.fps = 10

    def wait_for_enter(self, stdscr) -> None:
        """Ждёт нажатия клавиши и устанавливает флаг остановки."""
        stdscr.getch()
        self.running: bool = False

    def create_main_loop(self, stdscr) -> None:
        """Запускает все модули программы в цикле."""
        while self.running:
            with self.locker:
                counter: int = 0
                band_levels: list[float] = self.get_band_levels()
                for i in range(len(band_levels)):
                    Thread(target=self.safe_wrapper, args=(self.create_band, band_levels[i], self.x + counter)).start()
                    counter += len(band_levels) - 1
                stdscr.refresh()
                sleep(1.0 / max(1, self.fps))

    def create_wrapped_threads(self) -> None:
        """Запускает потоки."""
        self.safe_wrapper(self.init_curses, None)
        Thread(target=self.safe_wrapper, args=(self.wait_for_enter, None)).start()
        self.safe_wrapper(self.create_main_loop, None)
