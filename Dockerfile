# ... (previous content)

# Expose the port that Streamlit will run on
EXPOSE 8501

# Command to run the application
ENTRYPOINT ["streamlit", "run", "MG_WeightedIndicatorExplorer.py"]
