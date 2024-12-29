import os
import streamlit as st
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
import hashlib
import sqlite3


### SQLITE3 things

UPLOAD_DIR = "user_uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_NAME = "healthmate.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        #Users table
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
        
        # Files Table
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

init_db()

#### GEMINI API Things

load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')

import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_gemini_response(prev_chat):
    model = genai.GenerativeModel(model_name='gemini-pro')

    response = model.generate_content(f''' 
    Prompt:

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

The previous chat is provided, if the previous chat is not provided then consider that the session just started and greet the user and wait for his response
        Previous Chat : {prev_chat}
    ''')

    content = response.text
    return content


### STREAMLIT UI    

def main():
    st.set_page_config(page_title="HealthMate", page_icon="🩺")

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
                    else:
                        st.error("Invalid email or password.")


    if selected == "Consultation":
        if 'user_id' not in st.session_state:
            st.warning('You need to login first')

        else:
            st.title("Chat with HealthMate")
            st.info(f"Welcome {st.session_state['first_name']} {st.session_state['last_name']} !!")

            st.write("Describe your symptoms, ask for a diagnosis, or simply say hello!")

            if 'messages' not in st.session_state:
                st.session_state.messages = []

                st.session_state.messages.append(
                    {
                        'role':'assistant',
                        'content':'Welcome !! Start listing your symptoms and get the accurate diagnosis'
                    }
                )

            for message in st.session_state.messages:
                row = st.columns(2)
                if message['role']=='user':
                    row[1].chat_message(message['role']).markdown(message['content'])
                else:
                    row[0].chat_message(message['role']).markdown(message['content'])

            user_question = st.chat_input("Enter your symptoms here !!")
        
            if user_question:
                row_u = st.columns(2)
                row_u[1].chat_message('user').markdown(user_question)
                st.session_state.messages.append(
                    {'role':'user',
                    'content':user_question}
                )

                response = get_gemini_response(user_question)

                row_a = st.columns(2)
                row_a[0].chat_message('assistant').markdown(response)
                st.session_state.messages.append(
                    {'role':'assistant',
                    'content':response}
                )

    elif selected == "Medical Record Reader":
        if 'user_id' not in st.session_state:
            st.warning('You need to login first')
        
        else:
            st.title("Medical Record Reader")
            st.info(f'Welcome {st.session_state['first_name']} {st.session_state['last_name']} !!')
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


if __name__ == "__main__":
    main()

