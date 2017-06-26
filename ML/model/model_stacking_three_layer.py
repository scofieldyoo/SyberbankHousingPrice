#!/usr/local/miniconda2/bin/python
# _*_ coding: utf-8 _*_

"""
@author: MarkLiu
@time  : 17-6-24 下午12:01
"""
import os
import sys

module_path = os.path.abspath(os.path.join('..'))
sys.path.append(module_path)

import pandas as pd
import numpy as np
# remove warnings
import warnings

warnings.filterwarnings('ignore')

from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.linear_model import LassoCV,LassoLarsCV, ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import make_scorer, mean_squared_error

from model_stack.model_wrapper import XgbWrapper, SklearnWrapper, GridCVWrapper
from model_stack.model_stack import TwoLevelModelStacking, ThreeLevelModelStacking

# my own module
from features import data_utils
from conf.configure import Configure

def RMSLE_(y_val, y_val_pred):
    return np.sqrt(np.mean((np.log(y_val+1)-np.log(y_val_pred+1))**2))
RMSLE = make_scorer(RMSLE_, greater_is_better=False) 

def RMSE_(y_val, y_val_pred):
    return np.sqrt(np.mean((y_val-y_val_pred)**2))
RMSE = make_scorer(RMSE_, greater_is_better=False)

train, test, macro = data_utils.load_data()
train.fillna(0, inplace=True)
test.fillna(0)
mult = .969

train['price_doc'] = train["price_doc"] * mult + 10
# train['price_doc'] = np.log1p(train['price_doc'])
y_train = train['price_doc']
id_train = train['id']
train.drop(['id', 'price_doc'], axis=1, inplace=True)
submit_ids = test['id']
test.drop(['id'], axis=1, inplace=True)

# 合并训练集和测试集
conbined_data = pd.concat([train[test.columns.values], test])
conbined_data.drop(['timestamp'], axis=1, inplace=True)
print "conbined_data:", conbined_data.shape

# Deal with categorical values
for c in conbined_data.columns:
    if conbined_data[c].dtype == 'object':
        lbl = preprocessing.LabelEncoder()
        lbl.fit(list(conbined_data[c].values))
        conbined_data[c] = lbl.transform(list(conbined_data[c].values))

del conbined_data['school_education_centers_raion_ratio_dis']
del conbined_data['preschool_education_centers_raion_ratio_dis']
del conbined_data['sport_objects_raion_ratio_dis']
del conbined_data['additional_education_raion_ratio_dis']
del conbined_data['0_6_all_vs_preschool_quota_dis']

scaler = StandardScaler()
conbined_data = scaler.fit_transform(conbined_data)

train = conbined_data[:train.shape[0], :]
test = conbined_data[train.shape[0]:, :]

test_size = (1.0 * test.shape[0]) / train.shape[0]
print "submit test size:", test_size

# et_params = {
#     'n_jobs': 16,
#     'n_estimators': 100,
#     'max_features': 0.5,
#     'max_depth': 12,
#     'min_samples_leaf': 2,
# }

# rf_params = {
#     'n_jobs': 16,
#     'n_estimators': 100,
#     'max_features': 0.2,
#     'max_depth': 12,
#     'min_samples_leaf': 2,
# }

# xgb_params = {
#     'eta': 0.05,
#     'max_depth': 5,
#     'subsample': 0.7,
#     'colsample_bytree': 0.7,
#     'objective': 'reg:linear',
#     'eval_metric': 'rmse',
#     'silent': 1
# }

# rd_params = {
#     'alpha': 10
# }

# ls_params = {
#     'alpha': 0.005
# }

# SEED = 0

# xg = XgbWrapper(seed=SEED, params=xgb_params)
# et = SklearnWrapper(clf=ExtraTreesRegressor, seed=SEED, params=et_params)
# rf = SklearnWrapper(clf=RandomForestRegressor, seed=SEED, params=rf_params)
# rd = SklearnWrapper(clf=Ridge, seed=SEED, params=rd_params)
# ls = SklearnWrapper(clf=Lasso, seed=SEED, params=ls_params)

# level_1_models = [xg, et, rf, rd, ls]

rf_params1 = {'max_depth':6, 'n_jobs':-1, 'n_estimators':500, 'max_features':.95}

rf_params2 = {'max_depth':12, 'min_samples_leaf':2, 'n_jobs':-1, 'n_estimators':100, 'max_features':.2}

et_params1 = {'min_samples_leaf':2, 'max_depth':12, 'n_jobs':-1, 'n_estimators':100, 'max_features':.5}

et_params2 = {'min_samples_leaf':2, 'max_depth':12, 'n_jobs':-1, 'n_estimators':100, 'max_features':.5}

gb_params1 = {'learning_rate':0.02, 'n_estimators':500, 'min_samples_leaf':70, 'min_samples_split':200, 
              'max_features':'sqrt', 'max_depth':6, 'subsample':0.85}

gb_params2 = {'n_estimators':500, 'max_features':15, 'max_depth':6, 'learning_rate':0.05, 'subsample':0.8}

xgb_params1 = {'learning_rate':.05, 'subsample':.95, 'max_depth':4, 'min_child_weight':4, 'n_estimators':620, 
              'colsample_bytree':0.95, 'gamma':.4}

xgb_params2 = {'learning_rate':.05, 'subsample':.7, 'max_depth':5, 'n_estimators':309, 'colsample_bytree':0.7}

lcv_params = {'alphas' : [1, 0.1, 0.001, 0.0005]}

rd_params = {'alpha': 10}

ls_params = {'alpha': 0.005}

eln_params = {}

knr_params1 = {'n_neighbors' : 5}

knr_params2 = {'n_neighbors' : 10}

SEED = 0

level_1_models = [XgbWrapper(seed=SEED, params=xgb_params1), XgbWrapper(seed=SEED, params=xgb_params2)]

#level_1_models = [SklearnWrapper(clf=RandomForestRegressor,seed=SEED,params={}), #SklearnWrapper(clf=GradientBoostingRegressor,seed=SEED,params={})]
                
#level_1_models = level_1_models + [SklearnWrapper(clf=KNeighborsRegressor,  params=knr_params1),
                 #SklearnWrapper(clf=KNeighborsRegressor,  params=knr_params2)]

params_list = [rf_params1, rf_params2, et_params1, et_params2, gb_params1, gb_params2, 
               lcv_params, rd_params, ls_params, eln_params]

func_list = [RandomForestRegressor, RandomForestRegressor, ExtraTreesRegressor, ExtraTreesRegressor, 
             GradientBoostingRegressor, GradientBoostingRegressor, LassoCV, Ridge, Lasso, ElasticNet]
#level_1_models = level_1_models + \
    #list(map(lambda x: SklearnWrapper(clf=x[1], seed=SEED, params=x[0]), zip(params_list, func_list)))

level_2_models = [SklearnWrapper(clf=ExtraTreesRegressor,seed=SEED,params={}),
                 XgbWrapper(seed=SEED, params=xgb_params1)]
    
# xgb_params = {
#     'eta': 0.05,
#     'max_depth': 5,
#     'subsample': 0.7,
#     'colsample_bytree': 0.7,
#     'objective': 'reg:linear',
#     'eval_metric': 'rmse',
#     'silent': 1
# }

#stacking_model = XgbWrapper(seed=SEED, params=xgb_params)
stacking_model = GridCVWrapper(Ridge, seed=SEED, cv_fold=5, params={}, scoring=RMSLE, param_grid = {
            'alpha': [1e-3,5e-3,1e-2,5e-2,1e-1,0.2,0.3,0.4,0.5,0.8,1e0,3,5,7,1e1]})

model_stack = TwoLevelModelStacking(train, y_train, test, level_1_models, stacking_model=stacking_model, stacking_with_pre_features=False, n_folds=5, random_seed=0, isLog1p=False)

#model_stack = ThreeLevelModelStacking(train, y_train, test, level_1_models, #level_2_models, 
#stacking_model=stacking_model, stacking_with_pre_features=False, n_folds=5, #random_seed=0, isLog1p=False)

predicts, score = model_stack.run_stack_predict()

df_sub = pd.DataFrame({'id': submit_ids, 'price_doc': predicts})
df_sub.to_csv(Configure.submission_path+str(score)+'.csv', index=False)