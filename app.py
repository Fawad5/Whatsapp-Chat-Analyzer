import streamlit as st
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout='wide')
st.title('WhatsApp Chat Analyzer')

st.sidebar.title("Upload Chat File")
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
    # Remove the trailing ' - ' and use mixed format to handle different space types
    df_uploaded['message_date'] = df_uploaded['message_date'].str.rstrip(' - ')
    df_uploaded['message_date'] = pd.to_datetime(df_uploaded['message_date'], format='mixed')

    # Separate users and messages
    users = []
    messages = []
    for message_entry in df_uploaded['user_messages']:
        # Check for presence of ':' to distinguish user messages from group notifications
        if ': ' in message_entry:
            parts = message_entry.split(': ', 1)
            users.append(parts[0])
            messages.append(parts[1])
        else:
            # Handle group notifications or messages without a clear sender prefix
            users.append('group_notification')
            messages.append(message_entry)


    df_uploaded['user'] = users
    df_uploaded['message'] = messages
    df_uploaded.drop(columns=['user_messages'], inplace=True)

    # NEW LOGIC FOR MEDIA AND LINKS
    # Identify media messages
    df_uploaded['media_messages'] = df_uploaded['message'].apply(lambda x: 1 if '<Media omitted>' in x else 0)

     # Extract URLs with a more comprehensive pattern
    url_pattern = r'\b(?:https?://|www\.)[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?|\b[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?'
    df_uploaded['urls'] = df_uploaded['message'].apply(lambda x: re.findall(url_pattern, x))

    # Count number of URLs
    df_uploaded['num_urls'] = df_uploaded['urls'].apply(len)
    # END NEW LOGIC

    # Extract date and time components
    df_uploaded['year'] = df_uploaded['message_date'].dt.year
    df_uploaded['month'] = df_uploaded['message_date'].dt.month
    df_uploaded['month_name'] = df_uploaded['message_date'].dt.month_name()
    df_uploaded['day'] = df_uploaded['message_date'].dt.day
    df_uploaded['hour'] = df_uploaded['message_date'].dt.hour
    df_uploaded['minute'] = df_uploaded['message_date'].dt.minute
    df_uploaded['day_name'] = df_uploaded['message_date'].dt.day_name() # New: Extract day name

    # NEW LOGIC FOR HEATMAP DATA
    # Aggregate message counts by hour of the day and day of the week
    heatmap_data = df_uploaded.groupby(['day_name', 'hour']).size().reset_index(name='message_count')

    # Pivot the data for heatmap visualization
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data_pivot = heatmap_data.pivot_table(index='day_name', columns='hour', values='message_count').fillna(0)
    heatmap_data_pivot = heatmap_data_pivot.reindex(day_order, fill_value=0)
    # END NEW LOGIC

    st.success("File uploaded and processed successfully!")
    # st.dataframe(df_uploaded.head())

    selected_analysis = st.sidebar.radio(
        "Select Analysis Type",
        ('Overall Statistics', 'Individual Statistics')
    )

    if selected_analysis == 'Overall Statistics':
        st.subheader('Chat Overview')
        total_messages = df_uploaded.shape[0]
        unique_participants = df_uploaded['user'].nunique() - (1 if 'group_notification' in df_uploaded['user'].unique() else 0)
        start_date = df_uploaded['message_date'].min().strftime('%Y-%m-%d')
        end_date = df_uploaded['message_date'].max().strftime('%Y-%m-%d')

        st.write(f"Total Messages: {total_messages}")
        st.write(f"Date Range: {start_date} to {end_date}")
        st.write(f"Number of Participants: {unique_participants}")

        # Display overall media and link statistics
        total_media_messages = df_uploaded['media_messages'].sum()
        total_links_sent = df_uploaded['num_urls'].sum()
        st.write(f"Total Media Messages: {total_media_messages}")
        st.write(f"Total Links Sent: {total_links_sent}")


        st.subheader('Messages Over Time')
        messages_per_day = df_uploaded['message_date'].dt.date.value_counts().sort_index()
        st.line_chart(messages_per_day, color='#4CAF50') # Green color

        st.subheader('Top 10 Most Active Users')
        top_10_users = df_uploaded['user'].value_counts().head(10)
        st.bar_chart(top_10_users, color='#2196F3') # Blue color

        st.subheader('Most Busy Days')
        busy_days = df_uploaded['message_date'].dt.day_name().value_counts()
        st.bar_chart(busy_days, color='#FFC107') # Amber color

        st.subheader('Most Busy Months')
        busy_months = df_uploaded['message_date'].dt.month_name().value_counts()
        st.bar_chart(busy_months, color='#9C27B0') # Purple color

        # Activity Heatmap
        st.subheader('Activity Heatmap (Overall Chat)')
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(heatmap_data_pivot, cmap='YlGnBu', annot=True, fmt='g', ax=ax, linewidths=.5)
        ax.set_title('Message Activity by Day of Week and Hour of Day')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Day of Week')
        st.pyplot(fig)

    elif selected_analysis == 'Individual Statistics':
        # Create a list of unique users, excluding 'group_notification'
        participant_list = df_uploaded[df_uploaded['user'] != 'group_notification']['user'].unique().tolist()
        # Add a default selection option
        participant_list.insert(0, 'Select a User')

        selected_user = st.sidebar.selectbox(
            "Select a User",
            participant_list
        )

        if selected_user != 'Select a User':
            st.subheader(f'Statistics for {selected_user}')
            user_df = df_uploaded[df_uploaded['user'] == selected_user]

            # Display total messages for the selected user
            st.write(f"Total Messages: {user_df.shape[0]}")

            # Display individual media and link statistics
            individual_media_messages = user_df['media_messages'].sum()
            individual_links_sent = user_df['num_urls'].sum()
            st.write(f"Media Messages Sent: {individual_media_messages}")
            st.write(f"Links Sent: {individual_links_sent}")

            # Display messages over time for the selected user
            st.subheader(f'Messages Over Time for {selected_user}')
            messages_per_day_user = user_df['message_date'].dt.date.value_counts().sort_index()
            st.line_chart(messages_per_day_user, color='#F44336') # Red color

            st.subheader(f'Most Busy Days for {selected_user}')
            busy_days_user = user_df['message_date'].dt.day_name().value_counts()
            st.bar_chart(busy_days_user, color='#E91E63') # Pink color

            st.subheader(f'Most Busy Months for {selected_user}')
            busy_months_user = user_df['message_date'].dt.month_name().value_counts()
            st.bar_chart(busy_months_user, color='#00BCD4') # Cyan color

            # Activity Heatmap for Individual User
            st.subheader(f'Activity Heatmap for {selected_user}')
            individual_heatmap_data = user_df.groupby(['day_name', 'hour']).size().reset_index(name='message_count')
            individual_heatmap_data_pivot = individual_heatmap_data.pivot_table(index='day_name', columns='hour', values='message_count').fillna(0)
            individual_heatmap_data_pivot = individual_heatmap_data_pivot.reindex(day_order, fill_value=0)

            fig_individual, ax_individual = plt.subplots(figsize=(12, 6))
            sns.heatmap(individual_heatmap_data_pivot, cmap='YlGnBu', annot=True, fmt='g', ax=ax_individual, linewidths=.5)
            ax_individual.set_title(f'Message Activity by Day of Week and Hour of Day for {selected_user}')
            ax_individual.set_xlabel('Hour of Day')
            ax_individual.set_ylabel('Day of Week')
            st.pyplot(fig_individual)

else:
    st.info("Please upload a WhatsApp chat file to get started.")
