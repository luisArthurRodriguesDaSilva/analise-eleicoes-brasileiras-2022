import folium
import requests
import pandas as pd
import numpy as np
from zipfile import ZipFile
import os
import branca.colormap as cmp
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


def get_uf_sg(large_uf: str):
    print(large_uf)
    try:
        return dict_ufs[get_nearest(large_uf.upper(), dict_ufs)]
    except Exception as e:
        print(e)
        return "nan"


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


def format_geo_data(geo_data):
    for index, mun in enumerate(geo_data["features"]):
        geo_data["features"][index]["properties"]["name"] = mun["properties"][
            "name"
        ].upper()
    return geo_data


def get_municipe_names(geo_data_uf):
    municipe_names = list(
        map(lambda x: x["properties"]["name"], geo_data_uf["features"])
    )  # noqa
    return municipe_names


def get_geo_json(uf):
    code = get_uf_Code(uf)
    geo_data_uf = requests.get(f"{geo_json_url}geojs-{code}-mun.json").json()

    geo_data_uf = format_geo_data(geo_data_uf)

    munNames = get_municipe_names(geo_data_uf)
    return geo_data_uf, munNames


tse_url = "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/buweb/"  # noqa


def downloadUfData(uf):
    path = (
        f"{dados_municipais_salvos_path}bweb_2t_{uf.upper()}_311020221535.csv"  # noqa
    )
    if not os.path.isfile(path):
        zipado = requests.get(f"{tse_url}bweb_2t_{uf.upper()}_311020221535.zip")  # noqa

        file = "./zipe.zip"
        open(file, "wb").write(zipado.content)

        with ZipFile(file, "r") as zip:
            zip.printdir()
            zip.extractall(dados_municipais_salvos_path)
        os.remove(f"{dados_municipais_salvos_path}leiame-boletimurnaweb.pdf")
        os.remove("zipe.zip")


def getUfData(uf: str) -> pd.DataFrame:
    downloadUfData(uf)
    with open(
        f"{dados_municipais_salvos_path}bweb_2t_{uf.upper()}_311020221535.csv",
        "rb",
    ) as f:
        munUfData = pd.read_csv(f, sep=";", encoding="latin-1")

    simpleData = munUfData[["NM_MUNICIPIO", "NR_PARTIDO", "QT_VOTOS"]]

    simpUfdata = simpleData.groupby(by=["NM_MUNICIPIO", "NR_PARTIDO"]).agg(
        quantidade=("QT_VOTOS", "sum")
    )
    return simpUfdata


def get_nearest_mun(ufMunData: pd.DataFrame, mun: str) -> str:
    muns_list = list(set([key[0] for key in ufMunData["quantidade"].keys()]))
    return get_close_matches(mun, muns_list)[0]


def getPP(ufMunData: pd.DataFrame, mun: str, num) -> float:
    try:
        bolso = ufMunData["quantidade"][mun][22]
        lula = ufMunData["quantidade"][mun][13]
        totalValid = bolso + lula
        return ufMunData["quantidade"][mun][num] / totalValid
    except Exception as e:
        try:
            print(e, "deu erro na atribuição 1")
            bolso = ufMunData["quantidade"][get_nearest_mun(ufMunData, mun)][22]  # noqa
            lula = ufMunData["quantidade"][get_nearest_mun(ufMunData, mun)][13]
            totalValid = bolso + lula
            return ufMunData["quantidade"][mun][num] / totalValid
        except Exception as e:
            print(e, "deu erro na atribuição 2")
            return 0.5


def getDfs(ufMunData, munNames):
    lulaScores = list(map(lambda mun: getPP(ufMunData, mun, 13), munNames))
    lulaDf = pd.DataFrame(
        np.c_[munNames, lulaScores], columns=["municipio", "% Votos"]
    )  # noqa
    lulaDf["% Votos"] = pd.Series(lulaScores, dtype=float)
    return lulaDf


linear = cmp.LinearColormap(
    [(0, 150, 0), (255, 255, 255), (150, 0, 0)],
    vmin=0,
    vmax=100,
    caption="% de votos para Lula",
)


def styleFunction(lulaDf):
    return lambda feature: (
        {
            "fillColor": linear(
                lulaDf[lulaDf["municipio"] == feature["properties"]["name"]].values[
                    0
                ][  # noqa
                    1
                ]
                * 100
            ),
            "color": "black",
            "weight": 1,
            "fillOpacity": 1,
        }
    )


def generateUfMap(ufs: list) -> folium.Map:
    mapa = folium.Map(location=[-16, -45], zoom_start=4.5)
    for i, uf in enumerate(ufs):
        geo_data, munNames = get_geo_json(uf)
        ufMunData = getUfData(uf)
        lulaDf = getDfs(ufMunData, munNames)

        folium.GeoJson(geo_data, style_function=styleFunction(lulaDf)).add_to(
            mapa
        )  # noqa

    linear.add_to(mapa)
    folium.LayerControl().add_to(mapa)
    return mapa


def get_uf_df(uf):
    with open(f"../notebooks/csvs/bweb_2t_{uf}_311020221535.csv", "rb") as f:
        df = pd.read_csv(f, sep=";", encoding="latin-1")
        df = df[df["CD_CARGO_PERGUNTA"] == 1][watched_columns]
        return df


def get_nearest(target, data):
    return get_close_matches(target, data)[0]


def string_code_to_int(string_code):
    return int(string_code.replace("\xa0", ""))
