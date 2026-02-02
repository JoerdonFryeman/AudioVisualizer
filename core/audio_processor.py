import math
import queue
import numpy as np
import sounddevice as sd

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
        """Преобразует входной буфер в 1D моно numpy-массив dtype float32."""
        mono = np.mean(buffer, axis=1) if buffer.ndim > 1 else buffer
        return mono.astype(np.float32, copy=False)

    def _enqueue_mono_block(self, buffer) -> bool:
        """Помещает моно-блок в очередь; при переполнении удаляет старый элемент и повторяет."""
        mono_block = self._convert_to_mono(buffer)
        try:
            self.audio_queue.put_nowait(mono_block)
            return True
        except queue.Full:
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.audio_queue.put_nowait(mono_block)
                return True
            except queue.Full:
                return False

    def audio_callback(self, block, *args):
        """Callback аудиопотока: конвертирует блок и ставит в очередь."""
        self._enqueue_mono_block(block)

    def start_stream(self):
        """Создаёт и запускает входной аудиопоток."""
        if getattr(self.stream, "active", False):
            self.logger.info(f'start_stream called but stream already active device: {self.device}')
            return
        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                blocksize=self.samples_number,
                device=self.device,
                channels=self.channels_number,
                callback=self.audio_callback,
            )
            self.stream.start()
            self.logger.info(f'Audio stream started. {self.all_sets}')
        except Exception:
            self.logger.exception(f'Failed to start audio stream device: {self.device}')
            try:
                if self.stream is not None:
                    self.stream.close()
            except Exception:
                pass
            finally:
                self.stream = None
            raise

    def stop_stream(self):
        """Останавливает и закрывает аудиопоток, гарантирует сброс атрибута stream."""
        if self.stream is None:
            self.logger.info(f'stop_stream called but no stream present device: {self.device}')
            return
        try:
            if getattr(self.stream, "active", False):
                try:
                    self.stream.stop()
                except Exception:
                    self.logger.exception(f'Error stopping stream device: {self.device}')
            try:
                self.stream.close()
            except Exception:
                pass
            self.logger.info(f'Audio stream stopped. {self.all_sets}')
        finally:
            self.stream = None

    def grab_samples(self):
        """Собирает все доступные блоки из очереди и возвращает окно фиксированной длины."""
        blocks = []
        while True:
            try:
                blocks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        if not blocks:
            return [0.0] * self.samples_number

        arr = np.concatenate(blocks) if len(blocks) > 1 else blocks[0]
        arr = arr.astype(np.float32, copy=False)

        total = arr.size
        if total >= self.samples_number:
            window = arr[-self.samples_number:]
        else:
            pad = np.zeros(self.samples_number - total, dtype=np.float32)
            window = np.concatenate((pad, arr))

        return window.tolist()


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
