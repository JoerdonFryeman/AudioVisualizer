from time import sleep
from threading import Thread, Lock

from .audio_processor import Analyzer


class RunProgram(Analyzer):
    __slots__ = ('locker', 'running', 'fps')

    def __init__(self):
        super().__init__()
        self.locker = Lock()
        self.running: bool = True
        self.fps: int = 10

    def build_app(self, stdscr) -> None:
        """Создаёт потоки для каждого уровня полосы."""
        with self.locker:
            counter = 0
            band_levels: list[float] = self.get_band_levels()
            for i in range(len(band_levels)):
                Thread(target=self.safe_wrapper, args=(self.create_band, band_levels[i], self.x + counter)).start()
                counter += len(band_levels) - 1
            stdscr.refresh()
            sleep(self.fps / 100)

    def wait_for_enter(self, stdscr) -> None:
        """Ждёт нажатия клавиши и устанавливает флаг остановки."""
        stdscr.getch()
        self.running: bool = False

    def create_main_loop(self, stdscr) -> None:
        """Главный цикл."""
        while self.running:
            self.build_app(stdscr)

    def create_wrapped_threads(self) -> None:
        """Запускает init_curses и create_main_loop через safe_wrapper и отдельный поток для wait_for_enter."""
        self.safe_wrapper(self.init_curses, None)
        Thread(target=self.safe_wrapper, args=(self.wait_for_enter, None)).start()
        self.safe_wrapper(self.create_main_loop, None)
