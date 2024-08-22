# External packages
import streamlit as st
import whisper

# Python In-built packages
import pandas as pd
from io import BytesIO
import time
import tempfile
from pathlib import Path
from audiorecorder import audiorecorder
from streamlit.runtime.uploaded_file_manager import UploadedFile


TEMP_DIR = Path(tempfile.gettempdir())

@st.cache_resource()
def create_whisper_model(
    model_path : str = "model/medium.en.pt",
):
    """
    Create a Whisper model for text transcription.

    Args:
        model_path (str): The path to the Llama model.
        
    Returns:
        Whisper: The created whisper model.
    """
        
    return whisper.load_model(model_path)

@st.cache_data
def generate_summary(transcripts:str):
    """
    Generates a summary of the transcripts

    Parameters:
    - transcripts (str): The transcripts to generate the summary from.

    Returns:
    - str: The generated summary.
    """
    return "Not implemented"

@st.cache_data
def load_file(file):
    # Streamlit file uploader returns a BytesIO object
    # bytes will be saved to a temporary directory

    dest_path = TEMP_DIR / file.name
    # Save file to destination path
    with open(dest_path, "wb") as f:
        f.write(file.getvalue())
    return dest_path

@st.cache_data
def transcribe(dest_path):

    transcription = st.session_state.local_model.transcribe(str(dest_path))

    if isinstance(transcription, dict):
        text = transcription['text']
        transcript_df = pd.DataFrame(transcription['segments'])
    else:
        text = transcription.text
        transcript_df = pd.DataFrame(transcription.segments)
    transcript_df = transcript_df[['start', 'end', 'text']]

    return transcript_df, text

# Setting page layout
st.set_page_config(
    page_title="Captain's Log",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="expanded"
)

if "local_model" not in st.session_state:
    st.session_state.local_model = create_whisper_model()

# Main page heading
st.title("Captain's Log 🖖📜")

# Sidebar
with st.sidebar:
    st.header("Data Upload")

    audio_files = st.sidebar.file_uploader(
        "Select Audio or Video File", 
        accept_multiple_files=True,
        type=["mp4", "avi", "mov", "mkv", "mp3", "wav", "m4a"])  # TODO: Expand this list

    st.header("Record your audio")
    recording = audiorecorder("Click to record", "Click to stop recording")
    if st.button("Clear Recording"):
        recording = None
    if recording is not None and len(recording)> 0:
        # its a pain in the ass to deal with this see if we can clean it later
        file = recording.export(TEMP_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}_Captains_Log.wav", format="wav")
        audio_stream = BytesIO()
        recording.export(audio_stream, format='wav')
        audio_stream.seek(0)
        file.file_id = 'recording'
        file.type = "audio/wav"
        file.data = audio_stream.getvalue()
        file = UploadedFile(record = file, file_urls=TEMP_DIR / f"audio.wav")
        
        # show the recording
        st.header("Your recording")
        recording

        #add to the list
        audio_files.append(file)
    st.header("Made with ❤️ by the Data Science Team")


if len(audio_files)>0:
    transcripts = ""
    for file in audio_files:
        # rename becase I am a hack
        file.name = file.name.split('\\')[-1]
        # file.name = 'test'
        dest_path = load_file(file)

        transcription_df, text = transcribe(str(dest_path))
        transcripts = transcripts + f'{file.name}: \n\n {text}\n\n'
        with st.expander(file.name):
            
            st.video(str(dest_path))

            st.write(transcription_df)

            st.markdown(transcripts)

            st.download_button(
                label="Download Transcript",
                data=transcription_df.to_csv(index=False).encode('utf-8'),
                file_name='transcript_' + file.name.split('.')[0] + '.csv',
                mime="text/csv")


    if st.sidebar.button("Rerun"):
        st.cache_data.clear()

else:
    st.warning("Please upload a file.")


