from setuptools import setup
# PyPi steps
# python -m build
# twine upload dist/*
setup(
    name='py5canvas',
    version='0.5.9',
    description='Library to create drawings and animations with an interface similar to p5js and Processing.',
    author='Daniel Berio',
    author_email='drand48@gmail.com',
    packages=['py5canvas'],
    install_requires=['pycairo',
                      'glfw',
                      'moderngl',
                      'PyOpenGL',
                      'numpy',
                      'pillow',
                      'easydict',
                      'xdialog',
                      'perlin-noise'],
    entry_points={
        'console_scripts': [
            'py5sketch = py5canvas.run_sketch:main'
        ]
    },
    license='MIT',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
    ),
)
