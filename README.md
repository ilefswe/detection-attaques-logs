# Détection d'attaques dans les logs d'un serveur web avec Hadoop MapReduce

Projet Big Data (traitement batch) : un programme MapReduce analyse les logs d'accès Apache d'un site web
et détecte 5 types de menaces : **brute force** sur `/login`, **scan** de vulnérabilités,
**injections SQL**, **XSS / Path Traversal** et **flood (DoS)**.

## Démarrage rapide (GitHub Codespaces)

```bash
./scripts/demarrer-cluster.sh      # cluster Hadoop : 1 master + 2 workers (Docker)
./scripts/lancer-analyses.sh       # logs -> HDFS -> 5 jobs MapReduce -> rapport
```

Interfaces web : onglet **PORTS** → `9870` (HDFS) et `8088` (YARN).
Résultats : `resultats/rapport.md` et `resultats/rapport.png`.

## Les 5 analyses (un seul job, paramètre `mode`)

| Mode | Question | Règle |
|---|---|---|
| `ip` | Qui envoie le plus de requêtes ? | compte les requêtes par IP |
| `statut` | Quelle est la santé du site ? | compte les codes HTTP |
| `bruteforce` | Qui essaie de deviner des mots de passe ? | `POST /login` → `401`, alerte si ≥ 20 par IP |
| `scan` | Qui cherche des pages cachées ? | réponses `404`, alerte si ≥ 20 par IP |
| `attaques` | Quelles attaques par injection ? | signatures SQLi, XSS, Path Traversal dans l'URL |

```bash
hadoop jar securite-logs-1.jar securite.LogDriver [-D seuil=N] <entrée> <sortie> <mode>
```

## Structure

```
.devcontainer/devcontainer.json   configuration Codespaces (Docker, Java, Maven, Python)
pom.xml                           projet Maven (Hadoop 3.3.6, Java 8)
src/main/java/securite/           LogMapper, SommeCombiner, AlerteReducer, LogDriver
generer_logs.py                   générateur de logs réalistes avec 5 attaquants cachés
rapport.py                        rapport d'alertes + graphiques
scripts/                          démarrage du cluster et pipeline complet
```
