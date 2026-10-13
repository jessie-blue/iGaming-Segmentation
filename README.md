# Betty_v1 — Player Segmentation & Clustering

A data-science project that turns **100,000 raw player records** from a single CSV
into **six actionable player segments** (product / marketing / business interpretation),
including a full K-Means pipeline, five-algorithm model comparison, stability analysis,
and a ready-to-use slide deck.

---

## 1. Project objective

- Explore and profile a raw iGaming player dataset (100,000 accounts × 77 attributes).
- Engineer meaningful behavioural features (life cycle, engagement, economics).
- Cluster players with K-Means (and benchmark against GMM, Hierarchical, DBSCAN, HDBSCAN).
- Verify the clusters are stable and business-meaningful.
- Deliver interpretations and recommendations for CRM / VIP / marketing.

---

## 2. Repository layout (key artefacts)

| Path | Description |
|---|---|
| `Data Science Task Data.xlsx - Result 1.csv` | **Sole data source** (100,000 × 77). |
| `build_dataset.ipynb` | Cleans/enriches raw data → `transformed_data/player_dataset.csv` + `dataset_dictionary.csv`. |
| `feature_engineering.ipynb` | Builds **43 derived features** → `features/player_features.csv` + `feature_dictionary.csv`. |
| `new_eda.ipynb` | EDA: skew, missingness, correlations, clustering matrix → `new_eda_output/`. |
| `models/clustering_models.ipynb` | The 5 clustering models, hyperparameter grids, metrics, stability, visualisations. |
| `models/kmeans_profiling.ipynb` | K-Means cluster profiling and archetypes. |
| `master_dataset_clusters.csv` | Raw data + cluster labels (K-Means/GMM/Hierarchical/DBSCAN/HDBSCAN) per player. |
| `models/csv/` | All metrics, assignments, centers, profiles (CSV). |
| `models/viz/` | Charts: elbow, silhouette, dendrogram, AIC/BIC, PCA scatters, 3D rotating GIFs. |
| `presentation_materials/` | Ready-made reports: cluster profiling, business differentiation, recommendations, **`Betty_Player_Segmentation.pptx`**. |
| `requirements.txt` | Python dependencies. |
| `prompts.md` | Log of the prompts this project was developed against. |



## 3. Data snapshot conventions

- **REFERENCE_DATE** = `max(loaded_at)` = **2025-11-13 08:03:42** (the data snapshot, not "today").
- `tenure_months` = `tenure_days / 30.4375`; division by zero → `NaN` (never `inf`).
- Nullable booleans stay `NaN` when unrecorded (`NaN ≠ False`); only 59,922 complete-case
  players enter clustering.

---

## 4. The notebooks — run order

Run top to bottom. Steps 1 and 2 are independent of each other (both read the raw CSV),
but **3 depends on 1 and 2**, and **4 depends on 2**, and **5 depends on 4**.

| # | Notebook | Purpose | Key input(s) | Key output(s) | ~Runtime |
|---|---|---|---|---|---|
| 1 | `build_dataset.ipynb` | Clean & enrich raw data; produce the canonical dataset + dictionary | raw CSV | `transformed_data/player_dataset.csv`, `transformed_data/dataset_dictionary.csv` | minutes |
| 2 | `feature_engineering.ipynb` | Engineer 43 derived features (rates, ratios, flags) with full documentation | raw CSV | `features/player_features.csv`, `features/feature_dictionary.csv` | minutes |
| 3 | `new_eda.ipynb` | EDA: distributions, skew ranking, missingness, bivariate/correlation audits | raw CSV + outputs of 1 & 2 | `new_eda_output/` (stats, correlations, clustering matrix) | tens of minutes |
| 4 | `models/clustering_models.ipynb` | Build the 11-feature z-scored matrix; run K-Means, GMM, Hierarchical, DBSCAN, HDBSCAN; metrics, stability, 2D/3D viz | raw CSV + `features/player_features.csv` | `models/csv/*_metrics.csv`, `*_assignments.csv`, `kmeans_centers.csv`, `feature_matrix_11_complete.csv`, `models/viz/*` | ~30–45 min (DBSCAN/Hier on subsamples) |
| 5 | `models/kmeans_profiling.ipynb` | Profile the K-Means segments (numeric/ categorical/risk) and name the archetypes | `master_dataset_clusters.csv`, `models/csv/kmeans_cluster_numeric_profiles.csv` | `models/csv/kmeans_cluster_*_profiles.csv`, `kmeans_cluster_archetypes.csv`, `kmeans_cluster_flags.csv` | minutes |

> **Between 4 and 5:** `master_dataset_clusters.csv` is produced by merging the raw data
> with the K-Means assignments (`models/csv/kmeans_assignments.csv`) on `player_id`.
> It adds five columns: `cluster_kmeans`, `cluster_gmm`, `cluster_hier`,
> `cluster_dbscan`, `cluster_hdbscan`.

**Order summary:** `1 → 2 → 3 → 4 → 5` (1 and 2 interchangeable, run before 3; ML notebook
and profiling notebook can be re-run to regenerate all downstream artefacts).

> **Note on `eda_notebook.ipynb`:** this is an earlier EDA version, superseded by
> `new_eda.ipynb`. It is kept for reference (it also uses `eda.py`).

---

## 5. Reproducibility

- Environment: Python **3.11** (miniconda); see **`requirements.txt`** for pinned versions
  (pandas 3.0.6, scikit-learn 1.9.1, scipy, matplotlib, seaborn, Pillow, hdbscan 0.8.44,
  python-pptx 1.0.2).
- Deterministic seeds are used across the notebook; K-Means bootstrap stability
  (ARI 0.996 ± 0.002, NMI 0.993) shows runs are reproducible.
- Subsample sizes (Hierarchical n=6,000; DBSCAN n=15,000; HDBSCAN n=30,000) are fixed.
- Visual artefacts (GIFs) are `models/viz/*_3d.gif` (96 frames @ 12 fps); charts are PNG.

---

## 6. Headline results

- **6 K-Means segments**, no noise: Steady Regulars (15%), Dormant (22%), Whales (18%),
  Casual Winners (25%), Net-Loss Gamers (14%), Slow-Converters (6%).
- Whales ≈ **90% of gross gaming revenue**; Net-Loss Gamers have **negative GGR**.
- K-Means is the most stable (ARI 0.996) and most actionable; HDBSCAN would leave 31k
  players unassigned.
- Business actions are prioritised in `recommendations.md`.
