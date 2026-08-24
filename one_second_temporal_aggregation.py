import pandas as pd

# =====================================================
# FILE PATHS — EVENT02 MODEL CSV
# =====================================================

csv_path = r"D:\2023 Videos\Event02\final_sponge_object_resultsBB2iou.csv"

output_file = r"D:\2023 Videos\Event02\ModelYolo_Unique_CountsBB2iou.xlsx"

# =====================================================
# READ CSV
# =====================================================

df = pd.read_csv(csv_path)

print("CSV loaded successfully.")
print("Columns found:")
print(df.columns.tolist())

# =====================================================
# CLEAN REQUIRED COLUMNS
# =====================================================

df["time_seconds"] = pd.to_numeric(
    df["time_seconds"],
    errors="coerce"
)

df["frame"] = pd.to_numeric(
    df["frame"],
    errors="coerce"
)

df["track_id"] = pd.to_numeric(
    df["track_id"],
    errors="coerce"
)

df = df.dropna(
    subset=["time_seconds", "frame", "track_id"]
).copy()

df["frame"] = df["frame"].astype(int)
df["track_id"] = df["track_id"].astype(int)

# =====================================================
# CREATE 1-SECOND WINDOWS
# =====================================================

df["window"] = df["time_seconds"].astype(int)

# =====================================================
# COUNT UNIQUE TRACK IDS PER WINDOW
# =====================================================

summary = (
    df.groupby("window")
      .agg(
          frames_used=(
              "frame",
              lambda x: ", ".join(
                  map(str, sorted(x.unique()))
              )
          ),
          algorithm_unique_count=(
              "track_id",
              "nunique"
          ),
          track_ids_used=(
              "track_id",
              lambda x: ", ".join(
                  map(str, sorted(x.unique()))
              )
          )
      )
      .reset_index()
)

# =====================================================
# CREATE TIME WINDOW LABELS
# =====================================================

summary["time_window"] = (
    summary["window"].astype(str)
    + "-"
    + (summary["window"] + 1).astype(str)
    + " s"
)

summary = summary[
    [
        "time_window",
        "frames_used",
        "algorithm_unique_count",
        "track_ids_used"
    ]
]

# =====================================================
# SAVE TO EXCEL
# =====================================================

summary.to_excel(output_file, index=False)

print("\n1-second unique model counts:")
print(summary)

print("\nDone!")
print(f"Saved to:\n{output_file}")  