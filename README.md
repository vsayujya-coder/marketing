
Marketing Intelligence Streamlit App
------------------------------------
Files included:
- streamlit_app.py     : The Streamlit app. Put your CSVs (Facebook.csv, Google.csv, TikTok.csv, Business.csv) in the same folder.
- requirements.txt     : Python dependencies for Streamlit Cloud or local deployment.

How to run locally:
1. pip install -r requirements.txt
2. Put your CSV files (Facebook.csv, Google.csv, TikTok.csv, Business.csv) in this folder.
3. streamlit run streamlit_app.py

How to deploy on Streamlit Cloud:
1. Create a new GitHub repo with these files + your CSVs (or add CSVs via the repo).
2. Sign in to Streamlit Cloud and link the GitHub repo. Select streamlit_app.py as the app entrypoint.
3. Click Deploy — you will get a shareable link.
