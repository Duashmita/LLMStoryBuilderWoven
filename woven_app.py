import streamlit as st
import openai
from dotenv import load_dotenv
import os

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state setup
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "genre": None,
        "name": None,
        "current_emotion": None,
        "target_emotion": None,
        "summary": [],
        "turn_count": 0,
        "total_turns": 5,
        "user_input": None
    }

st.title("🧶 Woven: into your story")

# Create a container for the input fields
input_container = st.container()

# Let user set parameters
with input_container:
    name = st.text_input("What is your name?")
    genre = st.selectbox("Choose your genre", ["fantasy", "mystery", "dreamlike", "sci-fi", "horror", "romance", "comedy", "adventure"])
    current_emotion = st.text_input("How do you feel right now?")
    target_emotion = st.text_input("What do you want to feel?")
    turns = st.slider("How many minutes do you have?", 2, 10, 5)

# Save to session state
st.session_state.story_state["name"] = name
st.session_state.story_state["current_emotion"] = current_emotion
st.session_state.story_state["target_emotion"] = target_emotion
st.session_state.story_state["genre"] = genre
st.session_state.story_state["total_turns"] = turns
st.session_state.story_state["turn_count"] = 0

def final_print():
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"""The story so far (summary): {', '.join(st.session_state.story_state['summary'])}.
        The main character is {st.session_state.story_state['name']}. The genre is {st.session_state.story_state['genre']}.
        {st.session_state.story_state['name']} is currently feeling {st.session_state.story_state['current_emotion']}, but the story will end with them feeling {st.session_state.story_state['target_emotion']}.
        So far, the story has been: {', '.join(st.session_state.story_state['summary'])}

        Write the last paragraph of the story. Your response should be in this exact format:
        'the paragraph
        ~~~~
        Then write a 20-word summary of the story so far.'"""}])

    # Get the story output
    output = response.choices[0].message.content.split("~~~~")
    story_output = output[0]
    summary = output[2]

    # print the story output
    st.write(story_output)
    st.caption("The End!")

    # Save the turn
    st.session_state.story_state["summary"].append(summary)
    st.session_state.story_state["turn_count"] += 1
    st.stop()
    

def normal_print():
    while st.session_state.story_state["turn_count"] < st.session_state.story_state["total_turns"]-1:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"""The story so far (summary): {', '.join(st.session_state.story_state['summary'])}.
        The main character is {st.session_state.story_state['name']}. The genre is {st.session_state.story_state['genre']}.
        {st.session_state.story_state['name']} is currently feeling {st.session_state.story_state['current_emotion']}, but the story will end with them feeling {st.session_state.story_state['target_emotion']}.
        So far, the story has been: {', '.join(st.session_state.story_state['summary'])}

        Write the next paragraph of the story that ends with a new choice (action, path, or dialogue). Your response should be in this exact format:
        the paragraph
        ~~~~
        Then pose the choice as a question.
        ~~~~
        Then write a 20-word summary of the story so far."""}])

        # Get the story output
        output = response.choices[0].message.content.split("~~~~")
        story_output = output[0]
        question = output[1]
        summary = output[2]

        # print the story output
        st.write(story_output)
        st.caption(question)

        # Save the turn
        st.session_state.story_state["summary"].append(summary)
        st.session_state.story_state["turn_count"] += 1

    final_print()

if st.button("Submit"):
    # Clear the input container
    input_container.empty()

for turn_count in range(st.session_state.story_state["total_turns"]):
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"""The story so far (summary): {', '.join(st.session_state.story_state['summary'])}.
        The main character is {st.session_state.story_state['name']}. The genre is {st.session_state.story_state['genre']}.
        {st.session_state.story_state['name']} are currently feeling {st.session_state.story_state['current_emotion']}, but the story will end with them feeling {st.session_state.story_state['target_emotion']}.
        Write the first paragraph of the story that ends with a new choice (action, path, or dialogue). Your response should be in this exact format:
        the paragraph
        ~~~~
        Then pose the choice as a question.
        ~~~~
        Then write a 20-word summary of the story so far."""}])

    # Get the story output
    output = response.choices[0].message.content.split("~~~~")
    story_output = output[0]
    question = output[1]
    summary = output[2]

    # print the story output
    st.write(story_output)
    st.caption(question)

    # Save the turn
    st.session_state.story_state["summary"].append(summary)
    st.session_state.story_state["turn_count"] += 1

    normal_print()


# st.markdown("---")
# st.subheader("Your Story So Far:")

# for turn in st.session_state.story_state["turns"]:
#     st.markdown(f"**You:** {turn['user_input']}")
#     st.markdown(f"*{turn['story_output']}*")

# if st.session_state.story_state["turn_count"] >= st.session_state.story_state["chosen_turns"]:
#     st.markdown("✨ **The story concludes...**")
#     st.stop()