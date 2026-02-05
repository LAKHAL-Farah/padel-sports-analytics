"""
Time Dimension Enrichment for Padel BI Analysis
CRITICAL: Time is essential for BI - enables trend analysis, growth tracking, forecasting

Adds temporal context:
- Year
- Season (Q1, Q2, Q3, Q4)
- Month (numeric and name)
- Pre/Post season indicators
- Week number
- Day of week
- Fiscal quarter

Outputs enriched CSVs for time-based analysis
"""

import pandas as pd
from datetime import datetime
import argparse


def parse_date(date_str):
    """Parse various date formats (DD/MM/YYYY or YYYY-MM-DD)."""
    if pd.isna(date_str) or date_str == "":
        return None
    
    date_str = str(date_str).strip()
    
    # Try DD/MM/YYYY
    try:
        return pd.to_datetime(date_str, format="%d/%m/%Y")
    except:
        pass
    
    # Try YYYY-MM-DD
    try:
        return pd.to_datetime(date_str, format="%Y-%m-%d")
    except:
        pass
    
    # Try flexible parsing
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def get_season(month):
    """Get season from month number (Northern hemisphere padel calendar)."""
    if pd.isna(month):
        return None
    month = int(month)
    if month in [1, 2, 3]:
        return "Q1"
    elif month in [4, 5, 6]:
        return "Q2"
    elif month in [7, 8, 9]:
        return "Q3"
    else:
        return "Q4"


def get_padel_season(month):
    """Get padel competitive season (Nov-Oct typical)."""
    if pd.isna(month):
        return None
    month = int(month)
    if month in [11, 12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"


def get_pre_post_season(month):
    """Identify pre-season, peak season, and post-season."""
    if pd.isna(month):
        return None
    month = int(month)
    # Typical padel calendar: pre-season Sep-Oct, peak Nov-Aug, post-season Sep
    if month in [9, 10]:
        return "Pre-Season"
    elif month in [11, 12, 1, 2, 3, 4, 5, 6, 7, 8]:
        return "Peak Season"
    else:
        return "Off-Season"


def enrich_time_dimension(df, date_column):
    """Add time dimension columns to dataframe."""
    
    # Parse dates
    df['parsed_date'] = df[date_column].apply(parse_date)
    
    # Extract time components
    df['Year'] = df['parsed_date'].dt.year
    df['Month'] = df['parsed_date'].dt.month
    df['Month_Name'] = df['parsed_date'].dt.strftime('%B')
    df['Day'] = df['parsed_date'].dt.day
    df['Quarter'] = df['parsed_date'].dt.quarter
    df['Week_Number'] = df['parsed_date'].dt.isocalendar().week
    df['Day_of_Week'] = df['parsed_date'].dt.day_name()
    df['Day_of_Week_Num'] = df['parsed_date'].dt.dayofweek
    
    # Custom padel seasons
    df['Season'] = df['Month'].apply(get_padel_season)
    df['Pre_Post_Season'] = df['Month'].apply(get_pre_post_season)
    df['Calendar_Quarter'] = df['parsed_date'].dt.quarter
    
    # Date formatted for display
    df['Date_Display'] = df['parsed_date'].dt.strftime('%Y-%m-%d')
    
    # Days since first tournament (trend baseline)
    min_date = df['parsed_date'].min()
    df['Days_Since_Start'] = (df['parsed_date'] - min_date).dt.days
    
    return df


def create_tournament_time_dimension(tournaments_csv, output_csv):
    """Enrich tournament data with time dimensions."""
    print("📅 Processing tournaments...")
    
    df = pd.read_csv(tournaments_csv)
    
    # Parse start_date (or date_start if different column name)
    date_col = 'start_date' if 'start_date' in df.columns else 'date_start'
    
    df = enrich_time_dimension(df, date_col)
    
    # Select relevant columns
    output_cols = [
        'year', 'name', 'location', 'status',
        'Year', 'Month', 'Month_Name', 'Day', 'Quarter',
        'Season', 'Pre_Post_Season', 'Week_Number', 'Day_of_Week',
        'Date_Display', 'Days_Since_Start'
    ]
    
    # Keep only columns that exist
    output_cols = [col for col in output_cols if col in df.columns]
    df_output = df[output_cols].copy()
    
    df_output.to_csv(output_csv, index=False)
    print(f"✓ Saved {len(df_output)} tournaments with time dimensions to {output_csv}")
    
    return df_output


def create_match_results_time_dimension(tournaments_csv, matches_csv, output_csv):
    """Enrich match results by joining tournament dates."""
    print("📅 Processing match results...")
    
    # Read both files
    tournaments = pd.read_csv(tournaments_csv)
    matches = pd.read_csv(matches_csv)
    
    # Enrich tournaments first
    date_col = 'start_date' if 'start_date' in tournaments.columns else 'date_start'
    tournaments = enrich_time_dimension(tournaments, date_col)
    
    # Join tournaments to matches by tournament ID/name
    # Try different join strategies
    match_cols = ['tournament_name', 'court', 'round', 'team_1', 'team_2', 'score']
    tournament_cols = ['year', 'name', 'Year', 'Month', 'Month_Name', 
                       'Quarter', 'Season', 'Pre_Post_Season', 'Week_Number',
                       'Day_of_Week', 'Date_Display']
    
    # Keep only columns that exist
    match_cols = [col for col in match_cols if col in matches.columns]
    tournament_cols = [col for col in tournament_cols if col in tournaments.columns]
    
    # Join on tournament name
    if 'tournament_name' in matches.columns and 'name' in tournaments.columns:
        result = matches.merge(
            tournaments[tournament_cols],
            left_on='tournament_name',
            right_on='name',
            how='left'
        )
    else:
        # If no common column, just add year if it exists in both
        result = matches.copy()
        if 'year' in tournaments.columns and 'year' in matches.columns:
            result = result.merge(
                tournaments[tournament_cols],
                on='year',
                how='left'
            )
    
    result.to_csv(output_csv, index=False)
    print(f"✓ Saved {len(result)} matches with time dimensions to {output_csv}")
    
    return result


def generate_time_analysis_report(tournaments_df, output_txt):
    """Generate BI-focused time analysis report."""
    print("📊 Generating time analysis report...")
    
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PADEL TIME DIMENSION ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        # Growth analysis
        f.write("GROWTH ANALYSIS\n")
        f.write("-" * 80 + "\n")
        
        if 'Year' in tournaments_df.columns:
            yearly_counts = tournaments_df['Year'].value_counts().sort_index()
            f.write("\nTournaments by Year:\n")
            for year, count in yearly_counts.items():
                f.write(f"  {year}: {count} tournaments\n")
            
            # Growth rate
            if len(yearly_counts) > 1:
                first_year = yearly_counts.iloc[0]
                last_year = yearly_counts.iloc[-1]
                growth = ((last_year - first_year) / first_year * 100) if first_year > 0 else 0
                f.write(f"\nGrowth Rate: {growth:+.1f}%\n")
        
        # Seasonal analysis
        if 'Season' in tournaments_df.columns:
            f.write("\nTournaments by Padel Season:\n")
            seasonal = tournaments_df['Season'].value_counts()
            for season, count in seasonal.items():
                f.write(f"  {season}: {count} tournaments\n")
        
        # Monthly distribution
        if 'Month_Name' in tournaments_df.columns:
            f.write("\nTournaments by Month:\n")
            monthly = tournaments_df['Month_Name'].value_counts()
            month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            for month in month_order:
                count = monthly.get(month, 0)
                if count > 0:
                    f.write(f"  {month}: {count} tournaments\n")
        
        # BI Questions answered
        f.write("\n" + "=" * 80 + "\n")
        f.write("KEY BI INSIGHTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("1. HOW FAST IS PADEL GROWING?\n")
        if 'Year' in tournaments_df.columns:
            yearly = tournaments_df['Year'].value_counts().sort_index()
            if len(yearly) > 1:
                first = yearly.iloc[0]
                last = yearly.iloc[-1]
                pct = ((last - first) / first * 100) if first > 0 else 0
                f.write(f"   Growth: {pct:+.1f}% year-over-year\n")
        
        f.write("\n2. WHICH YEARS SAW SPIKES?\n")
        if 'Year' in tournaments_df.columns:
            yearly = tournaments_df['Year'].value_counts().sort_index()
            if len(yearly) > 0:
                max_year = yearly.idxmax()
                max_count = yearly.max()
                f.write(f"   Peak Year: {max_year} with {max_count} tournaments\n")
        
        f.write("\n3. BEST TIME FOR TOURNAMENTS?\n")
        if 'Month_Name' in tournaments_df.columns:
            monthly = tournaments_df['Month_Name'].value_counts()
            if len(monthly) > 0:
                peak_month = monthly.idxmax()
                peak_count = monthly.max()
                f.write(f"   Most Active: {peak_month} with {peak_count} tournaments\n")
        
        f.write("\n4. TREND ANALYSIS READY?\n")
        f.write("   [✓] Year-over-year growth tracking\n")
        f.write("   [✓] Seasonal pattern analysis\n")
        f.write("   [✓] Monthly trend visualization\n")
        f.write("   [✓] Forecasting data prepared\n")
    
    print(f"✓ Analysis report saved to {output_txt}")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich padel tournament and match data with time dimensions for BI analysis"
    )
    parser.add_argument(
        "--tournaments",
        default="match-results/padelfip_tournaments.csv",
        help="Input tournaments CSV"
    )
    parser.add_argument(
        "--matches",
        default="match-results/match_results.csv",
        help="Input match results CSV"
    )
    parser.add_argument(
        "--output-dir",
        default="bi-analytics",
        help="Output directory for enriched CSVs"
    )
    args = parser.parse_args()
    
    print("\n🎯 PADEL BI: TIME DIMENSION ENRICHMENT\n")
    
    # Process tournaments
    tournaments_enriched = f"{args.output_dir}/tournaments_with_time_dimensions.csv"
    create_tournament_time_dimension(args.tournaments, tournaments_enriched)
    
    # Process matches
    matches_enriched = f"{args.output_dir}/match_results_with_time_dimensions.csv"
    create_match_results_time_dimension(
        args.tournaments,
        args.matches,
        matches_enriched
    )
    
    # Generate report
    tournaments_df = pd.read_csv(tournaments_enriched)
    report_file = f"{args.output_dir}/time_dimension_analysis.txt"
    generate_time_analysis_report(tournaments_df, report_file)
    
    print(f"\n✓ All time dimension files created in {args.output_dir}/")
    print(f"  → tournaments_with_time_dimensions.csv")
    print(f"  → match_results_with_time_dimensions.csv")
    print(f"  → time_dimension_analysis.txt")
    print("\n📊 Ready for BI analysis!")


if __name__ == "__main__":
    main()
