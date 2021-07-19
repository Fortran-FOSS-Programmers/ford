from setuptools import setup
import site
import sys

# https://github.com/pypa/pip/issues/7953
if len(sys.argv) >= 3 and sys.argv[1] == "develop":
    site.ENABLE_USER_SITE = "--user" in sys.argv[2:]

setup()
