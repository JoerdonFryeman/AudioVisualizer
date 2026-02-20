import math
import queue
import numpy as np
import sounddevice as sd
from pulsectl import Pulse

from .band_levels import BandLevels


class DeviceSelection(BandLevels):
    __slots__ = ('device_list',)

    def __init__(self):
        super().__init__()
        try:
            self.device_list = sd.query_devices()
        except Exception as e:
            self.logger.debug('Failed to query audio devices: %s', e)

    def _get_device_name(self) -> str | None:
        """Возвращает имя системного устройства вывода или None."""
        system: str | None = self.verify_os()

        if system is None:
            self.logger.debug('Unknown platform.system() value: %s', system)
            return None

        if system == 'Linux':
            try:
                with Pulse('get-default-output') as pulse:
                    default = pulse.server_info().default_sink_name
                    if not default:
                        return None
                    try:
                        sink = pulse.get_sink_by_name(default)
                    except Exception:
                        self.logger.exception('Failed to set sink; setting sink=None')
                        sink = None
                    if sink:
                        return sink.description or sink.name
                    return default
            except Exception as e:
                self.logger.exception('Failed to get default PulseAudio sink: %s', e)
                return None

        return None

    def _get_outputs(self, log: str) -> int | None:
        """Пытается вернуть последний индекс списка звуковых устройств"""
        self.logger.info(log)
        outputs = [d for d in self.device_list if d.get('max_output_channels', 0) > 0]
        if outputs:
            return outputs[-1].get('index')
        return None

    def verify_device(self) -> int | None:
        """Проверяет и возвращает индекс выбранного устройства, с откатом к последнему выходному."""
        if self.device is not None:
            return self.device

        target: str | None = self._get_device_name()

        if not target:
            return self._get_outputs('No preferred device name obtained; falling back to last output-capable device')

        target_lower: str = str(target).lower().strip()

        for d in self.device_list:
            name: str = str(d.get('name', '')).lower().strip()
            if target_lower == name or target_lower in name:
                index: int = d.get('index')
                self.logger.info('Selected device: %s, index: %s', name, index)
                return index

        return self._get_outputs('Preferred device not found; falling back to last output-capable device')

    def verify_selected_device(self) -> int:
        """Возвращает индекс выбранного устройства или кидает RuntimeError, если не найден."""
        device: int | None = self.verify_device()
        if device is None:
            raise RuntimeError('Preferred device not found — please specify device index manually.')
        return device


class AudioCapture(DeviceSelection):
    __slots__ = ('selected_device', 'samplerate', 'audio_queue', 'stream')

    def __init__(self):
        super().__init__()
        self.selected_device = self.verify_selected_device()
        self.samplerate = int(self.device_list[self.selected_device].get("default_samplerate", 48000))
        self.audio_queue = queue.Queue(self.maxsize)
        self.stream = None

    @staticmethod
    def _convert_to_mono(buffer: np.ndarray) -> np.ndarray:
        """Преобразует входной буфер в 1D моно numpy-массив dtype float32."""
        if buffer.ndim > 1:
            return np.mean(buffer, axis=1, dtype=np.float32)
        elif buffer.dtype == np.float32:
            return buffer
        return buffer.astype(np.float32, copy=False)

    def _enqueue_mono_block(self, buffer) -> bool:
        """Помещает моно-блок в очередь; при переполнении удаляет старый элемент и повторяет."""
        mono_block: np.ndarray = self._convert_to_mono(buffer)
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

    def _audio_callback(self, block, *args) -> None:
        """Callback аудиопотока: конвертирует блок и ставит в очередь."""
        self._enqueue_mono_block(block)

    def start_stream(self) -> None:
        """Создаёт и запускает входной аудиопоток."""
        self.logger.info('Available devices:\n%s', self.device_list)

        if getattr(self.stream, "active", False):
            self.logger.info('start_stream called but stream already active selected device: %s', self.selected_device)
            return None
        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                blocksize=self.samples_number,
                device=self.selected_device,
                channels=self.channels_number,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.logger.info(
                'Samplerate: %s, channels: %s, blocksize: %s, maxsize: %s',
                self.samplerate, self.channels_number, self.samples_number, self.maxsize
            )
            self.logger.info('Audio stream started.')
        except Exception:
            self.logger.exception('Failed to start audio stream selected device: %s', self.selected_device)
            try:
                if self.stream is not None:
                    self.stream.close()
            except Exception:
                self.logger.exception(
                    'Failed to close stream after start failure selected device: %s', self.selected_device
                )
            finally:
                self.stream = None
            raise

    def stop_stream(self) -> None:
        """Останавливает и закрывает аудиопоток, гарантирует сброс атрибута stream."""
        if self.stream is None:
            self.logger.info('stop_stream called but no stream present selected device: %s', self.selected_device)
            return None
        try:
            if getattr(self.stream, "active", False):
                try:
                    self.stream.stop()
                except Exception:
                    self.logger.exception('Error stopping stream selected device: %s', self.selected_device)
            try:
                self.stream.close()
            except Exception:
                self.logger.exception('Error closing stream selected device: %s', self.selected_device)
            self.logger.info('Audio stream stopped.')
        finally:
            self.stream = None


class AudioBuilder(AudioCapture):

    @staticmethod
    def _build_waveform(blocks: list) -> np.ndarray:
        """Конкатенирует блоки в единый ndarray и сводит в моно по последней оси."""
        if not blocks:
            return np.empty(0, dtype=np.float32)
        waveform: np.ndarray = np.concatenate(blocks, axis=0) if len(blocks) > 1 else blocks[0].copy()
        if waveform.ndim > 1:
            waveform = waveform.mean(axis=-1, dtype=np.float32)
        return waveform

    def _collect_blocks(self) -> list:
        """Возвращает список всех доступных блоков из очереди (может быть пустым)."""
        blocks: list = []
        while True:
            try:
                blocks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break
        return blocks

    def _finalize_window(self, waveform: np.ndarray) -> np.ndarray:
        """Приводит к dtype=np.float32 и возвращает окно фиксированной длины (паддинг слева)."""
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32, copy=False)
        total: int = waveform.size
        if total >= self.samples_number:
            return waveform[-self.samples_number:]
        padding: np.ndarray = np.zeros(self.samples_number - total, dtype=np.float32)
        return np.concatenate((padding, waveform))

    def grab_samples(self) -> np.ndarray:
        """Собирает все доступные блоки и возвращает окно фиксированной длины (np.float32)."""
        blocks: list = self._collect_blocks()
        if not blocks:
            return np.zeros(self.samples_number, dtype=np.float32)
        waveform: np.ndarray = self._build_waveform(blocks)
        return self._finalize_window(waveform)


class Analyzer(AudioBuilder):

    @staticmethod
    def get_window_vector(samples_number: int, window_type: str = "hann") -> np.ndarray:
        """Возвращает numpy-массив коэффициентов оконной функции (dtype=np.float32)."""
        if samples_number <= 0:
            return np.empty(0, dtype=np.float32)
        if samples_number == 1:
            return np.array([1.0], dtype=np.float32)

        wt: str = window_type.lower()
        if wt in ("hann", "hanning"):
            a, b = 0.5, 0.5
        elif wt == "hamming":
            a, b = 0.54, 0.46
        else:
            raise ValueError(f"Unknown window_type: {window_type}")

        factor = np.float32(2.0 * np.pi / (samples_number - 1))
        n = np.arange(samples_number, dtype=np.float32)
        w = a - b * np.cos(factor * n)
        return w

    @staticmethod
    def convert_to_percent(db: float, min_db: float = -80.0, gamma: float = 0.4) -> float:
        """Преобразовывает dBFS в проценты с помощью нелинейного отображения."""
        if db <= min_db:
            return 0.0
        if db >= 0.0:
            return 100.0
        x: float = (db - min_db) / (-min_db)
        return 100.0 * (x ** gamma)

    def apply_window_vector(self, signal, window_type: str = "hann") -> np.ndarray:
        """Возвращает новый массив, полученный поэлементным умножением входного сигнала на вектор окна."""
        x: np.ndarray = np.asarray(signal, dtype=np.float32)
        if x.size == 0:
            return x
        w: np.ndarray = self.get_window_vector(x.size, window_type)
        return x * w

    def calculate(self, signal, min_db: float = -80.0, eps: float = 1e-12) -> list[float]:
        """Анализирует входной фрейм signal (np.ndarray или list) и возвращает список уровней dBFS для полос."""
        x: np.ndarray = np.asarray(signal, dtype=np.float32)
        x_size: int = x.size

        if x_size == 0 or np.allclose(x, 0.0, atol=eps):
            return [min_db] * len(self.bands)

        if x.ndim > 1:
            x: np.ndarray = x.mean(axis=1, dtype=np.float32)
            x_size: int = x.size
            if x_size == 0 or np.allclose(x, 0.0, atol=eps):
                return [min_db] * len(self.bands)

        xw: np.ndarray = self.apply_window_vector(x, window_type="hann")
        amp: np.ndarray = np.abs(np.fft.rfft(xw)) / float(x_size)

        if x_size > 1:
            amp[1:-1] *= 2.0

        freqs: np.ndarray = np.fft.rfftfreq(x_size, d=1.0 / float(self.samplerate))
        power: np.ndarray = amp ** 2

        out: list[float] = []
        for low, high in self.bands:
            start = np.searchsorted(freqs, float(low), side='left')
            end = np.searchsorted(freqs, float(high), side='left')
            if end <= start:
                out.append(min_db)
                continue
            segment = power[start:end]
            rms: float = math.sqrt(float(np.mean(segment)))
            db: float = 20.0 * math.log10(rms + eps)
            out.append(float(max(db, min_db)))

        return out

    def get_band_levels(self) -> list[float]:
        """Возвращает уровни полос в процентах для текущего сигнала."""
        signal: np.ndarray = self.grab_samples()
        db_levels: list[float] = self.calculate(signal)
        return [self.convert_to_percent(d) for d in db_levels]
