from jinja2 import Environment

e = Environment()
t = {"nom": "N", "nom_utilisateur": "Nombre del usuario", "email": "E"}
print("dot_nom_util:", e.from_string("{{ t.nom_utilisateur }}").render(t=t))
print("dot_nom:", e.from_string("{{ t.nom }}").render(t=t))
print("bracket:", e.from_string("{{ t['nom_utilisateur'] }}").render(t=t))

t2 = {"email": "E"}
print("missing dot:", repr(e.from_string("{{ t.nom_utilisateur }}").render(t=t2)))
print("missing bracket:", repr(e.from_string("{{ t['nom_utilisateur'] }}").render(t=t2)))

# Test if t.nom_utilisateur is parsed as (t.nom) + utilisateur
t3 = {"nom": "ONLY_NOM", "email": "E"}
print("only nom key, dot_nom_util:", repr(e.from_string("{{ t.nom_utilisateur }}").render(t=t3)))
