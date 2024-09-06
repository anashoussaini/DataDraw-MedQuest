import streamlit as st
import json
import base64
import tempfile
import openai
import fitz  
from PIL import Image
import io
import cloudinary
import cloudinary.uploader
import cloudinary.api
from openai import OpenAI
import time
import os
import re


cloudinary.config( 
    cloud_name = st.secrets["cloudinary"]["cloud_name"],
    api_key = st.secrets["cloudinary"]["api_key"],
    api_secret = st.secrets["cloudinary"]["api_secret"],
    secure=True
)

def upload_image_to_cloudinary(image_path):
    response = cloudinary.uploader.upload(image_path)
    return response['secure_url']


with open('curriculum_structure.json', 'r') as f:
    curriculum_data = json.load(f)

with open('schools.json', 'r') as f:
    schools_data = json.load(f)




def get_json_download_link(json_data, filename):
    json_str = json.dumps(json_data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    return f'<a href="data:application/json;base64,{b64}" download="{filename}">Download JSON</a>'

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def display_metadata(metadata):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"School: {metadata['school']} ({metadata['school_type']})")
        st.write(f"Year: {metadata['exam_year']}")
    with col2:
        st.write(f"Subject: {metadata['subject_year']} - {metadata['semester']}")
        st.write(f"Topic: {metadata['topic']}")

def display_question(question, index, total):
    st.write(f"Question {index + 1} of {total}")
    st.write(question['question'])
    
    if question.get('hasImage', False):
        st.write("(This question has an image - display functionality to be implemented)")

    options = question['options']
    selected_options = []
    for option, text in options.items():
        if st.checkbox(f"{option}: {text}", key=f"q{index}_{option}"):
            selected_options.append(option)
    
    return selected_options



def display_metadata(metadata):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"School: {metadata['school']} ({metadata['school_type']})")
        st.write(f"Year: {metadata['exam_year']}")
    with col2:
        st.write(f"Subject: {metadata['subject_year']} - {metadata['semester']}")
        st.write(f"Topic: {metadata['topic']}")



def generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable):
    semester_map = {
        "First Year": {"S1": "S1", "S2": "S2"},
        "Second Year": {"S3": "S3", "S4": "S4"},
        "Third Year": {"S5": "S5", "S6": "S6"},
        "Fourth Year": {"S7": "S7", "S8": "S8"},
        "Fifth Year": {"S9": "S9", "S10": "S10"}
    }
    semester_code = semester_map[subject_year][semester]
    exam_year_str = exam_year if exam_year != "Unknown" else "UNK"
    exam_month_str = exam_month if exam_month != "Unknown" else "UNK"
    return f"{semester_code}_{school}_{topic}_{exam_year_str}_{exam_month_str}_{exam_variable}".replace(" ", "_")
def generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable):
    semester_map = {
        "First Year": {"S1": "S1", "S2": "S2"},
        "Second Year": {"S3": "S3", "S4": "S4"},
        "Third Year": {"S5": "S5", "S6": "S6"},
        "Fourth Year": {"S7": "S7", "S8": "S8"},
        "Fifth Year": {"S9": "S9", "S10": "S10"}
    }
    semester_code = semester_map.get(subject_year, {}).get(semester, "UNK")
    exam_year_str = exam_year if exam_year != "Unknown" else "UNK"
    exam_month_str = exam_month if exam_month != "Unknown" else "UNK"
    return f"{semester_code}_{school}_{topic}_{exam_year_str}_{exam_month_str}_{exam_variable}".replace(" ", "_")

def show_create_exam_page():
    st.header("Create Exam")

    # Initialize session state for exam data if not exists
    if 'exam_data' not in st.session_state:
        st.session_state.exam_data = {
            "metadata": {},
            "content": {"questions": []}
        }
    
    # Metadata input (only shown on first page)
    if 'metadata_submitted' not in st.session_state:
        st.subheader("Exam Metadata")
        col1, col2 = st.columns(2)
        
        with col1:
            school = st.selectbox("School", options=["Unknown"] + schools_data["private"] + schools_data["public"])
            school_type = "Private" if school in schools_data["private"] else "Public" if school in schools_data["public"] else "Unknown"
            st.write(f"School Type: {school_type}")
            exam_year = st.selectbox("Year of Exam", options=["Unknown"] + list(range(2000, 2101)))
            exam_month = st.selectbox("Month of Exam", options=["Unknown", "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"])

        with col2:
            subject_year = st.selectbox("Year of Subject", options=["Unknown"] + list(curriculum_data.keys()))
            semester = st.selectbox("Semester", options=["Unknown"] + (list(curriculum_data[subject_year].keys()) if subject_year != "Unknown" else []))
            topics = ["Unknown"] + (curriculum_data[subject_year][semester] if subject_year != "Unknown" and semester != "Unknown" else [])
            topic = st.selectbox("Topic", options=topics)
            exam_variable = st.number_input("Exam Variable", min_value=1, max_value=10, value=1, step=1, 
                                            help="Enter a number to represent the exam (e.g., 1 for first exam, 2 for second exam, etc.)")

        if st.button("Submit Metadata"):
            unique_id = generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable)
            st.session_state.exam_data["metadata"] = {
                "unique_id": unique_id,
                "school": school,
                "school_type": school_type,
                "exam_year": exam_year,
                "exam_month": exam_month,
                "exam_variable": exam_variable,
                "subject_year": subject_year,
                "semester": semester,
                "topic": topic
            }
            st.session_state.metadata_submitted = True
            st.rerun()
    else:
        st.write(f"Unique Exam ID: {st.session_state.exam_data['metadata']['unique_id']}")

    # Question input
    if 'metadata_submitted' in st.session_state:
        st.subheader("Questions")
        questions = st.session_state.exam_data["content"]["questions"]

        # Toggle between normal and JSON input
        input_method = st.radio("Input Method", ["Normal", "JSON"])

        if input_method == "Normal":
            # Add new question button
            if st.button("+ Add New Question"):
                questions.append({"question": "", "options": {}, "isAnswered": False})

            # Display all questions on the same page
            for i, question in enumerate(questions):
                st.write(f"Question {i + 1}")
                
                # Question text
                question['question'] = st.text_area(f"Question Text #{i+1}", question['question'], height=100, key=f"q{i}_text")

                # Image upload for question
                uploaded_image = st.file_uploader(f"Upload an image for question #{i+1}", type=["png", "jpg", "jpeg"], key=f"q{i}_image")
                if uploaded_image:
                    image = Image.open(uploaded_image)
                    st.image(image, caption="Uploaded Image", use_column_width=False, width=300)
                    image_url = upload_image_to_cloudinary(image)
                    question['image_url'] = image_url
                elif 'image_url' in question:
                    st.image(question['image_url'], caption="Question Image", width=300)

                # Options
                st.write("Options:")
                options = question['options']
                for option in ['A', 'B', 'C', 'D', 'E']:
                    options[option] = st.text_input(f"Option {option}", options.get(option, ""), key=f"q{i}_opt_{option}")

                # Correct answer using toggles
                st.write("Correct Answer(s):")
                correct_options = question.get('correct_answers', [])
                for option in ['A', 'B', 'C', 'D', 'E']:
                    if st.checkbox(option, value=option in correct_options, key=f"q{i}_correct_{option}"):
                        if option not in correct_options:
                            correct_options.append(option)
                    elif option in correct_options:
                        correct_options.remove(option)
                question['correct_answers'] = correct_options

                # Update isAnswered flag
                question['isAnswered'] = bool(correct_options)

                st.write("---")  # Separator between questions

        else:  # JSON input method
            json_input = st.text_area("Paste JSON for questions here", height=300)
            if st.button("Parse JSON"):
                try:
                    new_questions = json.loads(json_input)
                    if isinstance(new_questions, list):
                        for q in new_questions:
                            if 'question' in q and 'options' in q:
                                questions.append(q)
                        st.success(f"Successfully added {len(new_questions)} questions.")
                    else:
                        st.error("Invalid JSON format. Please provide a list of question objects.")
                except json.JSONDecodeError:
                    st.error("Invalid JSON. Please check your input.")

        # Generate and download JSON
        if st.button("Generate Exam JSON"):
            json_str = json.dumps(st.session_state.exam_data, indent=2)
            b64 = base64.b64encode(json_str.encode()).decode()
            file_name = f"{st.session_state.exam_data['metadata']['unique_id']}.json"
            href = f'<a href="data:application/json;base64,{b64}" download="{file_name}">Download Exam JSON</a>'
            st.markdown(href, unsafe_allow_html=True)



# Update the main function to include the new page
def main():
    st.set_page_config(page_title="MEDQUEST Admin Tool", layout="wide")

    # page = st.sidebar.selectbox("Select a page", ["Digitalization", "Answer Filling", "Correction Linking", "Create Exam"])
    page = st.sidebar.selectbox("Select a page", ["Create Exam"])

    # if page == "Digitalization":
    #     show_digitalization_page()
    # elif page == "Answer Filling":
    #     show_answer_filling_page()
    # elif page == "Correction Linking":
    #     show_correction_linking_page()
    if page == "Create Exam":
        show_create_exam_page()

if __name__ == "__main__":
    main()

