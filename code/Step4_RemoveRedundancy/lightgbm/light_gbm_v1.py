# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 10:01:36 2017

@author: Raymond
"""

import pandas as pd
import sklearn.metrics as mt

from faron_validator import CrossValidatorMT
from model_helpers import LgbValidator
import parameter_dicts as params


CURRENT_PARAMS = params.parameters_v1
TRAIN_PATH = '/ssd-1/clinical/clinical-abbreviations/data/full_train.csv'
TEST_PATH = '/ssd-1/clinical/clinical-abbreviations/data/full_test.csv'

def load_data(filename):
    """Load train from file and parse out target"""

    train_dataframe = pd.read_csv(filename, na_filter=False).drop("Unnamed: 0", axis=1)
    target = train_dataframe['target']
    train_dataframe.drop('target', axis=1, inplace=True)

    return train_dataframe, target


def run_lgb_models(train_df, target, test_df=None):
    """Run K-folded light GBM model"""

    clf = CrossValidatorMT(
        clf=LgbValidator,
        clf_params=CURRENT_PARAMS,
        nfolds=5,
        stratified=False,
        shuffle=True,
        seed=2020,
        regression=False,
        nbags=1,
        metric=mt.log_loss,
        average_oof=True,
        verbose=True
    )

    clf.run_cv(train_df, target, x_test=test_df)
    return clf


if __name__ == "__main__":

    train_df, target = load_data(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH, na_filter=False).drop("Unnamed: 0", axis=1)
    print(train_df.columns, test_df.columns)
    clf = run_lgb_models(train_df, target, test_df)

    thresholds = [.3, .4, .5, .6, .7]
    for threshold in thresholds:
        print('F1 at {}: '.format(threshold), mt.f1_score(target, clf.oof_predictions[0] > threshold))
        print('Recall at {}: '.format(threshold), mt.recall_score(target, clf.oof_predictions[0] > threshold))
        print('Precision at {}: '.format(threshold), mt.precision_score(target, clf.oof_predictions[0] > threshold))

    RAW_PATH = '/ssd-1/clinical/clinical-abbreviations/data/raw_train.csv'
    raw_data = pd.read_csv(RAW_PATH, na_filter=False)
    raw_data['target'] = target
    raw_data['predictions'] = clf.oof_predictions[0].reshape(-1,)
    raw_data.to_csv('/ssd-1/clinical/clinical-abbreviations/data/prediction_check.csv')

    test_preds = clf.oof_test
    print('Test shape: ', test_preds.shape)
    test_preds = pd.DataFrame(test_preds, columns=["test_preds"])
    test_preds.to_csv('/ssd-1/clinical/clinical-abbreviations/data/oof_test.csv', index=False)