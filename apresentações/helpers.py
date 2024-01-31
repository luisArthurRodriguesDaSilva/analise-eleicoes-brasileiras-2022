import pandas as pd


watched_columns = ["SG_UF", "NM_MUNICIPIO", "CD_MUNICIPIO", "NR_PARTIDO", "QT_VOTOS"] # noqa

BRASIL_UFS = [
    "RO",
    "AC",
    "AM",
    "RR",
    "PA",
    "AP",
    "TO",
    "MA",
    "PI",
    "CE",
    "RN",
    "PB",
    "PE",
    "AL",
    "SE",
    "BA",
    "MG",
    "ES",
    "RJ",
    "SP",
    "PR",
    "SC",
    "RS",
    "MS",
    "MT",
    "GO",
    "DF",
]
ufCodes = pd.read_html(
    "https://www.oobj.com.br/bc/article/quais-os-c%C3%B3digos-de-cada-uf-no-brasil-465.html"  # noqa
)[0]


def get_uf_Code(uf):
    return ufCodes[ufCodes["UF"] == uf.upper()]["Código UF"].values[0]


def get_uf_df(uf):
    with open(f"../notebooks/csvs/bweb_2t_{uf}_311020221535.csv", "rb") as f:
        df = pd.read_csv(f, sep=";", encoding="latin-1")
        df = df[df["CD_CARGO_PERGUNTA"] == 1][watched_columns]
        return df
