"""
dashboard.py — Salt City: Where Should We Open Next?

    streamlit run code/dashboard.py

Four tabs, each answering one of the owner's questions. The page only assembles:
every table comes from the saltcity package and every chart from charts.py.
"""
import streamlit as st
from streamlit_folium import st_folium

from pipeline import run
from saltcity import (
    REASONS,
    busy_table,
    close,
    demand_by_zip,
    make_choropleth,
    make_heatmap,
    make_shop_map,
    make_trend,
    make_violin,
    members_by_zip,
    monthly_sales,
    reason_table,
    site_scores,
)

st.set_page_config(page_title="Salt City: Where Should We Open Next?", layout="wide")
st.title("Salt City: Where Should We Open Next?")

data = run()
shops, zips, customers = data["shops"], data["zips"], data["customers"]
orders, visits = data["orders"], data["visits"]
our_shops = shops.loc[shops["kind"] == "ours", "shop"].tolist()

# The heading, the data, the tabs, and the When we're busy and Where we are tabs are
# provided. You write the other two tabs: Why they come (step 4) and Where to open
# next (step 6). The tests (pytest tests/test_pipeline.py -k dashboard) check them.
#
# Only the open tab runs (on_change="rerun"), so a picker on one tab never redraws
# the others' charts. That is why each tab's code sits under `if <tab>.open:`.
busy, why, where, next_shop = st.tabs(
    ["When we're busy", "Why they come", "Where we are", "Where to open next"],
    key="tab", on_change="rerun")

# 3. WHEN WE'RE BUSY  (provided)
if busy.open:
    with busy:
        choice = st.selectbox("Shop", ["All shops"] + our_shops, key="busy_shop")
        shop = None if choice == "All shops" else choice
        fig = make_heatmap(busy_table(orders, shop),
                           f"Orders by day and hour: {choice}")
        st.pyplot(fig)
        close(fig)
        left, right = st.columns(2)
        with left:
            st.plotly_chart(make_trend(monthly_sales(orders)))
        with right:
            fig = make_violin(orders)
            st.pyplot(fig)
            close(fig)

# 4. WHY THEY COME
if why.open:
    with why:
        choice = st.selectbox("Shop", ["All shops"] + our_shops, key="why_shop")
        shop = None if choice == "All shops" else choice
        shown = visits if shop is None else visits[visits["shop"] == shop]

        counts = shown["reason"].value_counts().reindex(REASONS, fill_value=0)
        cols = st.columns(len(REASONS))
        for col, reason in zip(cols, REASONS):
            with col:
                st.metric(label=reason, value=f"{counts[reason]:,}")

        fig = make_heatmap(
            reason_table(visits, shop), f"Visits by reason and hour: {choice}"
        )
        st.pyplot(fig)
        close(fig)

        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                make_trend(monthly_sales(shown, "reason"), "reason", "orders")
            )
        with right:
            fig = make_violin(shown, "reason")
            st.pyplot(fig)
            close(fig)

# 5. WHERE WE ARE  (provided)
if where.open:
    with where:
        st_folium(make_shop_map(shops, orders), height=500, use_container_width=True,
                  returned_objects=[], key="shops")

# 6. WHERE TO OPEN NEXT
if next_shop.open:
    with next_shop:
        members = members_by_zip(customers)
        demand = demand_by_zip(visits)

        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                make_choropleth(
                    zips, members, "members", "Where members live", shops
                )
            )
        with right:
            st.plotly_chart(
                make_choropleth(
                    zips, demand, "visits", "Where members are when they buy", shops
                )
            )

        scores = site_scores(demand, zips, shops)
        st.plotly_chart(
            make_choropleth(
                zips, scores, "score", "Site scores for shop #4", shops
            )
        )

        winner = scores.iloc[0]
        st.success(
            f"Shop #4 should open in ZIP {winner['zip']}: anchors "
            f"{winner['visits']:,} visits, and the nearest Salt City shop is "
            f"{winner['ours_km']} km away."
        )
        st.dataframe(scores.head(10), hide_index=True)
