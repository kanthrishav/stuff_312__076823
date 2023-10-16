import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error
from pygam import LinearGAM, s, l
import pandas as pd

# Generate sample data
np.random.seed(42)
X = np.random.rand(100000, 3)
y = np.sin(12 * X[:, 0]) + X[:, 1] - X[:, 2]**2 + np.random.randn(100000) * 0.2

# Step 1: Decouple the features using PCA
pca = PCA()
X_transformed = pca.fit_transform(X)

# Step 2 & 3: Identify individual relationships and select best transformation
def fit_transformations(x, y):
    # Linear
    lr = LinearRegression().fit(x.reshape(-1, 1), y)
    y_pred_linear = lr.predict(x.reshape(-1, 1))
    mse_linear = mean_squared_error(y, y_pred_linear)
    
    # Exponential
    lr_exp = LinearRegression().fit(x.reshape(-1, 1), np.log(y))
    y_pred_exp = np.exp(lr_exp.predict(x.reshape(-1, 1)))
    mse_exp = mean_squared_error(y, y_pred_exp)
    
    # Logarithmic
    lr_log = LinearRegression().fit(np.log(x.reshape(-1, 1)), y)
    y_pred_log = lr_log.predict(np.log(x.reshape(-1, 1)))
    mse_log = mean_squared_error(y, y_pred_log)
    
    # Polynomial
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(x.reshape(-1, 1))
    lr_poly = LinearRegression().fit(X_poly, y)
    y_pred_poly = lr_poly.predict(X_poly)
    mse_poly = mean_squared_error(y, y_pred_poly)
    
    # Select best transformation based on RMSE
    transformations = ['linear', 'exponential', 'logarithmic', 'polynomial']
    mse_values = [mse_linear, mse_exp, mse_log, mse_poly]
    
    best_transform = transformations[np.argmin(mse_values)]
    
    return best_transform

best_transformations = [fit_transformations(X_transformed[:, i], y) for i in range(X_transformed.shape[1])]

# Step 4: Formulate the GAM
terms = []
for i, transform in enumerate(best_transformations):
    if transform == 'linear':
        terms.append(l(i))
    else:
        terms.append(s(i))

print(f"Formulated GAM: f(x) = {' + '.join([str(term) for term in terms])}")

# Step 5: Train the GAM
gam = LinearGAM(terms).fit(X_transformed, y)

# Inference out the GAM equation
print("GAM equation:")
for i, term in enumerate(gam.terms):
    if term.isintercept:
        print(f"Intercept: {gam.coef_[i]:.3f}")
    else:
        # The coefficients of the smooth terms are more complex.
        # The smooth term for each feature is a weighted sum of spline basis functions.
        # The weights are the coefficients and are specific to the term.
        coef = gam.coef_[gam.terms[i].slice]
        print(f"Feature {i}: {coef}")

# Score
score = gam._estimate_r2(X_transformed, y)
print(f"R^2 Score: {score['explained_deviance']:.3f}")

# Export the PCA fit parameters and the GAM model for external inferencing
export_data = {
    "PCA_mean": pca.mean_.tolist(),
    "PCA_components": pca.components_.tolist(),
    "GAM_coefficients": gam.coef_.tolist(),
    "GAM_stats": gam.statistics_,
    "R2_score": score
}

with open("model_parameters.json", "w") as outfile:
    json.dump(export_data, outfile)
