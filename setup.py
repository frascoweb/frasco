from setuptools import setup, find_packages


setup(
    name='frasco',
    version='1.10.0',
    url='http://github.com/digicoop/frasco',
    license='MIT',
    author='Maxime Bouroumeau-Fuseau',
    author_email='maxime.bouroumeau@gmail.com',
    description='Set of extensions for Flask to develop SaaS applications',
    packages=find_packages(),
    package_data={
        'frasco': [
            'angular/static/*.js',
            'assets/*.js',
            'assets/*.html',
            'billing/invoicing/emails/*.html',
            'mail/templates/*.html',
            'mail/templates/layouts/*',
            'push/static/*.js',
            'templating/*.html',
            'templating/bootstrap/*.html',
            'users/emails/users/*.txt',
            'users/templates/users/*.html'
        ],
    },
    zip_safe=False,
    platforms='any',
    install_requires=[
        'ago~=0.0.93',
        'apispec~=2.0.2',
        'authlib~=0.14.1',
        'boto3~=1.12.1',
        'cssmin~=0.2.0',
        'eventlet~=0.25.1',
        'Flask~=1.1.1',
        'Flask-Assets==2.0',
        'Flask-Babel~=1.0.0',
        'Flask-Bcrypt~=0.7.1',
        'Flask-CORS~=3.0.8',
        'Flask-Login~=0.5.0',
        'Flask-Mail~=0.9.1',
        'Flask-Migrate~=2.5.2',
        'Flask-RQ2~=18.3',
        'Flask-SQLAlchemy~=2.4.1',
        'Flask-WTF~=0.14.3',
        'geoip2~=3.0.0',
        'glob2~=0.7.0',
        'goslate~=1.5.1',
        'htmlmin~=0.1.12',
        'inflection~=0.3.1',
        'jinja-layout~=0.1',
        'jinja-macro-tags~=0.1',
        'jsmin~=2.2.2',
        'Markdown~=3.1.1',
        'premailer~=3.6.1',
        'psycopg2-binary~=2.8.4',
        'pyotp~=2.3.0',
        'python-dateutil~=2.8.1',
        'python-slugify~=4.0.0',
        'python-socketio~=4.4.0',
        'PyYAML~=5.3',
        'redis~=3.4.1',
        'requests~=2.22.0',
        'simplejson~=3.17.0',
        'speaklater~=1.3',
        'stripe~=2.42.0',
        'suds==0.4',
        'werkzeug>=1.0.0',
    ],
    entry_points='''
        [console_scripts]
        frasco=flask.cli:main
    '''
)
