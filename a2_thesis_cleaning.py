import pandas as pd
import time
import os

TEST_PATH = '~/thesis/1_validated_tests/'
SURVEY_FILE = TEST_PATH + 'validated_survey_03-18__01-47-55.csv'
SAVE_PATH = '2_cleaned_tests/'

filename_list = ['demographics', 'cleaned_survey_responses', 'no_leak_survey_responses']
survey_dict = {}


def clean_test(survey_file, gc=[1], turk=False):
    # Save the original survey file
    df = pd.read_csv(survey_file)
    cleaned_df = df[df['Progress'] == 100]

    # Save the demographic columns into its own csv
    demographics1 = cleaned_df.iloc[:, :14]
    demographics2 = cleaned_df.iloc[:, 245:]

    survey_dict[filename_list[0]] = pd.concat([demographics1, demographics2], axis=1)

    # Save the survey responses into their own csv, adding the ResponseId and the GC column
    survey_responses = cleaned_df.iloc[:, 14:245]
    survey_responses.insert(0, 'gc', cleaned_df['gc'])
    survey_responses.insert(0, 'ResponseId', cleaned_df['ResponseId'])
    survey_responses['Q2.5'].fillna('None of the above conditions.', inplace=True)

    # Delete the parenthetical text after each word in 2.5
    survey_responses['Q2.5'].replace(regex=True, inplace=True, to_replace=r' \([^)]*\)', value=r'')
    survey_dict[filename_list[1]] = survey_responses

    # Create a no-leak, response-only csv
    dropped_qs = ['Q2.1', 'Q2.2', 'Q2.4', 'Q2.6', 'Q2.7', 'Q2.8', 'Q2.9', 'Q2.10_1', 'Q2.11',
                  'Q2.12_1', 'Q3.49_1', 'Q3.48_1']

    survey_dict[filename_list[2]] = survey_responses.drop(dropped_qs, axis=1)

    for name in survey_dict:
        path = '{}{}{}.csv'.format(SAVE_PATH, name, time.strftime("%m-%d__%H-%M-%S", time.gmtime()))
        if not os.path.isfile(path):
            survey_dict[name].to_csv(path, index=False)


if __name__ == "__main__":
    clean_test(SURVEY_FILE, turk=True)
