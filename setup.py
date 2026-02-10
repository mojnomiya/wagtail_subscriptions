from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A comprehensive subscription management system for Wagtail CMS"

try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = ["Django>=3.2,<5.0", "wagtail>=4.0,<6.0", "python-dateutil>=2.8.0", "stripe>=5.0.0"]

setup(
    name="wagtail-subscriptions",
    version="1.0.0",
    author="Wagtail Subscriptions Team",
    author_email="contact@wagtail-subscriptions.org",
    description="A comprehensive subscription management system for Wagtail CMS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wagtail-subscriptions/wagtail-subscriptions",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Wagtail",
        "Framework :: Wagtail :: 4",
        "Framework :: Wagtail :: 5",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
    keywords="wagtail django subscription billing saas payment",
    project_urls={
        "Bug Reports": "https://github.com/wagtail-subscriptions/wagtail-subscriptions/issues",
        "Source": "https://github.com/wagtail-subscriptions/wagtail-subscriptions",
        "Documentation": "https://wagtail-subscriptions.readthedocs.io/",
    },
)