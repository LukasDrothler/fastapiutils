from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastapiutils",
    version="0.3.0",
    author="Lukas Drothler",
    author_email="",
    description="FastAPI utilities for authentication, user management, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LukasDrothler/fastapiutils",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.68.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.2",
        "python-multipart>=0.0.5",
        "mysql-connector-python>=8.0.0",
        "pydantic>=1.8.0",
        "cryptography>=3.4.0",
        "PyJWT>=2.0.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.15.0",
            "httpx>=0.24.0",
        ],
    },
    include_package_data=True,
    package_data={
        "fastapiutils": ["locales/*.json", "*.sql"],
    },
)
