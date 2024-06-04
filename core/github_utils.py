import os
import subprocess


def clone_repository(url, local_path):
    """
    Clones a GitHub repository to a local directory using the 'git' command.

    Args:
        url (str): The URL of the GitHub repository.
        local_path (str): The local path where the repository should be cloned.
    """
    try:
        os.makedirs(local_path, exist_ok=True)
        subprocess.check_output(["git", "clone", url, local_path])
        print(f"Repository cloned successfully to: {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.output.decode()}")
    except Exception as e:
        print(f"Error cloning repository: {e}")
