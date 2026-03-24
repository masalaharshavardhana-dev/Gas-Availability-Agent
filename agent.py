from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_groq import ChatGroq
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_pandas_agent(df: pd.DataFrame, api_key: str = None, model_name: str = "llama-3.1-8b-instant"):
    """
    Creates and returns a LangChain Pandas Dataframe Agent for gas data.
    """
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        
    if not api_key:
        raise ValueError("Groq API Key is required.")

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0
    )

    prefix = (
        "You are an AI assistant helping users find gas cylinder availability. "
        "The dataframe 'df' contains columns: id, name, brand, city, area, pincode, latitude, longitude, availability, last_updated, phone. "
        "\nSTRICT WORKFLOW:\n"
        "1. Search for the user's mentioned 'area', 'city', or 'pincode' in 'df' (case-insensitive).\n"
        "2. If an exact or partial match is found for the 'area' or 'city', show up to 3 agencies from that location.\n"
        "3. If the location is NOT found in the sheet, state: 'Location not found. Here are the top 3 available agencies instead:' and then show the top 3 'Available' gas stations from the sheet.\n"
        "4. ALWAYS limit your response to EXACTLY the TOP 3 results total.\n"
        "6. ALWAYS format your output as a Markdown Table with columns: | Name | Area | Availability | Phone |.\n"
        "7. Be concise, professional, and helpful."
        "8. do not generate map"
    )

    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True,
        prefix=prefix,
        agent_executor_kwargs={"handle_parsing_errors": True}
    )
    
    return agent

