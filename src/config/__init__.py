# Copyright 2014 by CyberLife Labs, Inc.

import importlib
import logging.config
import os
import re
import sys


_command_line = {}
_properties   = {}


def add_module(key, name):
    add_property(key, importlib.import_module(name))


def add_property(name, value):
    if name in _properties:
        raise Exception('property already exists: {0}'.format(name))
    
    _properties[name] = value


def get_property(name, default=None, required=True):
    os_env_name = name.upper().replace('.', '_')
    
    if name in _command_line:
        return _command_line[name]
    elif os_env_name in os.environ:
        return os.environ[os_env_name]
    elif name in _properties:
        return _properties[name]
    elif default is not None:
        return default
    elif required:
        raise Exception('property not found: {0}'.format(name))
    else:
        return None


def get_runtime_profile():
    return get_property('runtime.profile', required=False)


def has_property(name):
    return get_property(name, required=False) is not None


def _initialize_logging():
    filename = get_property('logging.properties', required=False)
    
    if filename is None and os.path.exists('logging.properties'):
        filename = 'logging.properties'
    
    if filename is not None:
        logging.config.fileConfig(filename)
    else:
        logging.basicConfig(level=logging.INFO)
    
    if get_runtime_profile() == 'development' or has_property('debug'):
        logging.getLogger().setLevel(logging.DEBUG)
    
    if filename is not None:
        logging.getLogger().debug('logging configured from %s', filename)


def _load_all_properties():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    _load_properties_from_dir(this_dir)
    _load_properties_from_dir('.')
    
    external = get_property('application.properties', required=False)
    
    if external is not None:
        if os.path.exists(external):
            _load_properties_from(external)
        else:
            raise Exception('properties-file not found: {0}'.format(external))


def _load_profile_configuration():
    profile = get_runtime_profile()
    
    if profile is not None:
        module_name = 'config.{0}'.format(profile)
        
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            if not e.message.endswith(' ' + module_name):
                raise


def _load_properties_from(filename):
    if os.path.exists(filename):
        _logger.debug('loading properties from %s', filename)
        
        with open(filename, 'rt') as f:
            for line in f:
                line = line.strip()
                
                if line != '' and line[0] != '#':
                    name,value = [field.strip() for field in line.split('=', 1)]
                    _properties[name] = value


def _load_properties_from_dir(dir_name):
    _load_properties_from(dir_name + '/application.properties')
    
    profile = get_runtime_profile()
    
    if profile is not None:
        _load_properties_from('{0}/application-{1}.properties'.format(dir_name, profile))


def _parse_command_line():
    if len(sys.argv) > 1:
        pattern = re.compile('^--([^=]+)(=(.+))?$')
        
        for arg in sys.argv[1:]:
            match = pattern.search(arg)
            
            if match is not None:
                groups = match.groups()
                name   = groups[0]
                value  = groups[2]
                
                if value == None:
                    value = ''
                
                _command_line[name] = value


_parse_command_line()
_initialize_logging()

_logger = logging.getLogger(__name__)
profile = get_runtime_profile()

if profile is None:
    _logger.debug('no runtime-profile set')
else:
    _logger.debug('runtime-profile = %s', profile)

_load_all_properties()
_load_profile_configuration()

if has_property('debug'):
    _logger.debug('debug mode')
