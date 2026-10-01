import csv, os, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
DATA=os.path.join(ROOT,'dataset','processed','train.csv')
OUT=os.path.join(os.path.dirname(__file__),'models'); os.makedirs(OUT,exist_ok=True)
rows=list(csv.DictReader(open(DATA,encoding='utf-8-sig')))
vec=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)
X=vec.fit_transform([r['text'] for r in rows])
model=LogisticRegression(max_iter=2500,class_weight='balanced').fit(X,[r['intent'] for r in rows])
joblib.dump(vec,os.path.join(OUT,'intent_vectorizer.joblib')); joblib.dump(model,os.path.join(OUT,'intent_classifier.joblib'))
print('Saved intent model:',len(model.classes_),'classes')
