import os
import logging
import json
from datetime import datetime
import ollama  # Import the ollama library

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
# Avoid adding handler if it already exists (e.g., during reloads)
if not logger.handlers:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"

# Updated to use local Ollama model
def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Calls a local Ollama language model with the given prompt, using caching if enabled.

    Args:
        prompt: The input prompt for the language model.
        use_cache: Whether to use the file-based cache. Defaults to True.

    Returns:
        The response text from the language model or a cached response.
        Returns an error message string if interaction with Ollama fails.
    """
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")

    cache = {}
    if use_cache:
        # Load cache from disk
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache file '{cache_file}': {e}. Starting with empty cache.")
                cache = {} # Ensure cache is empty on load failure

        # Return from cache if exists
        if prompt in cache:
            cached_response = cache[prompt]
            logger.info(f"RESPONSE (cached): {cached_response}")
            return cached_response

    # Call Ollama if not in cache or cache disabled
    try:
        # Get the model name from environment variable or use a default
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-32k") # Example: default to 'llama3'
        logger.info(f"Calling Ollama model: {ollama_model}")

        # Call the Ollama generate function
        response_data = ollama.generate(
            model=ollama_model,
            prompt=prompt
            # You can add other Ollama parameters here if needed, e.g.:
            # system="You are a helpful assistant.",
            # options={'temperature': 0.7}
        )
        response_text = response_data['response'].strip() # Get the response string and strip whitespace

        # Log the response
        logger.info(f"RESPONSE (Ollama): {response_text}")

    except Exception as e:
        # Log the error and return an informative error message
        logger.error(f"Error calling Ollama: {e}")
        # Consider if raising the exception or returning None might be better depending on usage
        return f"Error: Could not get response from Ollama. Details: {e}"

    # Update cache if enabled
    if use_cache:
        # It's generally safer to reload the cache before writing
        # in case another process modified it, though less critical here.
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                 logger.warning(f"Failed to reload cache before saving: {e}. Overwriting might occur.")

        # Add to cache and save
        cache[prompt] = response_text
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=4) # Use indent for readability
        except IOError as e:
            logger.error(f"Failed to save cache to '{cache_file}': {e}")

    return response_text

# --- The previously commented-out functions for Anthropic/OpenAI would remain here ---

# # Use Anthropic Claude 3.7 Sonnet Extended Thinking
# # def call_llm(prompt, use_cache: bool = True):
# #     ...

# # Use OpenAI o1
# # def call_llm(prompt, use_cache: bool = True):
# #     ...

if __name__ == "__main__":
    # Ensure Ollama service is running and has a model like 'llama3' pulled.
    # You might need to run `ollama pull llama3` first.
    # Set OLLAMA_MODEL environment variable to use a different model.

    test_prompt = "Explain the concept of 'duck typing' in Python in one sentence."

    # Clear cache for clean test run (optional)
    if os.path.exists(cache_file):
        print(f"Removing existing cache file: {cache_file}")
        os.remove(cache_file)

    # First call - should hit the Ollama API
    print("\nMaking first call (cache miss expected)...")
    response1 = call_llm(test_prompt, use_cache=True)
    print(f"Response 1: {response1}")

    # Second call - should hit the cache
    print("\nMaking second call (cache hit expected)...")
    response2 = call_llm(test_prompt, use_cache=True)
    print(f"Response 2: {response2}")
    assert response1 == response2 # Verify cache hit returns same content

    # Call with cache disabled - should hit the Ollama API again
    print("\nMaking call with cache disabled...")
    response3 = call_llm(test_prompt, use_cache=False)
    print(f"Response 3: {response3}")

    # Test error handling (Example: Stop Ollama service temporarily)
    # print("\nTesting Ollama connection error (stop Ollama service now if possible)...")
    # error_prompt = "This prompt should cause an error if Ollama is down."
    # error_response = call_llm(error_prompt, use_cache=False)
    # print(f"Error response test: {error_response}")
    # assert "Error: Could not get response from Ollama" in error_response