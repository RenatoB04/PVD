"""Estatísticas determinísticas de tendência e correlação (Parte II, Fase 1)."""
import numpy as np
import pandas as pd
from scipy import stats as st
from statsmodels.tsa.seasonal import STL

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def series_stats(s: pd.Series) -> dict:
    """Tendência (regressão sobre a série dessazonalizada via STL) e sazonalidade."""
    s = s.sort_index().asfreq("MS")
    if s.isna().any():
        raise ValueError("A série tem meses em falta")
    fit = STL(s, period=12, robust=True).fit()
    deseason = (s - fit.seasonal).to_numpy()
    t = np.arange(len(s)) / 12.0                      # tempo em anos
    lr = st.linregress(t, deseason)
    rho, _ = st.spearmanr(t, deseason)
    media = float(s.mean())
    by_month = fit.seasonal.groupby(fit.seasonal.index.month).mean()
    last12, prev12 = float(s.iloc[-12:].sum()), float(s.iloc[-24:-12].sum())
    return {
        "periodo": f"{s.index[0]:%Y-%m} a {s.index[-1]:%Y-%m}",
        "n_meses": int(len(s)),
        "media_mensal_gwh": round(media, 1),
        "variacao_gwh_mes_por_ano": round(float(lr.slope), 2),
        "tendencia_pct_por_ano": round(float(lr.slope) / media * 100, 2),
        "r_pearson": round(float(lr.rvalue), 2),
        "r2": round(float(lr.rvalue ** 2), 2),
        "p_valor": round(float(lr.pvalue), 4),
        "rho_spearman": round(float(rho), 2),
        "mes_pico_sazonal": MESES[int(by_month.idxmax()) - 1],
        "mes_vale_sazonal": MESES[int(by_month.idxmin()) - 1],
        "amplitude_sazonal_pct": round(float((by_month.max() - by_month.min()) / media * 100), 1),
        "periodo_ultimos_12m": f"{s.index[-12]:%Y-%m} a {s.index[-1]:%Y-%m}",
        "variacao_12m_pct": round((last12 / prev12 - 1) * 100, 1),
        "nota": "p_valor indicativo: a série tem autocorrelação",
    }


def region_stats(long_df: pd.DataFrame) -> dict:
    """Resumo da tendência por região (para a figura comparativa)."""
    out = {}
    for regiao, g in long_df.groupby("regiao"):
        s = series_stats(g.set_index("data")["consumo_gwh"])
        out[regiao] = {k: s[k] for k in ("tendencia_pct_por_ano", "r2",
                                         "variacao_12m_pct", "amplitude_sazonal_pct")}
    return out


def correlation_stats(df: pd.DataFrame, x: str = "bt_gwh", y: str = "mt_gwh") -> dict:
    """Associação entre duas variáveis (concelhos com ambas > 0), em escala log-log."""
    d = df[(df[x] > 0) & (df[y] > 0)]
    lx, ly = np.log10(d[x]), np.log10(d[y])
    r, p = st.pearsonr(lx, ly)
    rho, _ = st.spearmanr(d[x], d[y])
    lr = st.linregress(lx, ly)
    r_raw, _ = st.pearsonr(d[x], d[y])
    return {
        "n_concelhos": int(len(d)),
        "n_excluidos_mt_zero": int(len(df) - len(d)),
        "r_pearson_log": round(float(r), 2),
        "r2_log": round(float(r ** 2), 2),
        "p_valor_pearson": round(float(p), 4),
        "rho_spearman": round(float(rho), 2),
        "declive_loglog": round(float(lr.slope), 2),
        "r_pearson_bruto": round(float(r_raw), 2),
        "pct_concelhos_mt_maior_que_bt": round(float((d[y] > d[x]).mean() * 100), 1),
        "nota": "a associação reflete em grande parte a dimensão do concelho",
    }