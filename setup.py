from setuptools import setup, find_packages

setup(name='smpsmlchecker',
      version='0.1',
      description='Tool for checking SML/SMP entries',
      author='Rik Ribbers',
      author_email='rik.ribbers@gmail.com',
      url='https://github.com/rikribbers/smpchecker',
      install_requires=[
          'flask',
          'dnspython'
      ],
      packages=find_packages(),
      include_package_data=True,
      )
