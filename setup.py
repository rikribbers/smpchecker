from distutils.core import setup

setup(name='SMP/SML Checker',
      version='0.1',
      description='Tool for checking SML/SMP entries',
      author='Rik Ribbers',
      author_email='rik.ribbers@gmail.com',
      url='https://github.com/rikribbers/smpchecker',
      install_requires=[
          'flask',
          'dnspython'
      ]
     )