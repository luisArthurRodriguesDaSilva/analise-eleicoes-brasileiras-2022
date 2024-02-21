import pandas as pd
from difflib import get_close_matches

watched_columns = [
    "SG_UF",
    "NM_MUNICIPIO",
    "CD_MUNICIPIO",
    "NR_PARTIDO",
    "QT_VOTOS",
]  # noqa

dict_ufs = {
    "RIO DE JANEIRO": "RJ",
    "SÃO PAULO": "SP",
    "MINAS GERAIS": "MG",
    "BAHIA": "BA",
    "RIO GRANDE DO SUL": "RS",
    "PARANÁ": "PR",
    "CEARÁ": "CE",
    "PERNAMBUCO": "PE",
    "PARAÍBA": "PB",
    "RIO GRANDE DO NORTE": "RN",
    "ALAGOAS": "AL",
    "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS",
    "GOIÁS": "GO",
    "MARANHÃO": "MA",
    "PARÁ": "PA",
    "AMAZONAS": "AM",
    "TOCANTINS": "TO",
    "RORAIMA": "RR",
    "ACRE": "AC",
    "AMAPÁ": "AP",
    "SERGIPE": "SE",
    "ESPÍRITO SANTO": "ES",
    "SANTA CATARINA": "SC",
    "DISTRITO FEDERAL": "DF",
    "PIAUÍ": "PI",
    "RONDÔNIA": "RO",
    "RIO GRANDE DO SUL": "RS",
}

geo_json_url = (
    "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/"  # noqa
)

dados_municipais_salvos_path = "../RESULTADOS/DADOS/CSVs/municipios/"

ufCodes = pd.read_html(
    "https://www.oobj.com.br/bc/article/quais-os-c%C3%B3digos-de-cada-uf-no-brasil-465.html"  # noqa
)[0]


def get_uf_sg(large_uf: str):
    print(large_uf)
    try:
        return dict_ufs[get_nearest(large_uf.upper(), dict_ufs)]
    except Exception as e:
        print(e)
        return "nan"


brasil_ufs = [
    "ac",
    "al",
    "am",
    "ap",
    "ba",
    "ce",
    "df",
    "es",
    "go",
    "ma",
    "mt",
    "ms",
    "mg",
    "pa",
    "pb",
    "pr",
    "pe",
    "pi",
    "rj",
    "rn",
    "ro",
    "rs",
    "rr",
    "sc",
    "se",
    "sp",
    "to",
]
BRASIL_UFS = list(map(lambda x: x.upper(), brasil_ufs))


def get_uf_Code(uf):
    return ufCodes[ufCodes["UF"] == uf.upper()]["Código UF"].values[0]


def get_uf_df(uf):
    with open(f"../notebooks/csvs/bweb_2t_{uf}_311020221535.csv", "rb") as f:
        df = pd.read_csv(f, sep=";", encoding="latin-1")
        df = df[df["CD_CARGO_PERGUNTA"] == 1][watched_columns]
        return df


def get_nearest(target, data):
    try:
        return get_close_matches(target, data)[0]
    except Exception as e:
        print(e)
        return "nan"


def string_code_to_int(string_code):
    return int(string_code.replace("\xa0", ""))
