import pandas as pd
import time

# Likert encodings of responses
CODE_DICT = {
    'Strongly disagree': -3,
    'Moderately disagree': -2,
    'Slightly disagree': -1,
    'Neither agree nor disagree': 0,
    'Slightly agree': 1,
    'Moderately agree': 2,
    'Strongly agree': 3
    }

TEST_PATH = '0_diagnostic_tests/'
SURVEY_FILE = '{}'.format(TEST_PATH) + 'raw_diagnostic.csv'

# VALIDATION_CONSTANT is how far two validation questions can differ before they fail the test
# ALLOWED_VAL_FAILS is how many validation checks that can be failed before they fail the validation
VALIDATION_CONSTANT = 1
DIRECTION_CHECK_CONSTANT = 2
ALLOWED_VAL_FAILS = 2

# Save the raw diagnostic test, and drop the 2 secondary index rows
unvalidated_results = pd.read_csv(SURVEY_FILE)
unvalidated_results.drop(unvalidated_results.index[[0, 1]], inplace=True)

# Also drop useless columns like name, email, and hidden obsolete questions
unvalidated_results.drop(['RecipientFirstName', 'RecipientLastName', 'RecipientEmail',
                          'ExternalReference', 'Q3.156', 'Q3.157_1', 'Q3.158_1', 'Q3.155'],
                          axis=1, inplace=True)

# Create a deep copy of the unvalidated results for manipulation
survey = unvalidated_results.copy()

# Replace each text answer with the likert scale number
for answer in CODE_DICT:
    survey.replace(answer, CODE_DICT[answer], inplace=True)

# A dictionary of the validation questions, and whether they are positive or negative valence in
# what they're validating (i.e. responses to positive q's should be reversed from negative ones)
pos_validation_questions = {1: ['Q3.8_1'], 2: ['Q3.21_1'], 3: ['Q3.32_1'],
                            4: ['Q3.73_1'], 5: ['Q3.164_1', 'Q3.167_1'],
                            6: ['Q3.63_1', 'Q3.174_1']}

neg_validation_questions = {1: ['Q3.10_1'], 2: ['Q3.22_1'], 3: ['Q3.42_1'], 4: ['Q3.83_1'],
                            5: ['Q3.178_1'], 6: []}

# Initialize the list of validated questions
validated_questions = {}


def check_validation(column1, column2, check_type_list=['opposite']):
    """
    Takes one column of responses to a validation question, and checks them against another column
    depending on how the check is called
    """

    # If the questions are supposed to opposite, the validation score will be the abs of their sum
    opposite = abs(column1 + column2)

    # If they're supposed to be the same, the score is the absolute value of their difference
    same = abs(column1 - column2)

    # A direction check weights their response's absolute distance less than whether the valence
    # of their response reverses (i.e. "strongly agree" vs. "slightly agree" is an acceptable
    # change, but "slightly agree" to "slightly disagree" is not, despite being the same distance)
    dir_check = (column1 * column2 >= 0) & (abs(column1 - column2) <= DIRECTION_CHECK_CONSTANT)

    # This dictionary stores the validation columns, ready to be returned as the result depending on
    # the desired checks
    check_dict = {'opposite': opposite <= VALIDATION_CONSTANT, 'same': same <= VALIDATION_CONSTANT,
                  'direction_check': dir_check}

    # Store the first item on the list as the result
    result = check_dict[check_type_list[0]]

    # If there is a larger list of checks, then and-chain them to make sure it
    # passes all desired validation checks
    for type_ in range(1, len(check_type_list)):
        result &= check_dict[check_type_list[type_]]
    return result, opposite, same, dir_check


def validation(unvalidated_results):
    """
    Perform the full validation! Go through each of the 7 validation sets
    """
    # Iterate through each of the validation question groups
    for i in range(1, 7):
        # List of the validation questions
        val_questions = [pos_validation_questions[i], neg_validation_questions[i]]

        # For the validation questions 1-4, validation score is just a simple opposite check
        if i < 5:
            validation_score = check_validation(
                survey[val_questions[0][0]], survey[val_questions[1][0]])

            unvalidated_results['Validation #{}'.format(i)] = validation_score[0]

            unvalidated_results['Validation distance #{}'.format(i)] = validation_score[1]

        # For val question 5, first perform a same check on the positive questions
        elif i == 5:
            validation_score = check_validation(
                survey[val_questions[0][0]], survey[val_questions[0][1]], ['same'])

            survey['Validation #{}'.format(i)] = validation_score[0]
            unvalidated_results['Validation #{}'.format(i)] = validation_score[0]

            unvalidated_results['Positive validation distance #{}-0'.format(i)] = \
                validation_score[2]

            index = 1

            # Then, go through each positive question and check it against the negative question
            for pos_question in val_questions[0]:
                validation_score = check_validation(survey[pos_question],
                                                    survey[val_questions[1][0]])

                survey['Validation #{}'.format(i)] &= validation_score[0]

                unvalidated_results['Positive validation distance #{}-{}'.format(i, index)] = \
                    validation_score[1]
                index += 1

            unvalidated_results['Validation #{}'.format(i)] = survey['Validation #{}'.format(i)]

        # For question 6, perform only a similarity test
        elif i == 6:
            validation_score = check_validation(survey[val_questions[0][0]],
                                                survey[val_questions[0][1]], ['same'])

            unvalidated_results['Validation #{}'.format(i)] = validation_score[0]

            unvalidated_results['Positive validation distance #{}'.format(i)] = validation_score[2]

    # Create list of validation columns
    list_of_val_columns = ['Validation #{}'.format(i) for i in range(1, 7)]

    # Create column that tracks the failed validation count for each subject
    unvalidated_results['Failed_Validation_Count'] = 6 - unvalidated_results[list_of_val_columns]\
        .select_dtypes(include=['bool']).sum(axis=1)

    # Check if they failed the tests
    print(len(unvalidated_results[unvalidated_results.Failed_Validation_Count >
          ALLOWED_VAL_FAILS].index))
    print(len(unvalidated_results[unvalidated_results['gc'].isin([1])][unvalidated_results.Failed_Validation_Count <=
          ALLOWED_VAL_FAILS].index))
    results = unvalidated_results[unvalidated_results.Failed_Validation_Count <= ALLOWED_VAL_FAILS]
    return results


if __name__ == "__main__":
    validated_results = validation(unvalidated_results)
    validated_results.to_csv('~/thesis/1_validated_tests/validated_survey_{}.csv'.format(
        time.strftime("%m-%d__%H-%M-%S", time.gmtime())), index=False)
