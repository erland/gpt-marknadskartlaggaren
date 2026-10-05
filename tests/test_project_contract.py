from pathlib import Path
import json
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTests(unittest.TestCase):
    def test_canonical_core_markers_exist(self):
        cfg = yaml.safe_load((ROOT / "gpt-project.yaml").read_text(encoding="utf-8"))
        text = (ROOT / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
        markers = cfg["instructions"]["core_contract"]["required_markers"]
        for marker in markers:
            self.assertIn(marker, text)

    def test_core_has_no_knowledge_dependency(self):
        cfg = yaml.safe_load((ROOT / "gpt-project.yaml").read_text(encoding="utf-8"))
        core = cfg["instructions"]["core_contract"]
        self.assertTrue(core["knowledge_may_not_be_required_for_core_behavior"])
        for dep in core.get("required_runtime_dependencies", []):
            self.assertFalse(str(dep).replace("\\", "/").lstrip("./").startswith("knowledge/"))

    def test_report_template_has_required_sections(self):
        text = (ROOT / "runtime" / "templates" / "market-map-report.md").read_text(encoding="utf-8")
        required = [
            "## Behov och avgränsning",
            "## Metod",
            "## Sammanfattande marknadsbild",
            "## Produktöversikt",
            "## Detaljerad produktgenomgång",
            "## Observationer, osäkerheter och avgränsningar",
            "## Källor",
        ]
        for heading in required:
            self.assertIn(heading, text)

    def test_required_eval_ids_are_present(self):
        required = {
            "bootstrap-core-001",
            "multiturn-retention-001",
            "terminal-contract-001",
            "no-knowledge-core-001",
            "market-many-commercial-001",
            "market-mixed-001",
            "market-onprem-001",
            "market-narrow-001",
            "market-broad-multistep-001",
            "market-conflict-001",
        }
        ids = set()
        for path in (ROOT / "evals" / "instruction-adherence").glob("*.yaml"):
            ids.add(yaml.safe_load(path.read_text(encoding="utf-8"))["id"])
        self.assertTrue(required.issubset(ids), sorted(required - ids))

    def test_eval_schema_is_valid_json(self):
        json.loads((ROOT / "schemas" / "eval-case.schema.json").read_text(encoding="utf-8"))

    def test_openai_plugin_is_active_stateful_peer_runtime(self):
        cfg = yaml.safe_load((ROOT / "gpt-project.yaml").read_text(encoding="utf-8"))
        candidates = {item["runtime_id"]: item for item in cfg["analysis"]["runtime"]["candidates"]}
        plugin_candidate = candidates["openai_plugin"]
        self.assertEqual(plugin_candidate["suitability"], "ready")
        self.assertTrue(plugin_candidate["activate_by_default"])
        plugin = cfg["runtime"]["openai_plugin"]
        self.assertTrue(plugin["enabled"])
        self.assertEqual(plugin["mode"], "skills_first")
        self.assertEqual(plugin["compatibility"], "ready_runtime_dependent")
        self.assertEqual(plugin["web_dependency"], "required_host_runtime")
        self.assertEqual(plugin["persistent_state"], "required_host_runtime")
        self.assertFalse(plugin["mcp_generated"])
        self.assertEqual(plugin["script_resources"], "none")
        self.assertTrue(cfg["build"]["build_plugin_zip"])

    def test_runtime_parity_model_exists_and_marks_plugin_ready(self):
        parity = yaml.safe_load((ROOT / "runtime-parity.yaml").read_text(encoding="utf-8"))
        plugin = parity["runtimes"]["openai_plugin"]
        self.assertEqual(plugin["suitability"], "ready")
        self.assertTrue(plugin["active"])
        self.assertEqual(plugin["compatibility"], "ready_runtime_dependent")


if __name__ == "__main__":
    unittest.main()
