"""Local tests for xiaoqi-forecaster (no Metaculus account, no LLM keys).

Run:  uv run python -m unittest discover -s tests -v
Everything here runs offline: the LLM is stubbed and the Metaculus API is
never called. What these tests CANNOT verify (needs a real account):
- fetching live tournament questions
- publishing a forecast end to end
- GitHub Actions runs
"""

import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone
from typing import get_args, get_origin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as bot_module
from main import XiaoqiForecastBot, _build_llms

from forecasting_tools import (
    BinaryPrediction,
    BinaryQuestion,
    DatePercentile,
    DateQuestion,
    GeneralLlm,
    MultipleChoiceQuestion,
    NumericQuestion,
    Percentile,
    PredictedOption,
    PredictedOptionList,
)


class FakeLlm(GeneralLlm):
    """A GeneralLlm that returns canned text instead of calling any API."""

    def __init__(self, canned: str):
        super().__init__(model="openrouter/openai/gpt-4o-mini", temperature=0)
        self._canned = canned

    async def invoke(self, prompt, *args, **kwargs):  # noqa: D102
        return self._canned


BINARY_REASONING = (
    "(a) About 6 months left. (b) Status quo: no change. "
    "(c) No scenario: the event never happens. "
    "(d) Yes scenario: the event happens as announced. "
    "Probability: 62%"
)
MC_REASONING = "Option_A: 0.5\nOption_B: 0.3\nOption_C: 0.2"
NUMERIC_REASONING = (
    "Percentile 10: 10\nPercentile 20: 20\nPercentile 40: 40\n"
    "Percentile 60: 60\nPercentile 80: 80\nPercentile 90: 90"
)
DATE_REASONING = (
    "Percentile 10: 2027-01-01\nPercentile 20: 2027-02-01\n"
    "Percentile 40: 2027-03-01\nPercentile 60: 2027-04-01\n"
    "Percentile 80: 2027-05-01\nPercentile 90: 2027-06-01"
)


async def fake_structure_output(text_to_structure, output_type, **kwargs):
    """Stand-in for forecasting_tools.structure_output."""
    if output_type is BinaryPrediction:
        return BinaryPrediction(prediction_in_decimal=0.62)
    if output_type is PredictedOptionList:
        return PredictedOptionList(
            predicted_options=[
                PredictedOption(option_name="Alpha", probability=0.5),
                PredictedOption(option_name="Beta", probability=0.3),
                PredictedOption(option_name="Gamma", probability=0.2),
            ]
        )
    if get_origin(output_type) is list:
        (inner,) = get_args(output_type)
        if inner is Percentile:
            return [
                Percentile(percentile=p, value=v)
                for p, v in [
                    (0.1, 10.0),
                    (0.2, 20.0),
                    (0.4, 40.0),
                    (0.6, 60.0),
                    (0.8, 80.0),
                    (0.9, 90.0),
                ]
            ]
        if inner is DatePercentile:
            return [
                DatePercentile(percentile=p, value=d)
                for p, d in [
                    (0.1, datetime(2027, 1, 1, tzinfo=timezone.utc)),
                    (0.2, datetime(2027, 2, 1, tzinfo=timezone.utc)),
                    (0.4, datetime(2027, 3, 1, tzinfo=timezone.utc)),
                    (0.6, datetime(2027, 4, 1, tzinfo=timezone.utc)),
                    (0.8, datetime(2027, 5, 1, tzinfo=timezone.utc)),
                    (0.9, datetime(2027, 6, 1, tzinfo=timezone.utc)),
                ]
            ]
    raise AssertionError(f"Unexpected output_type in fake: {output_type!r}")


def make_bot(canned: str) -> XiaoqiForecastBot:
    llm = FakeLlm(canned)
    return XiaoqiForecastBot(
        research_reports_per_question=1,
        predictions_per_research_report=2,
        publish_reports_to_metaculus=False,
        skip_previously_forecasted_questions=False,
        llms={
            "default": llm,
            "researcher": llm,
            "summarizer": llm,
            "parser": llm,
        },
    )


def make_binary() -> BinaryQuestion:
    return BinaryQuestion(
        question_text="Will the test event happen by 2027-06-30?",
        page_url="https://www.metaculus.com/questions/1/test/",
        background_info="Test background.",
        resolution_criteria="Resolves Yes if the event happens.",
        fine_print="",
        already_forecasted=False,
    )


def make_mc() -> MultipleChoiceQuestion:
    return MultipleChoiceQuestion(
        question_text="Which option will happen first?",
        page_url="https://www.metaculus.com/questions/2/test/",
        background_info="Test background.",
        resolution_criteria="Resolves to the option that happens first.",
        fine_print="",
        options=["Alpha", "Beta", "Gamma"],
        already_forecasted=False,
    )


def make_numeric() -> NumericQuestion:
    return NumericQuestion(
        question_text="How many points will the test score reach?",
        page_url="https://www.metaculus.com/questions/3/test/",
        background_info="Test background.",
        resolution_criteria="Resolves to the final score.",
        fine_print="",
        unit_of_measure="points",
        lower_bound=0.0,
        upper_bound=100.0,
        open_lower_bound=False,
        open_upper_bound=False,
        already_forecasted=False,
    )


def make_date() -> DateQuestion:
    return DateQuestion(
        question_text="When will the test event happen?",
        page_url="https://www.metaculus.com/questions/4/test/",
        background_info="Test background.",
        resolution_criteria="Resolves to the event date.",
        fine_print="",
        lower_bound=datetime(2027, 1, 1, tzinfo=timezone.utc),
        upper_bound=datetime(2027, 12, 31, tzinfo=timezone.utc),
        open_lower_bound=False,
        open_upper_bound=False,
        already_forecasted=False,
    )


class TestLlmConfig(unittest.TestCase):
    def test_build_llms_defaults(self):
        env = {k: v for k, v in os.environ.items()}
        os.environ.pop("ASKNEWS_CLIENT_ID", None)
        os.environ.pop("ASKNEWS_SECRET", None)
        try:
            llms = _build_llms()
        finally:
            os.environ.clear()
            os.environ.update(env)
        self.assertIn("default", llms)
        self.assertIn("parser", llms)
        self.assertIn("researcher", llms)
        self.assertIn("summarizer", llms)
        # Without AskNews keys the researcher falls back to a smart searcher.
        self.assertIsInstance(llms["researcher"], str)
        self.assertTrue(llms["researcher"].startswith("smart-searcher/"))

    def test_build_llms_asknews(self):
        os.environ["ASKNEWS_CLIENT_ID"] = "x"
        os.environ["ASKNEWS_SECRET"] = "y"
        try:
            llms = _build_llms()
        finally:
            os.environ.pop("ASKNEWS_CLIENT_ID", None)
            os.environ.pop("ASKNEWS_SECRET", None)
        self.assertEqual(llms["researcher"], "asknews/news-summaries")


class TestForecastPipeline(unittest.TestCase):
    def setUp(self):
        self._real_structure_output = bot_module.structure_output
        bot_module.structure_output = fake_structure_output

    def tearDown(self):
        bot_module.structure_output = self._real_structure_output

    def test_binary_forecast_in_range(self):
        bot = make_bot(BINARY_REASONING)
        result = asyncio.run(bot._run_forecast_on_binary(make_binary(), "research"))
        self.assertGreaterEqual(result.prediction_value, 0.01)
        self.assertLessEqual(result.prediction_value, 0.99)
        self.assertIn("Probability", result.reasoning)

    def test_multiple_choice_sums_to_one(self):
        bot = make_bot(MC_REASONING)
        result = asyncio.run(
            bot._run_forecast_on_multiple_choice(make_mc(), "research")
        )
        names = [o.option_name for o in result.prediction_value.predicted_options]
        self.assertEqual(names, ["Alpha", "Beta", "Gamma"])
        total = sum(
            o.probability for o in result.prediction_value.predicted_options
        )
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_numeric_percentiles_ordered(self):
        bot = make_bot(NUMERIC_REASONING)
        result = asyncio.run(bot._run_forecast_on_numeric(make_numeric(), "research"))
        values = [p.value for p in result.prediction_value.declared_percentiles]
        self.assertEqual(values, sorted(values))
        self.assertTrue(all(0.0 <= v <= 100.0 for v in values))

    def test_date_percentiles_ordered(self):
        bot = make_bot(DATE_REASONING)
        result = asyncio.run(bot._run_forecast_on_date(make_date(), "research"))
        values = [p.value for p in result.prediction_value.declared_percentiles]
        self.assertEqual(values, sorted(values))

    def test_forecast_questions_end_to_end_dry_run(self):
        """Full pipeline over 3 fake questions, publish off, no network."""
        bot = make_bot(BINARY_REASONING)
        reports = asyncio.run(
            bot.forecast_questions(
                [make_binary(), make_mc(), make_numeric()],
                return_exceptions=True,
            )
        )
        self.assertEqual(len(reports), 3)
        for report in reports:
            self.assertFalse(
                isinstance(report, BaseException), f"Pipeline failed: {report!r}"
            )
            self.assertIsNotNone(report.prediction)
            self.assertTrue(report.question.page_url)


if __name__ == "__main__":
    unittest.main()
