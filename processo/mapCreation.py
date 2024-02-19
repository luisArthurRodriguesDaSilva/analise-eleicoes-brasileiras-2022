import folium
import branca.colormap as cmp
from difflib import get_close_matches
from helpers import (
    get_uf_Code,
    geo_json_url,
    dados_municipais_salvos_path,
    BRASIL_UFS,
    get_nearest,
)
import requests
from zipfile import ZipFile
import os
import pandas as pd
import numpy as np


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


def getDfs(ufMunData, munNames, values: str = "% Votos"):
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
    def values(feature):
        lulaDf[lulaDf["municipio"] == feature["properties"]["name"]].values[0]  # noqa

    return lambda feature: (
        {
            "fillColor": linear(values(feature)[1] * 100),
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


def values(df, feature):
    try:
        return df[df["NM_MUNICIPIO"] == feature["properties"]["name"]].values[0]
    except Exception as e:
        print(e)
        return df[
            df["NM_MUNICIPIO"] == get_nearest_mun(df, feature["properties"]["name"])
        ].values[0]
    return df[df["NM_MUNICIPIO"] == feature["properties"]["name"]].values[0]  # noqa


def default_style_function(df: pd.DataFrame):
    print("style function")
    return lambda feature: (
        {
            "fillColor": linear(values(df, feature)[1]),
            "color": "black",
            "weight": 1,
            "fillOpacity": 1,
        }
    )


def generate_map(
    df: pd.DataFrame,
    values_column: str,
    style_function=default_style_function,
    only=BRASIL_UFS,
):
    mapa = folium.Map(location=[-16, -45], zoom_start=4.5)
    for i, uf in enumerate(only):
        geo_data, munNames = get_geo_json(uf)
        print("a")
        folium.GeoJson(
            geo_data,
            style_function=style_function(df[["NM_MUNICIPIO", values_column]]),  # noqa
        ).add_to(
            mapa
        )  # noqa

    linear.add_to(mapa)
    folium.LayerControl().add_to(mapa)
    return mapa
