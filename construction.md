### Création venv avec python
#### 1. Va dans ton dossier projet
mkdir mon_projet && cd mon_projet

#### 2. Crée le venv (le dossier .venv sera créé ici)
python3 -m venv .venv

#### 3. Active-le
source .venv/bin/activate

#### 4. Ton prompt changera → (.venv) user@machine:~$
#### Installe tes dépendances
pip install pyodbc python-dotenv

#### Pour tkinter (GUI standard Python), il est inclus mais vérifie :
python3 -c "import tkinter; print('OK')"
#### Si erreur : sudo apt install python3-tk

#### 5. Génère le requirements.txt
pip freeze > requirements.txt

#### 6. Pour désactiver le venv quand tu as fini
deactivate

# Ajouter la clé Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -

# Ajouter le dépôt Microsoft (Ubuntu 22.04)
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
    | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Installer le driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Vérifier
python3 -c "import pyodbc; print(pyodbc.drivers())"
# Doit afficher : ['ODBC Driver 17 for SQL Server']