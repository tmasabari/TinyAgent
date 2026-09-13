import unittest
from datetime import datetime, timezone

from src.tinyagent import Runtime, TinyAgent, preflight
from src.tinyagent_nfr import DataCacheHook, RecordingEvents


class Deny:
    def before(self, context):
        return False if context.kind == "execute" else None

    def after(self, context, result):
        return None


class TinyAgentTests(unittest.TestCase):
    def runtime(self):
        return Runtime(
            knowledge_cutoff=datetime(2025, 6, 1, tzinfo=timezone.utc),
            current_datetime=datetime(2026, 9, 13, tzinfo=timezone.utc),
        )

    def test_preflight_requires_web_for_current_request(self):
        result = preflight("latest Python release", self.runtime())
        self.assertEqual(result[0].source.value, "web")

    def test_cache_hit_bypasses_data_adapter(self):
        calls = []
        cache = DataCacheHook()
        events = RecordingEvents()
        agent = TinyAgent(
            lambda system, request, context: {"answer": context[0]["result"]},
            lambda source, query: calls.append(query) or "fresh",
            lambda operation, param: None,
            self.runtime(),
            hooks=(cache,),
            events=events,
        )
        self.assertEqual(agent.run("latest Python release"), "fresh")
        self.assertEqual(agent.run("latest Python release"), "fresh")
        self.assertEqual(calls, ["latest Python release"])
        self.assertIn("ContextCacheHit", [name for name, _ in events.events])

    def test_security_hook_denies_execution(self):
        agent = TinyAgent(
            lambda system, request, context: {"execute": {"operation": "os", "param": "bad"}},
            lambda source, query: None,
            lambda operation, param: self.fail("must not execute"),
            self.runtime(),
            max_iterations=1,
            hooks=(Deny(),),
        )
        with self.assertRaises(PermissionError):
            agent.run("do it")


if __name__ == "__main__":
    unittest.main()
