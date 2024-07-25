# Scan2MCQ

A comprehensive platform for extracting, managing, and enhancing Multiple Choice Questions (MCQs) from scanned exams.

## Features

### 1. Digitalization Module (From Scan to Text)
- Upload scanned PDF files of MCQ exams
- Convert PDF pages to a structured JSON format
- Add metadata (school, exam year, subject, topic)
- Generate a unique ID for each exam
- Download the extracted content as a uniquely identified JSON file

### 2. Answer Filling and Verification Module
- Upload previously extracted JSON files for editing
- Review and edit extracted questions and options
- Select correct answers for each question
- Add or edit images associated with questions
- Navigate between questions for efficient review
- Track the status of answered questions
- Download updated JSON file with filled answers

### 3. Correction Linking Module
- Add explanations to MCQs
- Input text explanations for each question
- Upload supplementary images (e.g., screenshots from polycopy)
- Review and edit existing explanations
- Navigate easily between questions
- Download final JSON file with questions, answers, and explanations

## Key Feature
- Seamless navigation: Go back and forth between verification and correction modules as needed

## Getting Started

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/scan2mcq.git
   cd scan2mcq
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Configuration

1. Create a `.streamlit` folder in the project root if it doesn't exist.

2. Create a `secrets.toml` file inside the `.streamlit` folder with the following content:
   ```toml
   [openai]
   api_key = "your-openai-api-key"

   [cloudinary]
   cloud_name = "your-cloud-name"
   api_key = "your-cloudinary-api-key"
   api_secret = "your-cloudinary-api-secret"
   ```

3. Replace the placeholder values with your actual API keys and credentials.

### Running the Application

1. From the project root directory, run:
   ```
   streamlit run app.py
   ```

2. Open a web browser and go to `http://localhost:8501` to access the application.

### Usage

1. **Digitalization**: 
   - Navigate to the "Digitalization" page.
   - Upload a scanned PDF of MCQ exams.
   - Fill in the metadata and process the PDF.
   - Download the resulting JSON file.

2. **Answer Filling and Verification**:
   - Go to the "Answer Filling" page.
   - Upload the JSON file from the Digitalization step.
   - Review questions, select correct answers, and edit as needed.
   - Download the updated JSON file.

3. **Correction Linking**:
   - Access the "Correction Linking" page.
   - Upload the JSON file from the Answer Filling step.
   - Add explanations and supporting images for each question.
   - Download the final JSON file with all information.

Remember, you can switch between the Answer Filling and Correction Linking modules as needed to refine your work.

### Troubleshooting

If you encounter any issues:
- Ensure all API keys are correctly set in the `secrets.toml` file.
- Check that all required packages are installed.
- Verify that you're using a compatible Python version (3.7+).
