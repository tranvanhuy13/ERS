from setuptools import find_packages, setup
from typing import List



def get_requirements(file_path:str)->List[str]:
    '''
    Returns the requirements
    '''
    requirements = []
    with open(file_path) as file_obj:
        requirements = file_obj.readlines()
        
        for req in range(len(requirements)):
            requirements[req] = requirements[req].strip()
        
        if "-e ." in requirements:
            requirements.remove("-e .")

    return requirements




setup(name = 'Ecommerce-Recommender-System',
      version = '0.0.1',
      author = 'Tran Van Huy',
      author_email = 'tranvanhuyphu@gmail.com',
      packages = find_packages(),
      install_requires = get_requirements('requirements.txt')  )