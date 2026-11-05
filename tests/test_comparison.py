import unittest
from unittest.mock import Mock

from rle_compressor.features.benchmark.model import BenchmarkResult
from rle_compressor.features.comparison.controller import ComparisonController
from rle_compressor.features.comparison.model import (
    ALL_SERIES,
    ChartView,
    ComparisonSettings,
    DataKind,
    Measure,
    Series,
    SortOrder,
    build_comparison,
    data_kind_of,
)
from rle_compressor.features.comparison.value_scale import ValueScale
from rle_compressor.features.compression.archive_format import Algorithm
from rle_compressor.features.compression.model import CompressionMode

RLE_LOSSLESS = Series(Algorithm.RLE, CompressionMode.LOSSLESS)
HUFFMAN_LOSSLESS = Series(Algorithm.HUFFMAN, CompressionMode.LOSSLESS)
RLE_LOSSY = Series(Algorithm.RLE, CompressionMode.LOSSY)


def result(file_name, series, size_after, size_before=1000):
    return BenchmarkResult(
        file_name=file_name,
        algorithm=series.algorithm,
        mode=series.mode,
        size_before=size_before,
        size_after=size_after,
        ratio=size_before / size_after,
        is_identical=True,
    )


RESULTS = [
    result("a.txt", RLE_LOSSLESS, 2000),
    result("a.txt", HUFFMAN_LOSSLESS, 500),
    result("b.bmp", RLE_LOSSLESS, 10),
    result("b.bmp", HUFFMAN_LOSSLESS, 100),
    result("b.bmp", RLE_LOSSY, 5),
]


def settings(**overrides):
    values = {
        "series": (RLE_LOSSLESS, HUFFMAN_LOSSLESS),
        "measure": Measure.RATIO,
        "data_kind": DataKind.ALL,
        "sort_order": SortOrder.FILE_NAME,
        "use_log_scale": False,
        "view": ChartView.BARS,
    }
    values.update(overrides)
    return ComparisonSettings(**values)


class BuildComparisonTest(unittest.TestCase):
    def test_only_selected_series_are_included(self):
        comparison = build_comparison(RESULTS, settings())

        self.assertEqual(comparison.series, (RLE_LOSSLESS, HUFFMAN_LOSSLESS))
        self.assertEqual(set(comparison.rows[1].cells), {RLE_LOSSLESS, HUFFMAN_LOSSLESS})

    def test_series_order_does_not_depend_on_selection_order(self):
        comparison = build_comparison(RESULTS, settings(series=(HUFFMAN_LOSSLESS, RLE_LOSSLESS)))
        self.assertEqual(comparison.series, (RLE_LOSSLESS, HUFFMAN_LOSSLESS))

    def test_best_series_and_wins_for_higher_is_better(self):
        comparison = build_comparison(RESULTS, settings())

        by_file = {row.file_name: row for row in comparison.rows}
        self.assertEqual(by_file["a.txt"].best_series, {HUFFMAN_LOSSLESS})
        self.assertEqual(by_file["b.bmp"].best_series, {RLE_LOSSLESS})
        self.assertEqual(comparison.wins, {RLE_LOSSLESS: 1, HUFFMAN_LOSSLESS: 1})

    def test_smallest_size_wins_when_lower_is_better(self):
        comparison = build_comparison(RESULTS, settings(measure=Measure.SIZE_AFTER))

        by_file = {row.file_name: row for row in comparison.rows}
        self.assertEqual(by_file["a.txt"].best_series, {HUFFMAN_LOSSLESS})

    def test_tie_counts_for_both_series(self):
        tied = [result("a", RLE_LOSSLESS, 10), result("a", HUFFMAN_LOSSLESS, 10)]
        comparison = build_comparison(tied, settings())
        self.assertEqual(comparison.wins, {RLE_LOSSLESS: 1, HUFFMAN_LOSSLESS: 1})

    def test_data_kind_filter(self):
        comparison = build_comparison(RESULTS, settings(data_kind=DataKind.IMAGE))
        self.assertEqual([row.file_name for row in comparison.rows], ["b.bmp"])

    def test_sort_by_best_result(self):
        comparison = build_comparison(RESULTS, settings(sort_order=SortOrder.BEST_RESULT))
        self.assertEqual([row.file_name for row in comparison.rows], ["b.bmp", "a.txt"])

    def test_sort_by_best_result_for_lower_is_better_starts_with_smallest(self):
        comparison = build_comparison(
            RESULTS, settings(measure=Measure.SIZE_AFTER, sort_order=SortOrder.BEST_RESULT)
        )
        self.assertEqual([row.file_name for row in comparison.rows], ["b.bmp", "a.txt"])

    def test_missing_series_leaves_file_with_fewer_cells(self):
        comparison = build_comparison(RESULTS, settings(series=(RLE_LOSSLESS, RLE_LOSSY)))

        by_file = {row.file_name: row for row in comparison.rows}
        self.assertEqual(set(by_file["a.txt"].cells), {RLE_LOSSLESS})

    def test_no_matching_results_gives_none(self):
        self.assertIsNone(build_comparison(RESULTS, settings(series=(ALL_SERIES[3],))))

    def test_measures_and_descriptions(self):
        row = build_comparison(RESULTS, settings(measure=Measure.SPACE_SAVED)).rows[0]

        self.assertAlmostEqual(row.cells[RLE_LOSSLESS].value, -100)
        self.assertEqual(row.cells[RLE_LOSSLESS].text, "-100.0 %")
        self.assertEqual(row.cells[HUFFMAN_LOSSLESS].text, "+50.0 %")

    def test_log_scale_is_ignored_when_measure_does_not_support_it(self):
        comparison = build_comparison(
            RESULTS, settings(measure=Measure.SPACE_SAVED, use_log_scale=True)
        )
        self.assertFalse(comparison.scale.is_log)

    def test_data_kind_of_file(self):
        self.assertIs(data_kind_of("Muzyka.MP3"), DataKind.AUDIO)
        self.assertIs(data_kind_of("dane.bin"), DataKind.OTHER)


class ValueScaleTest(unittest.TestCase):
    def test_scale_contains_values_and_baseline(self):
        scale = ValueScale.for_values([2.0, 3.0], baseline=1.0, is_log=False)
        self.assertEqual((scale.minimum, scale.maximum), (1.0, 3.0))

    def test_linear_fraction(self):
        scale = ValueScale(0, 10, 0, False)
        self.assertEqual(scale.fraction(5), 0.5)

    def test_log_fraction_treats_equal_ratios_equally(self):
        scale = ValueScale(1, 100, 1, True)
        self.assertAlmostEqual(scale.fraction(10), 0.5)

    def test_single_value_does_not_divide_by_zero(self):
        scale = ValueScale.for_values([1.0], baseline=1.0, is_log=True)
        self.assertEqual(scale.fraction(1.0), 0.0)
        self.assertEqual(scale.ticks(), [1.0])

    def test_linear_ticks_are_round_and_in_range(self):
        ticks = ValueScale(-100, 100, 0, False).ticks()
        self.assertEqual(ticks, [-100, -50, 0, 50, 100])

    def test_log_ticks_cover_range_of_compression_ratios(self):
        ticks = ValueScale(0.5, 124.6, 1, True).ticks()
        self.assertEqual(ticks, [0.5, 1, 2, 5, 10, 20, 50, 100])

    def test_wide_log_range_keeps_only_powers_of_ten(self):
        ticks = ValueScale(0.001, 1000, 1, True).ticks()
        self.assertEqual(len(ticks), 7)
        self.assertAlmostEqual(ticks[0], 0.001)
        self.assertAlmostEqual(ticks[-1], 1000)

    def test_log_baseline_without_reference_point_is_positive(self):
        scale = ValueScale.for_values([0.03, 5.0], baseline=None, is_log=True)
        self.assertAlmostEqual(scale.baseline, 0.02)

    def test_linear_without_reference_point_starts_at_zero(self):
        scale = ValueScale.for_values([3.0, 5.0], baseline=None, is_log=False)
        self.assertEqual(scale.baseline, 0.0)


class ComparisonControllerTest(unittest.TestCase):
    def setUp(self):
        self.view = Mock()
        self.view.current_settings.return_value = settings()
        self.controller = ComparisonController(self.view)

    def test_without_results_asks_to_run_tests(self):
        self.assertIn("uruchom testy", self.view.show_message.call_args.args[0])
        self.view.show_comparison.assert_not_called()

    def test_results_are_shown_in_selected_view(self):
        self.view.current_settings.return_value = settings(view=ChartView.HEAT_MAP)

        self.controller.set_results(RESULTS)

        comparison, view = self.view.show_comparison.call_args.args
        self.assertEqual(len(comparison.rows), 2)
        self.assertIs(view, ChartView.HEAT_MAP)

    def test_no_series_selected_shows_message(self):
        self.controller.set_results(RESULTS)
        self.view.show_comparison.reset_mock()
        self.view.current_settings.return_value = settings(series=())

        self.controller.refresh()

        self.view.show_comparison.assert_not_called()
        self.assertIn("Zaznacz", self.view.show_message.call_args.args[0])

    def test_empty_selection_of_results_shows_message(self):
        self.controller.set_results(RESULTS)
        self.view.current_settings.return_value = settings(data_kind=DataKind.AUDIO)

        self.controller.refresh()

        self.assertIn("Brak wyników", self.view.show_message.call_args.args[0])

    def test_log_scale_control_follows_measure(self):
        self.view.current_settings.return_value = settings(measure=Measure.SPACE_SAVED)
        self.controller.refresh()
        self.view.set_log_scale_available.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
