import os
import time
from typing import Any

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from transformers import pipeline

from utils.custom import css_code



load_dotenv(find_dotenv())
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def progress_bar(amount_of_time: int) -> Any:
    """
    A progress bar that increases over time,
    then disappears when it reached completion
    :param amount_of_time: time taken
    :return: None
    """
    progress_text = "Please wait, the work is in progress! "
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(amount_of_time):
        time.sleep(0.04)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()


def generate_text_from_image(url: str) -> str:
    """
    Uses HuggingFace's BLIP (image-to-text) model to generate descriptive text from an image.
    The input is the file path or URL to an image.
    Returns the generated text describing the image.

    :param url: image location
    :return: text: generated text from the image
    """
    image_to_text: Any = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

    generated_text: str = image_to_text(url)[0]["generated_text"]

    print(f"Image filepath: {url}")
    print(f"BLIP model generated text: {generated_text}")
    return generated_text


def generate_story_from_text(scenario: str) -> str:
    """
    A function using a prompt template and GPT to generate a short story. LangChain is also
    used for chaining purposes
    :param scenario: generated text from the image
    :return: generated story from the text
    """
    prompt_template: str = f"""
    You are a talented story teller who can create a story from a simple narrative./
    Create a story using the following scenario; the story should have be maximum 50 words long;
    
    CONTEXT: {scenario}
    STORY:
    """

    prompt: PromptTemplate = PromptTemplate(template=prompt_template, input_variables=["scenario"])

    llm: Any = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9)

    story_llm: Any = LLMChain(llm=llm, prompt=prompt, verbose=True)

    try:
        generated_story = story_llm.predict(scenario=scenario)
        return generated_story
    except Exception as e:  # Catching all exceptions generally
        print(f"An error occurred (quota exceeded): {str(e)}")
        return "Error generating story(quota exceeded)"



def generate_speech_from_text(message: str) -> Any:
    """
    Uses HuggingFace's ESPnet text-to-speech model to generate audio from a story (message).
    Sends a POST request with the input text to the HuggingFace API and saves the response as a .flac audio file.
    :param message: short story generated by the GPT model
    :return: generated audio from the short story
    """
    API_URL: str = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
    headers: dict[str, str] = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payloads: dict[str, str] = {
        "inputs": message
    }

    response: Any = requests.post(API_URL, headers=headers, json=payloads)
    with open("generated_audio.flac", "wb") as file:
        file.write(response.content)


def main() -> None:
    """
    Main function
    :return: None
    """
    st.set_page_config(page_title= "GenAI Image-To-Speech Tool")

    st.markdown(css_code, unsafe_allow_html=True)

    

    st.header("GenAI Image-To-Speech Tool")
    uploaded_file: Any = st.file_uploader("Please choose an image to upload", type="jpg")

    if uploaded_file is not None:
        
        bytes_data: Any = uploaded_file.getvalue()
        with open(uploaded_file.name, "wb") as file:
            file.write(bytes_data)
        st.image(uploaded_file, caption="Uploaded Image",
                 use_container_width=True)
        progress_bar(100)
        scenario: str = generate_text_from_image(uploaded_file.name)
        story: str = generate_story_from_text(scenario)
        generate_speech_from_text(story)

        with st.expander("Generated Image scenario"):
            st.write(scenario)
        with st.expander("Generated short story"):
            st.write(story)

        st.audio("generated_audio.flac")


if __name__ == "__main__":
    main()