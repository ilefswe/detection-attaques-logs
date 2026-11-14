#!/usr/bin/env python3
"""Lit les résultats des 5 jobs (resultats/*.tsv), affiche le rapport d'alertes
et crée resultats/rapport.png (graphiques) et resultats/rapport.md (tableaux)."""
import os
import sys

dossier = sys.argv[1] if len(sys.argv) > 1 else "resultats"


def lire(mode):
    lignes = []
    with open(os.path.join(dossier, f"{mode}.tsv")) as f:
        for l in f:
            if "\t" in l:
                cle, val = l.rstrip("\n").split("\t")
                lignes.append((cle, int(val)))
    return sorted(lignes, key=lambda x: x[1], reverse=True)


ip, statut, brute, scan, attaques = (lire(m) for m in ["ip", "statut", "bruteforce", "scan", "attaques"])
total = sum(v for _, v in statut)
flood = [(c, v) for c, v in ip if v >= 1000]


def tableau(titre, entetes, lignes):
    md = [f"### {titre}", "", "| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    md += [f"| {c} | {v:,} |".replace(",", " ") for c, v in lignes] or ["| (aucune) | |"]
    print(f"\n{titre}")
    print("-" * len(titre))
    for c, v in lignes or [("(aucune)", 0)]:
        print(f"  {c:<20} {v:>10,}".replace(",", " "))
    return md + [""]


md = ["# Rapport d'analyse des logs", "", f"Requêtes analysées : **{total:,}**".replace(",", " "), ""]
print("=" * 60)
print("  RAPPORT DE DÉTECTION D'ATTAQUES")
print(f"  Requêtes analysées : {total:,}".replace(",", " "))
print("=" * 60)
md += tableau("[ALERTE] Brute force sur /login (>= 20 échecs)", ["IP", "Échecs de connexion"], brute)
md += tableau("[ALERTE] Scan de vulnérabilités (>= 20 erreurs 404)", ["IP", "Erreurs 404"], scan)
md += tableau("[ALERTE] Flood / DoS (>= 1000 requêtes)", ["IP", "Requêtes"], flood)
md += tableau("[ALERTE] Attaques détectées par signature", ["Type", "Requêtes"], attaques)
md += tableau("Top 10 des IP les plus actives", ["IP", "Requêtes"], ip[:10])
md += tableau("Répartition des codes HTTP", ["Code", "Nombre"], statut)

with open(os.path.join(dossier, "rapport.md"), "w") as f:
    f.write("\n".join(md))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    top = ip[:10][::-1]
    couleurs = ["#c0392b" if v >= 1000 or c in dict(brute) or c in dict(scan) else "#7f8c8d" for c, v in top]
    axes[0].barh([c for c, _ in top], [v for _, v in top], color=couleurs)
    axes[0].set_xscale("log")
    axes[0].set_title("Top 10 IP (requêtes, échelle log)\nrouge = alerte brute force, scan ou flood")
    axes[1].bar([c for c, _ in statut], [v for _, v in statut], color="#2c3e50")
    axes[1].set_yscale("log")
    axes[1].set_title("Codes HTTP (échelle log)")
    axes[2].barh([c for c, _ in attaques][::-1], [v for _, v in attaques][::-1], color="#c0392b")
    axes[2].set_title("Attaques détectées par signature")
    plt.tight_layout()
    plt.savefig(os.path.join(dossier, "rapport.png"), dpi=120)
    print(f"\nGraphiques : {dossier}/rapport.png   Tableaux : {dossier}/rapport.md")
except ImportError:
    print(f"\n(matplotlib absent : pas de graphique)   Tableaux : {dossier}/rapport.md")
