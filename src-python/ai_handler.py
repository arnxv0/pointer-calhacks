try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed")
    genai = None


class AIHandler:
    def __init__(self):
        self.model = None
    
    async def process_query(
        self,
        query: str,
        mode: str,
        api_key: str,
        model: str = "gemini-1.5-flash"
    ) -> str:
        if genai is None:
            return "Error: Google Generative AI library not installed"
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            
            if mode == "execute":
                prompt = f"Execute this command and provide the result: {query}"
            elif mode == "explain":
                prompt = f"Explain this in simple terms: {query}"
            elif mode == "insert":
                prompt = query
            else:
                prompt = query
            
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            return f"Error: {str(e)}"
