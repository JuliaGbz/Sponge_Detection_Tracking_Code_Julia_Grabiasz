import os
import glob
import math
import pandas as pd


# ============================================================
# 1. FOLDER CONTAINING THE EVENT NAVIGATION TXT FILES
# ============================================================

BASE_FOLDER = r"D:\cal\23010_OFOPS_cleaned"

OUTPUT_CSV = os.path.join(
    BASE_FOLDER,
    "ROV_Distance_and_Speed_Results.csv"
)


# ============================================================
# 2. REAL START AND END TIMES PROVIDED BY ALEXA
# ============================================================

# Event 62 which event 100 is intentionally excluded for as is a different dataset.

EVENT_TIMES = {
    "02": ("01:37:22", "01:38:10"),
    "08": ("22:42:17", "22:43:05"),
    "16": ("01:44:27", "01:45:15"),
    "32": ("05:42:16", "05:43:04"),
    "50": ("01:44:15", "01:45:03"),
    "69": ("05:41:19", "05:42:07"),
    "88": ("06:02:45", "06:03:33"),
    "89": ("15:27:25", "15:28:13"),
    "91": ("02:58:15", "02:59:03"),
}


# ============================================================
# 3. HAVERSINE DISTANCE FUNCTION
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two
    latitude/longitude positions.

    The result is returned in metres.

    The Haversine formula is used because latitude and longitude
    describe positions on the curved surface of the Earth.

    Earth radius used:
        6,371,000 metres
    """

    EARTH_RADIUS_M = 6_371_000

    # Convert degrees to radians.
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)

    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference between positions.
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine calculation.
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
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
# 4. FIND THE NAVIGATION FILE FOR EACH EVENT
# ============================================================

def find_event_file(event_number):
    """
    Find the TXT navigation file belonging to each event.

    This is flexible because your filenames are not all
    exactly the same.

    Examples:
        CE23010_Ev02_Formatted.txt
        CE23010_Ev16_unique_splined.txt
        CE23010_Ev91_Interpolated_Spline.txt
    """

    patterns = [
        os.path.join(
            BASE_FOLDER,
            f"*Ev{event_number}*.txt"
        )
    ]

    matches = []

    for pattern in patterns:
        matches.extend(
            glob.glob(pattern)
        )

    # Remove duplicates.
    matches = list(
        dict.fromkeys(matches)
    )

    if len(matches) == 0:
        return None

    return matches[0]


# ============================================================
# 5. STANDARDISE LATITUDE AND LONGITUDE COLUMN NAMES
# ============================================================

def standardise_coordinate_columns(df, event_number):
    """
    Your navigation files use two different coordinate formats.

    Some files use:

        SUB1_Lon
        SUB1_Lat

    Other files use:

        Longitude
        Latitude

    This function converts BOTH formats into:

        Longitude_std
        Latitude_std

    This allows the exact same Haversine calculation to be used
    across every event.
    """

    # Remove accidental spaces around column names.
    df.columns = df.columns.str.strip()


    # --------------------------------------------------------
    # FORMAT 1:
    # SUB1_Lon / SUB1_Lat
    # --------------------------------------------------------

    if (
        "SUB1_Lon" in df.columns
        and "SUB1_Lat" in df.columns
    ):

        df["Longitude_std"] = pd.to_numeric(
            df["SUB1_Lon"],
            errors="coerce"
        )

        df["Latitude_std"] = pd.to_numeric(
            df["SUB1_Lat"],
            errors="coerce"
        )

        coordinate_format = (
            "SUB1_Lon / SUB1_Lat"
        )


    # --------------------------------------------------------
    # FORMAT 2:
    # Longitude / Latitude
    # --------------------------------------------------------

    elif (
        "Longitude" in df.columns
        and "Latitude" in df.columns
    ):

        df["Longitude_std"] = pd.to_numeric(
            df["Longitude"],
            errors="coerce"
        )

        df["Latitude_std"] = pd.to_numeric(
            df["Latitude"],
            errors="coerce"
        )

        coordinate_format = (
            "Longitude / Latitude"
        )


    # --------------------------------------------------------
    # FORMAT NOT RECOGNISED
    # --------------------------------------------------------

    else:

        print(
            f"ERROR: Could not identify "
            f"latitude/longitude columns "
            f"for Event {event_number}"
        )

        print(
            "Columns available:"
        )

        print(
            df.columns.tolist()
        )

        return None, None


    print(
        f"Coordinate format: "
        f"{coordinate_format}"
    )


    # Remove any rows where coordinates are missing.
    df = df.dropna(
        subset=[
            "Longitude_std",
            "Latitude_std"
        ]
    )

    return df, coordinate_format


# ============================================================
# 6. PROCESS ONE EVENT
# ============================================================

def process_event(
    event_number,
    start_time,
    expected_end_time
):

    print("\n")
    print("=" * 70)
    print(
        f"PROCESSING EVENT {event_number}"
    )
    print("=" * 70)


    # --------------------------------------------------------
    # FIND NAVIGATION FILE
    # --------------------------------------------------------

    file_path = find_event_file(
        event_number
    )

    if file_path is None:

        print(
            f"ERROR: No navigation file "
            f"found for Event {event_number}"
        )

        return None


    print(
        "Navigation file:"
    )

    print(
        file_path
    )

    print(
        f"Alexa real clip start: "
        f"{start_time}"
    )

    print(
        f"Alexa real clip end:   "
        f"{expected_end_time}"
    )


    # --------------------------------------------------------
    # READ NAVIGATION FILE
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            file_path
        )

    except Exception as e:

        print(
            f"ERROR reading Event "
            f"{event_number}"
        )

        print(e)

        return None


    # Clean column names.
    df.columns = (
        df.columns
        .str.strip()
    )


    print(
        "\nColumns found:"
    )

    print(
        df.columns.tolist()
    )


    # --------------------------------------------------------
    # CHECK DATE AND TIME COLUMNS
    # --------------------------------------------------------

    if "Date" not in df.columns:

        print(
            f"ERROR: Date column "
            f"not found for "
            f"Event {event_number}"
        )

        return None


    if "Time" not in df.columns:

        print(
            f"ERROR: Time column "
            f"not found for "
            f"Event {event_number}"
        )

        return None


    # --------------------------------------------------------
    # STANDARDISE COORDINATES
    # --------------------------------------------------------

    df, coordinate_format = (
        standardise_coordinate_columns(
            df,
            event_number
        )
    )

    if df is None:
        return None


    # --------------------------------------------------------
    # CREATE FULL DATETIME
    # --------------------------------------------------------

    # Example:
    #
    # Date = 05/23/2023
    # Time = 01:37:22
    #
    # becomes:
    #
    # 2023-05-23 01:37:22

    df["datetime"] = pd.to_datetime(
        df["Date"].astype(str)
        + " "
        + df["Time"].astype(str),
        errors="coerce"
    )


    # Remove invalid timestamps.
    df = df.dropna(
        subset=["datetime"]
    )


    # Create a HH:MM:SS column.
    df["time_only"] = (
        df["datetime"]
        .dt.strftime("%H:%M:%S")
    )


    # --------------------------------------------------------
    # FIND ALEXA'S EXACT START TIME
    # --------------------------------------------------------

    start_matches = df[
        df["time_only"]
        == start_time
    ]


    if start_matches.empty:

        print(
            f"ERROR: Start time "
            f"{start_time} was not found "
            f"for Event {event_number}"
        )

        return None


    # Take the first exact match.
    start_datetime = (
        start_matches
        .iloc[0]["datetime"]
    )


    # --------------------------------------------------------
    # CLIP DURATION
    # --------------------------------------------------------

    CLIP_DURATION_SECONDS = 48


    # Calculate exact end timestamp.
    end_datetime = (
        start_datetime
        + pd.Timedelta(
            seconds=
            CLIP_DURATION_SECONDS
        )
    )


    # --------------------------------------------------------
    # SELECT ONLY THE EXACT 48-SECOND CLIP
    # --------------------------------------------------------

    clip_df = df[
        (df["datetime"]
         >= start_datetime)
        &
        (df["datetime"]
         <= end_datetime)
    ].copy()


    clip_df = (
        clip_df
        .sort_values("datetime")
        .reset_index(drop=True)
    )


    print(
        f"\nNavigation positions selected: "
        f"{len(clip_df)}"
    )

    print(
        f"Actual start used: "
        f"{start_datetime}"
    )

    print(
        f"Actual end used:   "
        f"{end_datetime}"
    )


    # --------------------------------------------------------
    # CHECK NAVIGATION POSITION COUNT
    # --------------------------------------------------------

    if len(clip_df) < 2:

        print(
            f"ERROR: Not enough navigation "
            f"positions for Event "
            f"{event_number}"
        )

        return None


    if len(clip_df) == 49:

        print(
            "Good: 49 navigation positions "
            "were found for the 48-second clip."
        )

    else:

        print(
            f"WARNING: Expected approximately "
            f"49 positions but found "
            f"{len(clip_df)}."
        )


    # ========================================================
    # 7. CALCULATE DISTANCE BETWEEN EACH POSITION
    # ========================================================

    # its distance is set to 0.

    distances = [0.0]


    for i in range(
        1,
        len(clip_df)
    ):

        # Previous position.
        lat1 = clip_df.loc[
            i - 1,
            "Latitude_std"
        ]

        lon1 = clip_df.loc[
            i - 1,
            "Longitude_std"
        ]


        # Current position.
        lat2 = clip_df.loc[
            i,
            "Latitude_std"
        ]

        lon2 = clip_df.loc[
            i,
            "Longitude_std"
        ]


        # Haversine distance between
        # the two GPS positions.
        distance = haversine_distance(
            lat1,
            lon1,
            lat2,
            lon2
        )


        distances.append(
            distance
        )


    # Add the individual distance values
    # to the dataframe.
    clip_df[
        "distance_from_previous_m"
    ] = distances


    # ========================================================
    # 8. CUMULATIVE DISTANCE
    # ========================================================

    clip_df[
        "cumulative_distance_m"
    ] = (
        clip_df[
            "distance_from_previous_m"
        ]
        .cumsum()
    )


    # Total distance travelled during
    # the 48-second clip.
    total_distance_m = (
        clip_df[
            "distance_from_previous_m"
        ]
        .sum()
    )


    # ========================================================
    # 9. CALCULATE AVERAGE ROV SPEED
    # ========================================================
    
    average_speed_m_s = (
        total_distance_m
        / CLIP_DURATION_SECONDS
    )


    # ========================================================
    # 10. PRINT RESULTS
    # ========================================================

    print(
        "\nRESULTS"
    )

    print(
        f"Total ROV distance: "
        f"{total_distance_m:.3f} m"
    )

    print(
        f"Average ROV speed: "
        f"{average_speed_m_s:.3f} m/s"
    )


    # ========================================================
    # 11. SAVE DETAILED EVENT CALCULATION
    # ========================================================

    detailed_output = os.path.join(
        BASE_FOLDER,
        f"Event{event_number}"
        f"_ROV_Distance_Details.csv"
    )


    # Columns we definitely want.
    output_columns = [
        "Date",
        "Time",
        "Latitude_std",
        "Longitude_std",
        "distance_from_previous_m",
        "cumulative_distance_m"
    ]


    # Add altitude/depth if it exists.
    if "Altitude" in clip_df.columns:

        output_columns.append(
            "Altitude"
        )


    elif (
        "SUB1_USBL_Depth"
        in clip_df.columns
    ):

        output_columns.append(
            "SUB1_USBL_Depth"
        )


    clip_df[
        output_columns
    ].to_csv(
        detailed_output,
        index=False
    )


    print(
        f"Detailed Event "
        f"{event_number} results "
        f"saved to:"
    )

    print(
        detailed_output
    )


    # ========================================================
    # 12. RETURN SUMMARY RESULT
    # ========================================================

    return {

        "Event":
            f"Event{event_number}",

        "Start_Time":
            start_time,

        "End_Time":
            expected_end_time,

        "Duration_s":
            CLIP_DURATION_SECONDS,

        "Navigation_Positions":
            len(clip_df),

        "Coordinate_Format":
            coordinate_format,

        "Total_Distance_m":
            total_distance_m,

        "Average_Speed_m_s":
            average_speed_m_s
    }


# ============================================================
# 13. RUN ALL EVENTS
# ============================================================

results = []

successful_events = []

failed_events = []


for event_number, times in EVENT_TIMES.items():

    start_time = times[0]

    end_time = times[1]


    result = process_event(
        event_number,
        start_time,
        end_time
    )


    if result is not None:

        results.append(
            result
        )

        successful_events.append(
            event_number
        )

        print(
            f"\nSUCCESS: "
            f"Event {event_number}"
        )


    else:

        failed_events.append(
            event_number
        )

        print(
            f"\nFAILED: "
            f"Event {event_number}"
        )


# ============================================================
# 14. CREATE FINAL SUMMARY TABLE
# ============================================================

results_df = pd.DataFrame(
    results
)


if not results_df.empty:

    results_df[
        "Total_Distance_m"
    ] = (
        results_df[
            "Total_Distance_m"
        ]
        .round(3)
    )


    results_df[
        "Average_Speed_m_s"
    ] = (
        results_df[
            "Average_Speed_m_s"
        ]
        .round(3)
    )


# ============================================================
# 15. SAVE FINAL SUMMARY CSV
# ============================================================

results_df.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# 16. PRINT FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 80)

print(
    "FINAL ROV DISTANCE AND "
    "SPEED RESULTS"
)

print("=" * 80)


if not results_df.empty:

    print(
        results_df.to_string(
            index=False
        )
    )

else:

    print(
        "No events were processed "
        "successfully."
    )


print("\n")
print("=" * 80)

print(
    "PROCESSING SUMMARY"
)

print("=" * 80)


print(
    "Successful events:",
    successful_events
)

print(
    "Failed events:",
    failed_events
)


print(
    "\nFinal summary saved to:"
)

print(
    OUTPUT_CSV
)