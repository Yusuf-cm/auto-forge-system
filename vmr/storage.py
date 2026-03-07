# vmr/storage.py
import os

def read_seed(project_name: str) -> dict:
    """
    Reads the three core AutoForge brief files for a given project.
    
    Args:
        project_name (str): The name of the project directory.
        
    Returns:
        dict: A dictionary containing the contents of the text files.
    """
    texts = {}
    # AutoForge Convention: Projects are stored in 'projects/'
    # Seeds are stored in the 'seed_texts' subfolder.
    base_path = os.path.join("projects", project_name, "seed_texts")
    
    if not os.path.isdir(base_path):
        print(f"Storage Warning: 'seed_texts' directory not found for project '{project_name}' at {base_path}.")
        return {'brief.txt': '', 'brand.txt': '', 'audience.txt': ''}

    # The new AutoForge naming convention
    for name in ["brief.txt", "brand.txt", "audience.txt"]:
        file_path = os.path.join(base_path, name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                texts[name] = f.read()
        except FileNotFoundError:
            # If a specific file is missing, provide an empty string so the LLM knows it's empty
            texts[name] = ""
            
    return texts