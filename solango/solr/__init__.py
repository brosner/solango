#
# Copyright 2008 Optaros, Inc.
#

"""
Will handle the base wrapper.

"""
from django.db.models.loading import get_model
from django.conf import settings 

#Helper Functions for getting and setting models
#The type field sets the value as app_label__module_name


def get_model_key(model):
    return '%s%s%s' % (model._meta.app_label, settings.SEARCH_SEPARATOR ,model._meta.module_name)

def get_model_from_key(type):
    app_label, module_name = type.split(settings.SEARCH_SEPARATOR)
    return get_model(app_label, module_name)