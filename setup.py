from setuptools import setup, find_packages

setup(
    name="beatport-auto",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'selenium>=4.0.0',
        'webdriver_manager>=4.0.0',
        'requests>=2.25.0',
        'python-dotenv>=0.19.0',
    ],
    entry_points={
        'console_scripts': [
            'beatport-auto=main:main',
            'beatport-test=test_selectors:main',
        ],
    },
    author="Your Name",
    description="Automated Beatport track downloader with resilient selector management",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="beatport, automation, web-scraping, music, download",
    url="https://github.com/yourusername/beatport-auto",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
