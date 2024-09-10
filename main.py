import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
import chromadb
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI



OPENAI_API_KEY = 'API_KEY_HERE'
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# transcribe_audio(file_path, lang):
# - takes user audio file and trascribes + translates into lang and outputs the response in lang
#     inputs:
#         file_path: user recorded audio file (query)
#         lang: language the user wants output in
#     output:
#         transcribes and translate file_path -> output in chat
#         sends user query to ask_gpt, translates response -> output in chat
#         audio dictatation response to user -> output under chat

def transcribe_audio(file_path, lang):

    client = OpenAI()                                                                           # Client to transcribe audio

    audio_file = open(file_path, "rb")                                                          # Audio file to transcribe
    transcript = client.audio.translations.create(                                              # Transcribed to ENGLISH
        model="whisper-1",                                                                      # transcript.text for transcription
        file=audio_file
    )

    modelt = ChatOpenAI()                                                                       # modelt to translate
    st.text(transcript.text)
    t_prompt = modelt.invoke("Translate the following word for word into" + lang + ": " + transcript.text)
    st.text(t_prompt.content)                                                                   # translate ENGLISH to LANG
    'Does the text above match? If not, re-record'

    if st.button("Send"):
        st.chat_message("user").markdown(t_prompt.content)
        st.session_state.messages.append({"role": "user", "content": t_prompt.content})         # UI for chat

        response = ask_gpt(transcript.text)                                                     # query GPT using ENGLISH transcription
        modelt = ChatOpenAI()
        response_text = modelt.invoke("Translate the following word for word into " + lang + ": " + response)   # translate ENGLISH to LANG

        st.chat_message("assistant").markdown(response_text.content)
        st.session_state.messages.append({"role": "assistant", "content": response_text.content})   #UI for chat

        with client.audio.speech.with_streaming_response.create(                                # create audio for LANG response
            model="tts-1",
            voice="nova",
            input=response_text.content,
        ) as text_to_speech:
            text_to_speech.stream_to_file("output.mp3")

        st.audio("output.mp3", format="audio/mpeg")                                             # UI for audio output 

# record_audio(lang):
# - Records an audio file given by user and saves locally
#     input:
#         lang: user chosen languauge for translation to send to transcribe_audio()
#     output: 
#         create audio file by recording user -> sent to transcribe_audio()
#         nothing is recorded -> NONE returned

def record_audio(lang):
    audio_bytes = audio_recorder(                                                               # Basic settings for recorder
        text = "Click to speak",
        recording_color = "#e8b62c",
        neutral_color = "#6aa36f",
        icon_name = "user",                                                                     # Icon to click for recording
        icon_size = "6x",
        pause_threshold = 3.0
    )

    if audio_bytes:                                                                             # If anything is recorded
        st.audio(audio_bytes, format="audio/wav")                                               # Displays audio to user
        audio_file = 'prompt.wav'                                                               # Saves file in dir

        with open(audio_file, 'wb') as f:
            f.write(audio_bytes)

        transcribe_audio(audio_file, lang)                                                      # send audio file and lang to func
    
    return None

# chunk_per_doc(dir):
# - Creates chunk out of the data at a given directory location
#     inputs:
#         dir: directory of content file
#     output: 
#         N/A - sends chunk to upload_to_chroma

def chunk_per_doc(dir):
    with open('./data/'+dir, 'r') as file:                                                      # Read file @ given dir
        text = file.read()

    rec_text_splitter = RecursiveCharacterTextSplitter(                                         # Creates chunks with settings
        chunk_size = 500,
        chunk_overlap = 0,
        length_function = len,
    )

    chunks = rec_text_splitter.split_text(text)
    docs = rec_text_splitter.create_documents(chunks)                                           # Make chunks into docs to feed DB
    upload_to_chroma(docs)

# upload_to_chroma(docs):
# inputs docs created by chunk_per_doc() to chromaDB for later use
#     inputs:
#         docs: has chunks contents
#     output: 
#         N/A

def upload_to_chroma(docs):
    embeddings = OpenAIEmbeddings()
    new_client = chromadb.EphemeralClient()
    global db
    db = Chroma.from_documents(
        docs, embeddings, client=new_client, collection_name="openai_collection"
    )

# init_session()
# function to set up data. Called once on initiation
# input:
#     N/A
# output:
#     N/A - send all files in ./data to chunk_per_doc()

def init_session():
    path = "./data"
    dir_list = os.listdir(path)                                                                 # Send each file in ./data to chunk_per_doc
    for dir in dir_list:
        chunk_per_doc(dir)

# ask_gpt(query):
# Handles entire response generation process. 3 types of outputs:
#     1. Based on data (from ./data)
#     2. Based on DB (wants to know user specific details)
#     3. Clarifying questions' response or invalid query

#     inputs:
#         query: users' question
#     output:
#         chat message based on above characteristics

def ask_gpt(query):
    results = db.similarity_search_with_relevance_scores(query, k=5)
    if len(results) != 0 and results[0][1] > 0.7:                                               # Vector DB found a match for query in chroma
        template = """                                                                          
        You are a playful and friendly A23 AI assistant using Retrieval-Augmented Generation (RAG) techniques to provide 
        accurate and helpful information. 
        Based on the following context, please answer the user's query strictly with the information provided in the 
        context without adding any unsupported information: 

            Context: {context} 
            Query: {query} 

        Answer (be playful but accurate)
        """

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])      
        
        prompt_template = ChatPromptTemplate.from_template(template)
        prompt = prompt_template.format(context=context_text, query=query)                      # Create template to ask GPT

        model = ChatOpenAI()
        response_text = model.invoke(prompt)
        return response_text.content
    else:                                                                                       # No match based on vector DB
        model = ChatOpenAI()
        template = """
        Input: {query}

        Task: Determine if the user query relates to either database information or app actions. 
        If it relates to database information, output one or more of the following keywords based on the query content: 
            "username", 
            "balance". 
        If it relates to app actions, output the specific action keyword: 
            "START_GAME", 
            "WITHDRAW_MONEY", 
            "DEPOSIT_MONEY". 

        Output format (output ONLY THE KEYWORD and nothing else):
        - For database information, output: "username", "balance".
        - For app actions, output: "START_GAME", "WITHDRAW_MONEY", or "DEPOSIT_MONEY".
        """

        prompt_template = ChatPromptTemplate.from_template(template)                            # Checks if they are asking for personal information
        prompt = prompt_template.format(query=query)
        response_text = model.invoke(prompt)

        if('username' in response_text.content):
            return "Add DB query for username" #ADD_DB_QUERY_HERE                               # Returns username
        elif('balance'in response_text.content):
            return "Add DB query for Balance" #ADD_DB_QUERY_HERE                                # Returns account balance
        elif('START_GAME'in response_text.content):
            return "Add function for START_GAME" #ADD_FUNC_CALL_HERE                            # Function to initialize game
        elif('WITHDRAW_MONEY'in response_text.content):
            return "Add function for WITHDRAW" #ADD_FUNC_CALL_HERE                              # Function to withdraw money
        elif('DEPOSIT_MONEY'in response_text.content):
            return "Add function for DEPOSIT" #ADD_FUNC_CALL_HERE                               # Function to deposit money
        
        else:                                                                                   # Doesn't match any of the above contexts
            last_msg = ""
            for i in st.session_state.messages:                                                 # Create contexts for clarifying questons
                if i['role'] == 'assistant':
                    last_msg += "assistant: (" + i['content'] + ") "
            template ="""
            query: {query}
            last messages: {last_msg}
            You are an A23 assitant designed to handle user interactions based on conversation history. 
            
            Your task is to provide responses based on the context of the conversation as follows:

                If the user asks a clarifying question related to the last message or any previous message in the 
                    conversation, relay relevant information from the entire history of the conversation to help them. 
                    Provide a summary or details that directly address their query.

                Else if the user's query does not relate to the last message or any previous messages, respond with a polite
                     acknowledgment that you do not understand the query. Reply as if you were texting.

            Respond with only one of the response types. Do not format the response.
            """
            prompt_template = ChatPromptTemplate.from_template(template)
            prompt = prompt_template.format(last_msg=last_msg, query=query)
            response_text = model.invoke(prompt)
            return response_text.content

# ------------------------------------- MAIN STREAMLIT CODE -----------------------------------
input = st.radio("How would you like to ask a question today?", ["Speech", "Text"])
st.cache_resource(init_session())
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("A23 Genie")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if input == "Speech":                                                                                               # Speech input with languages given below
    lang = st.selectbox("Supported languages", ["Choose a language", "English", "Hindi", "Telugu", "Kannada", "Tamil", "Marathi"])
    if lang not in (["Hindi", "Telugu", "Kannada", "Tamil", "Marathi"]):
        lang = "English"
    record_audio(lang)                                                                                              # ask user to record audio

elif input == "Text":                                                                                               # Text input (chat bot)
    if prompt := st.chat_input("What you wanna know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        response = ask_gpt(prompt)
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
