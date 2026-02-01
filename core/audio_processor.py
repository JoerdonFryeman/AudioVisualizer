import math
import queue
import numpy as np
import sounddevice as sd
from random import uniform

from .visualisation import Visualisation


class AudioCapture(Visualisation):
    __slots__ = ('device', 'samplerate', 'channels_number', 'audio_queue', 'maxsize', 'stream', 'all_sets')

    def __init__(self):
        super().__init__()
        self.device = 12
        self.samplerate = sd.query_devices(self.device)['default_samplerate']
        self.channels_number = 2
        self.maxsize = 16
        self.audio_queue = queue.Queue(self.maxsize)
        self.stream = None
        self.all_sets = (
            f'(device: {self.device}, samplerate: {self.samplerate}, '
            f'channels: {self.channels_number}, blocksize: {self.samples_number})'
        )

    @staticmethod
    def _convert_to_mono(buffer: np.ndarray) -> np.ndarray:
        pass

    def _enqueue_mono_block(self, buffer) -> bool:
        pass

    def audio_callback(self, block, frames, time_info, status):
        pass

    def start_stream(self):
        self.logger.info(f'Audio stream started {self.all_sets}')
        pass

    def stop_stream(self):
        self.logger.info(f'Audio stream stopped {self.all_sets}')
        pass

    def grab_samples(self):
        return [uniform(-0.01, 0.01) for _ in range(self.samples_number)]  # заглушка


class Analyzer(AudioCapture):

    @staticmethod
    def get_window_vector(samples_number: int, window_type: str = "hann"):
        """Возвращает вектор коэффициентов оконной функции заданного типа и длины samples_number."""
        if samples_number <= 0:
            return []
        if samples_number == 1:
            return [1.0]
        wt = window_type.lower()
        if wt in ("hann", "hanning"):
            a, b = 0.5, 0.5
        elif wt == "hamming":
            a, b = 0.54, 0.46
        else:
            raise ValueError(f"Unknown window_type: {window_type}")
        return [a - b * math.cos(2.0 * math.pi / (samples_number - 1) * n) for n in range(samples_number)]

    @staticmethod
    def convert_to_percent(db: float, min_db: float = -80.0, gamma: float = 0.4) -> float:
        """Преобразование dBFS в проценты с помощью нелинейного отображения."""
        if db <= min_db:
            return 0.0
        if db >= 0.0:
            return 100.0
        x = (db - min_db) / (-min_db)
        return 100.0 * (x ** gamma)

    def apply_window_vector(self, signal, window_type: str = "hann"):
        """Возвращает новый массив, полученный поэлементным умножением входного сигнала на вектор окна указанного типа."""
        x = np.asarray(signal, dtype=float)
        x_size = x.size
        if x_size == 0:
            return x.copy()
        w = np.asarray(self.get_window_vector(x_size, window_type), dtype=float)
        return x * w

    def calculate(self, signal, min_db=-80.0, eps=1e-12) -> list[float]:
        """Анализирует входной фрейм signal и возвращает список уровней dBFS для полос."""
        x = np.asarray(signal, dtype=float)
        x_size = x.size
        if x_size == 0 or np.allclose(x, 0.0, atol=eps):
            return [min_db] * len(self.bands)

        spec = np.fft.rfft(self.apply_window_vector(x, window_type="hann"))
        freqs = np.fft.rfftfreq(x_size, d=1.0 / self.samplerate)

        amp = np.abs(spec) / float(x_size)
        if x_size > 1:
            amp[1:-1] *= 2.0

        out = []
        for low, high in self.bands:
            idx = np.where((freqs >= float(low)) & (freqs < float(high)))[0]
            if idx.size == 0:
                out.append(min_db)
                continue
            rms = math.sqrt(float(np.mean(amp[idx] ** 2)))
            db = 20.0 * math.log10(rms + eps)
            out.append(float(max(db, min_db)))
        return out

    def get_band_levels(self) -> list[float]:
        """Возвращает уровни полос в процентах для текущего сигнала."""
        signal: list[float] = self.grab_samples()
        return [self.convert_to_percent(i) for i in self.calculate(signal)]
