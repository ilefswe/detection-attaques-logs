#!/usr/bin/env bash
# Pipeline complet : logs -> HDFS -> jar -> 5 jobs MapReduce -> rapport.
# Usage : ./scripts/lancer-analyses.sh [nombre_de_requetes_normales]   (défaut 500000)
set -e
cd "$(dirname "$0")/.."
NB=${1:-500000}
MODES="ip statut bruteforce scan attaques"

echo "==> 1/6 Génération des logs ($NB requêtes normales + attaques)"
mkdir -p data
python3 generer_logs.py data/access.log "$NB"

echo "==> 2/6 Compilation du projet Maven"
mvn -q clean package -DskipTests
ls -l target/securite-logs-1.jar

echo "==> 3/6 Copie des logs et du jar dans hadoop-master"
docker cp data/access.log hadoop-master:/root/access.log
docker cp target/securite-logs-1.jar hadoop-master:/root/securite-logs-1.jar

echo "==> 4/6 Chargement des logs dans HDFS (dossier logs/)"
docker exec hadoop-master bash -c "hdfs dfs -mkdir -p logs && hdfs dfs -put -f access.log logs/ && hdfs dfs -ls logs"

echo "==> 5/6 Lancement des 5 jobs MapReduce"
for m in $MODES; do
    echo "----- Job : $m -----"
    docker exec hadoop-master bash -c \
        "hdfs dfs -rm -r -f out_$m >/dev/null 2>&1; hadoop jar securite-logs-1.jar securite.LogDriver logs/access.log out_$m $m"
done

echo "==> 6/6 Récupération des résultats et rapport"
rm -rf resultats && mkdir -p resultats
for m in $MODES; do
    docker exec hadoop-master bash -c "hdfs dfs -cat out_$m/part-r-00000" > "resultats/$m.tsv"
done
python3 -c "import matplotlib" 2>/dev/null || pip install --user -q matplotlib
python3 rapport.py resultats
