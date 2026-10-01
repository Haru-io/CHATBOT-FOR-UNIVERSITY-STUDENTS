# Dataset Analysis

Source: supplied `2783642.zip` e-learning FAQ dataset.

After robust parsing and relationship resolution:

- English questions: **427**
- Answer records: **79**
- Categories: **11**
- Train: **297**
- Validation: **65**
- Test: **65**

## Categories
- Documents
- Assignments
- Test/Questionnaire
- Contents
- Uploading
- Registration
- Aggregation
- Login
- Contact
- Students
- Basic Usage

## Baseline model result
A fixed-seed TF-IDF + Logistic Regression classifier produced approximately **67.69% accuracy** on the held-out 65-question test set. This is a baseline, not the final expected performance. The final project should compare this baseline with stronger sentence-embedding retrieval and a larger, university-specific evaluation set.

## Important limitation
The dataset describes an e-learning system (kibaco/Tokyo Metropolitan University context). It must not be presented as the user's university's official knowledge base. It is appropriate as a research/NLP baseline. Official university documents should be added separately for the deployed chatbot.
