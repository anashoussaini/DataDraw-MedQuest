# MEDQUEST Admin Tool User Guide

## Table of Contents
1. Introduction
2. Understanding the Drive Structure
3. Accessing the Tool
4. Creating an Exam
   4.1 Filling in Metadata
   4.2 Adding Questions
   4.3 Uploading Images
   4.4 Setting Correct Answers
5. Visualizing an Exam
6. Downloading the Exam JSON
7. Tips and Best Practices

## 1. Introduction

The MEDQUEST Admin Tool is designed to help you digitalize and manage medical exams. This guide will walk you through the process of using the tool effectively, starting from understanding the drive structure to creating and managing exams.

## 2. Understanding the Drive Structure

Before using the tool, it's crucial to understand how the exam documents are organized in the drive. This structure directly informs how you'll fill in the metadata for each exam.

Drive Structure:
```
Final Directory
├── Rabat
│   └── S1
│       └── Exam Folders
└── Marrakech
    └── S1
        └── Exam Folders
```

Exam Folder Naming Convention:
Example: `E1_50Q_FEB22_AOD`

- E1: Exam number (E1, E2, E3, E4, or E5)
- 50Q: Number of questions in the document
- FEB22: Date (Month and Year)
- AOD: Answer on Document
  - Sometimes this can be AA, which means the answers are on another document

This structure and naming convention will guide you in filling out the metadata when digitalizing exams.

## 3. Accessing the Tool

Open your web browser and navigate to the MEDQUEST Admin Tool URL provided by your administrator.

## 4. Creating an Exam

### 4.1 Filling in Metadata

When you create a new exam, you'll need to fill in metadata based on the drive structure and exam folder name:

1. School: Select either "Rabat" or "Marrakech" based on the top-level folder.
2. Year of Subject: This corresponds to the semester folder (e.g., "First Year" for S1 or S2).
3. Semester: Select the appropriate semester (S1, S2, S3, etc.) from the folder name.
4. Topic: Select from the provided list of topics based on the exam content.
5. Exam Variable: Enter the number from the exam folder name (e.g., 1 for E1, 2 for E2, etc.).
6. Year of Exam: 
   - If known, select the year from the folder name (e.g., 22 for 2022 in FEB22).
   - If not present in the folder name, select "UNK".
7. Month of Exam:
   - If known, select the month from the folder name (e.g., "February" for FEB).
   - If not present in the folder name, select "UNK".

Additional Notes:
- The number of questions (e.g., 50Q) is for your reference when inputting questions.
- "AOD" or "AA" in the folder name indicates whether answers are in the same document or a separate one.

Click "Submit Metadata" when you're done.

### 4.2 Adding Questions

1. After submitting metadata, specify the number of questions based on the folder name (e.g., 50 for 50Q).
2. For each question:
   a. Enter the question text in the "Question Text" box.
   b. In the "Options" box, enter one option per line (max 5 lines for options A through E).
   c. The tool will automatically parse your options into separate fields.

### 4.3 Uploading Images

1. If a question has an associated image, click on "Upload an image for question #X".
2. Select the image file from your computer.
3. The image will be uploaded and associated with the question automatically.

### 4.4 Setting Correct Answers

1. In the "Correct Answer(s)" field, enter the letter(s) corresponding to the correct option(s).
2. For multiple correct answers, enter them without spaces (e.g., "ABC" for options A, B, and C being correct).
3. The tool will automatically validate and display the selected correct answers.

## 5. Visualizing an Exam

1. Navigate to the "Visualize Test" page using the sidebar.
2. Upload a previously created exam JSON file.
3. You can now view the exam metadata and navigate through questions.

## 6. Downloading the Exam JSON

1. After creating your exam, click the "Generate Exam JSON" button at the bottom of the page.
2. Your browser will download a JSON file containing all the exam data.
3. Save this file back to the appropriate folder in the drive structure for record-keeping.

## 7. Tips and Best Practices

- Always refer to the original exam folder name when filling in metadata to ensure accuracy.
- Use the non-JSON input method for easier image handling and automatic parsing.
- Double-check that the number of questions matches the "XQ" in the folder name.
- If the answers are in a separate document (AA), make sure to cross-reference when inputting correct answers.
- Regularly save your work by generating and downloading the JSON file.
- When uploading the JSON file back to the drive, ensure it's in the correct school and semester folder.
