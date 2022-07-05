#!/bin/bash

FILE=/tmp/schema-$(date +%s)
python gen_schema.py data/card.json > $FILE
jsonschema-gentypes --json-schema=$FILE --python=card_type_gen.py
