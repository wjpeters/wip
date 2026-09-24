import json
import pathlib
import unittest


class ContractTests(unittest.TestCase):
    def test_contract_schemas_are_valid_json_and_versioned(self):
        root = pathlib.Path(__file__).resolve().parents[3] / "packages" / "contracts"
        schemas = sorted(root.glob("*.schema.json"))
        self.assertEqual(len(schemas), 6)
        for path in schemas:
            schema = json.loads(path.read_text())
            self.assertTrue(schema["$id"].endswith(".v1"), path.name)
            self.assertEqual(schema["type"], "object")

    def test_financial_wire_values_are_decimal_strings(self):
        quote = json.loads((pathlib.Path(__file__).resolve().parents[3] / "packages/contracts/quote.schema.json").read_text())
        self.assertEqual(quote["properties"]["bid"]["type"], "string")


if __name__ == "__main__":
    unittest.main()
