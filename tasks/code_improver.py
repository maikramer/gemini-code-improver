import google.generativeai as genai


class CodeImprover:
    def __init__(self, api_db, application):
        self.api_db = api_db
        self.application = application # Store the application instance
        self.settings = application.settings

        genai.configure(api_key="AIzaSyD_490byi8IzpOe7ognNNWObHoVrfldZ-k")

    def create_upgrade_prompt(self, class_code, api_info):
        return f"""
        You are a C++ code modernization expert.
        Improve the following C++ class, using the latest version of the '{api_info.get('name', '')}' API:
        ```c++
        {class_code}
        ```
        Provide the improved code and a JSON format with the suggested changes, with the file path as key and improved code as value: 
        ```json
        {{"improved_code": "<improved_code>", "suggested_changes": {{"<file_path>": "<improved_code>"}}}}
        ```
        """

    def create_switch_api_prompt(self, class_code, old_api_info, new_api_info):
        # (To be implemented - see instructions below)
        # This prompt should guide Gemini to replace the old API
        # with the new API, providing necessary context and examples.
        pass

    def create_general_improvement_prompt(self, class_code):
        prompt = f"""
        Improve the structure, readability, and efficiency of the following C++ class: 

        ```c++
        {class_code}
        ```
        Provide the improved code and a JSON format with the suggested changes, with the file path as key and improved code as value: 
        ```json
        {{"improved_code": "<improved_code>", "suggested_changes": {{"<file_path>": "<improved_code>"}}}}
        ```
        """
        return prompt

    def improve(self, prompt, action="general"):
        # (You can add any logic here to further process the prompt or
        #  handle responses differently based on the 'action')
        response = self.generate_response(prompt)
        return response

    def generate_test_cases(self, code, api_info):
        """
        Generates unit test cases for the given code using the API information.
        """
        prompt = f"""
        You are an expert C++ developer and write excellent unit tests 
        using the Google Test framework.

        Here's a C++ class that uses the '{api_info.get('name', '')}' API:
        ```c++
        {code}
        ```

        Generate comprehensive Google Test test cases for this class.
        Consider these details about '{api_info.get('name', '')}':
        * {api_info.get('summary', 'N/A')} 

        Focus on testing the correct usage of the API and cover potential edge cases. 
        """
        test_cases = self.generate_response(prompt)
        return test_cases

    def generate_response(self, prompt):
        """Call Gemini API using the prompt and return the response."""
        return genai.generate_text(
            model="gemini-1.5-pro",
            prompt=prompt,
            temperature=self.settings.get("temperature", 0.7),
            max_output_tokens=self.settings.get("max_output_tokens", 2000),
        )
