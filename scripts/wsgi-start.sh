#!/bin/sh
cd $HOME/production

source venv/bin/activate
uwsgi --emperor wsgi/sites/sml.ini
deactivate
