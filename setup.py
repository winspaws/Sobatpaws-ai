from setuptools import setup, find_packages

setup(
    name="pawnia-client",
    version="1.0.0",
    description="Pawnia AI Client SDK - Veterinary AI Orchestrator",
    author="Naincode AI Dept",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=["httpx>=0.25.0", "pydantic>=2.0.0"],
)
