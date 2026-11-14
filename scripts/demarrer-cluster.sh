#!/usr/bin/env bash
# Crée (la 1re fois) ou redémarre le cluster Hadoop : 1 master + 2 workers.
set -e
IMAGE=liliasfaxi/hadoop-cluster:latest

echo "==> Réseau Docker 'hadoop'"
docker network inspect hadoop >/dev/null 2>&1 || docker network create --driver=bridge hadoop

if docker ps -a --format '{{.Names}}' | grep -q '^hadoop-master$'; then
    echo "==> Les conteneurs existent déjà : démarrage"
    docker start hadoop-master hadoop-worker1 hadoop-worker2
else
    echo "==> Téléchargement de l'image (la 1re fois : quelques minutes)"
    docker pull $IMAGE
    echo "==> Création des 3 conteneurs"
    docker run -itd --net=hadoop -p 9870:9870 -p 8088:8088 -p 7077:7077 -p 16010:16010 \
        --name hadoop-master --hostname hadoop-master $IMAGE
    docker run -itd -p 8040:8042 --net=hadoop --name hadoop-worker1 --hostname hadoop-worker1 $IMAGE
    docker run -itd -p 8041:8042 --net=hadoop --name hadoop-worker2 --hostname hadoop-worker2 $IMAGE
fi

echo "==> Attente du démarrage des conteneurs"
sleep 10

echo "==> Démarrage de Hadoop (HDFS + YARN)"
docker exec hadoop-master bash -c "cd /root && ./start-hadoop.sh"

echo "==> Attente de la sortie du mode sécurisé de HDFS"
docker exec hadoop-master bash -c "hdfs dfsadmin -safemode wait"

echo "==> Services Java lancés sur le master :"
docker exec hadoop-master bash -c "jps" || true
docker ps
echo
echo "Cluster prêt. Interfaces web : onglet PORTS -> 9870 (HDFS) et 8088 (YARN)."
