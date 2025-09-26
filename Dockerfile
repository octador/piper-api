# piper-backend/Dockerfile

# Étape 1: Utiliser une image Python officielle comme base
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /code

# Étape 2: Installer les dépendances système (unzip pour extraire Piper)
RUN apt-get update && apt-get install -y unzip && rm -rf /var/lib/apt/lists/*

# Étape 3: Installer Piper
# Copier la nouvelle archive .tar.gz
COPY ./docker/piper_linux_x86_64.tar.gz /tmp/piper.tar.gz

# Utiliser tar pour extraire l'archive. L'option -C spécifie le répertoire de destination.
RUN tar -xzf /tmp/piper.tar.gz -C /usr/local/bin/ && \
    rm /tmp/piper.tar.gz && \
    chmod +x /usr/local/bin/piper/piper

# Ajouter le dossier de piper au PATH pour pouvoir l'appeler directement
ENV PATH="/usr/local/bin/piper:${PATH}"

# Étape 4: Copier les modèles de voix
# Assure-toi que le dossier 'piper' existe bien dans 'piper-backend/docker/'
COPY ./docker/piper/ /models/

# Étape 5: Installer les dépendances Python
# On copie d'abord le code de l'app, puis on installe les dépendances
COPY ./app /code/app
# Ici, tu installes directement "fastapi[all]". Si tu as d'autres dépendances,
# il serait mieux de créer un fichier 'requirements.txt' dans 'piper-backend/'
# et de le copier/installer comme ceci :
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir "fastapi[all]"

# Étape 6: Définir la commande pour lancer l'API au démarrage du conteneur
# Uvicorn est un serveur ASGI qui exécute notre application FastAPI
# --host 0.0.0.0 permet d'écouter sur toutes les interfaces réseau
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]