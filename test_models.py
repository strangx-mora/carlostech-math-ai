import google.generativeai as genai

genai.configure(api_key="AIzaSyADV8Z8YNM-n5N_PM8DKRB9ATDAWUbMCS8")

for m in genai.list_models():
    print(m.name)