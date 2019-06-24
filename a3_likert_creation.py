import pandas as pd
import os
import datarobot as dr
# Save likert score code dictionary
CODE_DICT = {
    'Strongly disagree': 1,
    'Moderately disagree': 2,
    'Slightly disagree': 3,
    'Neither agree nor disagree': 4,
    'Slightly agree': 5,
    'Moderately agree': 6,
    'Strongly agree': 7
    }

# Save the columns which require reverse scoring!
reverse_scoring = pd.read_csv('reverse_columns.csv')['reverse'].tolist()

# Save a dictionary of the ranges of each section
section_dict = {'Automaticity': ['Q3.2_1', 'Q3.23_1'], 'Emotion Regulation': ['Q3.24_1', 'Q3.53_1'],
                'Impulse Control': ['Q3.54_1', 'Q3.71_1'], 'Reasoning': ['Q3.72_1', 'Q3.85_1'],
                'Moral Attribution': ['Q3.86_1', 'Q3.117_1'],
                'Motor Control': ['Q3.118_1', 'Q3.123_1'],
                'Perceptions of Agency': ['Q3.124_1', 'Q3.154_1'],
                'Personal Identity': ['Q3.159_1', 'Q3.163_1'],
                'Planning': ['Q3.164_1', 'Q3.178_1'], 'Risk Aversion': ['Q3.179_1', 'Q3.198'],
                'Time Persistence': ['Q3.199_1', 'Q3.219_1', 'Q3.211_1'],
                'Volition': ['Q3.220_1', 'Q3.223_1']}


# Replace these answers in the diagnosis responses
replace_diagnosis_list = ['(e.g. Generalized Anxiety Disorder, Phobias, Social Anxiety)',
                          '(e.g. Depression, Bipolar Disorder)', '(e.g. Anorexia, Bulimia)',
                          '(e.g. substance addiction, compulsive gambling)'
                          ]
# Save the paths
TEST_PATH = '2_cleaned_tests/'
SURVEY_FILE = '{}cleaned_survey_responses.csv'.format(TEST_PATH)

# survey_list = ['Anxiety disorders', 'Impulse Control', 'Mood disorders',
survey_list = ['Post-Traumatic Stress Disorder', 'Psychotic disorders', 'Eating disorders']

SURVEY_PATH = '~/thesis/2a_categorical_tests/'

likert_dict = {}


def create_likerts(survey, name):
    # Fix empty strings, etc.
    survey['Q2.5'].fillna('None of the above conditions.', inplace=True)
    for diagnosis in replace_diagnosis_list:
        survey['Q2.5'] = survey['Q2.5'].str.replace(diagnosis, '')

    # For each column in the survey, replace the answer with its corrolary, making sure to flip the
    # response score if the question is reverse scored
    for column in survey:
        for answer in CODE_DICT:
            if column in reverse_scoring:
                survey[column].replace(answer, 8 - CODE_DICT[answer], inplace=True)
            else:
                survey[column].replace(answer, CODE_DICT[answer], inplace=True)

    SAVE_PATH = '~/thesis/2b_likert_tests/'
    # if not os.path.isfile('{}{}_numeric_likert.csv'.format(SAVE_PATH, name)):
    survey.to_csv('{}{}_numeric_likert_encoded.csv'.format(SAVE_PATH, name), index=False)

    likert_file = pd.DataFrame()

    # For each section, sum the scores in that section
    for section in section_dict:
        _range = section_dict[section]
        likert_file[section] = survey.loc[:, _range[0]:_range[1]]
        

    # if not os.path.isfile('summed_likert_scores.csv'):
    # pd.concat([survey.iloc[:, 0:15], likert_file], axis=1).to_csv(
    #     '{}summed/{}_summed_likert_scores.csv'.format(SAVE_PATH, name), index=False)

    if not os.path.isfile('summed_likert_scores_matrix_only.csv'):
        likert_sum = pd.concat([survey.loc[:, ['Q2.5']], likert_file], axis=1)

        likert_sum.to_csv(
            '{}summed/{}_summed_likert_scores_matrix_only.csv'.format(SAVE_PATH, name), index=False)

    likert_dict[name] = likert_sum


def start_projects(survey, name):
    project = dr.Project.start(project_name='{} GC1 Likert'.format(name),
                               sourcedata=survey,
                               target='Q2.5',
                               worker_count=10)


if __name__ == "__main__":
    for survey in survey_list:
        df = pd.read_csv("{}gc1/{}_categorical_gc_1.csv".format(SURVEY_PATH, survey))
        create_likerts(df, survey)

    for survey in survey_list:
        start_projects(likert_dict[survey], survey)
