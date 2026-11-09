"""Translation quality guards: allow formatting, never lose numeric facts."""
import importlib.util
import unittest
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "translate_article_summaries.py"
spec = importlib.util.spec_from_file_location("translation_quality", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

KOREAN = "연구 결과에 따르면 해당 환자의 회복률이 증가했습니다."


class SummaryTranslationValidationTests(unittest.TestCase):
    def test_thousands_separator_normalization(self):
        self.assertTrue(module.acceptable("The trial enrolled 1,000 people.", KOREAN + " 1000명이 참여했습니다."))

    def test_numeric_facts_cannot_be_dropped(self):
        self.assertEqual(module.rejection_reason("The trial enrolled 1,000 people.", KOREAN), "missing_numeric_facts")

    def test_decimal_value_cannot_change(self):
        self.assertEqual(module.rejection_reason("The rate was 1.5 percent.", KOREAN + " 1.6퍼센트였습니다."), "missing_numeric_facts")

    def test_decimal_zero_formatting(self):
        self.assertTrue(module.acceptable("The rate was 1.0 percent.", KOREAN + " 1퍼센트였습니다."))

    def test_short_or_non_korean_translation_rejected(self):
        self.assertEqual(module.rejection_reason("A source report", "짧음"), "too_short")
        self.assertEqual(module.rejection_reason("A source report", "This is a lengthy English translation"), "insufficient_korean")


if __name__ == "__main__":
    unittest.main()
