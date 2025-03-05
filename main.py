import os
import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
import hashlib
import sqlite3
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

UPLOAD_DIR = "user_uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

DB_NAME = "healthmate.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)
    print("Database initialized.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sign_up(first_name, last_name, date_of_birth, email, password):
    with sqlite3.connect(DB_NAME) as conn:
        try:
            conn.execute("""
            INSERT INTO users (first_name, last_name, date_of_birth, email, password)
            VALUES (?, ?, ?, ?, ?)
            """, (first_name, last_name, date_of_birth, email, hash_password(password)))
            conn.commit()
            return True, "Account created successfully!, Now you can login"
        except sqlite3.IntegrityError:
            return False, "This email is already registered. Try logging in."

def login(email, password):
    with sqlite3.connect(DB_NAME) as conn:
        user = conn.execute("""
        SELECT user_id,first_name,last_name FROM users WHERE email = ? AND password = ?
        """, (email, hash_password(password))).fetchone()
        return user if user else None

def save_file(user_id, file_name, file_path):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        INSERT INTO files (user_id, file_name, file_path)
        VALUES (?, ?, ?)
        """, (user_id, file_name, file_path))
        conn.commit()

def get_user_files(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        files = conn.execute("""
        SELECT file_name, file_path FROM files WHERE user_id = ?
        """, (user_id,)).fetchall()
        return files

def delete_file(user_id, file_name):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        DELETE FROM files WHERE (file_name, user_id) = (?, ?)
        """, (file_name, user_id)).fetchall()
        conn.commit()

init_db()

embeddings = GoogleGenerativeAIEmbeddings(model = 'models/embedding-001')

def get_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size = 10000, chunk_overlap = 200)
    chunks = splitter.split_text(text)
    return chunks

@st.cache_resource
def get_vector_store(chunks):
    db = FAISS.from_texts(chunks, embedding = embeddings)
    return db

def get_rel_text(user_query,db):
    rel_text = db.similarity_search(user_query, k = 1)
    return rel_text[0].page_content
 
def bot_response(model, query, relevant_texts, history): 
    context = ' '.join(relevant_texts)
    prompt = f"""This is the context of the document 
    Context: {relevant_texts}
    And this is the user query
    User: {query}
    And this is the history of the conversation
    History: {history}
    Please generate a response to the user query based on the context and history
    The questions might be asked related to the provided context, and may also be in terms of the medical terms, diseases, etc..,
    Answer the query with respect to the medical report context provided, you can also use your additional knowledge too, but do not ignore the content of the provided medical report,
    Answer the queries like a professional doctor, having a lot of knowledge on the based report context
    Bot:
    """
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.65,
        )
    )
    return response.text

model = genai.GenerativeModel(model_name='gemini-2.0-flash', 
    system_instruction = """
    Your name is "CuraBot" and you are a doctor who gives the medications and let the user know the disease he is suffering from based on the symptoms he provides
    
        Your Role:
        1) Your a healthbot , who is highly intelligent in finding the particular disease or list of diseases for the given symptoms
        2) You are a doctor, you should let the user know through which he is suffering based on the symptoms he gives to you
        3) If possible you can also give the medication for that particular symptoms which he is encountering
        4) The best and the most important part is that you should tell him What he is suffering from based on the symptoms the user provides.
        5) You should provide him with the particular disease he is suffering from, and give the measures of it
        
        Points to remember:
        1) You should engage with the user like a fellow doctor, and give the user proper reply for his queries
        2) The concentration and the gist of the conversation no need to be completely on the symptoms and diagnosis itself, your flow of chat should be like a human conversation
        3) If the conversation goes way too out of the content of medicine and healthcare or if the user input is abusive, let the user know that the content is abusive or vulgar and we cannot tolerate those kind of messages.
        4) The important part is dont use the sentence "You should consult a doctor for further diagnosis" as you play the role of the doctor here.
    
    This is so important and I want you to stick to these points everytime without any mismatches, and I want you to maintain the consistency too.
    First start with the greetings message like "Welcome, How can I help you with the diagnosis today..??"
    """
    )

st.set_page_config(page_title="HealthMate", page_icon="🩺", layout = "wide")

if 'messages' not in st.session_state:
    st.session_state.messages = {}

with st.sidebar:
    selected = option_menu(
        "Menu", ["Landing Page","Login / SignUp","Consultation", "Medical Record Reader"],
        icons=["house", None,"chat", "file-medical"],
        menu_icon="cast", default_index=0
    )

if selected == 'Landing Page':
    st.title("HealthMate")
    st.header('Where Health Diagnosis Meets Technology')
    st.markdown("""
    In today’s fast-paced world, prioritizing your health and managing medical records shouldn’t be a hassle. 
    That’s where **HealthMate** steps in, revolutionizing how you approach healthcare. With HealthMate, you gain access to two powerful tools designed to simplify and enhance your healthcare journey:
    - **Symptom Checker and Medication Advisor Chatbot**
    - **Medical Record Reader and Organizer**
    """)

    st.subheader("🩺 Symptom Checker and Medication Advisor")
    st.markdown("""
    Not feeling well? Wondering what those symptoms could mean? 
    The **Symptom Checker and Medication Advisor Chatbot** is here to assist you anytime, anywhere.

    ### **Features:**
    - **24/7 Symptom Analysis:** Describe your symptoms and receive instant insights.
    - **Personalized Recommendations:** Get advice on medications and remedies tailored to your needs.
    - **Lifestyle Tips:** Learn practical steps to enhance your health.
    - **Medical Advice:** Know when it’s time to consult a doctor.

    ### **How It Works:**
    1. Start a chat and describe your symptoms.
    2. Let the AI-powered chatbot analyze your input.
    3. Receive personalized recommendations and next steps.

    """)

    st.subheader("📂 Medical Record Reader and Organizer")
    st.markdown("""
    Managing medical records can often feel overwhelming. With HealthMate's **Medical Record Reader and Organizer**, 
    you can easily upload, store, and access your health documents at the click of a button.

    ### **Features:**
    - **Secure Uploads:** Safely upload medical records from your device.
    - **Easy Access:** Retrieve documents anytime, anywhere.

    ### **How It Works:**
    1. Upload your medical records using the secure uploader.
    2. Let the app organize and analyze your records.
    3. Access or share your records as needed.

    """)

if selected == 'Login / SignUp':
    st.header("Login or Sign Up")

    if "user_id" in st.session_state:
        st.info(f"You are logged in as {st.session_state['first_name']} {st.session_state['last_name']}.")
        if st.button("Log Out"):
            st.session_state.clear()
            st.success("Logged out successfully!")

    else:
        action = st.selectbox("Select an action", ["Login", "Sign Up"])  

        if action == "Sign Up":
            st.subheader("Sign Up")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            dob = st.date_input("Date of Birth")  
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Create Account"):
                success, msg = sign_up(first_name, last_name, dob, email, password)
                if success:
                    st.success(str(msg))  
                else:
                    st.error(str(msg))

        elif action == "Login":
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Log In"):
                user = login(email, password)
                if user: 
                    st.session_state["user_id"], st.session_state["first_name"], st.session_state["last_name"] = user
                    st.success(f"Logged in as {user[1]} {user[2]}!")
                    st.session_state.messages[st.session_state['user_id']]  = []
                else:
                    st.error("Invalid email or password.")

if selected == "Consultation":
    st.title("Chat with HealthMate")
    if 'user_id' not in st.session_state:
        st.warning('You need to login first')

    else:
        st.info(f'Welcome {st.session_state['first_name']} {st.session_state['last_name']} !!')
        st.write("Describe your symptoms, ask for a diagnosis, or simply say hello!")
        chat_history = st.session_state.messages.get(st.session_state['user_id'], [])

        chat_bot = model.start_chat(
                        history = chat_history,
                    )

        for message in chat_history:
            row = st.columns(2)
            if message['role']=='user':
                row[1].chat_message(message['role']).markdown(message['parts'])
            else:
                row[0].chat_message(message['role']).markdown(message['parts'])

        user_question = st.chat_input("Enter your symptoms here !!")

        if user_question:
            row_u = st.columns(2)
            row_u[1].chat_message('user').markdown(user_question)
            chat_history.append(
                {'role':'user',
                'parts':user_question}
            )

            with st.spinner("Thinking ..."):
                response = chat_bot.send_message(user_question)

                row_a = st.columns(2)
                row_a[0].chat_message('assistant').markdown(response.text)

                chat_history.append(
                    {'role':'assistant',
                    'parts':response.text}
                )

            st.session_state.messages[st.session_state['user_id']] = chat_history

elif selected == "Medical Record Reader":
    st.title("Medical Record Reader")

    if 'user_id' not in st.session_state:
        st.warning('You need to login first')
    
    else:
        with st.expander("Select the feature ", expanded = True):
            choice = st.radio(
                label = "Select the type",
                options = ["Upload the Medical Record", "Chat with Medical Record"]
            )

        st.info(f'Welcome {st.session_state['first_name']} {st.session_state['last_name']} !!')

        if choice == "Upload the Medical Record":
            file = st.file_uploader(label='Upload your medical record',type='pdf')

            if file:
                file_name = file.name
                file_path = os.path.join(UPLOAD_DIR, f"{st.session_state['user_id']}_{file_name}")
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                if st.button('Save File'):
                    save_file(st.session_state["user_id"], file_name, file_path)
                    st.success(f"File '{file_name}' saved successfully!")

            st.subheader("Previously Uploaded Files")
            files = get_user_files(st.session_state["user_id"])
            if files:
                for file_name, file_path in files:
                    st.markdown(f"- {file_name}")
                    if st.button(f"Delete {file_name}"):
                        delete_file(st.session_state["user_id"], file_name)
                
                st.subheader('File Content Viewer')
                s_file = st.selectbox(label='Select the file', options=[i for i,v in files])

                def get_value(i, lst):
                    for pair in lst:
                        if pair[0] == i:  
                            return pair[1]  
                    return None

                if s_file:
                    file_path = get_value(s_file,files)
                    if st.button('View Content'):
                        with st.spinner('Giving the details'):
                            
                            pdf_reader = PdfReader(file_path)
                            text = ''
                            for page in pdf_reader.pages:
                                text+= page.extract_text()
                            
                            st.subheader(f"The content of {file_name}")
                            st.write(text)
            else:
                st.info("No files uploaded yet.")
        
        elif choice == "Chat with Medical Record":
            if "doc_paragraphs" not in st.session_state:
                st.session_state.doc_paragraphs = {}
            if "doc_messages" not in st.session_state:
                st.session_state.doc_messages = {}
            if "faiss" not in st.session_state:
                st.session_state.faiss = {}

            st.subheader("Chat with Medical Record")
            files = get_user_files(st.session_state["user_id"])
            s_file = st.selectbox(label='Select the file', options=[i for i,v in files])

            def get_value(i, lst):
                for pair in lst:
                    if pair[0] == i:  
                        return pair[1]  
                return None

            if s_file:
                if s_file not in st.session_state.doc_messages:
                    st.session_state.doc_messages[s_file] = []

                file_path = get_value(s_file,files)

                if s_file not in st.session_state.doc_paragraphs:
                    with st.spinner('Getting the details'):
                        pdf_reader = PdfReader(file_path)
                        text = ''
                        for page in pdf_reader.pages:
                            text+= page.extract_text()
                    
                        st.session_state.doc_paragraphs[s_file] = text
                    

                if s_file not in st.session_state.faiss:
                    chunks = get_chunks(st.session_state.doc_paragraphs[s_file])

                    with st.spinner("Reading records..."):
                        st.session_state.faiss[s_file] = get_vector_store(chunks)

                h_model = genai.GenerativeModel(model_name= "gemini-2.0-flash", 
                system_instruction = "You are a very professional doctor with a lots of years of experience and you are here to help the patient with their medical record."
                )

                doc_chat = st.session_state.doc_messages.get(s_file)

                for message in doc_chat:
                    row = st.columns(2)
                    if message['role'] == 'user':
                        row[1].chat_message(message['role']).markdown(message['content'])
                    else:
                        row[0].chat_message(message['role']).markdown(message['content'])

                try:
                    user_question = st.chat_input("Enter your query here !!")

                    if user_question:
                        row_u = st.columns(2)
                        row_u[1].chat_message('user').markdown(user_question)
                        doc_chat.append(
                            {'role': 'user',
                            'content': user_question}
                        )

                        with st.spinner("Generating response..."):
                            relevant_texts = get_rel_text(user_question, st.session_state.faiss[s_file])
                            bot_reply = bot_response(h_model, user_question, relevant_texts, doc_chat)

                        row_a = st.columns(2)
                        row_a[0].chat_message('assistant').markdown(bot_reply)

                        doc_chat.append(
                            {'role': 'assistant',
                            'content': bot_reply}
                        )


                except Exception as e:
                    st.chat_message('assistant').markdown(f'There might be an error, try again, {str(e)}')
                    doc_chat.append(
                        {
                            'role': 'assistant',
                            'content': f'There might be an error, try again, {str(e)}'
                        }
                    )

