import streamlit as st
from time import sleep
import dotenv
import os
import json
from player import Player
from player.types import MoveDirection, TurnDirection

# Load environment variables from .env file
dotenv.load_dotenv()

col1, col2 = st.columns([2, 5])
placeholder = col2.empty()

if "player" not in st.session_state:
    st.session_state["player"] = Player(
        game_controller_model=os.getenv("GAME_CONTROLLER_MODEL")
    )
aPlayer = st.session_state["player"]

col1_controls, col2_controls, col3_controls = col1.columns(3)
if col1_controls.button("TL"):
    aPlayer.turn(TurnDirection.LEFT)
if col2_controls.button("F"):
    aPlayer.move(MoveDirection.FORWARD)
if col3_controls.button("TR"):
    aPlayer.turn(TurnDirection.RIGHT)
if col1_controls.button("L"):
    aPlayer.move(MoveDirection.LEFT)
if col2_controls.button("B"):
    aPlayer.move(MoveDirection.BACKWARD)
if col3_controls.button("R"):
    aPlayer.move(MoveDirection.RIGHT)

with col1.form("action_form"):
    user_prompt = st.text_input("What to do?")
    st.form_submit_button("Submit")

tools_used = st.empty()
if len(user_prompt) > 0:
    tools = aPlayer.action_text(user_prompt)
    with tools_used.container():
        for tool in tools:
            st.write(tool.model_dump_json(indent=2))
    user_prompt = ""


@st.experimental_fragment()
def show_state(container):
    with container.container():
        st.write(f"Step: {aPlayer.state.step} Direction: {aPlayer.state.direction}")
        st.write(f"Coordinates: {aPlayer.state.coordinates}")
        st.write(aPlayer.screen)
        st.write(aPlayer.segmentview)
        st.button("Refresh")
        st.write(aPlayer.state.segments)


show_state(placeholder)
