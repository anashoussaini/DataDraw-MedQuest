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
            
            # Check if the content has the expected structure
            if not isinstance(content, dict) or "questions" not in content:
                raise ValueError("The JSON file does not have the expected structure. It should contain a 'questions' key at the top level.")
            
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
        except ValueError as ve:
            st.error(f"Error in JSON structure: {str(ve)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")


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

def upload_image_to_cloudinary(image):
    if image is not None:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        response = cloudinary.uploader.upload(buffer)
        return response['secure_url']
    return None

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
                correct_options = []
                for option in ['A', 'B', 'C', 'D', 'E']:
                    if st.checkbox(option, key=f"q{i}_correct_{option}"):
                        correct_options.append(option)
                options['correct_answers'] = correct_options

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

