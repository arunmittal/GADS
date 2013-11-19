#!/usr/bin/env python

from math import pi

import numpy as np
import pandas as pd
from patsy import *
from ggplot import *

from sklearn.linear_model import LinearRegression as LR
from sklearn.linear_model import LassoCV, RidgeCV, Lasso, Ridge
from sklearn.metrics import confusion_matrix
from sklearn import cross_validation
from sklearn.grid_search import GridSearchCV


TEST_PCT = 0.3
PENALTY='l2'
K = 10

def preprocess_data():
    sin_data = pd.DataFrame({'x' : np.linspace(0, 1, 101)})
    sin_data['y'] = np.sin(2 * pi * sin_data['x']) + np.random.normal(0, 0.1, 101)
    X = sin_data['x']
    y = sin_data['y']
    return X, y

def rmse(y,h):
    return(np.sqrt(np.mean(np.square(y-h))))

def test_rmse(X,y,test_pct=TEST_PCT):

    # Create Training / Test Split
    split_output = cross_validation.train_test_split(X, y, test_size=TEST_PCT)
    (X_train, X_test, y_train, y_test) = split_output

    # Fit Different Polynomials
    X_train_poly = dmatrix('C(X_train, Poly)')
    X_test_poly = dmatrix('C(X_test, Poly)')
    poly_degree = 30

    # Initialize results sets
    train_error, test_error,order = (np.zeros(poly_degree), np.zeros(poly_degree),
        np.zeros(poly_degree))

    for i in range(1, poly_degree + 1):

        #Set up the LR
        clf = LR()
        clf.fit(X_train_poly[:, 1: i + 1], y_train)

        #RMSE 
        train_error[i-1] = rmse(y_train,clf.predict(X_train_poly[:, 1:i+1]))
        test_error[i-1] =  rmse(y_test,clf.predict(X_test_poly[:, 1:i+1]))
        order[i-1] = i

    df = pd.DataFrame({'test error':test_error, 'training error':train_error,'poly_degree':order})
    df = pd.melt(df,id_vars= ['poly_degree'])
    g  = (ggplot(df, aes(x='poly_degree', y='value', color='variable')) +
            geom_line() +
            ylab('RMSE') +
            xlab('poly degree (model complexity)'))

    print g 
    plt.show(1)

def run_model(X, Y, test_pct=TEST_PCT, k=K): #penalty=PENALTY, k=K):
    """Perform train/test split, fit model and output results."""
    # Divide into test/training via cross_validation
    # A random split into training and test sets can be quickly computed with the train_test_split
    # helper function
    # http://scikit-learn.org/stable/modules/cross_validation.html
    split_output = cross_validation.train_test_split(X, Y, test_size=test_pct)
    (X_train, X_test, y_train, y_test) = split_output

    #Fit Different Polynomials
    X_train_poly = dmatrix('C(X_train, Poly)')
    X_test_poly = dmatrix('C(X_test, Poly)')

    #-------------------------------

    # Lasso L1
    lasso_model = LassoCV(cv = K, copy_X = True, normalize = False)
    lasso_fit = lasso_model.fit(X_train_poly[:, 1:11],y_train)
    alphas = lasso_fit.alphas_
    mse = np.zeros(len(alphas))
    for i, a in enumerate(alphas):
        clf = Lasso(alpha = a)
        clf.fit(X_train_poly[:, 1:11],y_train)
        predicted = clf.predict(X_test_poly[:, 1:11])
        mse[i] = rmse(predicted,y_test)

    df = pd.DataFrame({'mean_squared_error': mse, 'Lambda': -np.log(alphas)})
    # print (ggplot(df, aes('Lambda', 'mean_squared_error')) + geom_line() +
    #     ggtitle("Lasso Regression (L1)"))
    # plt.show(1)

    #-------------------------------

    # LassoCV
    # Testing 100 alphas (lambdas), 10-fold cross validation
    lasso_model = LassoCV(cv=K, n_alphas=100, normalize=False)
    lasso_fit = lasso_model.fit(X_train_poly[:, 1:11], y_train)
    df = pd.DataFrame({'Lambdas':-np.log(alphas),'RMSE':np.sqrt(lasso_fit.mse_path_).mean(axis = 1)})

    # print 'alpha = {0} (chosen to minimize RMSE)'.format(-np.log(lasso_fit.alpha_))
    # print ggplot(df,aes('Lambdas','RMSE'))+ geom_line() + ggtitle("Lasso CV")
    # plt.show(1)

    #-------------------------------

    # CrossValidation
    mse = np.zeros(len(alphas))
    for i, alpha in enumerate(alphas):
        clf = Lasso(alpha=alpha)
        mse[i] = cross_validation.cross_val_score(clf, X_train_poly[:, 1:11],
            y_train, cv=K, scoring='mean_squared_error').mean()

    df = pd.DataFrame({'Alphas': alphas, 'RMSE': mse})
    # print ggplot(df, aes('Alphas','RMSE'))+ geom_line() + ggtitle('Lasso')   
    # plt.show(1)

    # NOTE based on this plot, we may need to test larger values of alpha for this model!

    #-------------------------------

    # Ridge L2
    ridge_model = RidgeCV(cv=K)
    ridge_fit = ridge_model.fit(X_train_poly[:, 1: 11], y_train)
    alphas = ridge_fit.alphas
    mse = np.zeros(len(ridge_fit.alphas))
    for i, alpha in enumerate(alphas):
        clf = Ridge(alpha = alpha)
        clf.fit(X_train_poly[:, 1:11], y_train)
        predicted = clf.predict(X_test_poly[:, 1: 11])
        mse[i] = rmse(predicted, y_test)

    # print 'alphas = {0}'.format(alphas)
    # df = pd.DataFrame({'mean_squared_error': mse, 'Lambda': -np.log(alphas)})
    # print ggplot(df,aes('Lambda','mean_squared_error'))+geom_line() + ggtitle("Ridge Regression")
    df = pd.DataFrame({'mean_squared_error': mse, 'alpha': alphas})
    # print ggplot(df,aes('alpha','mean_squared_error'))+geom_line() + ggtitle("Ridge Regression")
    # plt.show(1)

    # NOTE this plot shows that the appropriate magnitude of lambda will be O(1)

    #-------------------------------

    # RidgeCV.
    alphas = np.array([0, 1, 10, 100])
    ridge_model = RidgeCV(cv=K, alphas=alphas)
    ridge_fit = ridge_model.fit(X_train_poly[:, 1:11], y_train)
    df = pd.DataFrame({'Alphas': ridge_fit.alphas_,
        'RMSE': np.sqrt(lasso_fit.mse_path_).mean(axis = 1)})

    print ggplot(df, aes('Lambdas','RMSE')) + geom_line() + ggtitle("Ridge")
    plt.show(1)
    return

    #-------------------------------

    # Cross-Validation Score. Loop through 'alphas' and calculate the CV score. 
    mse = np.zeros(len(alphas))
    for i, alpha in enumerate(alphas):
        clf = Ridge(alpha=alpha)
        mse[i] = cross_validation.cross_val_score(clf, X_train_poly[:, 1:11], y_train,
            cv=K, scoring='mean_squared_error').mean()

    df = pd.DataFrame({'Alphas':alphas,'RMSE':mse})
    print ggplot(df,aes('Alphas','RMSE'))+ geom_line() + ggtitle('Ridge')
    plt.show(1)

if __name__ == '__main__':

    X, y = preprocess_data()
    # test_rmse(X, y)
    run_model(X, y)
