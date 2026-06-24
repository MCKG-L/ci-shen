import unittest

from cishen_clicker.modules import get_module_spec, list_module_keys


class ModuleRegistryTests(unittest.TestCase):
    def test_module_registry_exposes_system_home_modules(self):
        self.assertEqual(list_module_keys(), ["mining", "dungeon", "summon", "garden"])
        self.assertEqual(get_module_spec("mining").label, "挖矿")
        self.assertEqual(get_module_spec("dungeon").label, "副本")
        self.assertEqual(get_module_spec("summon").label, "召唤")
        self.assertEqual(get_module_spec("garden").label, "菜园管理")

    def test_get_module_spec_rejects_unknown_module(self):
        with self.assertRaises(KeyError):
            get_module_spec("unknown")


if __name__ == "__main__":
    unittest.main()
