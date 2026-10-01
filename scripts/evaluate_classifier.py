import csv, os, sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P=os.path.join(ROOT,'dataset','processed')
def load(name):
    with open(os.path.join(P,name),encoding='utf-8-sig') as f:return list(csv.DictReader(f))
tr,te=load('train.csv'),load('test.csv')
vec=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)
X=vec.fit_transform([r['text'] for r in tr]); Xt=vec.transform([r['text'] for r in te])
model=LogisticRegression(max_iter=2500,class_weight='balanced').fit(X,[r['intent'] for r in tr])
p=model.predict(Xt); y=[r['intent'] for r in te]
print('Accuracy:',round(accuracy_score(y,p),4)); print(classification_report(y,p,zero_division=0))
