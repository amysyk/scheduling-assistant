import os


# enable logging
import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# set constants
LLM_PROVIDER = "ANTHROPIC" # GOOGLE, OPENAI, or ANTHROPIC

def llm_client ():
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
    return client

def system_prompt():
    with open('scheduling-assistant.md', 'r') as file:
        # Read the content of the file into a string variable
        relevant_context = file.read()

    # Tell the model today's date in pafic time zone
    from datetime import datetime
    import pytz
    pacific = pytz.timezone("America/Los_Angeles")
    pacific_time = datetime.now(pacific)

    relevant_context = relevant_context + f" Today's date is {pacific_time.date()}. "
    return relevant_context

# Function to interact with LLM
def llm_response(llm_client, system_prompt, user_input):
    try:
        if LLM_PROVIDER == "OPENAI":
            chat_completion = llm_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": system_prompt + user_input,
                    }
                ],
                model="gpt-4o-mini", #gpt-4o-mini
            )
            return chat_completion.choices[0].message.content
        elif LLM_PROVIDER == "ANTHROPIC":
            message = llm_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                system=[
                  {
                    "type": "text",
                    "text": system_prompt,
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
            response = llm_client.models.generate_content(
                model="gemini-2.0-flash", #gemini-1.5-pro
                contents=system_prompt + user_input
            )
            return response.text
    except Exception as e:
        print (e)
        return

# set system system prompt
system_prompt = system_prompt()
llm_client = llm_client()

# if requested, run evaluations
evaluations =  (
    {
        "input": "Today's date",
        "expected_response": "{Today's date}"
    },
    {
        "input": "Marco's activites on March 21, 2025",
        "expected_response": "{None}"
    },
    {
        "input": "Kids's activities on March 20, 2025",
        "expected_response": "Marco has basballe practice at Ross at 5:00. Nina swims at Redwood at 5:30."
    },
)


# Streamlit App
import streamlit as st

# if evals requested, do evals and quit
import sys
if len(sys.argv) > 1 and sys.argv[1].upper()=="EVALS":
    for eval in evaluations:
        logger.info(f'INPUT: {eval["input"]}')
        logger.info(f'EXPECTED RESPONSE: {eval["expected_response"]}')
        logger.info(f'ACTUAL RESPONSE: {llm_response(llm_client, system_prompt, eval["input"])}')
        print()
    sys.exit()

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
    #log the mesage
    logger.info(
        {
            "event": {
                "event_name": "user_input",
                "input": f"{input}"
            }
        }
    )

    # Display user message in chat message container
    st.chat_message("user").markdown(input)
    # Add user message to chat history
    response = llm_response(llm_client, system_prompt + str(st.session_state.messages), input)
    st.session_state.messages.append({"role": "user", "content": input})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
        logger.debug(f"Answer: {response}")

    # Learn from response
    learning = llm_response(llm_client, system_prompt + str(st.session_state.messages), "Succinclty summarize information from the last user message that you didn't already have. If no new information, respond with only 'None'.")
    if learning.rstrip('.').upper() != "NONE":
        logger.info(
            {
                "event": {
                    "event_name": "memory",
                    "learning": f"{learning}"
                }
            }
        )
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
