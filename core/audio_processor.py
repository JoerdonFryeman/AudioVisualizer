from random import uniform

from .visualisation import Visualisation


class AudioCapture(Visualisation):
    pass


class Analyzer(AudioCapture):

    def get_band_levels(self) -> list[float]:
        return [uniform(0, 100) for _ in range(len(self.bands))]
