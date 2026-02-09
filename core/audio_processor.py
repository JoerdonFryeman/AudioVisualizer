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

    def get_device_name(self) -> str | None:
        """Возвращает имя системного устройства вывода или None."""
        system = self.verify_os()

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
                    return (sink.description or sink.name) if sink else default
            except Exception as e:
                self.logger.exception('Failed to get default PulseAudio sink: %s', e)
                return None

        return None

    def verify_device(self) -> int | None:
        """Проверяет и возвращает индекс выбранного устройства, с откатом к последнему выходному."""
        if self.device is not None:
            return self.device

        target = self.get_device_name()

        if not target:
            self.logger.info('No preferred device name obtained; falling back to last output-capable device')
            outputs = [d for d in self.device_list if d.get('max_output_channels', 0) > 0]
            return outputs[-1].get('index') if outputs else None

        target = str(target).lower()

        for d in self.device_list:
            name = str(d.get('name', '')).lower()
            if target == name or target in name:
                index = d.get('index')
                self.logger.info(
                    '| ЭЛЕКТРОНИКА 54 | AudioVisualizer (version 1.0.0) | '
                    'https://github.com/JoerdonFryeman/AudioVisualizer | '
                    'MIT License, (c) 2026 JoerdonFryeman |'
                )
                self.logger.info('Selected device: %s, index: %s', name, index)
                return index

        self.logger.info('Preferred device not found; falling back to last output-capable device')
        outputs = [d for d in self.device_list if d.get('max_output_channels', 0) > 0]
        return outputs[-1].get('index') if outputs else None

    def verify_selected_device(self) -> int:
        """Возвращает индекс выбранного устройства или возбуждает RuntimeError, если не найден."""
        device = self.verify_device()
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

    def _audio_callback(self, block, *args) -> None:
        """Callback аудиопотока: конвертирует блок и ставит в очередь."""
        self._enqueue_mono_block(block)

    def start_stream(self) -> None:
        """Создаёт и запускает входной аудиопоток."""
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

    def stop_stream(self):
        """Останавливает и закрывает аудиопоток, гарантирует сброс атрибута stream."""
        if self.stream is None:
            self.logger.info('stop_stream called but no stream present selected device: %s', self.selected_device)
            return
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

    def grab_samples(self) -> list[float]:
        """Собирает все доступные блоки из очереди и возвращает окно фиксированной длины."""
        blocks = []
        while True:
            try:
                blocks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        if not blocks:
            self.logger.debug(
                'No audio blocks in queue; returning zero-filled window of length %s', self.samples_number
            )
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
    def get_window_vector(samples_number: int, window_type: str = "hann") -> list[float]:
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

    def apply_window_vector(self, signal, window_type: str = "hann") -> np.ndarray:
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
