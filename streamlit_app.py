# MOYENNE DE CLASSE DANS TOUS NE MARCHE PAS
# prendre en compte les non notés
import pronotepy
from pronotepy.ent import ac_reims
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from datetime import datetime

# Connexion à Pronote
def connect_to_pronote(username, password):
    return pronotepy.Client(
        'https://0101016a.index-education.net/pronote/eleve.html',
        username=username,
        password=password,
        account_pin="1111",
        ent=ac_reims,
        device_name="pronotepy"
    )

# Charger les données des grades
def load_grades(client):
    grades_data = []
    for period in client.periods:
        for grade in period.grades:
            note_en_cours = grade.to_dict({"comment", 'subject', 'id', "max", "min", 'default_out_of', 'is_out_of_20'})
            note_en_cours["subject"] = grade.subject.name
            note_en_cours["date"] = grade.date
            grades_data.append(note_en_cours)
    return grades_data

# Calculer la moyenne pour chaque note et mettre à jour les dates des bonus/facultatifs
def calculate_moving_average(df):
    df['grade'] = df['grade'].str.replace(",", ".").astype(float)
    df['normalized_grade'] = df['grade'].astype(float) * 20 / df['out_of'].astype(float)
    df['average'] = df['average'].str.replace(",", ".").astype(float)
    df['normalized_grade_average'] = df['average'].astype(float) * 20 / df['out_of'].astype(float)
    df.loc[df['out_of'] == 20, 'normalized_grade'] = df['grade']


    # Trier les lignes avec is_optionnal=False et is_bonus=False par date
    df_no_bonus_optional = df[(df['is_optionnal'] == False) & (df['is_bonus'] == False)].sort_values(by='date', ascending=True)

    # Trier les autres lignes par normalized_grade en ordre décroissant
    df_other = df[(df['is_optionnal'] != False) | (df['is_bonus'] != False)].sort_values(by='normalized_grade', ascending=False)

    # Trouver la dernière date des notes obligatoires (non facultatives et non bonus)
    if not df_no_bonus_optional.empty:
        last_mandatory_date = df_no_bonus_optional['date'].max()
    else:
        last_mandatory_date = pd.Timestamp.now()  # Si aucune note obligatoire n'existe, utilisez aujourd'hui.

    # Ajouter 1 jour à la dernière date obligatoire pour les notes facultatives ou bonus
    df_other['date'] = df_other['date'].apply(
        lambda d: last_mandatory_date + pd.Timedelta(days=1) if pd.notnull(d) else d
    )

    # Fusionner les deux DataFrames
    return pd.concat([df_no_bonus_optional, df_other])

def calculer(df, average):
    liste_moyennes, liste_dates = [], []
    moyenne = 0
    coefficient_moyen = 0
    num = 0

    for _, row in df.iterrows():
        if average:
            grade = float(row['normalized_grade_average'])
            raw_grade = float(row['average'])
        else:
            grade = float(row['normalized_grade'])
            raw_grade = float(row['grade'])
        out_of = float(row['out_of'])
        coefficient = float(row['coefficient'])
        is_bonus = row['is_bonus']
        is_optionnal = row['is_optionnal']

        moyenne_note = out_of / 2

        if is_bonus and raw_grade > moyenne_note:
            bonus = 20 * (raw_grade - moyenne_note) * coefficient / coefficient_moyen
            moyenne += bonus
            continue

        if is_optionnal and grade < moyenne:
            continue

        coefficient_moyen += out_of * coefficient
        num += coefficient * raw_grade
        moyenne = 20 * num / coefficient_moyen
        liste_moyennes.append(moyenne)
        liste_dates.append(row['date'])
    
    return liste_moyennes, liste_dates

# Afficher le graphique de la moyenne en fonction du temps
def plot_grades_over_time(df):
    # Calculer les moyennes dans le temps
    liste_moyennes, liste_dates = calculer(df, False)
    liste_moyennes_moyen, liste_dates = calculer(df, True)


    # Créer le graphique
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(liste_dates, liste_moyennes, marker='o', color='b', label='Moyenne élève')
    ax.axhline(y=10, color='gray', linestyle='--', label='Moyenne')
    ax.plot(liste_dates, liste_moyennes_moyen, marker='o', color='r', label='Moyenne de classe')
    # ax.set_xlim(right=20)

    
    ax.set_ylim(0, 20)

    ax.set_xlabel('Date')
    ax.set_ylabel('Moyenne')
    ax.set_title('Moyenne en fonction du temps')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45)
    ax.legend()

    # Afficher le graphique avec Streamlit
    st.pyplot(fig)

    df = df.sort_values(by='date', ascending=True)
    normalized_grade = df['normalized_grade'].tolist()  # Liste des normalized_grade
    normalized_grades_average = df['normalized_grade_average'].tolist()
    dates = df['date'].tolist()

    # Créer le graphique
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, normalized_grade, marker='o', color='b', label='Note élève')
    ax.axhline(y=10, color='gray', linestyle='--', label='Moyenne')
    ax.plot(dates, normalized_grades_average, marker='o', color='r', label='Note de classe')
    # ax.set_xlim(right=20)

    
    ax.set_ylim(0, 20)

    ax.set_xlabel('Date')
    ax.set_ylabel('Note')
    ax.set_title('Note en fonction du temps')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45)
    ax.legend()

    # Afficher le graphique avec Streamlit
    st.pyplot(fig)


# Interface utilisateur
def principal(passer=False):
    try:
        # Entrées de l'utilisateur
        username = st.text_input("Identifiant", value="", placeholder="Entrez votre identifiant", key="username_input")
        password = st.text_input("Mot de passe", value="", type="password", placeholder="Entrez votre mot de passe", key="password_input")

        
        def log():
            # Vérifier si le client Pronote est déjà en session
            if "client" not in st.session_state or not st.session_state.get("logged_in", False):
                if username and password:
                    client = connect_to_pronote(username, password)
                    if client.logged_in:
                        st.session_state.client = client
                        st.session_state.logged_in = True
                        st.session_state.grades_data = load_grades(client)
                        st.success("Connecté à Pronote !")
                    else:
                        st.error("Connexion à Pronote échouée. Vérifiez vos identifiants.")
                else:
                    st.warning("Veuillez entrer votre identifiant et mot de passe.")
                
                

            else:
                # Si l'utilisateur est déjà connecté
                client = st.session_state.client
                # Charger les données
                grades_data = st.session_state.grades_data
                df = pd.DataFrame(grades_data)
                df = df[df['grade'] != "NonNote"]

                # Convertir les dates en format datetime
                df['date'] = pd.to_datetime(df['date'])

                # Récupérer les matières uniques
                liste_matieres = sorted(df['subject'].unique())
                selected_matiere = st.selectbox("Choisissez une matière :", ["Toutes"] + liste_matieres, key="matiere_select")

                # Filtrer le DataFrame par matière sélectionnée
                if selected_matiere != "Toutes":
                    df = df[df['subject'] == selected_matiere]

                # Calculer les moyennes et mettre à jour les dates des bonus/facultatifs
                df_sorted = calculate_moving_average(df)

                # Afficher le graphique
                plot_grades_over_time(df_sorted)

                # Ajouter le bouton pour se déconnecter
                if st.button("Se déconnecter"):
                    # Supprimer la session et rediriger
                    st.session_state.clear()
                    st.success("Déconnecté avec succès.")
                    st.experimental_rerun()  # Rafraîchir pour réinitialiser l'interface
        log()
        if st.button("Se connecter"):
            log()
    except:pass

# Lancer l'application
if __name__ == "__main__":
    principal()
