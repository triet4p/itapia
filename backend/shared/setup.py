from setuptools import find_packages, setup

setup(
    name="itapia_common",
    version="0.5.1",
    packages=find_packages(),
    description="The common lib to connect db, get logger of ITAPIA, and define schemas between modules",
    install_requires=[
        "numpy==1.26.4",
        "pandas",
        "sqlalchemy",
        "psycopg2-binary",
        "python-dotenv",
        "redis",
        "pydantic",
        "fastapi",
    ],
)
