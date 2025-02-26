# HealthMate

**HealthMate** is an AI-powered health diagnosis and medical record management application. Built with Streamlit, HealthMate provides a comprehensive platform where users can securely sign up, log in, consult with an intelligent medical chatbot for symptom analysis and diagnosis, and manage/upload their medical records (PDFs) for further review and discussion.

## Features

- **User Authentication:**  
  Secure sign-up and login functionality using SQLite. New users can register, and existing users can log in to access the system.

- **Symptom Checker & Consultation:**  
  Chat with "CuraBot" — an AI doctor powered by Google Generative AI (Gemini) — to get insights into your symptoms, possible diagnoses, and medication recommendations. The chatbot maintains conversation context and provides responses tailored to medical report content.

- **Medical Record Reader & Organizer:**  
  Upload your medical records (PDFs) securely. The app extracts text from your documents, splits the content into manageable chunks using LangChain text splitters, and indexes the content with FAISS for similarity search. You can then interact with your medical records via a dedicated chat interface.

- **Secure File Handling:**  
  Uploaded files are stored locally in a dedicated directory. File metadata is maintained in a SQLite database for easy retrieval and management.

- **Intelligent Document Analysis:**  
  With document chunking and vector search, the chatbot can retrieve relevant sections from your uploaded records to answer your questions based on the document content.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Jnan-py/Healthmate.git
   cd Healthmate
   ```

2. **Create a Virtual Environment (Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables:**
   - Create a `.env` file in the project root.
   - Add your Google API key (and any other secrets):
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```
5. **Initialize the Database:**
   - The app automatically initializes the SQLite database (`healthmate.db`) on first run.

## Usage

1. **Run the Application:**

   ```bash
   streamlit run main.py
   ```

2. **Navigate the App:**

   - **Landing Page:** Learn about HealthMate and its features.
   - **Login / SignUp:** Create an account or log in to access your personalized dashboard.
   - **Consultation:** Chat with CuraBot for symptom analysis and medical advice.
   - **Medical Record Reader:** Upload and manage your medical records (PDFs), view file contents, and interact with your documents via chat.

3. **File Uploads & Chatting:**
   - Use the sidebar navigation to switch between the Consultation and Medical Record Reader sections.
   - For medical records, upload your PDF files, which will be stored locally and indexed for interactive querying.

## Project Structure

```
healthmate/
│
├── main.py                  # Main Streamlit application
├── healthmate.db           # SQLite database (auto-created)
├── user_uploaded_files/    # Directory for storing uploaded PDFs
├── .env                    # Environment variables file (create this file)
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```

## Technologies Used

- **Streamlit:** For the interactive web interface.
- **SQLite:** To securely store user credentials and file metadata.
- **Google Generative AI (Gemini):** For generating context-aware, professional medical responses.
- **PyPDF:** To extract text from PDF medical records.
- **LangChain:**
  - **Text Splitters:** To split documents into manageable chunks.
  - **Community Vector Store (FAISS):** To index text chunks for similarity search.
- **Python-Dotenv:** For environment variable management.
- **Streamlit Option Menu:** For intuitive sidebar navigation.
- **Hashlib:** For secure password hashing.

---

Save these files in your project directory. You can now run HealthMate with:

```bash
streamlit run main.py
```
````
