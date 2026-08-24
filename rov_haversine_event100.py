import os
import math
import pandas as pd


# ============================================================
# EVENT 62 = EVENT 100 IN Project
# ============================================================

FILE_PATH = r"D:\cal\CE16006_ofops_Event62.txt"

OUTPUT_FOLDER = r"D:\cal"


# ============================================================
# EXACT 48-SECOND CLIP INFORMATION FROM ALEXA
# ============================================================

# Alexa identified this interval as the real time corresponding
# to the 48-second Event 100 clip.

START_DATE = "06/09/2016"
START_TIME = "04:59:46"

CLIP_DURATION_SECONDS = 48


# ============================================================
# OUTPUT FILES
# ============================================================

DETAIL_OUTPUT = os.path.join(
    OUTPUT_FOLDER,
    "Event100_Event62_ROV_Distance_Details.csv"
)

SUMMARY_OUTPUT = os.path.join(
    OUTPUT_FOLDER,
    "Event100_Event62_ROV_Summary.csv"
)


# ============================================================
# HAVERSINE FUNCTION
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two ROV
    latitude/longitude positions.

    The result is returned in metres.

    This is the SAME Haversine calculation used for the
    2023 events.
    """

    # Mean radius of the Earth in metres
    EARTH_RADIUS_M = 6_371_000

    # Convert coordinates from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)

    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences between latitude and longitude
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    distance_m = EARTH_RADIUS_M * c

    return distance_m


# ============================================================
# 1. READ THE EVENT 62 FILE
# ============================================================


df = pd.read_csv(
    FILE_PATH,
    sep=r"\s+",
    engine="python"
)


# ============================================================
# 2. CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


print("\n")
print("=" * 70)
print("EVENT 62 / EVENT 100")
print("=" * 70)

print("\nColumns found:")
print(df.columns.tolist())


# ============================================================
# 3. CHECK REQUIRED ROV COORDINATE COLUMNS
# ============================================================

required_columns = [
    "#Date",
    "SUB1_Lon",
    "SUB1_Lat"
]


for column in required_columns:

    if column not in df.columns:

        print(
            f"\nERROR: Required column "
            f"'{column}' was not found."
        )

        print("\nAvailable columns:")
        print(df.columns.tolist())

        raise SystemExit


# ============================================================
# 4. FIX EVENT 62 DATE/TIME STRUCTURE
# ============================================================


df["Actual_Date"] = (
    df.index
    .astype(str)
    .str.strip()
)


df["Actual_Time"] = (
    df["#Date"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 5. CHECKING  ALEXA'S START TIME THAT IT EXISTS
# ============================================================

print("\nLooking for exact clip start:")

print(
    f"{START_DATE} {START_TIME}"
)


start_matches = df[
    (df["Actual_Date"] == START_DATE)
    &
    (df["Actual_Time"] == START_TIME)
]


print(
    "Number of exact matches:",
    len(start_matches)
)


if start_matches.empty:

    print(
        "\nERROR: The exact clip start "
        "was still not found."
    )

    print(
        "\nShowing navigation rows around 04:59:"
    )

    nearby = df[
        df["Actual_Time"]
        .str.startswith(
            "04:59",
            na=False
        )
    ]

    print(
        nearby[
            [
                "Actual_Date",
                "Actual_Time",
                "SUB1_Lon",
                "SUB1_Lat"
            ]
        ]
        .head(100)
        .to_string(index=False)
    )

    raise SystemExit


print(
    "\nSUCCESS: "
    "Alexa's clip start was found."
)


# ============================================================
# 6. CREATE PROPER DATETIME
# ============================================================


df["datetime"] = pd.to_datetime(

    df["Actual_Date"]
    + " "
    + df["Actual_Time"],

    format="%d/%m/%Y %H:%M:%S",

    errors="coerce"
)


# Remove rows where datetime genuinely cannot be interpreted
df = df.dropna(
    subset=["datetime"]
)


# ============================================================
# 7. CREATE EXACT START DATETIME
# ============================================================

start_datetime = pd.to_datetime(

    START_DATE
    + " "
    + START_TIME,

    format="%d/%m/%Y %H:%M:%S"
)


# ============================================================
# 8. CALCULATE EXACT END OF 48-SECOND CLIP
# ============================================================

end_datetime = (
    start_datetime
    +
    pd.Timedelta(
        seconds=CLIP_DURATION_SECONDS
    )
)


print("\nExact clip interval:")

print(
    f"Start: {start_datetime}"
)

print(
    f"End:   {end_datetime}"
)


# ============================================================
# 9. SELECT ONLY THE EXACT 48-SECOND INTERVAL
# ============================================================

clip_df = df[
    (df["datetime"] >= start_datetime)
    &
    (df["datetime"] <= end_datetime)
].copy()


# Sort everything into chronological order
clip_df = (
    clip_df
    .sort_values("datetime")
    .reset_index(drop=True)
)


print(
    f"\nNavigation positions selected: "
    f"{len(clip_df)}"
)


# ============================================================
# 10. SHOW FIRST AND LAST SELECTED ROWS
# ============================================================

if not clip_df.empty:

    print(
        "\nFirst selected row:"
    )

    print(
        clip_df.loc[
            0,
            [
                "Actual_Date",
                "Actual_Time",
                "SUB1_Lon",
                "SUB1_Lat"
            ]
        ]
    )


    print(
        "\nLast selected row:"
    )

    print(
        clip_df.loc[
            len(clip_df) - 1,
            [
                "Actual_Date",
                "Actual_Time",
                "SUB1_Lon",
                "SUB1_Lat"
            ]
        ]
    )


# ============================================================
# 11. CHECK NUMBER OF POSITIONS
# ============================================================


if len(clip_df) == 49:

    print(
        "\nGood: 49 navigation positions "
        "were selected."
    )

else:

    print(
        f"\nNOTE: 49 positions were expected "
        f"if navigation is recorded once per second, "
        f"but {len(clip_df)} positions were found."
    )


if len(clip_df) < 2:

    print(
        "\nERROR: Not enough navigation positions "
        "to calculate distance."
    )

    raise SystemExit


# ============================================================
# 12. CONVERT ROV COORDINATES TO NUMERIC VALUES
# ============================================================


clip_df["Longitude"] = pd.to_numeric(
    clip_df["SUB1_Lon"],
    errors="coerce"
)


clip_df["Latitude"] = pd.to_numeric(
    clip_df["SUB1_Lat"],
    errors="coerce"
)


# ============================================================
# 13. CHECK FOR MISSING COORDINATES
# ============================================================

missing_coordinates = clip_df[
    clip_df[
        [
            "Longitude",
            "Latitude"
        ]
    ]
    .isna()
    .any(axis=1)
]


if not missing_coordinates.empty:

    print(
        "\nWARNING: Some rows contain "
        "missing ROV coordinates:"
    )

    print(
        missing_coordinates[
            [
                "Actual_Date",
                "Actual_Time",
                "SUB1_Lon",
                "SUB1_Lat"
            ]
        ]
        .to_string(index=False)
    )


# Remove rows only if coordinates really are missing
clip_df = clip_df.dropna(
    subset=[
        "Longitude",
        "Latitude"
    ]
).reset_index(drop=True)


print(
    f"\nValid ROV coordinate positions: "
    f"{len(clip_df)}"
)


if len(clip_df) < 2:

    print(
        "\nERROR: Not enough valid "
        "ROV coordinates remain."
    )

    raise SystemExit


# ============================================================
# 14. CALCULATE DISTANCE BETWEEN CONSECUTIVE POSITIONS
# ============================================================

distances = [0.0]


for i in range(
    1,
    len(clip_df)
):


    # Previous ROV position
    lat1 = clip_df.loc[
        i - 1,
        "Latitude"
    ]

    lon1 = clip_df.loc[
        i - 1,
        "Longitude"
    ]


    # Current ROV position
    lat2 = clip_df.loc[
        i,
        "Latitude"
    ]

    lon2 = clip_df.loc[
        i,
        "Longitude"
    ]


    # Calculate geographic distance
    distance_m = haversine_distance(
        lat1,
        lon1,
        lat2,
        lon2
    )


    distances.append(
        distance_m
    )


# ============================================================
# 15. SAVE EACH DISTANCE
# ============================================================

clip_df[
    "Distance_from_previous_m"
] = distances


# ============================================================
# 16. CALCULATE CUMULATIVE DISTANCE
# ============================================================

clip_df[
    "Cumulative_distance_m"
] = (
    clip_df[
        "Distance_from_previous_m"
    ]
    .cumsum()
)


# ============================================================
# 17. TOTAL DISTANCE TRAVELLED
# ============================================================

# Add all of the consecutive Haversine distances.

total_distance_m = (
    clip_df[
        "Distance_from_previous_m"
    ]
    .sum()
)


# ============================================================
# 18. AVERAGE ROV SPEED
# ============================================================


average_speed_m_s = (
    total_distance_m
    /
    CLIP_DURATION_SECONDS
)


# ============================================================
# 19. MEAN ROV MOVEMENT PER 1-SECOND WINDOW
# ============================================================

mean_movement_per_1s_window_m = (
    average_speed_m_s
    * 1
)


# ============================================================
# 20. PRINT FINAL RESULTS
# ============================================================

print("\n")
print("=" * 70)

print(
    "FINAL EVENT 100 RESULTS "
    "(NAVIGATION SOURCE = EVENT 62)"
)

print("=" * 70)


print(
    f"Total ROV distance: "
    f"{total_distance_m:.3f} m"
)


print(
    f"Average ROV speed: "
    f"{average_speed_m_s:.3f} m/s"
)


print(
    f"Mean ROV movement per "
    f"1-s window: "
    f"{mean_movement_per_1s_window_m:.3f} m"
)


# ============================================================
# 21. SAVE DETAILED CALCULATION
# ============================================================

detail_columns = [
    "Actual_Date",
    "Actual_Time",
    "SUB1_Lon",
    "SUB1_Lat",
    "Longitude",
    "Latitude",
    "Distance_from_previous_m",
    "Cumulative_distance_m"
]


# USBL depth is saved only as supporting information.
#
# It is NOT used in the Haversine distance calculation.

if "SUB1_USBL_Depth" in clip_df.columns:

    detail_columns.append(
        "SUB1_USBL_Depth"
    )


clip_df[
    detail_columns
].to_csv(
    DETAIL_OUTPUT,
    index=False
)


# ============================================================
# 22. CREATE FINAL SUMMARY
# ============================================================

summary_df = pd.DataFrame(
    [
        {
            "Event":
                "Event100",

            "Navigation_Event":
                "Event62",

            "Start_Date":
                START_DATE,

            "Start_Time":
                START_TIME,

            "End_Time":
                end_datetime.strftime(
                    "%H:%M:%S"
                ),

            "Duration_s":
                CLIP_DURATION_SECONDS,

            "Navigation_Positions":
                len(clip_df),

            "Total_ROV_Distance_m":
                round(
                    total_distance_m,
                    3
                ),

            "Average_ROV_Speed_m_s":
                round(
                    average_speed_m_s,
                    3
                ),

            "Mean_ROV_Movement_per_1s_Window_m":
                round(
                    mean_movement_per_1s_window_m,
                    3
                )
        }
    ]
)


# ============================================================
# 23. SAVE SUMMARY
# ============================================================

summary_df.to_csv(
    SUMMARY_OUTPUT,
    index=False
)


# ============================================================
# 24. DISPLAY FINAL SUMMARY
# ============================================================

print(
    "\nFinal summary:"
)

print(
    summary_df.to_string(
        index=False
    )
)


print(
    "\nDetailed calculation saved to:"
)

print(
    DETAIL_OUTPUT
)


print(
    "\nSummary saved to:"
)

print(
    SUMMARY_OUTPUT
)