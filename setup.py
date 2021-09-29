from __future__ import print_function
import os
import subprocess
from distutils.command.build import build as distutils_build
from setuptools import setup, find_packages, Command as SetupToolsCommand

VERSION = '1.0.0'


with open('requirements.txt', 'r') as f:
  install_requires = f.readlines()

CUSTOM_COMMANDS = [
  ['python', '-m', 'spacy', 'download', 'en'],
]


class Build(distutils_build):
  sub_commands = distutils_build.sub_commands + [('CustomCommands', None)]


class CustomCommands(SetupToolsCommand):
  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  @staticmethod
  def run_custom_command(command_list):
    print('Running: %s' % command_list)
    p = subprocess.Popen(command_list, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout_data, _ = p.communicate()
    print('Output: %s' % stdout_data)
    if p.returncode != 0:
      raise RuntimeError('Command %s failed: exit code: %s' % (command_list, p.returncode))

  def run(self):
    for command in CUSTOM_COMMANDS:
      self.run_custom_command(command)


setup(name='ConTEXT-Explorer',
      description='ConTEXT Explorer is an open Web-based system for exploring and visualizing concepts (combinations of occurring words and phrases) over time in the text documents.',
      url='https://github.com/alicia-ziying-yang/conTEXT-explorer',
      author='Ziying Yang',
      author_email='ziying.yang@unimelb.edu.au',
      version=VERSION,
      license='Apache License 2.0',
      packages=find_packages(),
      python_requires='==3.7.5',
      install_requires=install_requires,
      extras_require={},
      cmdclass={
          'build': Build,
          'CustomCommands': CustomCommands,
      })