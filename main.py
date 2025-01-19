import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Fonction pour scraper les données
def fetch_emails_and_announcements(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        all_text = soup.get_text(separator="\n")
        lines = all_text.split("\n")

        data = []
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        current_offer = None
        current_post = None

        for line in lines:
            line = line.strip()

            if re.search(email_pattern, line):
                email = re.search(email_pattern, line).group()
                data.append([current_offer, current_post, email])
            elif len(line) > 5:
                if "recrute" in line.lower() or "offre" in line.lower():
                    current_offer = line
                else:
                    current_post = line

        df = pd.DataFrame(data, columns=["Société", "Poste", "Email"])
        return df

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de la page : {e}")
        return pd.DataFrame()

# Création de l'application Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Scraper d'Emails depuis une URL", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            dcc.Input(
                id="url-input",
                type="url",
                placeholder="Entrez l'URL à scraper",
                className="form-control mb-3"
            ),
            dbc.Button("Scraper", id="scrape-button", color="primary", className="mb-3"),
            html.Div(id="message", className="text-success")
        ], width=6)
    ], justify="center"),
    dbc.Row([
        dbc.Col([
            dcc.Download(id="download-dataframe-xlsx")
        ])
    ])
], fluid=True)

@app.callback(
    Output("message", "children"),
    Output("download-dataframe-xlsx", "data"),
    Input("scrape-button", "n_clicks"),
    State("url-input", "value"),
    prevent_initial_call=True
)
def scrape_and_download(n_clicks, url):
    if not url:
        return "Veuillez entrer une URL valide.", dash.no_update

    df = fetch_emails_and_announcements(url)
    if df.empty:
        return "Aucune donnée extraite. Vérifiez l'URL ou le contenu de la page.", dash.no_update

    output_file = "announcements.xlsx"
    df.to_excel(output_file, index=False)

    return (
        f"Extraction réussie ! {len(df)} lignes trouvées.",
        dcc.send_file(output_file)
    )

# Exposer le serveur pour Gunicorn
server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
    