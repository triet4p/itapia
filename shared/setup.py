from setuptools import setup, find_packages

setup(
    name='itapia_common',
    version='0.5.0',
    packages=find_packages(),
    description='The common lib to connect db and get logger of ITAPIA',
    install_requires=['numpy==1.26.4','pandas', 'sqlalchemy', 'psycopg2-binary', 
                      'python-dotenv', 'redis', 'pydantic', 'fastapi']
)