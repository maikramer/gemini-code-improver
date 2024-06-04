import os
import subprocess
from urllib.request import urlopen
from urllib.error import URLError

from bs4 import BeautifulSoup
import google.generativeai as genai

from core import get_logger
from core.code_processor import extract_classes

logger = get_logger(__name__)


class CodeAnalyzer:
    def __init__(self, api_db, application):
        self.api_db = api_db
        self.main_window = application.main_window
        self.settings = application.settings
        self.api_db = api_db
        self.class_list = []
        genai.configure(api_key="AIzaSyD_490byi8IzpOe7ognNNWObHoVrfldZ-k")

    def analyze(self, repo_path):
        changed_files = self.get_changed_files(
            repo_path
        ) if self.main_window.settings.get("train_on_changed", False) else None
        cpp_files = self.get_cpp_files(repo_path, changed_files)
        self.class_list = []  # Clear previous results
        for file in cpp_files:
            classes = extract_classes(file)
            for class_name in classes:
                api_info = self.api_db.get_api_info_from_class(class_name)
                if api_info:
                    self.class_list.append(f"{class_name} ({api_info['name']})")
                else:
                    self.class_list.append(class_name)

    def get_class_list(self):
        return "\n".join(self.class_list)

    def get_changed_files(self, repo_path):
        """Retrieves a list of changed files using git diff."""
        try:
            output = subprocess.check_output(
                ["git", "-C", repo_path, "diff", "--name-only", "HEAD", "origin/main"]
            )  # Assuming 'origin/main' is the remote branch
            changed_files = output.decode().splitlines()
            return changed_files
        except subprocess.CalledProcessError as e:
            self.main_window.show_error(
                f"Error getting changed files: {e.output.decode()}"
            )
            return []

    def get_cpp_files(self, directory, changed_files=None):
        """
        Gets a list of .cpp, .h, .hpp, and .c files.
        If changed_files is provided, it only returns files present in that list.
        """
        cpp_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".cpp", ".h", ".hpp", ".c")) and (
                        changed_files is None or os.path.join(root, file) in changed_files
                ):
                    cpp_files.append(os.path.join(root, file))
        return cpp_files

    def summarize_api_doc(self, url):
        """
        Fetches the content of the API documentation page and uses
        Gemini to generate a summary.
        """
        try:
            with urlopen(url) as response:
                html_content = response.read()

            soup = BeautifulSoup(html_content, "html.parser")
            # (You'll likely need to adjust how you extract the relevant
            #  content from the API documentation based on its structure)
            doc_content = soup.get_text(separator="\n", strip=True)

            prompt = f"""
            You are an expert technical writer specializing in summarizing API changes.

            Here's the documentation:

            {doc_content}

            Please summarize the key changes in this API version, including:
            * New features and functionalities.
            * Deprecated methods and classes.
            * Any important migration notes for developers.
            """
            summary = self.generate_summary(prompt)
            return summary

        except URLError as e:
            return f"Error fetching URL: {e.reason}"
        except Exception as e:
            return f"Error summarizing documentation: {e}"

    def analyze_api_usage(self, code_snippet, api_name):
        """
        Analyzes the given code snippet for usage patterns of the specified API.
        """
        prompt = f"""
        You are an expert C++ code analyst.

        Analyze the following code for usage patterns of the '{api_name}' API:
        ```c++
        {code_snippet}
        ```

        Identify and explain common ways in which the API is used within this code.
        Provide specific examples and code snippets to illustrate the patterns.
        """
        usage_patterns = self.generate_response(prompt)
        return usage_patterns

    def generate_summary(self, prompt):
        """Call Gemini API using the prompt and return the summary."""
        return self.generate_response(prompt)

    def generate_response(self, prompt):
        """Call Gemini API using the prompt and return the response."""
        return genai.generate_text(
            model="gemini-1.5-pro",
            prompt=prompt,
            temperature=self.settings.get("temperature", 0.7),
            max_output_tokens=self.settings.get("max_output_tokens", 500),
        )
