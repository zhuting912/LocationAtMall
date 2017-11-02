# -*- coding: utf-8 -*-
# @Date    : 2017/11/2
# @Author  : hrwhisper

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import xgboost as xgb
from sklearn import preprocessing
from xgboost import XGBClassifier

from common_helper import ModelBase, XXToVec
from parse_data import read_mall_data, read_train_join_mall, read_test_data
from use_location2 import LocationToVec2
from use_price import PriceToVec
from use_strong_wifi import WifiStrongToVec
from use_wifi import WifiToVec
from use_wifi_kstrong import WifiKStrongToVec


class MyXGBoost(object):
    def __init__(self, param, number_round, n_jobs=4):
        self.param = param
        self.number_round = number_round
        self.bst = None
        self.label_encoder = preprocessing.LabelEncoder()
        self.n_jobs = n_jobs

    def fit(self, X_train, y_train, X_test=None, y_test=None):
        vals = set(list(y_train.values))
        if y_test is not None:
            vals = vals | set(list(y_test.values))

        self.label_encoder.fit(np.array(list(vals)))
        y_train = self.label_encoder.transform(y_train)
        self.param['num_class'] = len(self.label_encoder.classes_)

        X_train = xgb.DMatrix(X_train, label=y_train, nthread=self.n_jobs)
        if X_test is not None:
            y_test = self.label_encoder.transform(y_test)
            X_test = xgb.DMatrix(X_test, label=y_test, nthread=self.n_jobs)

        eval_list = [(X_train, 'train')] + ([] if X_test is None else [(X_test, 'test')])
        self.bst = xgb.train(self.param, X_train, self.number_round, eval_list)
        return self

    def predict(self, X):
        X = xgb.DMatrix(X, nthread=self.n_jobs)
        predicted = self.bst.predict(X)
        return self.label_encoder.inverse_transform(predicted.astype(int))


class UseMyXgboost(ModelBase):
    def _get_classifiers(self):
        return {
            'MyXgboost':
                MyXGBoost(
                    {
                        'booster': 'gbtree',
                        'objective': 'multi:softmax',
                        'eta': 0.1,
                        'max_depth': 10,
                        'eval_metric': 'merror',
                        'seed': 1080,  # 1024 1412
                        'missing': -999,
                        'silent': 1,
                    }
                    , number_round=100)
        }

    @staticmethod
    def trained_and_predict_location(cls, X_train, y_train, X_test, y_test=None):
        print('fitting2....')
        cls = cls.fit(X_train, y_train, X_test, y_test)
        print('predict....')
        predicted = cls.predict(X_test)
        return predicted


def train_test():
    XGBClassifier()
    task = UseMyXgboost()
    task.train_test([LocationToVec2(), WifiToVec(), WifiStrongToVec(), WifiKStrongToVec(), PriceToVec()])
    task.train_and_on_test_data([LocationToVec2(), WifiToVec(), WifiStrongToVec(), WifiKStrongToVec(), PriceToVec()])


if __name__ == '__main__':
    train_test()