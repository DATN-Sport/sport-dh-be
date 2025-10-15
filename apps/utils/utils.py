import os

def delete_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            # Log the error but continue with deletion
            print(f"Error deleting file {file_path}: {e}")
