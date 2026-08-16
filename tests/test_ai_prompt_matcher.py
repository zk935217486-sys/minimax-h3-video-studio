import unittest

from backend.ai_prompt_matcher import AIPromptMatcher


class PromptMatcherTests(unittest.TestCase):
    def setUp(self):
        self.matcher = AIPromptMatcher()

    def test_nature_prompt_selects_aerial_cinematic_skill(self):
        result = self.matcher.match_and_generate("清晨的海边，白色火车沿着悬崖驶过")
        self.assertEqual(result["analysis"]["scene"], "nature")
        self.assertEqual(result["analysis"]["camera"], "aerial")
        self.assertIn("航拍视角", result["enhanced"])

    def test_product_prompt_selects_commercial_style(self):
        analysis = self.matcher.analyze("一块智能手表在影棚中旋转")
        self.assertEqual(analysis["scene"], "product")
        self.assertEqual(analysis["style"], "commercial")

    def test_unknown_prompt_uses_reference_defaults(self):
        analysis = self.matcher.analyze("一个抽象的画面")
        self.assertEqual(analysis["style"], "cinematic")
        self.assertEqual(analysis["camera"], "slow_push")
        self.assertEqual(analysis["mood"], "peaceful")


if __name__ == "__main__":
    unittest.main()
