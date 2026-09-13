import unittest

from src.tinyagent import estimate_tokens, minify_context


class MinifierTests(unittest.TestCase):
    def test_removes_redundant_structure_and_duplicates(self):
        context = [
            {"type": "tool_result", "tool": "get_data", "source": "file", "query": "a.cs", "result": "A", "reason": "local"},
            {"type": "tool_result", "tool": "get_data", "source": "file", "query": "a.cs", "result": "A", "reason": "local"},
        ]
        result = minify_context(context)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"d": "file", "q": "a.cs", "r": "A"})

    def test_compaction_reduces_representation(self):
        context = [{"type": "tool_result", "tool": "get_data", "source": "file", "query": "a.cs", "result": "A" * 100}]
        compact = minify_context(context)
        self.assertLess(estimate_tokens(repr(compact)), estimate_tokens(repr(context)))


if __name__ == "__main__":
    unittest.main()
