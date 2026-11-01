import unittest
import numpy as np

from tools.voice_quality import autocorr_f0, detect_activity, run_intervals, syllable_peaks


class VoiceQualityMathTests(unittest.TestCase):
    def test_autocorrelation_tracks_pure_tone(self):
        sr = 22050
        t = np.arange(int(sr * 0.04)) / sr
        f0, periodicity = autocorr_f0(np.sin(2 * np.pi * 137.0 * t), sr)
        self.assertAlmostEqual(f0, 137.0, delta=4.0)
        self.assertGreater(periodicity, 0.7)

    def test_autocorrelation_rejects_silence(self):
        f0, strength = autocorr_f0(np.zeros(882))
        self.assertEqual(f0, 0.0)
        self.assertEqual(strength, 0.0)

    def test_run_intervals_counts_activity_runs(self):
        self.assertEqual(run_intervals(np.array([0, 1, 1, 0, 1, 0], dtype=bool)), [(1, 3), (4, 5)])
        self.assertEqual(run_intervals(np.array([], dtype=bool)), [])

    def test_energy_gate_finds_loud_frames(self):
        active, threshold = detect_activity(np.array([-80., -80., -30., -30.]))
        self.assertEqual(active.tolist(), [False, False, True, True])
        self.assertGreater(threshold, -80.)

    def test_syllable_envelope_peaks_are_separated(self):
        # Two clear Gaussian-like bursts with a quiet gap.
        n = 100
        x = np.full(n, -55.0)
        for center in (25, 70):
            x += 15 * np.exp(-0.5 * ((np.arange(n) - center) / 4) ** 2)
        peaks = syllable_peaks(x, x > -52, 0.01)
        self.assertEqual(len(peaks), 2)
        self.assertLess(abs(peaks[0] - 25), 4)
        self.assertLess(abs(peaks[1] - 70), 4)


if __name__ == "__main__":
    unittest.main()
