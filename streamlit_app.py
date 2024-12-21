import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Titre de l'application
st.title("Application Streamlit Simple et Complète 🎈")

# Sous-titre
st.subheader("Explorez vos données et visualisez des graphiques interactifs !")

# Charger ou générer des données
st.sidebar.header("Paramètres des données")
option = st.sidebar.radio("Choisissez une source de données :", ["Données aléatoires", "Importer un fichier CSV"])

if option == "Données aléatoires":
    # Génération de données aléatoires
    num_rows = st.sidebar.slider("Nombre de lignes", min_value=10, max_value=500, value=100)
    data = pd.DataFrame({
        "Colonne 1": np.random.randn(num_rows),
        "Colonne 2": np.random.randn(num_rows),
        "Catégorie": np.random.choice(["A", "B", "C"], size=num_rows)
    })
else:
    # Importer un fichier CSV
    uploaded_file = st.sidebar.file_uploader("Téléversez un fichier CSV", type=["csv"])
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        st.warning("Veuillez téléverser un fichier CSV pour continuer.")
        st.stop()

# Afficher les données
st.write("### Aperçu des données :")
st.dataframe(data.head())

# Statistiques descriptives
st.write("### Statistiques descriptives :")
st.write(data.describe())

# Graphiques interactifs
st.write("### Visualisation des données :")
col_x = st.selectbox("Choisissez une colonne pour l'axe X :", data.columns)
col_y = st.selectbox("Choisissez une colonne pour l'axe Y :", data.columns)

# Filtrage par catégorie (si applicable)
if "Catégorie" in data.columns:
    categories = st.multiselect("Filtrer par catégorie :", data["Catégorie"].unique(), default=data["Catégorie"].unique())
    data = data[data["Catégorie"].isin(categories)]

# Création du graphique
fig, ax = plt.subplots()
ax.scatter(data[col_x], data[col_y], alpha=0.7)
ax.set_xlabel(col_x)
ax.set_ylabel(col_y)
ax.set_title(f"Graphique : {col_x} vs {col_y}")
st.pyplot(fig)

# Fin de l'application
st.write("Merci d'avoir utilisé cette application ! 😊")
