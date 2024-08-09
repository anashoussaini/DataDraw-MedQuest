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

def pdf_to_jpg(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    image_paths = []
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        file_name = f"page_{page_num + 1}.jpg"
        file_path = os.path.join(output_folder, file_name)
        img.save(file_path, "JPEG", quality=95)
        image_paths.append(file_path)
    pdf_document.close()
    return image_paths


def generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable):
    semester_map = {
        "First Year": {"S1": "S1", "S2": "S2"},
        "Second Year": {"S3": "S3", "S4": "S4"},
        "Third Year": {"S5": "S5", "S6": "S6"},
        "Fourth Year": {"S7": "S7", "S8": "S8"},
        "Fifth Year": {"S9": "S9", "S10": "S10"}
    }
    semester_code = semester_map[subject_year][semester]
    return f"{semester_code}_{school}_{topic}_{exam_year}_{exam_month}_{exam_variable}".replace(" ", "_")


def extract_questions_from_text(text):
    # Simple regex-based question extraction
    questions = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL)
    return [{"question": q.strip(), "options": {}} for q in questions]


def get_json_download_link(json_data, filename):
    json_str = json.dumps(json_data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    return f'<a href="data:application/json;base64,{b64}" download="{filename}">Download JSON</a>'

def show_digitalization_page():
    st.header("Digitalization")

    col1, col2 = st.columns(2)
    
    with col1:
        school = st.selectbox("School", options=schools_data["private"] + schools_data["public"])
        school_type = "Private" if school in schools_data["private"] else "Public"
        st.write(f"School Type: {school_type}")
        exam_year = st.number_input("Year of Exam", min_value=2000, max_value=2100, value=2024)
        exam_month = st.selectbox("Month of Exam", options=[
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ])

    with col2:
        subject_year = st.selectbox("Year of Subject", options=list(curriculum_data.keys()))
        semester = st.selectbox("Semester", options=list(curriculum_data[subject_year].keys()))
        topics = curriculum_data[subject_year][semester]
        topic = st.selectbox("Topic", options=topics)
        exam_variable = st.number_input("Exam Variable", min_value=1, max_value=10, value=1, step=1, 
                                        help="Enter a number to represent the exam (e.g., 1 for first exam, 2 for second exam, etc.)")

    unique_id = generate_unique_id(school, subject_year, semester, topic, exam_year, exam_month, exam_variable)
    st.write(f"Unique Exam ID: {unique_id}")

    uploaded_file = st.file_uploader("Upload JSON file", type="json")
    
    if uploaded_file is not None and st.button("Process JSON"):
        try:
            content = json.load(uploaded_file)
            
            metadata = {
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
            
            full_response = {
                "metadata": metadata,
                "content": content
            }
            
            st.json(full_response)
            
            st.markdown(get_json_download_link(full_response, f"{unique_id}.json"), unsafe_allow_html=True)
        
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid JSON file.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


def show_answer_filling_page():
    st.header("Answer Filling and Verification")
    st.write("This page is under construction.")

def show_correction_linking_page():
    st.header("Correction Linking")
    st.write("This page is under construction.")

###############################################
# Answer Filling Page
###############################################

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




def upload_image_to_cloudinary_2(image):
    if image is not None:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        response = cloudinary.uploader.upload(buffer)
        return response['secure_url']
    return None
def show_answer_filling_page():
    if 'data' not in st.session_state:
        uploaded_file = st.file_uploader("Upload JSON file", type="json")
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                # Add isAnswered flag to each question if not present
                for question in data['content']['questions']:
                    if 'isAnswered' not in question:
                        question['isAnswered'] = bool(question['options'].get('correct_answers', []))
                st.session_state.data = data
                st.session_state.original_filename = uploaded_file.name
                st.session_state.current_question = 0  # Initialize current question
                st.rerun()
            except Exception as e:
                st.error(f"Error loading JSON file: {str(e)}")
    
    if 'data' in st.session_state:
        try:
            data = st.session_state.data
            questions = data['content']['questions']

            # Sidebar for question navigation
            with st.sidebar:
                st.write("Questions:")
                for i, q in enumerate(questions):
                    question_text = q['question'].split('\n')[0][:30] + "..."  # Truncate for display
                    if st.button(f"Q{i+1}{' ✓' if q['isAnswered'] else ''}", key=f"nav_{i}"):
                        st.session_state.current_question = i
                        st.rerun()

            current_question = st.session_state.get('current_question', 0)

            # Main content area
            st.progress((current_question + 1) / len(questions))
            st.write(f"Question {current_question + 1} of {len(questions)}")

            # Question display and editing
            question_text = questions[current_question]['question'].split('\n')[0]
            st.markdown(f"### Question:")
            new_question_text = st.text_area("", question_text, key=f"q{current_question}_text", height=100)
            
            full_question = questions[current_question]['question']
            options_text = '\n'.join(full_question.split('\n')[1:])
            questions[current_question]['question'] = f"{new_question_text}\n{options_text}"

            # Image handling
            uploaded_image = st.file_uploader("Upload an image for this question", type=["png", "jpg", "jpeg"], key=f"q{current_question}_image")
            if uploaded_image:
                image = Image.open(uploaded_image)
                max_width = 300
                width_percent = (max_width / float(image.size[0]))
                height_size = int((float(image.size[1]) * float(width_percent)))
                image = image.resize((max_width, height_size), Image.LANCZOS)
                st.image(image, caption="Uploaded Image", use_column_width=False)
                image_url = upload_image_to_cloudinary_2(Image.open(uploaded_image))
                questions[current_question]['image_url'] = image_url
            elif 'image_url' in questions[current_question]:
                st.image(questions[current_question]['image_url'], caption="Question Image", width=300)

            # Options handling
            st.write("Options:")
            options = questions[current_question]['options']
            selected_options = []
            for option, text in options.items():
                if option != 'correct_answers':
                    new_text = st.text_input(f"Option {option}", text, key=f"q{current_question}_opt_{option}")
                    options[option] = new_text
                    if st.checkbox(f"Correct: {option}", 
                                   value=option in options.get('correct_answers', []),
                                   key=f"q{current_question}_check_{option}"):
                        selected_options.append(option)

            # Update correct answers and flags
            questions[current_question]['options']['correct_answers'] = selected_options
            questions[current_question]['isAnswered'] = bool(selected_options)

            # Navigation and download buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if current_question > 0 and st.button("Previous"):
                    st.session_state.current_question = current_question - 1
                    st.rerun()
            with col3:
                if current_question < len(questions) - 1 and st.button("Next"):
                    st.session_state.current_question = current_question + 1
                    st.rerun()
            with col2:
                if st.button("Download Document"):
                    json_str = json.dumps(data, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    original_name = st.session_state.original_filename
                    new_name = f"corrected_{original_name}"
                    href = f'<a href="data:application/json;base64,{b64}" download="{new_name}">Download JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)

            # Metadata display
            st.write("---")
            st.write("Metadata:")
            display_metadata(data['metadata'])

            # Update session state
            st.session_state.data = data

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")



def display_metadata(metadata):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"School: {metadata['school']} ({metadata['school_type']})")
        st.write(f"Year: {metadata['exam_year']}")
    with col2:
        st.write(f"Subject: {metadata['subject_year']} - {metadata['semester']}")
        st.write(f"Topic: {metadata['topic']}")




############################
#CORRECTION 
############################

import streamlit as st
import json
import base64
import cloudinary
import cloudinary.uploader
from PIL import Image
import io

def upload_image_to_cloudinary_3(image):
    if image is not None:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        response = cloudinary.uploader.upload(buffer)
        return response['secure_url']
    return None

def show_correction_linking_page():
    if 'data' not in st.session_state:
        uploaded_file = st.file_uploader("Upload JSON file", type="json")
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.data = data
                st.session_state.original_filename = uploaded_file.name
                st.session_state.current_question = 0  # Initialize current question
                st.rerun()
            except Exception as e:
                st.error(f"Error loading JSON file: {str(e)}")
    
    if 'data' in st.session_state:
        try:
            data = st.session_state.data
            questions = data['content']['questions']

            # Sidebar for question navigation
            with st.sidebar:
                st.write("Questions:")
                for i, q in enumerate(questions):
                    question_text = q['question'].split('\n')[0][:30] + "..."  # Truncate for display
                    if st.button(f"Q{i+1}{' ✓' if 'explanation' in q else ''}", key=f"nav_{i}"):
                        st.session_state.current_question = i
                        st.rerun()

            current_question = st.session_state.get('current_question', 0)

            # Main content area
            st.progress((current_question + 1) / len(questions))
            st.write(f"Question {current_question + 1} of {len(questions)}")

            # Display the question
            st.markdown(f"### Question:")
            st.write(questions[current_question]['question'])

            # Display current explanation if it exists
            if 'explanation' in questions[current_question]:
                st.markdown("### Current Explanation:")
                if 'text' in questions[current_question]['explanation']:
                    st.write(questions[current_question]['explanation']['text'])
                if 'image_url' in questions[current_question]['explanation']:
                    st.image(questions[current_question]['explanation']['image_url'], caption="Explanation Image", width=300)

            # Add or edit explanation
            st.markdown("### Add/Edit Explanation:")
            explanation_text = st.text_area("Explanation Text", 
                                            value=questions[current_question].get('explanation', {}).get('text', ''),
                                            height=150)

            uploaded_image = st.file_uploader("Upload an explanation image", type=["png", "jpg", "jpeg"], key=f"q{current_question}_exp_image")
            if uploaded_image:
                image = Image.open(uploaded_image)
                st.image(image, caption="Uploaded Explanation Image", width=300)
                image_url = upload_image_to_cloudinary_3(image)
            else:
                image_url = questions[current_question].get('explanation', {}).get('image_url', None)

            if st.button("Save Explanation"):
                questions[current_question]['explanation'] = {
                    'text': explanation_text,
                    'image_url': image_url
                }
                st.success("Explanation saved successfully!")

            # Navigation buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if current_question > 0 and st.button("Previous"):
                    st.session_state.current_question = current_question - 1
                    st.rerun()
            with col3:
                if current_question < len(questions) - 1 and st.button("Next"):
                    st.session_state.current_question = current_question + 1
                    st.rerun()
            with col2:
                if st.button("Download Updated Document"):
                    json_str = json.dumps(data, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    original_name = st.session_state.original_filename
                    new_name = f"corrected_with_explanations_{original_name}"
                    href = f'<a href="data:application/json;base64,{b64}" download="{new_name}">Download JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)

            # Display metadata
            st.write("---")
            st.write("Metadata:")
            display_metadata(data['metadata'])

            # Update session state
            st.session_state.data = data

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def main():
    st.set_page_config(page_title="MEDQUEST Admin Tool", layout="wide")

    page = st.sidebar.selectbox("Select a page", ["Digitalization", "Answer Filling", "Correction Linking"])

    if page == "Digitalization":
        show_digitalization_page()
    elif page == "Answer Filling":
        show_answer_filling_page()
    elif page == "Correction Linking":
        show_correction_linking_page()

if __name__ == "__main__":
    main()


