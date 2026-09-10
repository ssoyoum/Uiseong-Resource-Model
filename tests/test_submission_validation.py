"""Regression checks for misleading submission counts and plotting cohorts."""

import unittest

import pandas as pd

from analysis.validate_sgis_submission import figure_cohort_check, number_claim, table_claim


class SubmissionValidationTests(unittest.TestCase):
    def test_wrong_table_count_is_not_hidden_by_correct_number_elsewhere(self):
        result = table_claim("본문: 175개\n| 5분 인구 확보 | 220 | 원수집 |", "5분 인구 확보", 175)
        self.assertEqual(result["status"], "FAIL")

    def test_ambiguous_duplicate_table_claim_fails(self):
        result = table_claim("| 분석 목록 | 427 | 전체 |\n| 분석 목록 | 426 | 전체 |", "분석 목록", 427)
        self.assertEqual(result["status"], "FAIL")

    def test_same_scatter_count_with_excluded_facility_fails(self):
        paired = pd.DataFrame({"pond_id": ["2", "3"]})
        result = figure_cohort_check({"plotted_pond_ids": ["1", "3"], "paired_count": 2}, paired)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["details"]["unexpected_ids"], ["1"])

    def test_duplicate_scatter_id_fails(self):
        paired = pd.DataFrame({"pond_id": ["2", "3"]})
        self.assertEqual(figure_cohort_check({"plotted_pond_ids": ["2", "2", "3"], "paired_count": 2}, paired)["status"], "FAIL")

    def test_matching_cohort_and_missing_claim(self):
        paired = pd.DataFrame({"pond_id": ["2", "3"]})
        self.assertEqual(figure_cohort_check({"plotted_pond_ids": ["3", "2"], "paired_count": 2}, paired)["status"], "PASS")
        self.assertEqual(number_claim("", "missing", r"총 (\d+)개", 427)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
