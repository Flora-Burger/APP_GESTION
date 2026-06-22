"""Check which es.py module the running app would load."""
import sys
sys.path.insert(0, "e:/FLORA/APP_GESTION")

import backend.app.traductions.es as es_mod
print("module file:", es_mod.__file__)
print("nom key:", repr(es_mod.TRADUCTIONS.get("nom")))
