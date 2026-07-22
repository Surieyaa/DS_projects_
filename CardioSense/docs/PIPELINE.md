# CardioSense — Cardiovascular Disease Risk Prediction Pipeline

**Model**: Random Forest (feature selection) + Optimized SVM (classification)
**Dataset**: BRFSS-derived Cardiovascular Diseases Risk Prediction (Kaggle), 308,854 rows, 19 columns

---

## 1. Data Collection

- Source: Kaggle's BRFSS-derived Cardiovascular Diseases Risk Prediction dataset — a real-world U.S. health survey (Behavioral Risk Factor Surveillance System).
- Loaded as a single CSV with 308,854 records and 19 features, including demographics (age, sex), self-reported health conditions (diabetes, arthritis, cancers, depression), lifestyle habits (exercise, smoking, alcohol, diet), and the binary target `Heart_Disease`.
- No missing values in the raw file — a rare and convenient property of this dataset that simplified preprocessing considerably.

## 2. Data Cleaning & Preprocessing

- Removed duplicate rows with `drop_duplicates()`.
- Dropped the `Checkup` column (last doctor visit timing) — not predictive for this modeling goal and added noise to feature selection.
- Verified class balance of the target: `Heart_Disease` is heavily imbalanced (~91% No / ~9% Yes), which shaped every downstream decision (class weighting, threshold tuning, calibration).

## 3. Exploratory Data Analysis (EDA)

- Checked value distributions for all categorical fields (`General_Health`, `Diabetes`, `Age_Category`, etc.) to confirm expected categories and no encoding surprises.
- Examined the target's relationship with key lifestyle variables by grouping mean consumption levels (fruit, vegetables, alcohol, fried food) by `Heart_Disease` status.
- **Key EDA finding**: this comparison uncovered a reverse-causality confound — people already diagnosed with heart disease reported *lower* alcohol and fried-food consumption than people without heart disease, most likely reflecting post-diagnosis lifestyle changes rather than true risk direction. This finding directly shaped the feature selection stage (see Section 5) and is one of the more important methodological insights in the project.

## 4. Feature Encoding

- **Binary categorical columns** (`Exercise`, `Skin_Cancer`, `Other_Cancer`, `Depression`, `Arthritis`, `Sex`, `Smoking_History`, `Heart_Disease`) encoded via `LabelEncoder`.
- **Ordinal columns** encoded with explicit, meaning-preserving maps rather than arbitrary label encoding:
  - `General_Health`: Poor=0 → Excellent=4
  - `Age_Category`: sorted numerically by age-range lower bound
  - `Diabetes`: collapsed into No / borderline / Yes, since "told only during pregnancy" and "no, borderline" are clinically closer to No than to a full diabetes diagnosis
- This ordinal-aware encoding (rather than naive label encoding) preserves the natural ordering the models can exploit — important for tree-based and margin-based methods alike.

## 5. Feature Selection (Random Forest)

- Excluded `Alcohol_Consumption` and `FriedPotato_Consumption` **before** feature selection, based on the reverse-causality confound identified in EDA.
- Split data 80/20 (stratified on the target to preserve class balance in both sets).
- Standardized all features with `StandardScaler` (fit on train, applied to test — no leakage).
- Trained a `RandomForestClassifier` (300 trees, `class_weight='balanced'`) on the full feature set and ranked features by `feature_importances_`.
- Selected the **top 10 features**: `Age_Category, BMI, Weight_(kg), General_Health, Green_Vegetables_Consumption, Fruit_Consumption, Height_(cm), Diabetes, Arthritis, Smoking_History`.
- **Sanity-checked feature direction** post-selection by holding all-but-one feature constant and varying each in turn — confirming predicted risk moves the expected direction (older age, worse health, higher weight, smoking, arthritis → higher risk; more fruit/vegetables → lower risk) before proceeding.

## 6. Model Training — Optimized SVM

- **Why SVM needed care**: with ~247K training rows, a full grid search or full-dataset fit on `SVC` (O(n²)–O(n³) complexity) was computationally impractical — an early attempt hung for 30+ minutes.
- **Hyperparameter tuning**: `RandomizedSearchCV` on a stratified 8,000-row tuning subsample (small enough for speed, large enough to keep positive-class examples in every CV fold), searching `C`, `gamma`, and kernel (`rbf`), with `max_iter` capped and `cache_size` increased to prevent runaway fits.
  - *Note*: an initial attempt used `HalvingRandomSearchCV` for speed, but its aggressive resource-shrinking produced tiny CV folds with zero positive examples on this imbalanced target, yielding meaningless near-random scores (AUC ≈ 0.51). Switched back to plain `RandomizedSearchCV` with a fixed, adequately-sized tuning sample — CV ROC-AUC recovered to a sound 0.82.
  - Best params found: `kernel='rbf', C=0.1, gamma=0.01`.
- **Final fit**: trained on a larger 40,000-row stratified subsample with `class_weight='balanced'` to counter the 91:9 imbalance.

## 7. Threshold Tuning & Probability Calibration

Two distinct problems surfaced after initial training, each requiring a targeted fix:

**a) Decision threshold.** At the default 0.5 cutoff, `class_weight='balanced'` pushed the model to classify nearly every sample as "Yes" (0% recall on "No"). Fixed by scanning the precision-recall curve and selecting the threshold that maximizes F1 on the minority class — landing at a data-driven cutoff rather than the arbitrary 0.5 default.

**b) Probability calibration.** Even after threshold tuning, the *displayed* probabilities were badly miscalibrated: `class_weight='balanced'` combined with a smooth decision boundary compressed nearly all predictions into an uninformative 17–54% band — genuinely healthy people scored a median 41% "risk," nearly indistinguishable from unhealthy profiles. Fixed by wrapping the tuned SVM in `CalibratedClassifierCV` (isotonic method) fit on a held-out calibration split. This remapped raw scores to probabilities matching true population rates (mean predicted probability ≈ 8.1%, matching the actual ≈ 8.1% test-set prevalence) while preserving ranking performance (AUC unchanged).

## 8. Evaluation

Final calibrated SVM on the held-out test set (61,755 rows):

| Metric | No (majority) | Yes (minority) |
|---|---|---|
| Precision | 0.94 | 0.24 |
| Recall | 0.89 | 0.41 |
| F1-score | 0.92 | 0.30 |

Overall accuracy: 0.85 · ROC-AUC: 0.76

**Compared against Random Forest** (same test set, default 0.5 threshold): Random Forest achieved higher raw accuracy (0.92) and ROC-AUC (0.81), but only 4% recall on the minority class — it was barely detecting true heart-disease cases. The SVM's threshold and calibration tuning traded some raw accuracy for far better recall (41% vs 4%), the more clinically meaningful tradeoff for a screening tool where missing true cases is costlier than false alarms.

## 9. Deployment

- Exported the full inference pipeline (trained SVM + calibrator, scaler, selected features, encoding maps, decision threshold) as a single pickled artifact for portability.
- Built a Streamlit web app (`CardioSense`) with:
  - Form inputs for the 10 selected features, each explicitly titled
  - A gauge visualization and color-coded risk tier (Healthy / Borderline / Elevated / High) driven by the calibrated probability
  - A heartbeat-themed loading animation during inference
  - Sidebar documentation of the model configuration and methodology notes (including the reverse-causality and calibration fixes) for transparency

---

## Key methodological takeaways (useful for report discussion/limitations sections)

1. **Reverse-causality confounding** is a real risk in observational survey data — features correlated with an outcome aren't necessarily *causing* it in the expected direction, especially for post-diagnosis behavior changes.
2. **`class_weight='balanced'` fixes decision boundaries, not probability calibration.** These are two separate problems requiring two separate fixes (threshold tuning + isotonic calibration).
3. **Accuracy is a misleading metric under class imbalance.** Random Forest's 92% accuracy hid a near-useless 4% recall on the minority class — always check per-class metrics (precision, recall, F1) alongside accuracy.
4. **SVM doesn't scale to large datasets by default.** Subsampling for hyperparameter search and final training was a necessary practical tradeoff, not a shortcut — worth explicitly justifying in a methods section.
