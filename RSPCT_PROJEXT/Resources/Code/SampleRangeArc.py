import datetime
import os
import pandas as pd
import numpy as np
import math
from pytz import timezone



def calculate_arcs(x, y):
    # Calculate arcs with corrected direction
    angle = np.degrees(np.arctan2(y, -x))  # Negate x to mirror around the y-axis
    angle = (angle + 360) % 360  # Normalize to [0, 360)
    return angle


def classify_sessions(shot_df):
    classifications = {
        'FT': 0,
        '3pts': 0,
        '2pts': 0,
    }
    # Free Throws classification
    ft_shots = shot_df[(shot_df['originX'].between(-500, 500)) & (shot_df['originY'].between(4000, 5000))]
    if not ft_shots.empty:
        classifications['FT'] = 1

    # 3pts and 2pts classification
    sectors = {
        'RC': (0, 36),
        'RW': (36, 72),
        'TK': (72, 108),
        'LW': (108, 144),
        'LC': (144, 360)
    }

    # Adding Range and Arc to the DataFrame for classification
    shot_df = shot_df.copy()  # Create a copy to avoid modifying the original DataFrame
    shot_df.loc[:, 'Range'] = np.sqrt(shot_df['originX'] ** 2 + shot_df['originY'] ** 2)
    shot_df.loc[:, 'Arc'] = calculate_arcs(shot_df['originX'], shot_df['originY'])

    arc_shots = shot_df[shot_df['Range'] > 5500]

    sector_counts = {key: arc_shots[(arc_shots['Arc'] >= value[0]) & (arc_shots['Arc'] < value[1])].shape[0] for
                     key, value in sectors.items()}
    sector_hits = sum(1 for count in sector_counts.values() if count > 0)

    if sector_hits >= 3:
        classifications['3pts'] = 1
    else:
        arc_shots = shot_df[shot_df['Range'] <= 5500]

        sector_counts = {key: arc_shots[(arc_shots['Arc'] >= value[0]) & (arc_shots['Arc'] < value[1])].shape[0] for
                         key, value in sectors.items()}
        sector_hits = sum(1 for count in sector_counts.values() if count > 0)

        if sector_hits >= 3:
            classifications['2pts'] = 1

    return classifications


def fetch_and_log_player_sessions(player_id, player_first_name, player_last_name, start_date, end_date, username,
                                  password, client_id, client_secret, print_frequency, calculate_origin_analytics,
                                  min_range_mms, local_tz, generate_session_ids_too):
    ## HERE GOT THE DATA FROM API
    
	## HERE GOT THE DATA FROM API

    period_start = int(start_date.timestamp() * 1000)
    period_end = int(end_date.timestamp() * 1000)

    session_data = []

    def process_sessions_for_player(player_id):
        ## HERE GOT THE DATA FROM API
        sessions = ## HERE GOT THE DATA FROM API
        for i, curSession in enumerate(sessions):
            try:
                shots = ## HERE GOT THE DATA FROM API
                displayname = f"{player_first_name}{player_last_name}_{len(shots)}_Shots_{datetime.datetime.utcfromtimestamp(curSession['startTime'] / 1000).strftime('%Y-%m-%d__%H%M')}-{datetime.datetime.utcfromtimestamp(curSession['endTime'] / 1000).strftime('%H%M')}"

                session_start = datetime.datetime.utcfromtimestamp(curSession['startTime'] / 1000)
                local_start = session_start.astimezone(timezone(local_tz))

                session_info = {
                    'Display Name': displayname,
                    'Session ID': curSession['id'],
                    'Original Date': session_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'Local Date': local_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'Number of Shots': len(shots)
                }

                if calculate_origin_analytics and len(shots) < 150:
                    shot_df = pd.DataFrame(shots).copy()  # Create a copy to avoid modifying the original DataFrame
                    shot_df.loc[:, 'Range'] = np.sqrt(shot_df['originX'] ** 2 + shot_df['originY'] ** 2)
                    shot_df.loc[:, 'Arc'] = calculate_arcs(shot_df['originX'], shot_df['originY'])

                    # Filter shots above the minimum range
                    valid_shots = shot_df[shot_df['Range'] >= min_range_mms]

                    if not valid_shots.empty:
                        filtered_origin_xs = valid_shots['originX'].values
                        filtered_origin_ys = valid_shots['originY'].values
                        filtered_ranges = valid_shots['Range'].values
                        filtered_angles = valid_shots['Arc'].values

                        sector_counts = {
                            'RC': np.sum(filtered_angles < 36),
                            'RW': np.sum((filtered_angles >= 36) & (filtered_angles < 72)),
                            'TK': np.sum((filtered_angles >= 72) & (filtered_angles <= 108)),
                            'LW': np.sum((filtered_angles >= 108) & (filtered_angles < 144)),
                            'LC': np.sum(filtered_angles >= 144),
                        }

                        session_info.update({
                            'Min OriginX': int(filtered_origin_xs.min()),
                            'Max OriginX': int(filtered_origin_xs.max()),
                            'DeltaX': int(filtered_origin_xs.max() - filtered_origin_xs.min()),
                            'Min OriginY': int(filtered_origin_ys.min()),
                            'Max OriginY': int(filtered_origin_ys.max()),
                            'DeltaY': int(filtered_origin_ys.max() - filtered_origin_ys.min()),
                            'Min Range': int(filtered_ranges.min()),
                            'Max Range': int(filtered_ranges.max()),
                            'Delta Range': int(filtered_ranges.max() - filtered_ranges.min()),
                            'Min Angle': int(filtered_angles.min()),
                            'Max Angle': int(filtered_angles.max()),
                            'Delta Angle': int(filtered_angles.max() - filtered_angles.min()),
                            'RC Shots': sector_counts['RC'],
                            'RW Shots': sector_counts['RW'],
                            'TK Shots': sector_counts['TK'],
                            'LW Shots': sector_counts['LW'],
                            'LC Shots': sector_counts['LC']
                        })

                        classifications = classify_sessions(valid_shots)
                        session_info.update(classifications)
                    else:
                        session_info.update({
                            'Min OriginX': None,
                            'Max OriginX': None,
                            'DeltaX': None,
                            'Min OriginY': None,
                            'Max OriginY': None,
                            'DeltaY': None,
                            'Min Range': None,
                            'Max Range': None,
                            'Delta Range': None,
                            'Min Angle': None,
                            'Max Angle': None,
                            'Delta Angle': None,
                            'RC Shots': 0,
                            'RW Shots': 0,
                            'TK Shots': 0,
                            'LW Shots': 0,
                            'LC Shots': 0,
                            'FT': 0,
                            '3pts': 0,
                            '2pts': 0
                        })

                session_data.append(session_info)

                if (i + 1) % print_frequency == 0:
                    print(f"Processed {i + 1} sessions for player {player_first_name} {player_last_name}")
            except TokenExpiredError:
                print("Token expired, reinitializing API client...")
                ## HERE GOT THE DATA FROM API
                print("API client reinitialized successfully.")

    process_sessions_for_player(player_id)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Ensure the directory exists
    output_dir = 'PlayerSessionAnalysis'
    os.makedirs(output_dir, exist_ok=True)

    player_name = f"{player_first_name}{player_last_name}"

    if generate_session_ids_too:
        session_ids_filename = os.path.join(output_dir,
                                            f'SessionIdsToo_{player_name}_{start_date_str}-{end_date_str}.csv')
        session_ids_df = pd.DataFrame(session_data)[['Display Name', 'Session ID']]
        session_ids_df.to_csv(session_ids_filename, index=False, na_rep='')
        print(f'Session IDs data saved to {session_ids_filename}')
    else:
        report_filename = os.path.join(output_dir, f'PlayerReport_{player_name}_{start_date_str}-{end_date_str}.csv')

        # Write session data to CSV
        session_df = pd.DataFrame(session_data)
        session_df.to_csv(report_filename, index=False, na_rep='')

        print(f'Player session data saved to {report_filename}')


# Hardcoded values for player ID, player name, start date, end date, API credentials, print frequency, analytics flag, minimum range in mms, local timezone, and generate session IDs flag
player_id = 'xxx'
player_first_name = 'xxx'
player_last_name = 'xxx'
start_date = datetime.datetime(2024, 8, 10)
end_date = datetime.datetime(2024, 8, 13)
calculate_origin_analytics = True  # Set to False if you do not want to calculate origin analytics
min_range_mms = 3048  # 10 feet in millimeters
local_tz = 'Australia/Brisbane'  # Local timezone of the sessions
generate_session_ids_too = False  # Set to True if you want to generate the session IDs CSV

fetch_and_log_player_sessions(player_id, player_first_name, player_last_name, start_date, end_date, username, password,
                              client_id, client_secret, print_frequency, calculate_origin_analytics, min_range_mms,
                              local_tz, generate_session_ids_too)
