from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from nyfs import config
from nyfs.data import GRADE_COLORS, GRADE_ORDER, RISK_COLORS, DashboardData, load_dashboard_data


MAP_POINT_LIMIT = 5000
DEFAULT_GRADE_SELECTION = ["A", "B", "C", "Pending / Not Yet Graded", "Missing / Unknown"]
DEFAULT_RISK_SELECTION = ["Low", "Medium", "High"]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 3rem;}
        .hero {
            padding: 1.2rem 1.3rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #f7fbf7 0%, #eef5ff 100%);
            border: 1px solid #d7e4ea;
            margin-bottom: 1rem;
        }
        .info-card {
            padding: 1rem 1.1rem;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .section-note {
            color: #475569;
            font-size: 0.96rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Loading local NYFS data...")
def _get_dashboard_data() -> DashboardData:
    return load_dashboard_data()


def _format_timestamp(raw_value: str | None) -> str:
    if not raw_value:
        return "Unknown"
    try:
        return pd.to_datetime(raw_value).strftime("%B %d, %Y")
    except Exception:
        return "Unknown"


def _reset_filters() -> None:
    keys = [
        "borough_filter",
        "cuisine_filter",
        "grade_filter",
        "risk_filter",
        "critical_filter",
        "date_filter",
        "restaurant_query",
        "halal_filter",
        "map_color_mode",
    ]
    for key in keys:
        st.session_state.pop(key, None)


def _render_sidebar(latest_df: pd.DataFrame, metadata: dict[str, str]) -> pd.DataFrame:
    st.sidebar.title("Filter Restaurants")
    st.sidebar.caption("Use these controls to narrow the current map and charts.")
    if st.sidebar.button("Reset filters", use_container_width=True):
        _reset_filters()
        st.rerun()

    boroughs = sorted(latest_df["borough"].dropna().unique().tolist())
    cuisines = sorted(latest_df["cuisine_type"].dropna().unique().tolist())

    selected_boroughs = st.sidebar.multiselect(
        "Borough",
        boroughs,
        default=boroughs,
        key="borough_filter",
    )
    selected_cuisines = st.sidebar.multiselect(
        "Cuisine type",
        cuisines,
        default=cuisines,
        key="cuisine_filter",
    )
    selected_grades = st.sidebar.multiselect(
        "Inspection grade",
        DEFAULT_GRADE_SELECTION,
        default=DEFAULT_GRADE_SELECTION,
        key="grade_filter",
    )
    selected_risks = st.sidebar.multiselect(
        "Risk level",
        DEFAULT_RISK_SELECTION,
        default=DEFAULT_RISK_SELECTION,
        key="risk_filter",
    )
    critical_filter = st.sidebar.selectbox(
        "Critical violations",
        ["All restaurants", "Has critical violations", "No critical violations"],
        key="critical_filter",
    )

    min_date = latest_df["inspection_date"].min()
    max_date = latest_df["inspection_date"].max()
    selected_dates = st.sidebar.date_input(
        "Latest inspection date",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
        key="date_filter",
    )
    search_text = st.sidebar.text_input(
        "Restaurant name",
        key="restaurant_query",
        placeholder="Search for a restaurant",
    ).strip()

    halal_disabled_label = "Not supported in source data"
    st.sidebar.selectbox(
        "Halal filter",
        [halal_disabled_label],
        key="halal_filter",
        help=metadata.get(
            "halal_note",
            "Halal filtering is not available because the inspection dataset does not include a reliable halal field.",
        ),
    )

    filtered = latest_df[
        latest_df["borough"].isin(selected_boroughs)
        & latest_df["cuisine_type"].isin(selected_cuisines)
        & latest_df["inspection_grade"].isin(selected_grades)
        & latest_df["risk_level"].isin(selected_risks)
    ].copy()

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered = filtered[
            filtered["inspection_date"].dt.date.between(start_date, end_date)
        ]

    if critical_filter == "Has critical violations":
        filtered = filtered[filtered["has_critical_violations"]]
    elif critical_filter == "No critical violations":
        filtered = filtered[~filtered["has_critical_violations"]]

    if search_text:
        filtered = filtered[
            filtered["restaurant_name"].str.contains(search_text, case=False, na=False)
        ]

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Risk level is a NYFS informational metric based on inspection score, critical violations, grade, recency, and repeated poor performance. It is not an official NYC label."
    )
    return filtered


def _render_header(metadata: dict[str, str]) -> None:
    st.title(config.APP_TITLE)
    st.markdown(
        """
        <div class="hero">
            <h4 style="margin:0 0 .4rem 0;">A public guide to NYC restaurant inspection patterns</h4>
            <p style="margin:0;" class="section-note">
                NYFS helps residents, students, and visitors quickly interpret the latest available inspection results,
                compare borough and cuisine patterns, and understand where caution may be warranted.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    source_name = metadata.get("source", "local dataset")
    refreshed_on = _format_timestamp(metadata.get("refreshed_at_utc") or metadata.get("last_updated"))
    st.caption(
        f"Source: NYC Open Data restaurant inspections. Dashboard cache source: {source_name}. Last refresh: {refreshed_on}."
    )


def _render_kpis(filtered_df: pd.DataFrame) -> None:
    total_restaurants = int(filtered_df["restaurant_id"].nunique())
    avg_score = filtered_df["inspection_score"].mean()
    high_risk = int(filtered_df["risk_level"].eq("High").sum())
    grade_a_pct = filtered_df["inspection_grade"].eq("A").mean() * 100
    critical_count = int(filtered_df["has_critical_violations"].sum())

    columns = st.columns(5)
    columns[0].metric("Restaurants in view", f"{total_restaurants:,}")
    columns[1].metric("Average inspection score", f"{avg_score:.1f}")
    columns[2].metric("High-risk restaurants", f"{high_risk:,}")
    columns[3].metric("Grade A share", f"{grade_a_pct:.1f}%")
    columns[4].metric("With critical violations", f"{critical_count:,}")


def _render_map(filtered_df: pd.DataFrame) -> None:
    st.subheader("Map of latest restaurant inspections")
    st.caption(
        "Each dot shows the latest available inspection for one restaurant. Color can reflect official grade or NYFS risk level."
    )
    map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()
    if map_df.empty:
        st.info("No restaurants in the current view have usable coordinates.")
        return

    if len(map_df) > MAP_POINT_LIMIT:
        map_df = map_df.nlargest(MAP_POINT_LIMIT, "risk_score")

    color_mode = st.radio(
        "Map color",
        ["Risk level", "Inspection grade"],
        horizontal=True,
        key="map_color_mode",
    )
    color_column = "risk_level" if color_mode == "Risk level" else "inspection_grade"
    color_map = RISK_COLORS if color_column == "risk_level" else GRADE_COLORS
    size_column = "critical_violations"
    map_df["map_marker_size"] = map_df[size_column].clip(lower=1)

    fig = px.scatter_map(
        map_df,
        lat="latitude",
        lon="longitude",
        color=color_column,
        color_discrete_map=color_map,
        hover_name="restaurant_name",
        hover_data={
            "borough": True,
            "cuisine_type": True,
            "inspection_grade": True,
            "inspection_score": ":.0f",
            "risk_level": True,
            "critical_violation_label": True,
            "inspection_date": "|%Y-%m-%d",
            "full_address": True,
            "latitude": False,
            "longitude": False,
        },
        size="map_marker_size",
        size_max=16,
        zoom=9.8,
        center={"lat": 40.7128, "lon": -74.0060},
        height=620,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text=color_mode)
    st.plotly_chart(fig, use_container_width=True)


def _render_charts(filtered_df: pd.DataFrame, inspections_df: pd.DataFrame) -> None:
    st.subheader("What stands out in the current view")
    chart_col_1, chart_col_2 = st.columns(2)

    borough_chart = (
        filtered_df.groupby("borough", as_index=False)["inspection_score"]
        .mean()
        .rename(columns={"inspection_score": "avg_inspection_score"})
        .sort_values("avg_inspection_score", ascending=False)
    )
    fig_borough = px.bar(
        borough_chart,
        x="borough",
        y="avg_inspection_score",
        color="avg_inspection_score",
        color_continuous_scale=["#FDE68A", "#F59E0B", "#B91C1C"],
        title="Average inspection score by borough",
        labels={"avg_inspection_score": "Average score", "borough": ""},
    )
    chart_col_1.plotly_chart(fig_borough, use_container_width=True)

    grade_chart = (
        filtered_df["inspection_grade"]
        .value_counts()
        .reindex(GRADE_ORDER, fill_value=0)
        .rename_axis("inspection_grade")
        .reset_index(name="restaurant_count")
    )
    fig_grade = px.bar(
        grade_chart,
        x="inspection_grade",
        y="restaurant_count",
        color="inspection_grade",
        color_discrete_map=GRADE_COLORS,
        title="Grade distribution",
        labels={"inspection_grade": "", "restaurant_count": "Restaurants"},
    )
    chart_col_2.plotly_chart(fig_grade, use_container_width=True)

    chart_col_3, chart_col_4 = st.columns(2)
    cuisine_chart = (
        filtered_df.groupby("cuisine_type", as_index=False)["critical_violations"]
        .sum()
        .sort_values("critical_violations", ascending=False)
        .head(12)
    )
    fig_cuisine = px.bar(
        cuisine_chart,
        x="critical_violations",
        y="cuisine_type",
        orientation="h",
        color="critical_violations",
        color_continuous_scale=["#FDE2E2", "#EF4444", "#991B1B"],
        title="Cuisines with the most critical violations",
        labels={"critical_violations": "Critical violations", "cuisine_type": ""},
    )
    fig_cuisine.update_layout(yaxis={"categoryorder": "total ascending"})
    chart_col_3.plotly_chart(fig_cuisine, use_container_width=True)

    trend_df = inspections_df[
        inspections_df["restaurant_id"].isin(filtered_df["restaurant_id"])
    ].copy()
    trend_chart = (
        trend_df.dropna(subset=["inspection_date"])
        .assign(month=lambda frame: frame["inspection_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["inspection_score"]
        .mean()
        .rename(columns={"inspection_score": "average_score"})
        .sort_values("month")
    )
    fig_trend = px.line(
        trend_chart,
        x="month",
        y="average_score",
        markers=True,
        title="Average inspection score over time",
        labels={"month": "", "average_score": "Average score"},
    )
    chart_col_4.plotly_chart(fig_trend, use_container_width=True)


def _render_top_risk_table(filtered_df: pd.DataFrame) -> None:
    st.subheader("Restaurants that merit a closer look")
    risk_table = filtered_df[
        [
            "restaurant_name",
            "borough",
            "cuisine_type",
            "inspection_grade",
            "inspection_score",
            "risk_level",
            "critical_violations",
            "inspection_date",
        ]
    ].sort_values(["risk_score", "inspection_score"], ascending=[False, False]).head(15)
    st.dataframe(
        risk_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "restaurant_name": "Restaurant",
            "borough": "Borough",
            "cuisine_type": "Cuisine",
            "inspection_grade": "Grade",
            "inspection_score": st.column_config.NumberColumn("Score", format="%d"),
            "risk_level": "Risk",
            "critical_violations": st.column_config.NumberColumn("Critical", format="%d"),
            "inspection_date": st.column_config.DateColumn("Latest inspection"),
        },
    )


def _render_search_detail(filtered_df: pd.DataFrame, inspections_df: pd.DataFrame) -> None:
    st.subheader("Restaurant lookup")
    if filtered_df.empty:
        st.info("Adjust filters to search for a restaurant.")
        return

    search_options = (
        filtered_df["restaurant_name"]
        + " | "
        + filtered_df["borough"]
        + " | "
        + filtered_df["cuisine_type"]
    )
    selected_label = st.selectbox(
        "Choose a restaurant to view its latest inspection details",
        search_options.tolist(),
    )
    selected_restaurant = filtered_df.iloc[search_options.tolist().index(selected_label)]
    restaurant_history = inspections_df[
        inspections_df["restaurant_id"].eq(selected_restaurant["restaurant_id"])
    ].sort_values("inspection_date", ascending=False)

    left, right = st.columns([1, 1])
    left.markdown(
        f"""
        <div class="info-card">
            <h4 style="margin-top:0;">{selected_restaurant['restaurant_name']}</h4>
            <p><strong>Latest grade:</strong> {selected_restaurant['inspection_grade']}</p>
            <p><strong>Latest score:</strong> {selected_restaurant['inspection_score']:.0f}</p>
            <p><strong>Latest inspection:</strong> {selected_restaurant['inspection_date'].strftime('%Y-%m-%d') if pd.notna(selected_restaurant['inspection_date']) else 'Unknown'}</p>
            <p><strong>Address:</strong> {selected_restaurant['full_address']}</p>
            <p><strong>Risk level:</strong> {selected_restaurant['risk_level']}</p>
            <p>{selected_restaurant['risk_summary']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    right.markdown(
        f"""
        <div class="info-card">
            <h4 style="margin-top:0;">Latest inspection details</h4>
            <p><strong>Critical violations:</strong> {int(selected_restaurant['critical_violations'])}</p>
            <p><strong>Total violations:</strong> {int(selected_restaurant['total_violations'])}</p>
            <p><strong>Inspection type:</strong> {selected_restaurant['inspection_type'] or 'Unknown'}</p>
            <p><strong>Action:</strong> {selected_restaurant['action'] or 'Unknown'}</p>
            <p><strong>Recent violation details:</strong></p>
            <p class="section-note">{selected_restaurant['violations'] or 'No violation text was recorded for this latest inspection.'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history_chart = restaurant_history[["inspection_date", "inspection_score", "inspection_grade"]].copy()
    fig_history = px.line(
        history_chart.sort_values("inspection_date"),
        x="inspection_date",
        y="inspection_score",
        markers=True,
        title="Inspection history for this restaurant",
        labels={"inspection_date": "", "inspection_score": "Inspection score"},
    )
    st.plotly_chart(fig_history, use_container_width=True)


def _render_education(metadata: dict[str, str]) -> None:
    st.subheader("How to read this dashboard")
    education_left, education_right = st.columns(2)

    education_left.markdown(
        """
        **What inspection grades mean**

        - `A`: the strongest posted result among standard grades.
        - `B`: more issues were found than an A-grade inspection.
        - `C`: more serious concerns were found than A or B.
        - `Pending / Not Yet Graded`: a current posted grade is not available yet.
        - `Missing / Unknown`: the source data does not show enough grade information.

        **What is a critical violation?**

        Critical violations are issues the inspection system flags as more directly related to food safety risk, such as conditions that may increase the chance of contamination or illness.
        """
    )

    education_right.markdown(
        """
        **What NYFS risk level means**

        NYFS risk level is an internal indicator based on the latest inspection score, critical violations, official grade, how old the inspection is, and whether a restaurant has had repeated poor results recently.

        It is meant to help the public compare inspection patterns quickly. It is **not** an official NYC rating or legal designation.

        **Dashboard limitations**

        - Inspections are not real-time.
        - A restaurant can improve or worsen between inspections.
        - Missing coordinates or grade details can affect what appears on the map.
        - Halal filtering is not currently supported because the source data does not include a trustworthy halal field.
        """
    )

    if metadata.get("halal_note"):
        st.caption(metadata["halal_note"])


def _render_empty_state() -> None:
    st.warning("No restaurants match the current filters. Try broadening the selections in the sidebar.")


def build_dashboard() -> None:
    st.set_page_config(page_title=config.APP_TITLE, layout="wide")
    _inject_styles()

    dashboard_data = _get_dashboard_data()
    latest_df = dashboard_data.latest.copy()
    inspections_df = dashboard_data.inspections.copy()
    metadata = dashboard_data.metadata or {}

    _render_header(metadata)
    filtered_df = _render_sidebar(latest_df, metadata)
    if filtered_df.empty:
        _render_empty_state()
        _render_education(metadata)
        return

    _render_kpis(filtered_df)
    st.markdown("---")
    _render_map(filtered_df)
    st.markdown("---")
    _render_charts(filtered_df, inspections_df)
    st.markdown("---")
    _render_top_risk_table(filtered_df)
    st.markdown("---")
    _render_search_detail(filtered_df, inspections_df)
    st.markdown("---")
    _render_education(metadata)
