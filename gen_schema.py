from genson import SchemaBuilder
import json
import sys


builder = SchemaBuilder()
_schema_attempt = {
    "type": "object",
    "properties": {
        "data": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "booster": {
                            "type": "object",
                            "patternProperties": {
                                ".*": {
                                    "type": "object",
                                    "properties": {
                                        "sheets": {
                                            "type": "object",
                                            "patternProperties": {
                                                ".*": {
                                                    "type": "object",
                                                    "properties": {
                                                        "cards": {
                                                            "type": "object",
                                                            "patternProperties": {
                                                                ".*": None
                                                            },
                                                        }
                                                    },
                                                }
                                            },
                                        }
                                    },
                                }
                            },
                        }
                    },
                }
            },
        }
    },
}

with open(sys.argv[1]) as f:
    d = json.load(f)

builder.add_object(d)

print(builder.to_json())
