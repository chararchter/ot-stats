from pathlib import Path
import re
from textwrap import fill

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent


def load_data(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load phenotype categories and the exported YTD Analytics report."""
    phenotypes_df = pd.read_csv(data_dir / "phenotype_categories.tsv", sep="\t")

    analytics_path = data_dir / "Pages_and_screens_Page_path_and_screen_class.csv"
    # Skip only the leading export metadata, preserving any # in page URLs.
    metadata_rows = 0
    with analytics_path.open(encoding="utf-8-sig") as report:
        for line in report:
            if not line.startswith("#"):
                break
            metadata_rows += 1

    analytics_df = pd.read_csv(analytics_path, skiprows=metadata_rows)
    analytics_df = analytics_df.drop(columns=["Total revenue"])
    return phenotypes_df, analytics_df


def plot_category_summary(
    category_summary_df: pd.DataFrame,
    group_column: str = "originalCategory",
    title: str = "Traffic by original phenotype category",
    filename: str = "category_summary.png",
    footnote: str = (
        "Active users are summed across URLs, not unique users per category.\n"
        "Totals cover identifiable matching URLs in the exported report; "
        "GA's (other) row is excluded."
    ),
) -> Path:
    """Save three bar-chart panels with a separate count scale per metric."""
    plot_df = category_summary_df.sort_values("Views", ascending=False)
    labels = [fill(str(category), width=25) for category in plot_df[group_column]]
    metrics = ["Views", "Active users", "Event count"]
    colors = ["#2878A0", "#258579", "#8A609A"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 7), sharey=True)
    for ax, metric, color in zip(axes, metrics, colors):
        bars = ax.barh(range(len(plot_df)), plot_df[metric], color=color, height=0.65)
        ax.set_yticks(range(len(plot_df)), labels)
        ax.set_title(metric, fontsize=13, pad=14)
        ax.set_xlabel("Count")
        ax.set_xlim(0, max(float(plot_df[metric].max()) * 1.25, 1))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.bar_label(bars, labels=[f"{value:,.0f}" for value in plot_df[metric]],
                     padding=5, fontsize=10)
        ax.set_axisbelow(True)
        ax.grid(axis="x", alpha=0.18)
        ax.tick_params(axis="y", length=0, labelsize=11)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
    axes[0].invert_yaxis()
    fig.suptitle(title, fontsize=18, y=0.96)
    fig.text(0.02, 0.045, footnote, fontsize=10, color="#555555")
    fig.subplots_adjust(left=0.23, right=0.98, top=0.84, bottom=0.18, wspace=0.25)
    chart_path = DATA_DIR / filename
    fig.savefig(chart_path, dpi=180, facecolor="white")
    plt.close(fig)
    return chart_path


def plot_phenotype_counts(phenotype_category_counts_df: pd.DataFrame) -> Path:
    """Plot the number of distinct phenotype IDs in each original category."""
    plot_df = phenotype_category_counts_df.sort_values("Disease count", ascending=True)
    labels = [fill(str(category), width=30) for category in plot_df["originalCategory"]]
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(labels, plot_df["Disease count"], color="#2878A0", height=0.65)
    ax.bar_label(bars, padding=6, fontsize=11)
    ax.set_title("Phenotype IDs by original category", fontsize=17, pad=18)
    ax.set_xlabel("Number of distinct disease IDs")
    ax.set_xlim(0, max(float(plot_df["Disease count"].max()) * 1.15, 1))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=0.18)
    ax.tick_params(axis="y", length=0, labelsize=11)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    fig.text(0.02, 0.025,
             f"Source: phenotype_categories.tsv | "
             f"Total: {plot_df['Disease count'].sum():,} IDs across "
             f"{len(plot_df)} categories", fontsize=10, color="#555555")
    fig.subplots_adjust(left=0.36, right=0.96, top=0.88, bottom=0.14)
    chart_path = DATA_DIR / "phenotype_category_counts.png"
    fig.savefig(chart_path, dpi=180, facecolor="white")
    plt.close(fig)
    return chart_path


def main():
    phenotypes_df, analytics_df = load_data()

    # Use the same six report rows in all panels, ranked by Views.
    top_analytics_df = analytics_df.nlargest(6, "Views").reset_index(drop=True)
    top_analytics_path = DATA_DIR / "top_5_analytics.csv"
    top_analytics_df.to_csv(top_analytics_path, index=False)
    top_analytics_chart_path = plot_category_summary(
        top_analytics_df,
        group_column=analytics_df.columns[0],
        title="Top 6 Analytics report rows by Views",
        filename="top_5_analytics.png",
        footnote=(
            "The same six report rows are shown in all panels, ranked by Views.\n"
            "(other) is Google's aggregated report bucket, not an individual URL."
        ),
    )

    # Count the entire phenotype list, including IDs absent from Analytics.
    phenotype_category_counts_df = (
        phenotypes_df.groupby("originalCategory", dropna=False)["diseaseId"]
        .nunique()
        .rename("Disease count")
        .reset_index()
        .sort_values("Disease count", ascending=False)
        .reset_index(drop=True)
    )
    phenotype_counts_path = DATA_DIR / "phenotype_category_counts.csv"
    phenotype_category_counts_df.to_csv(phenotype_counts_path, index=False)
    phenotype_chart_path = plot_phenotype_counts(phenotype_category_counts_df)

    # Match the IDs anywhere in the URL, regardless of its path structure.
    disease_ids = phenotypes_df["diseaseId"].dropna().astype(str).str.strip()
    disease_ids = disease_ids[disease_ids.ne("")].unique()
    pattern = "|".join(re.escape(disease_id) for disease_id in disease_ids)
    urls = analytics_df.iloc[:, 0].astype("string")
    matches = urls.str.contains(pattern, na=False) if pattern else pd.Series(
        False, index=analytics_df.index
    )
    filtered_analytics_df = analytics_df.loc[matches].copy()

    # Many URLs may map to the same disease; keep every Analytics row.
    filtered_analytics_df["diseaseId"] = (
        filtered_analytics_df.iloc[:, 0]
        .astype("string")
        .str.extract(f"({pattern})", expand=False)
    )
    phenotype_metadata = phenotypes_df[
        ["diseaseId", "curatedName", "originalCategory"]
    ].copy()
    phenotype_metadata["diseaseId"] = phenotype_metadata["diseaseId"].str.strip()
    filtered_analytics_df = filtered_analytics_df.merge(
        phenotype_metadata,
        on="diseaseId",
        how="left",
        validate="many_to_one",
    )
    filtered_analytics_df = filtered_analytics_df[
        [analytics_df.columns[0], "diseaseId", "curatedName", "originalCategory"]
        + analytics_df.columns[1:].tolist()
    ]

    output_path = DATA_DIR / "filtered_analytics.csv"
    filtered_analytics_df.to_csv(output_path, index=False)

    # Inspect all Alzheimer-related URL rows, including named subtypes,
    # before combining URLs or calculating disease-level totals.
    alzheimer_analytics_df = filtered_analytics_df.loc[
        filtered_analytics_df["curatedName"].str.contains(
            "Alzheimer", case=False, regex=False, na=False
        )
    ].copy()
    alzheimer_path = DATA_DIR / "alzheimer_analytics.csv"
    alzheimer_analytics_df.to_csv(alzheimer_path, index=False)

    # Keep the original phenotype categories separate.
    # Active users are summed per URL, not deduplicated across the category.
    category_summary_df = (
        filtered_analytics_df.groupby("originalCategory", dropna=False)[
            ["Views", "Active users", "Event count"]
        ]
        .sum()
        .reset_index()
    )
    summary_path = DATA_DIR / "category_summary.csv"
    category_summary_df.to_csv(summary_path, index=False)
    chart_path = plot_category_summary(category_summary_df)

    # Split Neurologic using exactly the rows in the existing Alzheimer subset.
    neurologic_analytics_df = filtered_analytics_df.loc[
        filtered_analytics_df["originalCategory"].eq("Neurologic")
    ].copy()
    assert alzheimer_analytics_df.index.isin(neurologic_analytics_df.index).all(), (
        "The Alzheimer subset contains rows outside the Neurologic category."
    )
    is_alzheimer = neurologic_analytics_df.index.isin(alzheimer_analytics_df.index)
    non_alzheimer_analytics_df = neurologic_analytics_df.loc[~is_alzheimer].copy()
    neurologic_analytics_df["diseaseGroup"] = "Non-Alzheimer"
    neurologic_analytics_df.loc[is_alzheimer, "diseaseGroup"] = "Alzheimer"
    metrics = ["Views", "Active users", "Event count"]
    neurologic_summary_df = (
        neurologic_analytics_df.groupby("diseaseGroup")[metrics]
        .sum()
        .reindex(["Alzheimer", "Non-Alzheimer"], fill_value=0)
        .reset_index()
    )

    # Verify a complete, disjoint split and reconcile all three metric totals.
    assert not alzheimer_analytics_df.index.isin(non_alzheimer_analytics_df.index).any()
    assert len(alzheimer_analytics_df) + len(non_alzheimer_analytics_df) == len(
        neurologic_analytics_df
    )
    pd.testing.assert_series_equal(
        neurologic_summary_df[metrics].sum(),
        category_summary_df.set_index("originalCategory").loc["Neurologic", metrics],
        check_names=False,
    )
    neurologic_summary_path = DATA_DIR / "neurologic_summary.csv"
    neurologic_summary_df.to_csv(neurologic_summary_path, index=False)
    neurologic_chart_path = plot_category_summary(
        neurologic_summary_df,
        group_column="diseaseGroup",
        title="Neurologic traffic: Alzheimer vs non-Alzheimer",
        filename="neurologic_summary.png",
    )

    print(f"Phenotype categories: {len(phenotypes_df):,} rows")
    print(phenotypes_df.head().to_string(index=False))
    print("\nPhenotype IDs by original category:")
    print(phenotype_category_counts_df.to_string(index=False))
    print(f"Saved to {phenotype_counts_path}")
    print(f"Bar chart saved to {phenotype_chart_path}")
    print(f"\nAnalytics pages: {len(analytics_df):,} rows")
    print(analytics_df.head().to_string(index=False))
    print(f"Top 6 Analytics rows saved to {top_analytics_path}")
    print(f"Bar chart saved to {top_analytics_chart_path}")
    print(f"\nMatching Analytics pages: {len(filtered_analytics_df):,} rows")
    print(f"Saved to {output_path}")
    print(f"\nAlzheimer-related URL rows: {len(alzheimer_analytics_df):,}")
    print(f"Saved to {alzheimer_path}")
    print("\nTotals by category (Active users are summed across URLs):")
    print(category_summary_df.to_string(index=False))
    print(f"Saved to {summary_path}")
    print(f"Bar chart saved to {chart_path}")
    print("\nNeurologic split (verified against the full category totals):")
    print(neurologic_summary_df.to_string(index=False))
    print(f"Saved to {neurologic_summary_path}")
    print(f"Bar chart saved to {neurologic_chart_path}")


if __name__ == "__main__":
    main()
