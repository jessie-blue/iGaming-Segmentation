import os
import textwrap
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="talk")

CSV = "Data Science Task Data.xlsx - Result 1.csv"
OUT = "eda_output"
os.makedirs(OUT, exist_ok=True)

lines = []


def log(msg=""):
    print(msg)
    lines.append(str(msg))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    log(f"[saved] {path}")


# ---------------------------------------------------------------- load
df = pd.read_csv(CSV, low_memory=False)
n_rows, n_cols = df.shape

log("=" * 78)
log("EXPLORATORY DATA ANALYSIS")
log("=" * 78)
log(f"File: {CSV}")
log(f"Shape: {n_rows} rows x {n_cols} columns")
log("")

# ---------------------------------------------------------------- dtypes
log("=" * 78)
log("1. DATA TYPES")
log("=" * 78)

dtype_summary = df.dtypes.value_counts().rename_axis("dtype").to_frame("n_columns")
log(dtype_summary.to_string())
log("")

dt = pd.DataFrame({
    "column": df.columns,
    "dtype": [str(t) for t in df.dtypes],
    "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
    "n_missing": [df[c].isna().sum() for c in df.columns],
    "missing_pct": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
})
log(dt.to_string(index=False))
log("")

# classify columns
numeric_cols = list(df.select_dtypes(include="number").columns)
bool_cols = list(dict.fromkeys(
    list(df.select_dtypes(include="boolean").columns) +
    list(df.select_dtypes(include="bool").columns)))
string_cols = list(df.select_dtypes(include=["object", "string"]).columns)


def looks_like_date(s):
    s = s.dropna().astype(str)
    if s.empty:
        return False
    return s.str.match(r"\d{4}-\d{2}-\d{2}").mean() > 0.9


date_cols = [c for c in string_cols if looks_like_date(df[c])]
categorical_cols = [c for c in df.columns
                    if c not in numeric_cols and c not in bool_cols and c not in date_cols]

# parse dates
for c in date_cols:
    df[c] = pd.to_datetime(df[c], errors="coerce")

log(f"Numeric columns ({len(numeric_cols)}): {numeric_cols}")
log(f"Boolean columns ({len(bool_cols)}): {bool_cols}")
log(f"Datetime columns ({len(date_cols)}): {date_cols}")
log(f"Categorical/object columns ({len(categorical_cols)})")
log("")

# ---------------------------------------------------------------- missing
log("=" * 78)
log("2. MISSING VALUES")
log("=" * 78)

miss = pd.DataFrame({
    "n_missing": df.isna().sum(),
    "pct_missing": (df.isna().mean() * 100).round(2),
    "n_present": df.notna().sum(),
}).sort_values("pct_missing", ascending=False)
log(miss.to_string())
log("")
log(f"Columns with NO missing values: {(miss['n_missing'] == 0).sum()}")
log(f"Columns with ANY missing values: {(miss['n_missing'] > 0).sum()}")
log(f"Columns >90% missing: {(miss['pct_missing'] > 90).sum()}")
log(f"Total missing cells: {int(df.isna().sum().sum())} "
    f"({df.isna().mean().mean() * 100:.2f}% of all cells)")
log("")

# missingness bar chart
fig, ax = plt.subplots(figsize=(16, 10))
plot_miss = miss[miss["n_missing"] > 0].sort_values("pct_missing")
colors = ["#c0392b" if p > 50 else "#e67e22" if p > 20 else "#2980b9"
          for p in plot_miss["pct_missing"]]
ax.barh(plot_miss.index.astype(str), plot_miss["pct_missing"], color=colors)
ax.set_xlabel("% missing")
ax.set_title(f"Missing values by column ({len(plot_miss)} of {n_cols} columns have missing data)")
for i, (v, name) in enumerate(zip(plot_miss["pct_missing"], plot_miss.index.astype(str))):
    ax.text(v + 0.6, i, f"{v:.1f}%", va="center", fontsize=9)
ax.set_xlim(0, min(105, plot_miss["pct_missing"].max() * 1.15 + 3))
save(fig, "missing_values.png")

# missingness heatmap (sampled rows to keep it readable)
fig, ax = plt.subplots(figsize=(18, 9))
miss_mat = df.isna().astype(int)
sample_idx = np.linspace(0, n_rows - 1, min(300, n_rows)).astype(int)
sns.heatmap(miss_mat.iloc[sample_idx], cmap=["#ecf0f1", "#c0392b"],
            cbar_kws={"label": "missing"}, yticklabels=False, ax=ax)
ax.set_xticks(np.arange(0, n_cols, max(1, n_cols // 40)) + 0.5,
              labels=[c for c in df.columns][::max(1, n_cols // 40)],
              rotation=90, fontsize=7)
ax.set_title("Missingness pattern (300 sampled rows)")
save(fig, "missingness_heatmap.png")

# ---------------------------------------------------------------- describe
log("=" * 78)
log("3. DESCRIPTIVE STATISTICS - NUMERIC")
log("=" * 78)
log(df[numeric_cols].describe().T.to_string())
log("")
log("Skewness:")
log(df[numeric_cols].skew().sort_values(ascending=False).round(3).to_string())
log("")

log("=" * 78)
log("4. DESCRIPTIVE STATISTICS - CATEGORICAL")
log("=" * 78)
cat_desc = pd.DataFrame({
    "count": [df[c].notna().sum() for c in categorical_cols],
    "unique": [df[c].nunique(dropna=True) for c in categorical_cols],
    "top": [df[c].mode(dropna=True).iloc[0] if df[c].notna().any() else None
            for c in categorical_cols],
    "top_freq": [df[c].value_counts(dropna=True).iloc[0] if df[c].notna().any() else 0
                 for c in categorical_cols],
}, index=pd.Index(categorical_cols, name="column"))
log(cat_desc.to_string())
log("")

log("-" * 78)
log("Value counts for key low-cardinality categoricals")
log("-" * 78)
key_cats = [c for c in ["status", "status_reason", "gender", "gaming_level",
                        "aml_risk_rating", "rg_risk_rating", "country", "city",
                        "occupation", "industry", "allow_sms", "allow_email",
                        "is_test_account", "is_bonus_abuser", "is_pep",
                        "has_sanctions", "ever_self_excluded", "registration_platform",
                        "traffic_source", "sub_traffic_source", "utm_source",
                        "operational_profit_segment", "portfolio_vip_status",
                        "vip_status_updated_at", "max_profit_segment_rank",
                        "has_mfa_enabled", "marketing_network"]
            if c in df.columns]
for c in key_cats:
    vc = df[c].value_counts(dropna=False).head(15)
    log(f"\n{c} ({df[c].nunique(dropna=True)} unique):")
    for k, v in vc.items():
        log(f"    {repr(k):<45} {v:>7} ({v / n_rows * 100:5.2f}%)")
log("")

# ---------------------------------------------------------------- numeric dist
log("=" * 78)
log("5. DISTRIBUTIONS - NUMERIC")
log("=" * 78)

# histogram grid for all numeric columns
n = len(numeric_cols)
ncols = 4
nrows = int(np.ceil(n / ncols))
fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 3.4 * nrows))
axes = np.array(axes).ravel()
for i, c in enumerate(numeric_cols):
    ax = axes[i]
    s = df[c].dropna()
    if s.empty:
        ax.set_title(f"{c} (all missing)")
        continue
    ax.hist(s, bins=40, color="#2980b9", edgecolor="white", linewidth=0.3)
    ax.set_title(f"{c}", fontsize=11)
    ax.tick_params(labelsize=7)
for j in range(i + 1, len(axes)):
    axes[j].axis("off")
fig.suptitle("Distribution of numeric variables", y=1.0, fontsize=16)
fig.tight_layout()
save(fig, "numeric_distributions.png")

# log-scale versions for heavily skewed money/count columns
skewed = [c for c in numeric_cols if abs(df[c].skew(skipna=True)) > 2]
if skewed:
    n = len(skewed)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 3.4 * nrows))
    axes = np.array(axes).ravel()
    for i, c in enumerate(skewed):
        ax = axes[i]
        s = df[c].dropna()
        s = s[s > 0]
        if s.empty:
            ax.set_title(f"{c} (no positive values)")
            continue
        ax.hist(np.log10(s), bins=40, color="#8e44ad", edgecolor="white", linewidth=0.3)
        ax.set_title(f"{c} (log10, positive only)", fontsize=11)
        ax.tick_params(labelsize=7)
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    fig.suptitle(f"Log-scale distributions ({n} skewed variables)", y=1.0, fontsize=16)
    fig.tight_layout()
    save(fig, "numeric_distributions_log.png")
log(f"Skewed (|skew| > 2) numeric columns: {skewed}")
log("")

# boxplots for key financial columns
money_cols = [c for c in ["total_deposits", "total_withdrawals", "total_bets",
                          "total_wins", "total_logins", "first_deposit_day"]
              if c in numeric_cols]
if money_cols:
    fig, axes = plt.subplots(1, len(money_cols), figsize=(4.5 * len(money_cols), 5))
    for ax, c in zip(np.atleast_1d(axes), money_cols):
        s = df[c].dropna()
        ax.boxplot(s, vert=True, showfliers=False)
        ax.set_title(c)
        ax.set_ylabel("value")
        med, p95 = s.median(), s.quantile(0.95)
        ax.set_xticks([])
        ax.text(0.5, -0.12, f"median={med:,.1f}\np95={p95:,.1f}\nmax={s.max():,.1f}",
                transform=ax.transAxes, ha="center", fontsize=9)
    fig.suptitle("Box plots of engagement/financial variables (outliers hidden)", fontsize=14)
    fig.tight_layout()
    save(fig, "numeric_boxplots.png")

# ---------------------------------------------------------------- categorical dist
log("=" * 78)
log("6. DISTRIBUTIONS - CATEGORICAL")
log("=" * 78)

high_card_skip = set(numeric_cols) | set(date_cols)
bar_cats = [c for c in categorical_cols
            if 1 < df[c].nunique(dropna=True) <= 25]
log(f"Columns plotted as bar charts (2-25 unique values): {bar_cats}")

ncols = 3
n = len(bar_cats)
nrows = int(np.ceil(n / ncols)) if n else 1
fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 4.2 * nrows))
axes = np.array(axes).ravel()
for i, c in enumerate(bar_cats):
    ax = axes[i]
    vc = df[c].value_counts(dropna=False).head(25)
    labels = [str(v)[:28] for v in vc.index]
    sns.barplot(x=vc.values, y=labels, ax=ax, color="#2980b9")
    ax.set_title(f"{c} ({df[c].nunique(dropna=True)} uniq)", fontsize=11)
    ax.set_xlabel("count")
    ax.tick_params(axis="y", labelsize=8)
    for p in ax.patches:
        w = p.get_width()
        ax.text(w + w * 0.01, p.get_y() + p.get_height() / 2,
                f"{int(w)}", va="center", fontsize=7)
if n:
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    fig.suptitle("Categorical variable distributions", fontsize=16)
    fig.tight_layout()
    save(fig, "categorical_distributions.png")

# top-N for high cardinality categoricals
high_card = [c for c in categorical_cols if df[c].nunique(dropna=True) > 25]
log("")
log(f"High-cardinality categorical columns ({len(high_card)}):")
for c in high_card:
    log(f"    {c}: {df[c].nunique(dropna=True)} unique values, "
        f"{df[c].isna().sum()} missing")

if high_card:
    ncols = 2
    n = min(len(high_card), 12)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(9 * ncols, 3.6 * nrows))
    axes = np.array(axes).ravel()
    for i, c in enumerate(high_card[:n]):
        ax = axes[i]
        vc = df[c].value_counts().head(15)
        labels = [str(v)[:35] for v in vc.index]
        sns.barplot(x=vc.values, y=labels, ax=ax, color="#16a085")
        ax.set_title(f"{c} - top 15 of {df[c].nunique()}", fontsize=11)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_xlabel("count")
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    fig.suptitle("High-cardinality categoricals (top 15 values each)", fontsize=16)
    fig.tight_layout()
    save(fig, "high_cardinality_top15.png")

# date distributions
if date_cols:
    log("")
    log("Date column ranges:")
    for c in date_cols:
        s = df[c].dropna()
        log(f"    {c}: {s.min()} -> {s.max()}  (missing {df[c].isna().sum()})")
    fig, axes = plt.subplots(len(date_cols), 1,
                             figsize=(14, 3.2 * len(date_cols)), squeeze=False)
    for ax, c in zip(axes.ravel(), date_cols):
        s = df[c].dropna()
        try:
            s.dt.to_period("M").value_counts().sort_index().plot(kind="bar", ax=ax,
                                                                 color="#e67e22")
            ax.set_title(c)
            ax.set_ylabel("count")
            ax.tick_params(axis="x", labelrotation=90, labelsize=7)
        except Exception as e:
            ax.set_title(f"{c} (plot failed: {e})")
    fig.tight_layout()
    save(fig, "datetime_distributions.png")

# ---------------------------------------------------------------- correlations
log("")
log("=" * 78)
log("7. CORRELATIONS")
log("=" * 78)

corr = df[numeric_cols].corr(method="pearson")
all_missing = [c for c in numeric_cols if df[c].notna().sum() == 0]
if all_missing:
    log(f"Excluded from correlation (100% missing): {all_missing}")
    corr = corr.drop(index=all_missing, columns=all_missing, errors="ignore")
log("Pearson correlation matrix:")
log(corr.round(3).to_string())
log("")

# strong pairs
pairs = []
cols = list(corr.columns)
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        r = corr.iloc[i, j]
        if pd.notna(r):
            pairs.append((cols[i], cols[j], r))
pairs.sort(key=lambda t: abs(t[2]), reverse=True)
log("Top 20 strongest |correlations|:")
for a, b, r in pairs[:20]:
    log(f"    {a} <-> {b}: {r:+.3f}")
log("")
log("Moderate/strong correlations (|r| >= 0.5):")
strong = [(a, b, r) for a, b, r in pairs if abs(r) >= 0.5]
if strong:
    for a, b, r in strong:
        log(f"    {a} <-> {b}: {r:+.3f}")
else:
    log("    (none)")
log("")

# heatmap
fig, ax = plt.subplots(figsize=(16, 13))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
            annot=len(numeric_cols) <= 20, fmt=".2f",
            linewidths=0.3, ax=ax, annot_kws={"size": 7})
ax.set_title("Pearson correlation heatmap (lower triangle)")
ax.tick_params(labelsize=8)
save(fig, "correlation_heatmap.png")

spearman = df[corr.columns].corr(method="spearman")
fig, ax = plt.subplots(figsize=(16, 13))
sns.heatmap(spearman, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
            linewidths=0.3, ax=ax)
ax.set_title("Spearman rank correlation heatmap (lower triangle)")
ax.tick_params(labelsize=8)
save(fig, "correlation_heatmap_spearman.png")

# scatter plots of top correlated pairs
top_pairs = pairs[:6]
if top_pairs:
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    for ax, (a, b, r) in zip(axes, top_pairs):
        sub = df[[a, b]].dropna()
        if len(sub) > 3000:
            sub = sub.sample(3000, random_state=42)
        ax.scatter(sub[a], sub[b], s=6, alpha=0.35, color="#2980b9")
        ax.set_xlabel(a, fontsize=9)
        ax.set_ylabel(b, fontsize=9)
        ax.set_title(f"r = {r:+.3f}", fontsize=11)
    for ax in axes[len(top_pairs):]:
        ax.axis("off")
    fig.suptitle("Scatter plots of strongest correlated pairs", fontsize=16)
    fig.tight_layout()
    save(fig, "correlation_scatters.png")

# ---------------------------------------------------------------- extras
log("")
log("=" * 78)
log("8. ADDITIONAL NOTES")
log("=" * 78)
log(f"Duplicate rows: {df.duplicated().sum()}")
if "player_id" in df.columns:
    log(f"player_id unique: {df['player_id'].nunique()} / {n_rows} "
        f"(duplicates: {df['player_id'].duplicated().sum()})")
log(f"Numeric columns: {len(numeric_cols)}, Categorical: {len(categorical_cols)}, "
    f"Datetime: {len(date_cols)}, Boolean: {len(bool_cols)}")

report_path = os.path.join(OUT, "eda_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nReport written to {report_path}")
