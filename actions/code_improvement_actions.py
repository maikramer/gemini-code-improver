import difflib
import os
import re

from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtGui import QFont


class CodeImprovementActions:
    def __init__(self, main_window, api_db, code_improver):
        self.main_window = main_window
        self.api_db = api_db
        self.code_improver = code_improver

    def upgrade_apis(self):
        selected_class = self.main_window.class_dropdown.currentText()
        if not selected_class:
            self.main_window.show_error("Please select a class.")
            return

        class_name = selected_class.split("(")[0].strip()  # Extract class name
        class_code = self._get_class_code(class_name)  # Get the class code
        if not class_code:
            return  # Error message already shown in _get_class_code

        api_info = self.api_db.get_api_info_from_code(class_code)
        if not api_info:
            self.main_window.show_error("No known APIs found in the class.")
            return

        prompt = self.code_improver.create_upgrade_prompt(class_code, api_info)
        self.main_window.start_background_task(
            "improve_class",
            prompt=prompt,
            action="upgrade",
            code_improver=self.code_improver,
        )

    def switch_api(self):
        selected_class = self.main_window.class_dropdown.currentText()
        if not selected_class:
            self.main_window.show_error("Please select a class.")
            return

        class_name = selected_class.split("(")[0].strip()  # Extract class name
        class_code = self._get_class_code(class_name)  # Get the class code
        if not class_code:
            return  # Error message already shown in _get_class_code

        # --- Get Old API Information ---
        old_api_info = self.api_db.get_api_info_from_code(class_code)

        # --- Get New API Information (Prompt user for input) ---
        new_api_name, ok = QInputDialog.getText(
            self.main_window,
            "Switch API",
            "Enter the name of the new API:",
        )
        if not ok or not new_api_name:
            return  # User canceled or entered nothing

        new_api_info = self.api_db.get_api_info_from_class(new_api_name)
        if not new_api_info:
            self.main_window.show_error(f"API '{new_api_name}' not found in the database.")
            return

        prompt = self.code_improver.create_switch_api_prompt(class_code, old_api_info, new_api_info)
        self.main_window.start_background_task(
            "improve_class",
            prompt=prompt,
            action="switch",
            code_improver=self.code_improver,
        )

    def apply_general_improvements(self):
        selected_class = self.main_window.class_dropdown.currentText()
        if not selected_class:
            self.main_window.show_error("Please select a class.")
            return

        class_code = self._get_class_code(selected_class)

        prompt = self.code_improver.create_general_improvement_prompt(class_code)
        self.main_window.start_background_task(
            "improve_class",
            prompt=prompt,
            action="general",
            code_improver=self.code_improver,
        )

    def apply_code_changes(self):
        if self.main_window.suggested_changes:
            confirmation = QMessageBox.question(
                self.main_window,
                "Confirm Changes",
                "Are you sure you want to apply the suggested changes to your code?\n\n"
                "Make sure you have a backup of your code before proceeding.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmation == QMessageBox.StandardButton.Yes:
                try:
                    for file_path, new_content in self.main_window.suggested_changes.items():
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                    self.main_window.show_message("Changes applied successfully!")
                except Exception as e:
                    self.main_window.show_error(f"Error applying changes: {e}")

    def display_diff(self, suggested_changes):
        diff_output = []
        for file_path, new_content in suggested_changes.items():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                diff = difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    lineterm='',
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}"
                )
                diff_output.append("".join(diff))
            except FileNotFoundError:
                self.main_window.show_error(f"File not found: {file_path}")
                return  # Stop processing diffs if a file is not found

        self.main_window.diff_view.setPlainText("\n".join(diff_output))
        self.main_window.diff_view.setFont(QFont("Courier New", 10))  # Set a monospaced font for better readability

    def _get_class_code(self, class_name):
        """
        Gets the code for the specified class from the user's repository.

        Args:
            class_name (str): The name of the class.

        Returns:
            str: The code of the class, or an empty string if not found.
        """
        # 1. Find the file containing the class:
        class_file = self._find_class_file(class_name)
        if not class_file:
            self.main_window.show_error(f"Could not find file containing class '{class_name}'.")
            return ""

        # 2. Extract the class code from the file:
        class_code = self._extract_class_from_file(class_name, class_file)
        return class_code

    def _find_class_file(self, class_name):
        """
        Finds the file in the user's repository that contains the given class definition.

        This is a basic implementation that assumes a simple naming convention.
        You might need to adjust this based on your project's structure and
        how classes are organized.

        Args:
            class_name (str): The name of the class to find.

        Returns:
            str: The path to the file containing the class, or None if not found.
        """
        repo_path = self.main_window.user_repo_path
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith((".cpp", ".h", ".hpp")):
                    # Simple check: assume class name is part of the file name
                    if class_name in file:
                        return os.path.join(root, file)
        return None

    def _extract_class_from_file(self, class_name, file_path):
        """
        Extracts the code block defining the specified class from the given file.

        This is a basic implementation using regex. You might need to adjust
        it based on your coding style and how classes are defined.

        Args:
            class_name (str): The name of the class to extract.
            file_path (str): The path to the file containing the class.

        Returns:
            str: The code block defining the class, or an empty string if not found.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic regex to find class definition and its content:
        class_regex = re.compile(rf"\bclass\s+{class_name}\s*{{(.*?)}}", re.DOTALL)
        match = class_regex.search(content)
        if match:
            return match.group(1).strip()
        else:
            return ""
