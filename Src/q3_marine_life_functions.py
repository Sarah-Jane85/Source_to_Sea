# =============================================================
# q3_marine_life.py
# Modular functions for Q3 — Impact on marine life
# Usage: from q3_marine_life import *
# =============================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from itertools import combinations
from scipy.stats import kruskal, mannwhitneyu, chi2_contingency
from sklearn.neighbors import BallTree
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import classification_report, roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from scipy.stats import randint


# ── Constants ─────────────────────────────────────────────────
RADIUS_KM = 50
EARTH_RADIUS_KM = 6371.0
CLASS_ORDER = ["Very Low", "Low", "Medium", "High", "Very High"]
FIGURES_DIR = "../Figures"


# ── H1: Species × Microplastics ───────────────────────────────

def clean_species(species: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing coordinates."""
    before = len(species)
    clean = species.dropna(subset=["latitude", "longitude"]).copy()
    print(f"Species: {before:,} → {len(clean):,} rows after dropping missing coords")
    print(f"Dropped: {before - len(clean):,} rows ({(before - len(clean)) / before:.1%})")
    return clean


def clean_microplastics(microplastics: pd.DataFrame) -> pd.DataFrame:
    """Standardise concentration_class as ordered categorical."""
    mp = microplastics.copy()
    mp["concentration_class"] = mp["concentration_class"].str.strip()
    mp["concentration_class"] = pd.Categorical(
        mp["concentration_class"],
        categories=CLASS_ORDER,
        ordered=True
    )
    print(f"Microplastics concentration_class after cleaning:")
    print(mp["concentration_class"].value_counts().sort_index())
    print(f"Unexpected values: {mp['concentration_class'].isnull().sum()}")
    return mp


def spatial_join_species_mp(
    species_clean: pd.DataFrame,
    microplastics: pd.DataFrame,
    radius_km: float = RADIUS_KM
) -> pd.DataFrame:
    """
    Match each species observation to the nearest microplastic sample
    within radius_km using BallTree haversine.
    Adds: dist_to_nearest_mp_km, within_radius, concentration_class
    """
    radius_rad = radius_km / EARTH_RADIUS_KM

    mp_coords_rad = np.radians(microplastics[["lat", "lng"]].values)
    species_coords_rad = np.radians(species_clean[["latitude", "longitude"]].values)

    tree = BallTree(mp_coords_rad, metric="haversine")
    distances_rad, indices = tree.query(species_coords_rad, k=1)
    distances_km = distances_rad[:, 0] * EARTH_RADIUS_KM

    result = species_clean.copy()
    result["dist_to_nearest_mp_km"] = distances_km
    result["within_radius"] = distances_km <= radius_km

    nearest_idx = indices[:, 0]
    result["concentration_class"] = microplastics["concentration_class"].iloc[nearest_idx].values
    result.loc[~result["within_radius"], "concentration_class"] = np.nan

    n_matched = result["within_radius"].sum()
    n_total = len(result)
    print(f"Matched within {radius_km} km : {n_matched:,} / {n_total:,} ({n_matched/n_total:.1%})")
    print(result["concentration_class"].value_counts().sort_index())
    return result


def ingestion_rate_by_class(species_ml: pd.DataFrame) -> pd.DataFrame:
    """Calculate ingestion rate per concentration class for matched animals."""
    matched = species_ml[species_ml["within_radius"]].copy()
    result = (
        matched.groupby("concentration_class", observed=True)["has_ingestion"]
        .agg(n_animals="count", n_with_ingestion="sum")
        .assign(ingestion_rate=lambda d: d["n_with_ingestion"] / d["n_animals"] * 100)
        .reset_index()
    )
    print(result.to_string(index=False))
    return result


def run_kruskal_wallis(species_ml: pd.DataFrame) -> tuple:
    """Run Kruskal-Wallis test across concentration classes."""
    matched = species_ml[species_ml["within_radius"]].copy()
    groups = [
        matched[matched["concentration_class"] == cls]["has_ingestion"].values
        for cls in CLASS_ORDER
        if cls in matched["concentration_class"].values
    ]
    stat, p = kruskal(*groups)
    print(f"Kruskal-Wallis H = {stat:.3f},  p = {p:.4f}")
    if p < 0.05:
        print("→ Significant difference across classes (p < 0.05)")
    else:
        print("→ No significant difference (p ≥ 0.05)")
    return stat, p


def run_pairwise_mannwhitney(species_ml: pd.DataFrame) -> pd.DataFrame:
    """Run pairwise Mann-Whitney tests with Bonferroni correction."""
    matched = species_ml[species_ml["within_radius"]].copy()
    pairs = list(combinations(CLASS_ORDER, 2))
    n = len(pairs)
    threshold = 0.05 / n
    print(f"Bonferroni threshold: {threshold:.4f}\n")

    results = []
    for cls_a, cls_b in pairs:
        a = matched[matched["concentration_class"] == cls_a]["has_ingestion"].values
        b = matched[matched["concentration_class"] == cls_b]["has_ingestion"].values
        if len(a) == 0 or len(b) == 0:
            continue
        stat, p_raw = mannwhitneyu(a, b, alternative="two-sided")
        p_adj = min(p_raw * n, 1.0)
        sig = "✓" if p_adj < 0.05 else "—"
        results.append({
            "pair": f"{cls_a} vs {cls_b}",
            "p_adjusted": round(p_adj, 4),
            "significant": sig
        })
        print(f"{cls_a} vs {cls_b}: p_adj={p_adj:.4f}  {sig}")
    return pd.DataFrame(results)


def plot_ingestion_by_class(profile: pd.DataFrame, save: bool = True) -> go.Figure:
    color_map = {
        "Very Low": "#5DCAA5", "Low": "#5DCAA5",
        "Medium": "#5DCAA5", "High": "#E24B4A", "Very High": "#5DCAA5"
    }
    
    # Sort by class order first
    profile["concentration_class"] = pd.Categorical(
        profile["concentration_class"].astype(str),
        categories=CLASS_ORDER, ordered=True
    )
    profile = profile.sort_values("concentration_class")
    
    fig = go.Figure(go.Bar(
        x=profile["concentration_class"].astype(str),
        y=profile["ingestion_rate"],
        marker_color=[color_map.get(str(c), "#5DCAA5") for c in profile["concentration_class"]],
        text=[f"{r:.1f}%<br>n={int(n)}" for r, n in zip(profile["ingestion_rate"], profile["n_animals"])],
        textposition="outside",
        width=0.45,
    ))
    fig.update_layout(
        title=dict(text="H1 — Plastic ingestion rate by microplastic concentration class", font=dict(size=15)),
        xaxis=dict(title="Microplastic concentration class", categoryorder="array", categoryarray=CLASS_ORDER),
        yaxis=dict(title="Animals with plastic ingestion (%)", ticksuffix="%", range=[0, 50]),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=100, l=60, r=40), width=700, height=480,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q3_h1_ingestion_by_concentration.html")
    return fig


# ── H2: Ghost net entanglement ────────────────────────────────

def run_ghost_net_chi2(species: pd.DataFrame) -> tuple:
    """Chi-square test and odds ratio for is_large vs ghost_net_entanglement."""
    contingency = pd.crosstab(species["is_large"], species["ghost_net_entanglement"])
    chi2, p, dof, _ = chi2_contingency(contingency)

    a = contingency.loc[1, 1]
    b = contingency.loc[1, 0]
    c = contingency.loc[0, 1]
    d = contingency.loc[0, 0]
    odds_ratio = (a * d) / (b * c)

    print(f"Chi-square: {chi2:.3f},  p = {p:.4f},  df = {dof}")
    print(f"Odds ratio: {odds_ratio:.3f}")
    print(f"\nEntanglement rate — Small: {c/(c+d):.1%},  Large: {a/(a+b):.1%}")
    return chi2, p, odds_ratio


def plot_ghost_net(chi2: float, p: float, odds_ratio: float, save: bool = True) -> go.Figure:
    """Bar chart: ghost net entanglement rate by size class."""
    fig = go.Figure()
    for cat, rate, n, color in zip(
        ["Small (< 200cm)", "Large (≥ 200cm)"],
        [8.18, 11.25],
        [4952, 5460],
        ["#5DCAA5", "#E24B4A"]
    ):
        fig.add_trace(go.Bar(
            x=[cat], y=[rate],
            marker_color=color,
            text=f"{rate}%<br>n={n}",
            textposition="outside",
            width=0.4,
            showlegend=False,
            name=cat,  # add this line
        ))
    fig.add_shape(type="line", x0=0, x1=1, y0=13.5, y1=13.5, line=dict(color="#444", width=1))
    fig.add_shape(type="line", x0=0, x1=0, y0=13.0, y1=13.5, line=dict(color="#444", width=1))
    fig.add_shape(type="line", x0=1, x1=1, y0=13.0, y1=13.5, line=dict(color="#444", width=1))
    fig.add_annotation(x=0.5, y=14.2, text=f"p<0.001  |  OR={odds_ratio:.2f}", showarrow=False, font=dict(size=11, color="#444"))
    fig.update_layout(
        title=dict(text="H2 — Ghost net entanglement rate by animal size", font=dict(size=15)),
        xaxis_title="Animal size class",
        yaxis=dict(title="Ghost net entanglement rate (%)", range=[0, 17], ticksuffix="%"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=100, l=60, r=40), width=500, height=420,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q3_h2_ghost_net_entanglement.html")
    return fig


# ── H3: Plastic type by animal group ─────────────────────────

PLASTIC_COLS = ["hard", "soft", "thread", "line", "fisheries", "rope", "foam", "bag", "rubber", "balloon"]
MAIN_GROUPS = ["Manatee", "Turtle", "Shearwater", "Prion", "Toothed Whale"]


def build_plastic_profile(species: pd.DataFrame) -> pd.DataFrame:
    """Presence/absence plastic type profile per animal group."""
    ingestion_df = species[
        (species["has_ingestion"] == 1) &
        (species["group"].isin(MAIN_GROUPS))
    ].copy()
    ingestion_df[PLASTIC_COLS] = (ingestion_df[PLASTIC_COLS] > 0).astype(int)
    col_order = ["hard", "soft", "thread", "line", "fisheries", "rope", "bag", "foam", "rubber", "balloon"]
    profile = (ingestion_df.groupby("group")[col_order].mean() * 100).round(1)
    return profile


def plot_plastic_heatmap(profile: pd.DataFrame, save: bool = True) -> go.Figure:
    """Heatmap: plastic type ingestion profile by animal group."""
    col_order = ["hard", "soft", "thread", "line", "fisheries", "rope", "bag", "foam", "rubber", "balloon"]
    group_order = ["Prion", "Shearwater", "Toothed Whale", "Turtle", "Manatee"]
    heatmap_data = profile[col_order].loc[group_order]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[c.capitalize() for c in col_order],
        y=group_order,
        colorscale=[[0.0, "#E1F5EE"], [0.5, "#1D9E75"], [1.0, "#04342C"]],
        text=heatmap_data.values,
        texttemplate="%{text}%",
        textfont=dict(size=11),
        hoverongaps=False,
        colorbar=dict(title="% of animals<br>with plastic type", ticksuffix="%")
    ))
    fig.update_layout(
        title=dict(text="H3 — Plastic type ingestion profile by animal group", font=dict(size=15)),
        xaxis=dict(title="Plastic type", side="bottom"),
        yaxis=dict(title="Animal group"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=100, l=120, r=40), width=750, height=400,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q3_h3_plastic_type_by_group.html")
    return fig


# ── ML: Ingestion risk model ──────────────────────────────────

HONEST_FEATURES = ["group", "is_large", "latitude", "longitude", "gyre_region", "concentration_class"]
CAT_COLS = ["group", "gyre_region", "concentration_class"]


def encode_features(species_ml: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Label encode categorical features. Returns encoded df and encoder dict."""
    df = species_ml.copy()
    df["concentration_class"] = df["concentration_class"].astype(str).replace("nan", "Unknown")
    encoders = {}
    for col in CAT_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders


def split_data(df_enc: pd.DataFrame) -> tuple:
    """Train/test split stratified on has_ingestion."""
    X = df_enc[HONEST_FEATURES]
    y = df_enc["has_ingestion"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")
    print(f"Positive rate — train: {y_train.mean():.1%}  |  test: {y_test.mean():.1%}")
    return X_train, X_test, y_train, y_test


def train_baseline_rf(X_train, y_train) -> RandomForestClassifier:
    """Train baseline Random Forest with balanced class weights."""
    rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    return rf


def tune_rf(X_train, y_train) -> RandomizedSearchCV:
    """Tune Random Forest with RandomizedSearchCV."""
    param_dist = {
        "n_estimators": randint(100, 500),
        "max_depth": [None, 5, 10, 15, 20],
        "min_samples_split": randint(2, 20),
        "max_features": ["sqrt", "log2", 0.5],
    }
    search = RandomizedSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1),
        param_distributions=param_dist,
        n_iter=30, scoring="roc_auc", cv=5, random_state=42, verbose=1, n_jobs=-1
    )
    search.fit(X_train, y_train)
    print(f"Best params : {search.best_params_}")
    print(f"Best CV AUC : {search.best_score_:.3f}")
    return search


def train_gradient_boosting(X_train, y_train) -> GradientBoostingClassifier:
    """Train Gradient Boosting with balanced sample weights."""
    gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
    weights = compute_sample_weight("balanced", y_train)
    gb.fit(X_train, y_train, sample_weight=weights)
    return gb


def evaluate_model(model, X_test, y_test, name: str = "Model") -> float:
    """Print classification report and return ROC-AUC."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    print(f"\n=== {name} ===")
    print(classification_report(y_test, y_pred, target_names=["No ingestion", "Ingestion"]))
    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC-AUC : {auc:.3f}")
    return auc


def plot_feature_importance(model, save: bool = True) -> go.Figure:
    """Horizontal bar chart of feature importances."""
    importances = pd.Series(model.feature_importances_, index=HONEST_FEATURES).sort_values(ascending=True)
    colors = ["#378ADD" if f in ["latitude", "longitude"] else "#1D9E75" if f == "group" else "#888780"
              for f in importances.index]
    fig = go.Figure(go.Bar(
        x=importances.values, y=importances.index, orientation="h",
        marker_color=colors,
        text=[f"{v:.1%}" for v in importances.values], textposition="outside",
    ))
    fig.update_layout(
        title=dict(text="Feature importance — predicting plastic ingestion risk", font=dict(size=15)),
        xaxis=dict(title="Feature importance", tickformat=".0%", range=[0, 0.55]),
        yaxis=dict(title=""),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=80, l=150, r=60), height=380, width=680,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/ml_feature_importance.html")
    return fig


def plot_roc_curve(model, X_test, y_test, save: bool = True) -> go.Figure:
    """ROC curve with random baseline."""
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", line=dict(color="#378ADD", width=2), name=f"Random Forest (AUC={auc:.3f})"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color="#888", dash="dash", width=1), name="Random baseline (AUC=0.5)"))
    fig.update_layout(
        title=dict(text="ROC curve — plastic ingestion risk model", font=dict(size=15)),
        xaxis=dict(title="False positive rate"),
        yaxis=dict(title="True positive rate"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=60, l=60, r=40), height=420, width=560,
        legend=dict(x=0.4, y=0.1),
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/ml_roc_curve.html")
    return fig


def plot_probability_distribution(model, X_test, y_test, save: bool = True) -> go.Figure:
    """Overlapping histogram of predicted probabilities by actual class."""
    y_prob = model.predict_proba(X_test)[:, 1]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=y_prob[y_test == 0], name="No ingestion (actual)", opacity=0.7, marker_color="#5DCAA5", nbinsx=40))
    fig.add_trace(go.Histogram(x=y_prob[y_test == 1], name="Ingestion (actual)", opacity=0.7, marker_color="#E24B4A", nbinsx=40))
    fig.add_vline(x=0.5, line_dash="dash", line_color="#444", line_width=1,
                  annotation_text="decision threshold 0.5", annotation_position="top right", annotation_font_size=10)
    fig.update_layout(
        barmode="overlay",
        title=dict(text="Predicted ingestion probability by actual class", font=dict(size=15)),
        xaxis=dict(title="Predicted probability of ingestion"),
        yaxis=dict(title="Number of animals"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=60, l=60, r=40), width=700, height=420,
        legend=dict(x=0.55, y=0.95),
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/ml_probability_distribution.html")
    return fig
