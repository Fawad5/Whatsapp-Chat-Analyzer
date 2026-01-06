import streamlit as st
import pandas as pd
import re

st.set_page_config(layout='wide')
st.title('WhatsApp Chat Analyzer')

uploaded_file = st.sidebar.file_uploader("Upload your WhatsApp chat file", type=["txt"])

if uploaded_file is not None:
    # Read the content of the uploaded file
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")

    # Use the existing pattern to split messages and find dates
    pattern = "\\d{1,2}/\\d{1,2}/\\d{2,4}, \\d{1,2}:\\d{2}\\u202f[AP]M\\s-\\s"
    messages_list = re.split(pattern, data)[1:]
    dates_list = re.findall(pattern, data)

    # Create a DataFrame
    df_uploaded = pd.DataFrame({'user_messages': messages_list, 'message_date': dates_list})

    # Convert 'message_date' to datetime objects
    df_uploaded['message_date'] = pd.to_datetime(df_uploaded['message_date'], format='%m/%d/%y, %I:%M\u202f%p - ')

    # Separate users and messages
    users = []
    messages = []
    for message_entry in df_uploaded['user_messages']:
        entry = re.split('([w\\W]+?):\\s', message_entry)
        if entry[1:]:
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df_uploaded['user'] = users
    df_uploaded['message'] = messages
    df_uploaded.drop(columns=['user_messages'], inplace=True)

    # Extract date and time components
    df_uploaded['year'] = df_uploaded['message_date'].dt.year
    df_uploaded['month'] = df_uploaded['message_date'].dt.month
    df_uploaded['month_name'] = df_uploaded['message_date'].dt.month_name()
    df_uploaded['day'] = df_uploaded['message_date'].dt.day
    df_uploaded['hour'] = df_uploaded['message_date'].dt.hour
    df_uploaded['minute'] = df_uploaded['message_date'].dt.minute

    st.success("File uploaded and processed successfully!")
    st.dataframe(df_uploaded.head())

    st.subheader('Chat Overview')
    total_messages = df_uploaded.shape[0]
    unique_participants = df_uploaded['user'].nunique() - (1 if 'group_notification' in df_uploaded['user'].unique() else 0)
    start_date = df_uploaded['message_date'].min().strftime('%Y-%m-%d')
    end_date = df_uploaded['message_date'].max().strftime('%Y-%m-%d')

    st.write(f"Total Messages: {total_messages}")
    st.write(f"Date Range: {start_date} to {end_date}")
    st.write(f"Number of Participants: {unique_participants}")

    st.subheader('Messages Over Time')
    messages_per_day = df_uploaded['message_date'].dt.date.value_counts().sort_index()
    st.line_chart(messages_per_day,color='green')

    st.subheader('Top 10 Most Active Users')
    top_10_users = df_uploaded['user'].value_counts().head(10)
    st.bar_chart(top_10_users)
else:
    st.info("Please upload a WhatsApp chat file to get started.")
