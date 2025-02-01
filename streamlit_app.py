import streamlit as st
import json
import base64
import io
import time
import os
import re
from PIL import Image

# Google / Cloud Libraries
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

import cloudinary
import cloudinary.uploader
import cloudinary.api

from datetime import datetime


# ---------------------------
# 1. Load your JSON config files
# ---------------------------
with open('curriculum_structure.json', 'r') as f:
    curriculum_data = json.load(f)

with open('schools.json', 'r') as f:
    schools_data = json.load(f)


# ---------------------------
# 2. Configure Cloudinary
# ---------------------------
cloudinary.config(
    cloud_name = st.secrets["cloudinary"]["cloud_name"],
    api_key    = st.secrets["cloudinary"]["api_key"],
    api_secret = st.secrets["cloudinary"]["api_secret"],
    secure=True
)


# ---------------------------
# 3. Google APIs Setup
# ---------------------------
def get_gdrive_service():
    credentials_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials)

def get_gsheet_service():
    credentials_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=credentials)

def upload_json_to_drive(json_data, filename):
    """Uploads a JSON string to a specified Google Drive folder."""
    drive_service = get_gdrive_service()

    folder_id = st.secrets["gcp_drive"]["folder_id"]  # Where we want to upload
    media = MediaInMemoryUpload(json_data.encode('utf-8'), mimetype='application/json')

    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return uploaded_file  # returns a dict with 'id' and 'webViewLink'


def append_metadata_to_gsheet(exam_data):
    """
    Appends exam info (metadata + question count + timestamp) to a Google Sheet.
    Make sure your sheet has a tab named "Metadata" or change the range below.
    """
    sheets_service = get_gsheet_service()
    spreadsheet_id = st.secrets["gcp_sheets"]["spreadsheet_id"]

    metadata   = exam_data.get("metadata", {})
    questions  = exam_data.get("content", {}).get("questions", [])
    timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    q_count    = len(questions)

    # Extract metadata fields and cast them to strings
    unique_id = str(metadata.get("unique_id", ""))
    school = str(metadata.get("school", ""))
    exam_year = str(metadata.get("exam_year", ""))
    exam_month = str(metadata.get("exam_month", ""))
    exam_variable = str(metadata.get("exam_variable", ""))
    subject_year = str(metadata.get("subject_year", ""))
    semester = str(metadata.get("semester", ""))
    topic = str(metadata.get("topic", ""))

    # (Optional) entire metadata as JSON
    import json
    metadata_json_str = json.dumps(metadata)

    # Build the row to append (Columns: A to K)
    new_row = [
        timestamp,          # A
        unique_id,          # B
        school,             # C
        exam_year,          # D
        exam_month,         # E
        exam_variable,      # F
        subject_year,       # G
        semester,           # H
        topic,              # I
        q_count,            # J
        metadata_json_str   # K (optional)
    ]

    body = {
        "values": [new_row]
    }

    # Append to row range A1:K. If your sheet is named differently, change "Metadata"
    result = sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Metadata!A1:K",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

    return result


# ---------------------------
# 4. Other Utility Functions
# ---------------------------
def upload_image_to_cloudinary(image):
    if image is not None:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        response = cloudinary.uploader.upload(buffer)
        return response['secure_url']
    return None

def parse_options(options_text):
    options_list = options_text.split('\n')[:5]  # Limit to 5 options
    parsed_options = {}
    for idx, opt in enumerate(options_list):
        option_letter = chr(65 + idx)  # A, B, C, D, E
        parsed_options[option_letter] = opt.strip()
    return parsed_options


def generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable):
    semester_map = {
        "First Year":  {"S1": "S1",  "S2": "S2"},
        "Second Year": {"S3": "S3",  "S4": "S4"},
        "Third Year":  {"S5": "S5",  "S6": "S6"},
        "Fourth Year": {"S7": "S7",  "S8": "S8"},
        "Fifth Year":  {"S9": "S9", "S10": "S10"}
    }
    semester_code = semester_map[subject_year][semester]
    exam_year_str = exam_year if exam_year != "Unknown" else "UNK"
    exam_month_str = exam_month if exam_month != "Unknown" else "UNK"
    return f"{semester_code}_{school}_{topic}_{exam_year_str}_{exam_month_str}_{exam_variable}".replace(" ", "_")


# ---------------------------
# 5. Page Sections
# ---------------------------
def show_metadata_form(metadata):
    """Display form fields for exam metadata and return user inputs."""
    col1, col2 = st.columns(2)
    
    with col1:
        all_schools = schools_data["Schools"]
        default_school = metadata.get("school", all_schools[0])
        school_index = all_schools.index(default_school) if default_school in all_schools else 0
        school = st.selectbox("School", options=all_schools, index=school_index)
        
        exam_years = ["UNK"] + list(range(2000, 2101))
        default_year = metadata.get("exam_year", "UNK")
        year_index = exam_years.index(default_year) if default_year in exam_years else 0
        exam_year = st.selectbox("Year of Exam", options=exam_years, index=year_index)
        
        exam_months = ["UNK", "January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        default_month = metadata.get("exam_month", "UNK")
        month_index = exam_months.index(default_month) if default_month in exam_months else 0
        exam_month = st.selectbox("Month of Exam", options=exam_months, index=month_index)

    with col2:
        subject_years = list(curriculum_data.keys())
        default_subject_year = metadata.get("subject_year", subject_years[0])
        subject_year_index = subject_years.index(default_subject_year) if default_subject_year in subject_years else 0
        subject_year = st.selectbox("Year of Subject", options=subject_years, index=subject_year_index)
        
        semesters = list(curriculum_data[subject_year].keys())
        default_semester = metadata.get("semester", semesters[0])
        semester_index = semesters.index(default_semester) if default_semester in semesters else 0
        semester = st.selectbox("Semester", options=semesters, index=semester_index)
        
        topics = curriculum_data[subject_year][semester]
        default_topic = metadata.get("topic")
        if default_topic in topics:
            topic_index = topics.index(default_topic)
        else:
            topic_index = 0
            if default_topic:
                st.warning(f"Previously selected topic '{default_topic}' is not available in the current semester. Please select a new topic.")
        topic = st.selectbox("Topic", options=topics, index=topic_index)
        
        exam_variable = st.number_input("Exam Variable", min_value=1, max_value=1000, 
                                        value=metadata.get("exam_variable", 1), step=1, 
                                        help="Enter a number to represent the exam (e.g., 1 for first exam, 2 for second exam, etc.)")

    return school, exam_year, exam_month, subject_year, semester, topic, exam_variable


def show_create_exam_page():
    st.header("Create Exam")

    # A) Initialize session state
    if 'exam_data' not in st.session_state:
        st.session_state.exam_data = {
            "metadata": {},
            "content": {"questions": []}
        }
    
    # B) Display / Update Metadata
    if 'metadata_submitted' not in st.session_state or st.session_state.get('edit_metadata', False):
        st.subheader("Exam Metadata")

        # Grab current metadata, if any
        school, exam_year, exam_month, subject_year, semester, topic, exam_variable = show_metadata_form(
            st.session_state.exam_data.get("metadata", {})
        )

        if st.button("Submit Metadata"):
            unique_id = generate_unique_id(
                school, subject_year, semester, topic, exam_year, exam_month, exam_variable
            )
            st.session_state.exam_data["metadata"] = {
                "unique_id": unique_id,
                "school": school,
                "exam_year": exam_year,
                "exam_month": exam_month,
                "exam_variable": exam_variable,
                "subject_year": subject_year,
                "semester": semester,
                "topic": topic
            }
            st.session_state.metadata_submitted = True
            st.session_state.edit_metadata = False

            st.success("Metadata has been set. Scroll down to add questions.")

    else:
        st.write(f"Unique Exam ID: {st.session_state.exam_data['metadata']['unique_id']}")
        if st.button("Edit Metadata"):
            st.session_state.edit_metadata = True

    # C) Question Input
    if 'metadata_submitted' in st.session_state:
        st.subheader("Questions")

        num_questions = st.number_input(
            "Number of Questions",
            min_value=1,
            value=len(st.session_state.exam_data["content"]["questions"]) or 20,
            step=1
        )
        
        # Adjust the question list length
        while len(st.session_state.exam_data["content"]["questions"]) < num_questions:
            st.session_state.exam_data["content"]["questions"].append({
                "question": "",
                "options": {},
                "correct_answers": [],
                "isAnswered": False
            })
        st.session_state.exam_data["content"]["questions"] = \
            st.session_state.exam_data["content"]["questions"][:num_questions]

        questions = st.session_state.exam_data["content"]["questions"]

        input_method = st.radio("Input Method", ["Normal", "JSON"])

        if input_method == "Normal":
            # Each question in an expander
            for i, question in enumerate(questions):
                with st.expander(f"Question {i+1}", expanded=True):
                    question_text = st.text_area(
                        f"Question Text #{i+1}",
                        question['question'],
                        height=100,
                        key=f"q{i}_text"
                    )
                    question['question'] = question_text

                    st.write("Parsed Question:")
                    st.text(question['question'])

                    # Image upload
                    uploaded_image = st.file_uploader(
                        f"Upload an image for question #{i+1}",
                        type=["png", "jpg", "jpeg"],
                        key=f"q{i}_image"
                    )
                    if uploaded_image:
                        image_obj = Image.open(uploaded_image)
                        st.image(image_obj, caption="Uploaded Image", width=300)
                        image_url = upload_image_to_cloudinary(image_obj)
                        question['image_url'] = image_url
                    elif 'image_url' in question:
                        st.image(question['image_url'], caption="Question Image", width=300)

                    # Options input
                    options_text = st.text_area(
                        "Options (one option per line, max 5 lines)",
                        value="\n".join(question.get('options', {}).values()),
                        height=150,
                        key=f"q{i}_options"
                    )
                    new_options = parse_options(options_text)
                    question['options'] = new_options

                    st.write("Parsed Options:")
                    for key, val in question['options'].items():
                        st.text(f"{key}: {val}")

                    correct_answers_input = st.text_input(
                        "Correct Answer(s) (e.g., ABC, DE, A)",
                        value="".join(question.get('correct_answers', [])),
                        key=f"q{i}_correct_input"
                    )
                    new_correct_answers = [ans for ans in correct_answers_input.upper()
                                           if ans in question['options']]
                    question['correct_answers'] = new_correct_answers
                    question['isAnswered'] = bool(new_correct_answers)

                    st.write("Parsed Correct Answer(s):")
                    st.text(", ".join(question['correct_answers']))

        else:  # JSON input method
            json_input = st.text_area("Paste JSON for questions here", height=300)
            if st.button("Parse JSON"):
                try:
                    new_questions = json.loads(json_input)
                    if isinstance(new_questions, list):
                        for q in new_questions:
                            if 'question' in q and 'options' in q:
                                q['correct_answers'] = q.get('correct_answers', [])
                                q['isAnswered'] = q.get('isAnswered', False)
                                questions.append(q)
                        st.session_state.exam_data["content"]["questions"] = questions
                        st.success(f"Successfully added {len(new_questions)} questions.")
                    else:
                        st.error("Invalid JSON format. Must be a list of question objects.")
                except json.JSONDecodeError:
                    st.error("Invalid JSON. Please check your input.")

        # D) Submit Exam
        st.markdown("---")
        if st.button("Submit Exam"):
            # 1. Get exam_data
            exam_data = st.session_state.exam_data

            # 2. Convert to JSON
            json_str = json.dumps(exam_data, indent=2)

            # 3. Upload JSON to Drive
            filename = f"{exam_data['metadata']['unique_id']}.json"
            upload_json_to_drive(json_str, filename)

            # 4. Append to Google Sheet
            append_metadata_to_gsheet(exam_data)

            # 5. Show a simple success message
            st.success("Exam has been successfully submitted and recorded in Google Sheets!")




def show_visualize_test_page():
    st.header("Visualize Test")

    uploaded_file = st.file_uploader("Upload JSON file", type="json")
    
    if uploaded_file is not None:
        try:
            exam_data = json.load(uploaded_file)
            
            # Display metadata
            st.subheader("Exam Metadata")
            metadata = exam_data.get("metadata", {})
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"School: {metadata.get('school', 'N/A')}")
                st.write(f"School Type: {metadata.get('school_type', 'N/A')}")
                st.write(f"Exam Year: {metadata.get('exam_year', 'N/A')}")
                st.write(f"Exam Month: {metadata.get('exam_month', 'N/A')}")
            with col2:
                st.write(f"Subject Year: {metadata.get('subject_year', 'N/A')}")
                st.write(f"Semester: {metadata.get('semester', 'N/A')}")
                st.write(f"Topic: {metadata.get('topic', 'N/A')}")
                st.write(f"Exam Variable: {metadata.get('exam_variable', 'N/A')}")
            
            st.write(f"Unique Exam ID: {metadata.get('unique_id', 'N/A')}")
            
            # Display questions
            questions = exam_data.get("content", {}).get("questions", [])
            if questions:
                st.subheader("Questions")
                
                # Question navigation
                question_index = st.number_input("Go to question", min_value=1, max_value=len(questions), value=1) - 1
                
                # Display current question
                question = questions[question_index]
                st.write(f"Question {question_index + 1} of {len(questions)}")
                st.write(question.get("question", ""))
                
                # Display image if present
                if "image_url" in question:
                    try:
                        response = requests.get(question["image_url"])
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption="Question Image", use_column_width=True)
                    except Exception as e:
                        st.error(f"Error loading image: {str(e)}")
                
                # Display options
                options = question.get("options", {})
                for option in ['A', 'B', 'C', 'D', 'E']:
                    if option in options:
                        st.write(f"{option}: {options[option]}")
                
                # Display correct answers
                correct_answers = question.get("correct_answers", [])
                st.write("Correct Answer(s):", ", ".join(correct_answers))
                
                # Navigation buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if question_index > 0:
                        if st.button("Previous"):
                            st.session_state.question_index = question_index - 1
                            st.rerun()
                with col3:
                    if question_index < len(questions) - 1:
                        if st.button("Next"):
                            st.session_state.question_index = question_index + 1
                            st.rerun()
            else:
                st.warning("No questions found in the uploaded JSON.")
        
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid exam JSON file.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")



def show_edit_json_page():
    st.header("Edit JSON")

    if 'edited_data' not in st.session_state:
        st.session_state.edited_data = None

    uploaded_file = st.file_uploader("Upload JSON file", type="json")
    
    if uploaded_file is not None:
        try:
            if st.session_state.edited_data is None:
                st.session_state.edited_data = json.load(uploaded_file)
            
            data = st.session_state.edited_data
            
            # Metadata editing
            st.subheader("Exam Metadata")
            metadata = data.get("metadata", {})
            school, exam_year, exam_month, subject_year, semester, topic, exam_variable = show_metadata_form(metadata)
            
            if st.button("Update Metadata"):
                unique_id = generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable)
                data["metadata"] = {
                    "unique_id": unique_id,
                    "school": school,
                    "exam_year": exam_year,
                    "exam_month": exam_month,
                    "exam_variable": exam_variable,
                    "subject_year": subject_year,
                    "semester": semester,
                    "topic": topic
                }
                st.session_state.edited_data = data
                st.success("Metadata updated successfully!")
                st.rerun()
            
            # Display current metadata
            st.write("Current Metadata:")
            st.json(data["metadata"])
            
            # Display and edit questions
            st.subheader("Questions")
            questions = data.get("content", {}).get("questions", [])
            
            # Number of questions input
            num_questions = st.number_input("Number of Questions", min_value=1, value=len(questions), step=1)
            
            # Adjust the number of questions
            if len(questions) != num_questions:
                while len(questions) < num_questions:
                    questions.append({"question": "", "options": {}, "correct_answers": [], "isAnswered": False})
                questions = questions[:num_questions]  # Remove extra questions if number is reduced
                data["content"]["questions"] = questions
                st.session_state.edited_data = data
                st.rerun()
            
            for i, question in enumerate(questions):
                with st.expander(f"Question {i + 1}", expanded=False):
                    question['question'] = st.text_area(f"Question Text #{i+1}", question['question'], height=100, key=f"q{i}_text")
                    
                    if 'image_url' in question:
                        st.image(question['image_url'], caption="Question Image", width=300)
                        if st.button(f"Remove Image for Question {i + 1}", key=f"remove_image_{i}"):
                            del question['image_url']
                            st.session_state.edited_data = data
                            st.rerun()
                    
                    # Options input with automatic parsing
                    options_text = st.text_area(
                        "Options (one option per line, max 5 lines)",
                        value="\n".join(question.get('options', {}).values()),
                        height=150,
                        key=f"q{i}_options"
                    )
                    
                    # Parse options
                    new_options = parse_options(options_text)
                    if new_options != question.get('options', {}):
                        question['options'] = new_options
                        st.session_state.edited_data = data

                    # Display parsed options
                    st.write("Parsed Options:")
                    for key, value in question['options'].items():
                        st.text(f"{key}: {value}")
                    
                    # Correct answers input
                    correct_answers_input = st.text_input(
                        "Correct Answer(s) (e.g., ABC, DE, A)",
                        value="".join(question.get('correct_answers', [])),
                        key=f"q{i}_correct_input"
                    )

                    # Update correct answers
                    new_correct_answers = [ans for ans in correct_answers_input.upper() if ans in question['options']]
                    if new_correct_answers != question.get('correct_answers', []):
                        question['correct_answers'] = new_correct_answers
                        question['isAnswered'] = bool(new_correct_answers)
                        st.session_state.edited_data = data

                    # Display selected correct answers
                    st.write("Parsed Correct Answer(s):")
                    st.text(", ".join(question['correct_answers']))
            
            # Generate and download updated JSON
            if st.button("Download Updated JSON"):
                json_str = json.dumps(st.session_state.edited_data, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                file_name = f"updated_{uploaded_file.name}"
                href = f'<a href="data:application/json;base64,{b64}" download="{file_name}">Download Updated JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid exam JSON file.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Make sure to include the parse_options function if it's not already in your code
def parse_options(options_text):
    options_list = options_text.split('\n')[:5]  # Limit to 5 options
    parsed_options = {}
    for idx, opt in enumerate(options_list):
        option_letter = chr(65 + idx)  # A, B, C, D, E
        parsed_options[option_letter] = opt.strip()
    return parsed_options

# Update the main function to include the new page (if not already updated)
def main():
    st.set_page_config(page_title="MEDQUEST Admin Tool", layout="wide")

    page = st.sidebar.selectbox("Select a page", ["Create Exam", "Visualize Test", "Edit JSON"])

    if page == "Create Exam":
        show_create_exam_page()
    elif page == "Visualize Test":
        show_visualize_test_page()
    elif page == "Edit JSON":
        show_edit_json_page()

if __name__ == "__main__":
    main()
