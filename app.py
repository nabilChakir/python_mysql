from flask import Flask, render_template, request, render_template_string, redirect, url_for

# DeprecationWarning: 'flask.escape' is deprecated and will be removed 
# in Flask 2.4. Import 'markupsafe.escape' instead
from markupsafe import escape

# Bibliothèque python-dotenv permet charger les variables d'environnement à partir du fichier .env se trouvant
# idéalement à la racine du projet
from dotenv import load_dotenv
import mysql.connector
import os
import datetime
import re

# L'objet app est une instance de la classe Flask. Il s'agit d'un objet qui fournit toutes les fonctionnalités de 
# l'application Flask, telles que le routage des URL, le rendu des templates, la gestion des requêtes et 
# des réponses, ...
# __name__ est une variable spéciale en Python qui représente le nom du module actuel. 
# Lorsque vous utilisez __name__ comme argument pour la classe Flask, cela indique à Flask de déterminer 
# le nom de l'application en fonction du module dans lequel vous l'exécutez.
app = Flask(__name__)

# Répertoire par défaut pour le fichier .env est le répertoire courant. Si on définit .env dans un répertoire différent,
# il faudra mettre le chemin complet du fichier .env comme ceci: load_dotenv(dotenv_path="path_to_.env").
# load_dotenv() charge les variables d'environnement à partir d'un fichier .env et les rend disponibles en tant que variables 
# d'environnement dans le contexte d'exécution du script Python. Cela facilite l'utilisation et l'accès aux variables d'environnement 
# spécifiques à votre projet sans avoir à les définir manuellement dans l'environnement global de votre système d'exploitation.
load_dotenv()

# print(os.environ.items())  # checkpoint pour constater ce qui est dit dans le commentaire précédent

## MySQL
def connect_to_DB(): 
    # os.getenv("variable_key") renvoie la valeur de la clé de la variable d'environnement, si elle existe.
    passwd = os.getenv("MYSQL_PASSWORD")
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=passwd
        )
    # L'objet db_connection représente la connexion active à la base de données MySQL
    return db_connection

def createDB():
    db_connection=connect_to_DB()
    # L'objet mycursor est utilisé pour exécuter des requêtes SQL ou récupérer les résultats 
    mycursor=db_connection.cursor()
    # Debug
    mycursor.execute("SHOW DATABASES")
    sql_output = mycursor.fetchall()    # Récupère TOUTES les lignes du résultat d'une requête SQL précédemment 
    # exécutée et renvoie les données sous la forme d'une liste de tuples.
    print(f"DB's avant hypothétique création de la DB \"flaskDB\": {sql_output}")

    mycursor.execute("CREATE DATABASE IF NOT EXISTS flaskDB")

    mycursor.execute("SHOW DATABASES")
    sql_output = mycursor.fetchall()
    print(f"DB's après hypothétique création de la DB \"flaskDB\": {sql_output}")

    # Création hypothétique de la table "formulaire" liée à la DB "flaskDB"
    mycursor.execute("USE flaskDB")
    mycursor.execute("CREATE TABLE IF NOT EXISTS formulaire ( idFormulaire INT AUTO_INCREMENT PRIMARY KEY, "+
                     "dateHeure DATETIME, nom VARCHAR(20), prenom VARCHAR(20), genre CHAR(1),  pays VARCHAR(20), "+
                     "email VARCHAR(30), sujet VARCHAR(50), message VARCHAR(300) )")

    # Debug
    mycursor.execute("DESCRIBE formulaire")
    sql_output = mycursor.fetchall()
    db_connection.close()
    print(f"Table \"formulaire\": {sql_output}")

def updateDB(nom, prenom, genre, pays, email, sujets, message):
    db_connection=connect_to_DB()
    mycursor=db_connection.cursor()
    dateHeure = datetime.datetime.now()
    mycursor.execute("USE flaskDB")
    mycursor.execute("SELECT MAX(idFormulaire) FROM formulaire")
    result = mycursor.fetchone()    # Récupère LA prochaine ligne de résultats de la requête SQL effectuée précédemment. 
    # La méthode fetchone() renvoie un tuple contenant les valeurs de la première ligne de résultat, puis déplace 
    # le curseur vers la ligne suivante.
    next_id = result[0] + 1 if result[0] is not None else 1 # règle le problème qui est que lors de la création de
    # la DB et de sa table, la valeur par défaut de la colonne idFormulaire est égal à None
    query = "INSERT INTO formulaire(idFormulaire, dateHeure, nom, prenom, genre, pays, email, sujet, message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (next_id, dateHeure, nom, prenom, genre, pays, email, sujets, message)
    mycursor.execute(query, values)
    db_connection.commit()  # enregistre les modifications apportées 
    db_connection.close()
    print("DB mise à jour !")
##


# Désactive l'échappement automatique des variables dans les templates Jinja, permettrait de constater les effets d'une attaque XSS (*)
# app.jinja_env.autoescape = False

# Les routes sont des URLs spécifiques à votre application Flask. Elles indiquent à Flask quelles fonctions doivent 
# être exécutées lorsque l'utilisateur accède à une URL particulière.
# La liste methods=['GET'] spécifie que cette route ne sera associée qu'à la méthode GET. Cela signifie que lorsque 
# l'utilisateur accède à l'URL spécifiée, cette fonction sera appelée uniquement lorsqu'il effectue une requête 
# GET. Lorsque la méthode n'est pas spécifiée, la route est associée par défaut à la méthode GET.
@app.route('/') 
def index():
    return render_template('index.html')

# Le choix des noms de fonctions (index(), submit_form(), etc.) est libre, mais il est important de les choisir 
# de manière significative pour faciliter la compréhension et la maintenabilité du code.
# Le décorateur @app.route est l'élément clé qui permet d'associer une fonction à une route spécifique dans Flask. 
# Il facilite la gestion des différentes URL de votre application et permet d'organiser efficacement le code.
@app.route('/traitement', methods=['POST','GET'])
def submit_form():

    if request.method == 'POST':
        # SANITISATION des entrées utilisateur
        
        # request.form.get('clé') ne renvoies pas d'erreur (renvoies None) si la clé 'clé' n'existe pas >< à request.form['clé'].
        # request.form contient les données du formulaire sous la forme d'un dictionnaire like object, 
        # où les clés sont les noms des champs et les valeurs sont les valeurs soumises. Le nom des clés 
        # correspond à l attribut name du champ (cfr index.html). Dans le contexte de Flask, la fonction escape 
        # est importée à partir du module werkzeug.security et elle effectue une échappement HTML. 
        # Elle remplace les caractères spéciaux tels que <, >, &, ' et " par leur équivalent HTML 
        # (&lt;, &gt;, &amp;, &#39; et &quot; respectivement)
        prenom = escape(request.form.get('prenom'))
        nom = escape(request.form.get('nom'))
        email = escape(request.form.get('email'))
        message = escape(request.form.get('message'))
        pays = escape(request.form.get('pays'))
        genre = escape(request.form.get('genre'))
        sujets = request.form.getlist('sujets')

        honeypot = request.form.get('spam')
        # Si le champ honeypot est rempli, c'est probablement une soumission de spam
        if honeypot:
            return render_template_string('Salut le bot!') 

        # VALIDATION des entrées utilisateur

        errors = []  # Liste pour stocker les messages d'erreur
        prenom_pattern = r"^[A-Za-z]{3,15}$"
        email_pattern = r"^[\w.%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(prenom_pattern, prenom):
           errors.append("Le prénom n'est pas valide.")

        if not re.match(prenom_pattern, nom):
            errors.append("Le nom n'est pas valide.")

        if not re.match(email_pattern, email):
            errors.append("Le mail n'est pas valide.")
        else:
            if ".." in email:
                errors.append("Le mail n'est pas valide.")

        if not pays:
            errors.append("Veuillez sélectionner un pays!")

        if not genre:
            errors.append("Veuillez sélectionner un genre")
        
        if not message:
            errors.append("Veuillez entrer un message")
        
        if not sujets:
            sujets.append('Autre')
        
        if errors:
            return render_template('index.html', errors=errors)
        
        mem=''
        for sujet in sujets:
            mem += sujet+" "
    
        updateDB(nom, prenom, genre, pays, email, mem, message)
        # Si la validation réussit, le programme affiche une page de remerciement avec le résumé des informations
        return render_template('thankyou.html', prenom=prenom, nom=nom, email=email, pays=pays, message=message, genre=genre, sujets=sujets)
    else:
        # L'instruction redirect(url_for('index')) dans Flask permet de rediriger l'utilisateur vers une autre page 
        # de l'application. La fonction url_for génère une URL pour une route spécifique dans l'application Flask. 
        # L'argument 'index' correspond au nom de la fonction de vue associée à la route vers laquelle vous souhaitez 
        # rediriger l'utilisateur.La fonction redirect génère une réponse HTTP de redirection. Elle prend en argument 
        # l'URL cible vers laquelle vous souhaitez rediriger l'utilisateur. En combinant ces deux instructions, 
        # redirect(url_for('index')) génère une réponse HTTP de redirection vers l'URL associée à la fonction de 
        # vue nommée 'index'. Ainsi, lorsque l'utilisateur accède à la route correspondante, il est automatiquement 
        # redirigé vers cette URL spécifiée
         return redirect(url_for('index'))
    
if __name__ == '__main__':
    createDB()
    app.config['DEBUG'] = False  # à ne jamais mettre en True en PRODUCTION (fait pour aider le DEVELOPPEMENT)
    app.run()


    





