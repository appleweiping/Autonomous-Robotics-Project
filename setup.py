from glob import glob

from setuptools import find_packages, setup

package_name = 'agri_robots'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Weiping Yan',
    maintainer_email='152196713+appleweiping@users.noreply.github.com',
    description='Survey robot plus water, spray and seed robots for ROS 2 (simulated sensors).',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'navigator_node = agri_robots.navigator_node:main',
            'repeated_navigator = agri_robots.repeated_navigator:main',
            'waterbot_node = agri_robots.waterbot_node:main',
            'spraybot_node = agri_robots.spraybot_node:main',
            'seedbot_node = agri_robots.seedbot_node:main',
        ],
    },
)
