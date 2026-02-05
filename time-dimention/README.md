# BI Analytics - Time Dimension

## Overview

Critical time dimension enrichment for padel tournament and match data. **Time is essential for BI** - enables trend analysis, forecasting, and growth tracking.

## Files Generated

### 1. **tournaments_with_time_dimensions.csv**
Enriched tournament data with temporal context.

**Columns Added:**
- `Year`: Tournament year (2025, 2026)
- `Month`: Month number (1-12)
- `Month_Name`: Month name (January, February, etc.)
- `Day`: Day of month
- `Quarter`: Calendar quarter (Q1-Q4)
- `Season`: Padel season (Winter, Spring, Summer, Autumn)
- `Pre_Post_Season`: Season phase (Pre-Season, Peak Season, Off-Season)
- `Week_Number`: ISO week number
- `Day_of_Week`: Day name (Monday, Tuesday, etc.)
- `Date_Display`: Formatted date (YYYY-MM-DD)
- `Days_Since_Start`: Days since first tournament

### 2. **match_results_with_time_dimensions.csv**
Match results enriched with tournament dates and time dimensions.

**Joins:** Match-level data + Tournament dates for trend analysis

### 3. **time_dimension_analysis.txt**
BI-focused analysis answering critical questions.

## Key Insights

### Growth Analysis
- **2025**: 294 tournaments
- **2026**: 398 tournaments
- **Growth Rate**: +35.4% YoY

### Seasonal Patterns
- **Spring**: 225 tournaments (highest)
- **Summer**: 194 tournaments
- **Autumn**: 144 tournaments
- **Winter**: 129 tournaments

### Monthly Activity
- **Peak Month**: April (90 tournaments)
- **Lowest**: December (7 tournaments - holiday effect)

## BI Use Cases

### 1. **Trend Analysis**
```python
import pandas as pd
df = pd.read_csv('tournaments_with_time_dimensions.csv')

# Year-over-year growth
yearly = df.groupby('Year').size()
yoy_growth = yearly.pct_change() * 100
```

### 2. **Forecasting**
- Historical data by month for seasonal forecasting
- Linear trend analysis for growth prediction
- Peak period identification for planning

### 3. **Dashboard Metrics**
- Tournaments by month/season
- Growth trajectory
- Seasonal distribution
- Year-to-date comparisons

### 4. **Anomaly Detection**
- December spike (low - holiday effect)
- April peak (spring tournaments)
- Summer dip (vacation season)

## Next Steps

1. **Create visualizations** using Power BI, Tableau, or Python (matplotlib/seaborn)
2. **Build forecasting models** for tournament growth
3. **Implement dashboard** with monthly KPIs
4. **Track player performance** across seasons
5. **Analyze venue patterns** by tournament season

## Usage Example

```bash
# Regenerate time dimensions if source data changes
python add_time_dimensions.py --tournaments ../match-results/padelfip_tournaments.csv --matches ../match-results/match_results.csv
```

## Critical BI Concepts Implemented

- ✓ **Temporal Grain**: Day, week, month, quarter, year
- ✓ **Fiscal Periods**: Custom padel season definitions
- ✓ **Trend Baseline**: Days since start for continuous metrics
- ✓ **Seasonality**: Pre/post season indicators
- ✓ **Growth Tracking**: YoY comparisons ready

---

**Note**: Time dimension is CRITICAL for BI. Never build analytics without proper temporal context!
