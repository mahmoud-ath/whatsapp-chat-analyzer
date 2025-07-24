import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import emoji
from collections import Counter
import re
from io import StringIO
from PIL import Image
import string
import altair as alt

# CONFIG
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")
st.title("📱 WhatsApp Group Chat Analyzer")


# SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/733/733585.png", width=100)
    st.markdown("How it work")
    st.markdown("1. On WhatsApp, go to the group chat.")
    st.markdown ("2. Tap `⋮ > More > Export Chat")
    st.markdown ("3. Choose Without Media ")
    st.markdown ("4. You'll get a `.txt` file – use that with this app.")
    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    
    theme = st.radio("Theme", ["Light", "Dark"])
    


# MAIN APP
uploaded_file = st.file_uploader("Upload your exported WhatsApp chat (.txt)", type="txt")
st.markdown(
        """
        <style>
        /* Page background */
        .main {
            background-color: #f9fafb;
            padding: 1rem 2rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Headers */
        h1, h2, h3 {
            color: #333333;
            font-weight: 700;
        }

        /* Metric cards */
        .stMetric {
            background: #ffffff !important;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
            padding: 1rem 1.5rem;
        }

        /* Sidebar */
        .css-1d391kg {
            background-color: #e0e7ff !important;
            padding: 1rem 1.5rem !important;
            border-radius: 12px;
        }

        /* Dataframe styling */
        .stDataFrame table {
            border-collapse: separate !important;
            border-spacing: 0 10px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            font-size: 0.9rem !important;
        }

        .stDataFrame th {
            background-color: #dbeafe !important;
            color: #1e40af !important;
            padding: 0.5rem 1rem !important;
        }

        .stDataFrame td {
            background-color: #f3f4f6 !important;
            padding: 0.5rem 1rem !important;
        }

        /* Buttons */
        button[kind="primary"] {
            background-color: #2563eb !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.2rem !important;
        }

        button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
if uploaded_file:
    st.success("File uploaded! Processing...")

    # Read file
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    lines = stringio.readlines()

    # Parse messages
    pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - (.*?): (.*)'
    messages = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            date, time, sender, message = match.groups()
            full_datetime = f"{date} {time}"
            messages.append({
                "datetime": full_datetime,
                "sender": sender,
                "message": message
            })
    # Convert to DataFrame
    df = pd.DataFrame(messages)
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df.dropna(inplace=True)
    # Ensure datetime is parsed
    df['month_year'] = df['datetime'].dt.to_period('M')


    st.markdown("### 📊 Chat Overview")

    # Sidebar filter
    selected_month = st.sidebar.selectbox(
        "Filter chat by Month",
        options=["All"] + sorted(df['month_year'].dropna().astype(str).unique().tolist())
    )
    # Filter data accordingly
    if selected_month != "All":
        filtered_df = df[df['month_year'].astype(str) == selected_month]
    else:
        filtered_df = df

    # Use filtered_df below instead of df
    total_messages = len(filtered_df)
    top_sender = filtered_df['sender'].value_counts().idxmax()
    top_sender_count = filtered_df['sender'].value_counts().max()

    
    # Display as columns (cards)
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="💬 Total Messages", value=f"{total_messages}")

    with col2:
        st.metric(label="🏆 Top Sender", value=top_sender, delta=f"{top_sender_count} msgs")


    # Organize tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Raw Data", "📊 Users", "📈 Daily Activity", "🔤 Word Cloud", "😂 Emoji Stats"])

    with tab1:
        st.subheader("📋 Raw Messages")
        st.dataframe(filtered_df.head(total_messages))

    with tab2:
        st.subheader("👤 Messages per User")

        sender_counts = filtered_df['sender'].value_counts().reset_index()
        sender_counts.columns = ['sender', 'count']

        chart = alt.Chart(sender_counts).mark_bar().encode(
            y=alt.Y('sender', sort='-x'),  # sort descending by count
            x='count',
            tooltip=['sender', 'count']
        ).properties(
            width=600,
            height=900,
        )

        st.altair_chart(chart, use_container_width=True) 

    with tab3:
        st.subheader("📅 Messages Over Time")
        filtered_df['date'] = filtered_df['datetime'].dt.date
        daily_counts = filtered_df['date'].value_counts().sort_index()
        st.line_chart(daily_counts)

    with tab4:
        st.subheader("🔤 Most Common Words (Word Cloud)")
        all_text = " ".join(filtered_df['message'].dropna().astype(str))
        stopwords = set(["ok", "la", "oui", "non", "je", "tu", "il", "elle", "et", "le", "la", "de", "des", "pour", "sur", "avec", "un", "une", "c", "est", "ce", "pas", "plus", "ou", "en"])
        filtered_words = " ".join([word for word in all_text.split() if word.lower() not in stopwords])
        wordcloud = WordCloud(width=800, height=400, background_color='white' if theme == "Light" else 'black', colormap='viridis').generate(filtered_words)
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

    with tab5:
        st.subheader("😂 Emoji Usage Stats")

        def extract_emojis(s):
            return [c for c in s if c in emoji.EMOJI_DATA]

        emojis = []
        for msg in filtered_df['message']:
            emojis.extend(extract_emojis(str(msg)))

        emoji_counts = Counter(emojis).most_common(10)
        emoji_df = pd.DataFrame(emoji_counts, columns=['emoji', 'count'])

        st.write("Top 10 Most Used Emojis:")
        st.dataframe(emoji_df)
        st.bar_chart(emoji_df.set_index('emoji'))


else:
    st.info("Please upload a .txt WhatsApp chat export file.")

with st.sidebar:
     st.markdown("Made with ❤️ by mahmoud-ath")