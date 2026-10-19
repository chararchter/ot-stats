# %% Load both datasets into the Interactive window's variable explorer.
from main import load_data

phenotypes_df, analytics_df = load_data()
print(f"Loaded {len(phenotypes_df):,} phenotypes and {len(analytics_df):,} page paths.")

# %% Preview phenotypes; use the Variables panel to open the full DataFrame.
phenotypes_df.head()

# %% Preview Analytics; use the Variables panel to open the full DataFrame.
analytics_df.head()
