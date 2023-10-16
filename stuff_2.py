import numpy as np
import pandas as pd
import json
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
from sklearn.linear_model import SGDRegressor
from sklearn.svm import SVR
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

def read_data(filename):
    df = pd.read_feather(filename)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    return X, y

def deep_feedforward_nn(X, y):
    param_grid = {
        'hidden_layer_sizes': [(50,), (100,), (50, 50)],
        'activation': ['relu', 'tanh', 'logistic'],
        'alpha': [0.0001, 0.001, 0.01]
    }
    model = GridSearchCV(MLPRegressor(max_iter=1000), param_grid, cv=5)
    model.fit(X, y)
    return model

def gaussian_process_regression(X, y):
    kernel = 1.0 * RBF(length_scale=1.0)
    param_grid = {
        'kernel': [kernel],
        'alpha': [1e-10, 1e-8, 1e-6]
    }
    model = GridSearchCV(GaussianProcessRegressor(), param_grid, cv=5)
    model.fit(X, y)
    return model

def stochastic_gradient_descent(X, y):
    param_grid = {
        'loss': ['squared_loss', 'huber'],
        'penalty': ['l2', 'l1', 'elasticnet'],
        'alpha': [0.0001, 0.001, 0.01],
    }
    model = GridSearchCV(SGDRegressor(), param_grid, cv=5)
    model.fit(X, y)
    return model

def svr_rbf(X, y):
    param_grid = {
        'C': [0.1, 1, 10],
        'epsilon': [0.1, 0.2, 0.3],
        'gamma': ['scale', 'auto']
    }
    model = GridSearchCV(SVR(kernel='rbf'), param_grid, cv=5)
    model.fit(X, y)
    return model

def gradient_boost(X, y):
    param_grid = {
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4, 5],
    }
    model = GridSearchCV(GradientBoostingRegressor(), param_grid, cv=5)
    model.fit(X, y)
    return model

def xgboost(X, y):
    param_grid = {
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4, 5],
    }
    model = GridSearchCV(XGBRegressor(), param_grid, cv=5)
    model.fit(X, y)
    return model

def lightgbm(X, y):
    param_grid = {
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4, 5],
    }
    model = GridSearchCV(LGBMRegressor(), param_grid, cv=5)
    model.fit(X, y)
    return model

def main(filename):
    X, y = read_data(filename)
    
    models = {
        "Deep Feedforward NN": deep_feedforward_nn,
        "Gaussian Process Regression": gaussian_process_regression,
        "Stochastic Gradient Descent": stochastic_gradient_descent,
        "SVR RBF": svr_rbf,
        "Gradient Boost": gradient_boost,
        "XGBoost": xgboost,
        "LightGBM": lightgbm
    }
    
    results = {}
    for name, model_func in models.items():
        print(f"Training {name}...")
        model = model_func(X, y)
        results[name] = {
            'best_params': model.best_params_,
            'score': model.best_score_
        }
    
    with open('model_results.json', 'w') as outfile:
        json.dump(results, outfile)
    
if __name__ == '__main__':
    import sys
    main(sys.argv[1])
