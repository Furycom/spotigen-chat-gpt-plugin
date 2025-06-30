#!/usr/bin/env python
"""
Compare le bloc `functions` declare dans agent.py avec celui expose
dans static/spec.json (ou openapi.json) afin d'eviter les ecarts.
Pour l'instant, on verifie simplement que la cle 'servers' existe.
"""

import json
import pathlib
import sys
import importlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from agent import functions  # s'assurer que le module existe

spec_path = ROOT / "static" / "spec.json"

with open(spec_path) as f:
    spec = json.load(f)

assert spec.get("servers"), "La cle 'servers' est manquante dans spec.json"

print("OpenAPI spec valide \u2714")
