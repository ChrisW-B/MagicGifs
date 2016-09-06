from setuptools import setup, find_packages

setup(name='magicgifsbot',
      version='1.0',
      description=("A simple giphy bot for twitter, basically"),
      long_description=open('README.rst').read(),
      keywords='python giphy twitter',
      author='Chris Barry',
      author_email='me@chrisb.xyz',
      url='http://www.github.com/ChrisW-B/magicgifs/',
      license='MIT',
      packages=find_packages(),
      install_requires=['tweepy', 'textblob', 'wordfilter', 'requests']
      )
