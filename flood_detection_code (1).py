# -*- coding: utf-8 -*-
"""flood detection code

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1adqeHHOnJCiaI9yNl2SIMY_0eROaV9lS
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# !pip install catboost
# !pip install ppscore
# !pip install pandas === 1.5.3
# !pip install --upgrade --force-reinstall numpy pandas
# !pip install --force-reinstall numpy==1.23.5
#

# Data manipulation
#==============================================================================
import pandas as pd
import numpy as np

# Data visualization
#==============================================================================
import matplotlib.pyplot as plt
import seaborn as sns

# Stats
#==============================================================================
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
import ppscore as pps

# Data preprocessing
#==============================================================================
from sklearn.model_selection import train_test_split as tts
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
# Models
#==============================================================================
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# Metrics
#==============================================================================
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import confusion_matrix, classification_report

# tqdm
#==============================================================================
from tqdm.notebook import tqdm_notebook

# warnings
#==============================================================================
import warnings
warnings.filterwarnings('ignore')

import pandas as pd

# Corrected file path with proper function syntax
data = pd.read_excel("/content/MLPC_Flood_Dataset.xlsx")

# Display the first 5 rows of the dataset
data.head()

rows, cols = data.shape[0], data.shape[1]

print(f'rows: {rows}')
print(f'cols: {cols}')

print("##" * 30)
print(" " * 17, "Data set Information")
print("##" * 30)
print(data.info())

print(data.duplicated().sum())

df_null_values = data.isnull().sum().to_frame().rename(columns = {0:'count'})
df_null_values['%'] = (df_null_values['count'] / len(data)) * 100
df_null_values = df_null_values.sort_values('%', ascending = False)
df_null_values.style.background_gradient(cmap = 'Spectral')

numerical_features = data.select_dtypes(include = ['int', 'float']).columns.to_list()

print(f'Total Numerical features = {len(numerical_features)}')

categorical_feature = data.select_dtypes(include = ['object', 'category']).columns.to_list()

print(f'Total Categorical feature = {len(categorical_feature)}')

sns.set_style("darkgrid")

colors = sns.color_palette(palette = 'dark', n_colors = len(numerical_features))

fig,axs = plt.subplots(nrows = 3, ncols = 3, figsize = (12, 9))
axs = axs.flat

for i,num_feat in enumerate(numerical_features):
    sns.kdeplot(data, x = num_feat, fill = True, color = colors[i], ax = axs[i])
    sns.histplot(data, x = num_feat,bins = 30, stat = 'density', fill = False, color = colors[i], ax = axs[i])
    axs[i].set_xlabel("")
    axs[i].set_title(num_feat, fontsize = 10, fontweight = 'bold', color = 'darkblue')

fig.suptitle("Distribution of Variables", fontsize = 12, fontweight = 'bold', color = 'black')
fig.tight_layout()
fig.show()

fig,axs = plt.subplots(nrows = 3, ncols = 3, figsize = (12, 9))
axs = axs.flat

for i,num_feat in enumerate(numerical_features):
    sm.qqplot(data[num_feat], line = 'q', ax = axs[i], lw = 2.1)
    axs[i].set_title(num_feat, fontsize = 10, fontweight = 'bold', color = 'darkblue')

fig.suptitle("Q-Q Plots", fontsize = 12, fontweight = 'bold', color = 'black')
fig.tight_layout()
fig.show()

data[numerical_features].describe().T

plt.style.use('ggplot')

def autopct_fun(abs_values):
    gen = iter(abs_values)
    return lambda pct: f"{pct:.1f}%\n({next(gen)})"

fig,ax = plt.subplots(figsize = (6,3.4))

df_class = data['SUSCEP'].value_counts().to_frame()
labels = df_class.index.to_list()
values = df_class.iloc[:,0].to_list()
ax.pie(x = values, labels = labels, autopct=autopct_fun(values), shadow = True, textprops = {'color':'white', 'fontsize':8, 'fontweight':'bold'})
ax.legend(labels, loc = 'best')
ax.set_title('SUSCEP', fontsize = 15, fontweight = "bold", color = "black")
ax.axis('equal')
fig.show()

plt.style.use('default')
corr_matrix_spearman = data[numerical_features].corr(method = 'spearman')
mask = np.triu(np.ones_like(corr_matrix_spearman, dtype = bool))

fig,ax = plt.subplots(figsize = (9, 6))
sns.heatmap(corr_matrix_spearman,
            cmap = 'Spectral',
            annot = True,
            annot_kws = {'fontsize':6.5, 'fontweight':'bold'},
            linewidths = 1.5,
            square = True,
            mask = mask,
            ax = ax)
ax.set_title("Correlation Matrix", fontsize = 12, fontweight = 'bold', color = 'darkblue')
fig.show()

df_vif = {}

for i,num_feat in enumerate(numerical_features):
    df_vif[num_feat] = variance_inflation_factor(data[numerical_features].dropna(), i)

df_vif = pd.DataFrame.from_dict(df_vif, orient = 'index').rename(columns = {0:'vif'})
df_vif = df_vif.sort_values('vif', ascending = False)
df_vif.style.background_gradient(cmap = 'coolwarm')

X = data.drop('SUSCEP', axis = 1)
y = data['SUSCEP']

SEED = 1234

X_train, X_test, y_train, y_test = tts(X,
                                       y,
                                       test_size = 0.3,
                                       random_state = SEED)

LABELS = ['No_Flood', 'Low', 'Moderate', 'High', 'Very_High']
label2id = dict(zip(LABELS, range(len(LABELS))))
label2id

y_train = y_train.map(label2id)
y_test = y_test.map(label2id)

y_train.value_counts()

y_test.value_counts()

X_train.isnull().sum()

X_test.isnull().sum()

imputer = SimpleImputer(strategy = 'median')
X_train_imputed = imputer.fit_transform(X_train)
X_test_imputed = imputer.transform(X_test)

# We visualize how our variable looked after imputation.
fig,ax = plt.subplots(figsize = (5,3.5))
sns.kdeplot(X_train_imputed[:,2], ax = ax)
sns.kdeplot(data['Slope'], ax = ax)
plt.show()

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_imputed)
X_test_scaled = scaler.transform(X_test_imputed)

lr = LogisticRegression(multi_class = 'multinomial', max_iter = 1000, random_state = SEED, n_jobs = -1)
lr.fit(X_train_scaled, y_train)

y_pred_train_base = lr.predict(X_train_scaled)
y_pred_test_base = lr.predict(X_test_scaled)

print(f'Balanced Accuracy Train: {balanced_accuracy_score(y_train, y_pred_train_base)}')
print(f'Balanced Accuracy Test: {balanced_accuracy_score(y_test, y_pred_test_base)}')

# We define the candidate models, we choose the model that best generalizes.
clf1 = RandomForestClassifier(random_state = SEED, n_jobs = -1)
clf2 = ExtraTreesClassifier(bootstrap = True, n_jobs = -1, random_state = SEED)
clf3 = XGBClassifier(random_state = SEED)
clf4 = LGBMClassifier(random_state = SEED, n_jobs = -1, verbosity = -1)
clf5 = CatBoostClassifier(random_state = SEED, verbose = 0)

MODELS = [clf1, clf2, clf3, clf4, clf5]

# Training!!!
#=====================================================================
accuracy_train = {}
accuracy_test = {}

for model in tqdm_notebook(MODELS):
    name = type(model).__name__
    model.fit(X_train_imputed, y_train)
    y_pred_train = model.predict(X_train_imputed)
    y_pred_test = model.predict(X_test_imputed)
    accuracy_train[name] = balanced_accuracy_score(y_train, y_pred_train)
    accuracy_test[name] = balanced_accuracy_score(y_test, y_pred_test)
    print(f'* {name} finished.')

plt.style.use('ggplot')
metric_train = pd.DataFrame.from_dict(accuracy_train, orient = 'index')
metric_train = metric_train.rename(columns = {0:'Train'})

metric_test = pd.DataFrame.from_dict(accuracy_test, orient = 'index')
metric_test = metric_test.rename(columns = {0:'Test'})

fig,ax = plt.subplots(figsize = (12,4.5))

labels = metric_train.index.to_list()
values_train = metric_train.iloc[:,0].to_list()
values_test = metric_test.iloc[:,0].to_list()
x = np.arange(len(labels))
width = 0.35

rects1 = ax.bar(x = x - width/2, height = values_train, width = width, label = 'Train')
rects2 = ax.bar(x = x + width/2, height = values_test, width = width, label = 'Test')
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(text = f'{height:.4f}',
                    xy = (rect.get_x() + rect.get_width()/2, height),
                    xytext = (0,3),
                    textcoords = "offset points",
                    ha = "center",
                    va = "bottom")

autolabel(rects1)
autolabel(rects2)
ax.legend()
ax.set_title("Metric of Performance: Balanced Accuracy", fontsize = 12, fontweight = "bold", color = "black")
ax.set_ylabel("score", fontsize = 8, fontweight = "bold", color = "black")
ax.set_xlabel("Models", fontsize = 8, fontweight = "bold", color = "black")
ax.set_xticks(x)
ax.set_xticklabels(labels)
fig.show()

# Predictions !!!
y_pred_train_final = clf3.predict(X_train_imputed)
y_pred_test_final = clf3.predict(X_test_imputed)

print("##" * 40)
print(" " * 25, "Classification Report Train")
print("##" * 40)
print(classification_report(y_train, y_pred_train_final, target_names = LABELS))
print("")

print("##" * 40)
print(" " * 25, "Classification Report Test")
print("##" * 40)
print(classification_report(y_test, y_pred_test_final, target_names = LABELS))

cf_mx_train = confusion_matrix(y_train, y_pred_train_final)
cf_mx_test = confusion_matrix(y_test, y_pred_test_final)

fig,axs = plt.subplots(nrows = 1, ncols = 2, figsize = (10,5))
axs = axs.flat

sns.heatmap(cf_mx_train, cmap = 'Reds', annot = True, annot_kws = {'fontsize':11, 'fontweight':'bold'}, fmt = '', xticklabels = LABELS, yticklabels = LABELS, cbar = False, square = True, ax = axs[0])
sns.heatmap(cf_mx_test, cmap = 'Blues', annot = True, annot_kws = {'fontsize':11, 'fontweight':'bold'}, fmt = '', xticklabels = LABELS, yticklabels = LABELS, cbar = False, square = True, ax = axs[1])
axs[0].set_xlabel('Predicted', fontsize = 12, fontweight = "bold", color = "black")
axs[1].set_xlabel('Predicted', fontsize = 12, fontweight = "bold", color = "black")
axs[0].set_ylabel('True', fontsize = 12, fontweight = "bold", color = "black")
axs[1].set_ylabel('True', fontsize = 12, fontweight = "bold", color = "black")
axs[0].set_title('Confusion Matrix Train', fontsize = 14, fontweight = "bold", color = "black")
axs[1].set_title('Confusion Matrix Test', fontsize = 14, fontweight = "bold", color = "black")

fig.tight_layout()
fig.show()

feature_importance = clf3.feature_importances_
sorted_idx = np.argsort(feature_importance)
fig = plt.figure(figsize=(10, 5))
plt.barh(range(len(sorted_idx)), feature_importance[sorted_idx], align='center', color = 'red')
plt.yticks(range(len(sorted_idx)), np.array(imputer.get_feature_names_out())[sorted_idx])
plt.ylabel("Feature", fontsize = 10, fontweight = 'bold', color = 'black')
plt.title('Feature Importance', fontsize = 12, fontweight = 'bold', color = 'black')
plt.show()

"""# New section"""