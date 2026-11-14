#!/usr/bin/env python3
"""
Génère un faux fichier de logs Apache (format "combined") avec du trafic normal
et 5 attaquants cachés dedans. Usage :
    python3 generer_logs.py access.log 500000
"""
import random
import sys
from datetime import datetime, timedelta

fichier = sys.argv[1] if len(sys.argv) > 1 else "access.log"
nb_normales = int(sys.argv[2]) if len(sys.argv) > 2 else 500000
random.seed(2026)

PAGES = ["/", "/index.html", "/produits", "/produits?id=12", "/produits?id=45", "/panier",
         "/contact", "/a-propos", "/css/style.css", "/js/app.js", "/images/logo.png",
         "/blog", "/blog/article-1", "/blog/article-2", "/recherche?q=chaussures"]
AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0",
          "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1",
          "Mozilla/5.0 (X11; Linux x86_64) Firefox/131.0"]
debut = datetime(2026, 11, 14, 0, 0, 0)
utilisateurs = [f"41.{random.randint(224, 231)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                for _ in range(max(300, nb_normales // 50))]


def ligne(ip, methode, url, statut, agent=None, taille=None):
    t = debut + timedelta(seconds=random.randint(0, 86399))
    taille = taille if taille is not None else (random.randint(300, 20000) if statut == 200 else 0)
    agent = agent or random.choice(AGENTS)
    return (f'{ip} - - [{t:%d/%b/%Y:%H:%M:%S} +0100] "{methode} {url} HTTP/1.1" '
            f'{statut} {taille} "-" "{agent}"\n')


lignes = []
# 1) Trafic normal (avec quelques erreurs ordinaires : mot de passe oublié, lien cassé)
for _ in range(nb_normales):
    ip = random.choice(utilisateurs)
    r = random.random()
    if r < 0.02:
        lignes.append(ligne(ip, "POST", "/login", random.choice([200, 200, 401])))
    elif r < 0.03:
        lignes.append(ligne(ip, "GET", random.choice(["/ancienne-page", "/favicon.ico"]), 404))
    else:
        lignes.append(ligne(ip, "GET", random.choice(PAGES), 200))

# 2) Attaquant brute force : 600 mots de passe essayés sur /login, puis un succès
for _ in range(600):
    lignes.append(ligne("185.220.101.45", "POST", "/login", 401, "python-requests/2.31"))
lignes.append(ligne("185.220.101.45", "POST", "/login", 200, "python-requests/2.31"))

# 3) Scanner de vulnérabilités : teste des centaines de chemins sensibles
CHEMINS = ["/admin", "/wp-login.php", "/.env", "/phpmyadmin", "/backup.zip", "/.git/config",
           "/config.php", "/server-status", "/administrator", "/db.sql"]
for i in range(900):
    lignes.append(ligne("45.155.205.233", "GET", f"{random.choice(CHEMINS)}?v={i}", 404, "Nikto/2.5.0"))

# 4) Injections SQL, XSS et Path Traversal (encodées comme dans un vrai log)
for _ in range(150):
    lignes.append(ligne("103.75.190.12", "GET", random.choice([
        "/produits?id=1%27%20OR%20%271%27=%271",
        "/produits?id=1%20UNION%20SELECT%20username,password%20FROM%20users",
        "/produits?id=1;%20SELECT%20sleep(5)--"]), 500, "sqlmap/1.8"))
for _ in range(80):
    lignes.append(ligne("91.92.243.7", "GET", random.choice([
        "/recherche?q=%3Cscript%3Ealert(1)%3C/script%3E",
        "/recherche?q=%3Cimg%20src=x%20onerror=alert(document.cookie)%3E"]), 200))
for _ in range(60):
    lignes.append(ligne("91.92.243.7", "GET", random.choice([
        "/telecharger?fichier=../../../../etc/passwd",
        "/telecharger?fichier=..%2F..%2F..%2Fetc%2Fpasswd"]), 403))

# 5) Flood (DoS applicatif) : une IP qui martèle la page d'accueil
for _ in range(max(2000, nb_normales // 20)):
    lignes.append(ligne("196.203.77.18", "GET", "/", 200, "Go-http-client/1.1"))

# Quelques lignes corrompues
lignes += ["ligne illisible\n", "\n", "GET / HTTP/1.1\n"]

random.shuffle(lignes)
with open(fichier, "w") as f:
    f.writelines(lignes)
print(f"{len(lignes)} lignes écrites dans {fichier}")
