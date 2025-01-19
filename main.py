import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def scrape_page(url):
    """
    Récupère les emails, sociétés et postes depuis une page web.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        lines = soup.get_text(separator="\n").split("\n")

        data = []
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        current_offer, current_post = None, None

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
        return data
    except Exception as e:
        print(f"Erreur lors du scraping de la page : {e}")
        return []

def scrape_multiple_pages(base_url, total_pages):
    """
    Récupère les données de plusieurs pages.
    """
    all_data = []
    for page in range(1, total_pages + 1):
        url = f"{base_url}&pageNum_Re_av={page}"
        print(f"Scraping page : {url}")
        all_data.extend(scrape_page(url))
    return all_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Scraper d'Emails - Multipage", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            dcc.Input(
                id="url-input",
                type="url",
                placeholder="Entrez l'URL de base",
                className="form-control mb-3"
            ),
            dcc.Input(
                id="total-pages",
                type="number",
                placeholder="Nombre total de pages",
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
    State("total-pages", "value"),
    prevent_initial_call=True
)
def scrape_and_download(n_clicks, base_url, total_pages):
    if not base_url or not total_pages:
        return "Veuillez entrer une URL valide et le nombre total de pages.", dash.no_update
    all_data = scrape_multiple_pages(base_url, total_pages)
    if not all_data:
        return "Aucune donnée extraite.", dash.no_update
    df = pd.DataFrame(all_data, columns=["Société", "Poste", "Email"])
    output_file = "announcements_multipage.xlsx"
    df.to_excel(output_file, index=False)
    return (
        f"Extraction réussie ! {len(df)} lignes trouvées.",
        dcc.send_file(output_file)
    )

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
