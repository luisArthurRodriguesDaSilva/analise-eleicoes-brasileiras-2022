import folium
import branca.colormap as cmp
from difflib import get_close_matches
from helpers import get_uf_Code, geo_json_url, BRASIL_UFS
import requests
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


def get_nearest_mun(ufMunData: pd.DataFrame, mun: str) -> str:
    muns_list = list(set([key[0] for key in ufMunData["quantidade"].keys()]))
    return get_close_matches(mun, muns_list)[0]


def get_value_trated(df, values_column, mun):
    try:
        return df[df["NM_MUNICIPIO"] == mun][values_column].values[0]
    except Exception:
        try:
            return df[df["NM_MUNICIPIO"] == mun][values_column].values[0]
        except Exception:
            return df[values_column].mean()


def default_style_function(df: pd.DataFrame, linear: cmp.LinearColormap):

    def values(feature):
        return df[df["NM_MUNICIPIO"] == feature["properties"]["name"]].values[0]  # noqa

    return lambda feature: (
        {
            "fillColor": linear(values(feature)[1]),  # noqa
            "color": "black",
            "weight": 1,
            "fillOpacity": 1,
        }
    )


def get_linear(
    df: pd.DataFrame,
    values_column: str,
    colors: list[str],
    vmin=None,
    vmax=None,
):
    if vmin == vmax:
        vmin = df[values_column].min()
        vmax = df[values_column].max()
    print(min, max)
    return cmp.LinearColormap(
        colors=colors,
        vmin=vmin,
        vmax=vmax,
        caption=f"{values_column}",
    )


def generate_map(
    df: pd.DataFrame,
    values_column: str,
    style_function=default_style_function,
    colors=["blue", "red"],
    only=BRASIL_UFS,
    vmin=None,
    vmax=None,
):
    linear = get_linear(df, values_column, colors, vmin=vmin, vmax=vmax)
    mapa = folium.Map(location=[-16, -45], zoom_start=4.5)
    for i, uf in enumerate(only):
        geo_data, munNames = get_geo_json(uf)
        fill_data = list(
            map(lambda mun: get_value_trated(df, values_column, mun), munNames)
        )  # noqa
        fill_df = pd.DataFrame(
            np.c_[munNames, fill_data], columns=["NM_MUNICIPIO", values_column]
        )  # noqa
        fill_df[values_column] = pd.Series(fill_data, dtype=float)
        folium.GeoJson(
            geo_data,
            style_function=style_function(fill_df, linear=linear),  # noqa
        ).add_to(
            mapa
        )  # noqa

    linear.add_to(mapa)
    folium.LayerControl().add_to(mapa)
    return mapa
