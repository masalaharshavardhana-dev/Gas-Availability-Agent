from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

def get_gas_info_response(df, query, api_key=None, model_name="llama-3.1-8b-instant"):
    """
    Constructs a prompt with the top 3 results and gets a response from ChatGroq.
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


    context = df.to_markdown(index=False)

    prompt = (
        f"You are an AI assistant helping users find gas cylinder availability.\n"
        f"Here are the top 3 gas agencies near the user's location:\n\n"
        f"{context}\n\n"
        f"User question: {query}\n\n"
        f"STRICT WORKFLOW:\n"
        f"1. Based on the provided data, answer the user's question directly and concisely.\n"
        f"2. Use only the provided context to answer the question.\n"
        f"3. If any agency has availability, highlight it.\n"
        f"4. ALWAYS format your final response clearly, mentioning the nearest agency and its status.\n"
        f"5. Mention phone numbers if provided for contact.\n"
        f"6. If no agencies are found with the requested availability, state that clearly.\n"
        f"Be professional and helpful."
    )

    response = llm.invoke(prompt)
    return response.content
