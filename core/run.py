from time import sleep
from threading import Thread, Lock

from random import uniform


class RunProgram:
    __slots__ = ('locker', 'running')

    def __init__(self):
        self.locker = Lock()
        self.running: bool = True

    def wait_for_enter(self) -> None:
        self.running: bool = False

    def create_main_loop(self) -> None:
        while self.running:
            with self.locker:
                counter = 0
                band_levels: list[float] = [uniform(-0.2, 0.1) for _ in range(1024)]
            sleep(0.1)

    def create_wrapped_threads(self):
        pass
