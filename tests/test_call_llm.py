import os
import pytest
from dotenv import load_dotenv
from litellm import completion

# Opencode configuration
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY")
OPENCODE_BASE_URL = "https://opencode.ai/zen/go/v1"

# Load environment variables from .env file
load_dotenv()

# Define model constants to use throughout the app
EXTRACTION_MODEL = "deepseek-v4-flash"  # For extraction, logic, JSON
WRITER_MODEL = "deepseek-v4-pro"   

@pytest.mark.skip(reason="no wasting money trough API calls")
def test_call_llm():
    """ Test if the LLM is correctly set up and can be called. """

    prompt_1 = "give me only this ouput:Hello World"
    prompt_2 = "give me only this ouput:Hello Mars"

    testing_dict = {
        "prompts": [prompt_1, prompt_2],
        "models": [EXTRACTION_MODEL, WRITER_MODEL]
    }

    results = []

    for idx in range(len(testing_dict)):
        prompt = testing_dict["prompts"][idx]
        model = testing_dict["models"][idx]
        temperature = 0.0

        if not OPENCODE_API_KEY:
            raise ValueError("OPENCODE_API_KEY not found in environment variables.")
        
        try:
            response = completion(
                model=f"openai/{model}",  # litellm requires the "openai/" prefix for custom bases
                messages=[
                    {"role": "system", "content": prompt}
                ],
                temperature=temperature,
                api_base=OPENCODE_BASE_URL,
                api_key=OPENCODE_API_KEY
            )
            return results.append(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error calling LLM {model}: {e}")
            raise

        

    assert results == ["Hello World", "Hello Mars"]


