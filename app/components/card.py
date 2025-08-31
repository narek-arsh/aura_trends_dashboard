import streamlit as st

def render_card(item):
    with st.container():
        if item.get("image"):
            st.image(item["image"], use_column_width=True)
        st.markdown(f"### [{item['title']}]({item['link']})")
        st.markdown(f"🗓️ {item['published'][:10]}")
        st.markdown(item["summary"])

        with st.expander("💡 Why it matters"):
            item["why_it_matters"] = st.text_area("Relevancia", value=item.get("why_it_matters", ""), key=f"why_{item['id']}")

        with st.expander("🌟 Ideas de activación"):
            item["activation_ideas"] = st.text_area("Ideas", value=item.get("activation_ideas", ""), key=f"ideas_{item['id']}")

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("✨ Usar hoy", key=f"use_{item['id']}"):
                item["score"] = 10
        with cols[1]:
            item["saved"] = st.toggle("Guardar", value=item.get("saved", False), key=f"save_{item['id']}")