import os
import streamlit as st

LLM_PROVIDER = "ANTHROPIC"

#Gather relevant relevant relevant context
with open('scheduling-assistant.md', 'r') as file:
    # Read the content of the file into a string variable
    relevant_context = file.read()

# Tell the model today's date
from datetime import datetime
import pytz

# Get current date and time in Pacific Time Zone
pacific = pytz.timezone("America/Los_Angeles")
pacific_time = datetime.now(pacific)

# Extract just the date
today = pacific_time.date()
relevant_context = relevant_context + f" Today's date is {today}. "

if LLM_PROVIDER == "OPENAI":
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
elif LLM_PROVIDER == "ANTHROPIC":
    import anthropic
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
elif LLM_PROVIDER == "GOOGLE":
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Function to interact with LLM
def generate_response(user_input, llm_proivder = LLM_PROVIDER):
    try:
        if LLM_PROVIDER == "OPENAI":
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": relevant_context + user_input,
                    }
                ],
                model="gpt-4o-mini", #gpt-4o-mini
            )
            return chat_completion.choices[0].message.content
        elif LLM_PROVIDER == "ANTHROPIC":
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                system=[
                  {
                    "type": "text",
                    "text": relevant_context,
                    "cache_control": {"type": "ephemeral"}
                  }
                ],
                messages=[
                {"role": "user", "content": user_input}
                ],
            )
            for content_block in message.content:
                if content_block.type == "text":
                    text = content_block.text
            return text
        elif LLM_PROVIDER == "GOOGLE":
            response = client.models.generate_content(
                model="gemini-2.0-flash", #gemini-1.5-pro
                contents=relevant_context + user_input
            )
            return response.text
    except Exception as e:
        print (e)
        return


# Streamlit App
import streamlit as st
st.set_page_config(
    page_title="Don't Ask Dad",
    page_icon="🗓️"  # You can use an emoji or a file path to an image
)
st.title("Don't Ask Dad")
st.write("Ask me questions such as 'When does Nina swim tomorrow?' or 'What \
is kids schedule next week?''")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if input := st.chat_input("Message Don't Ask Dad"):
    # Display user message in chat message container
    st.chat_message("user").markdown(input)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": input})
    print (f"Question: {input}")
    response = generate_response(input)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
        print(f"Answer: {response}")
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
