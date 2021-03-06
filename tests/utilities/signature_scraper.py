import inspect
import sys
import pprint
import sklearn.linear_model
import numpy as np
import json

from numpydoc import docscrape
from sklearn.linear_model import LinearRegression
from tests.utilities import type_scraper


def get_signatures(module, class_names, type_table):
    """Getting the signatures of sklean.linear_model

        The Structure of the Output. 
        1. The first layer of the dictionary is the indicies of classes. 
           {0: {'class_name': 'LinearRegression'}, 1:{'class_name':'LogisticRegression'}}
        2. The second layer of the dictionary is include the information of the class including the name of the class,     the parameters of the class __init__ function and the member functinos.
        3. There are a number of properties or attributes owned by the class. Those attributes will not be exposed as      individual interface such as ```cms analytics lienar-regression coef_```. Those properties will be accessed     from the same interface by specifying the name of the attribute. For example, ```cms analytics                  linear regression properties=coef_/intercep_```. The value of the attributes will be returned

        Examples:
            {0: {'class_name': 'LinearRegression',
                    'constructor': {'copy_X': 'bool',
                                    'fit_intercept': 'bool',
                                    'n_jobs': 'int',
                                    'normalize': 'bool'},
                    'members': {'fit': {'X': 'list', 'y': 'list'},
                                '__property___': '__property___',
                                'get_params': {'deep': 'bool'},
                                'predict': {'X': 'list'},
                                'score': {'X': 'list', 'sample_weight': 'list', 'y': 'list'}}}}
        Parameters:
            Types: A accumulator to collection infomration of types.

        Notes:
            Some of the functions are private and only be used by other functions inside which should be excluded.

        Attention:
            1. So far the attributes will not be included in signatures. Attributes should be considered later.
            2. Users should specify the name of the attributes of a class object to request it. For example, 
               cms ``` analytics linear-regression property=coef_ ```. This command should return the value of the coef_ of the linear regression class object.
        Warnings:
            1. Orderdict: The order is not important if you specified the parameters names
            2. filtering the fucntions that are not public
            3. Attributes will not exist before applying fit, e.g., LinearRegression will not have coef_ attribute before applying fit.
    """
    res = {}
    # Traverse all classes and its members
    for i, class_name in enumerate(class_names):
        try:
            current_class = {}
            res[i] = current_class
            current_class['class_name'] = class_name

            # Get the clas obj and its doc string
            class_obj = getattr(module, class_name)
            doc = inspect.getdoc(class_obj)

            # Add members of the current class constructor
            current_class['constructor'] = get_parameters(
                doc, type_table)

            # Operate on individual members
            current_members = {}
            current_class['members'] = current_members

            for member_name, f in get_public_members(class_obj).items():
                if inspect.isfunction(f):
                    doc = inspect.getdoc(f)
                    paras_dict = get_parameters(doc, type_table)
                    current_members[member_name] = paras_dict
                else:
                    continue
        # Ignore the classes that do not have signatures
        except ValueError:
            pass

        # Delete the setter functions
        if 'set_params' in current_members.keys():
            del current_members['set_params']

        current_members['get_properties'] = {'name': 'str'}

        # current_members['get_properties'] = {'name':'str'}
    return res


def get_ab_class_sig(class_obj, current):
    current['constructor'] = get_ab_func_sig(
        dict(inspect.getmembers(class_obj))['__init__']
    )
    members = {}
    current['members'] = members
    for name, obj in get_public_members(dict(inspect.getmembers(class_obj))):
        members[name] = get_ab_func_sig(obj, current)
    return current


def get_ab_func_sig(func_obj):
    paras_dict = dict(inspect.signature(func_obj).parameters)
    simple_paras = {}

    for name in paras_dict.keys():
        if name != 'self':
            simple_paras[name] = ''
    return simple_paras


def get_ab_signatures(module):
    module_members = get_public_members(module)

    res = {}
    # Traverse all classes and its members
    for i, name in enumerate(module_members.keys()):
        try:
            current = {}
            res[i] = current

            if inspect.isclass(module_members[name]):
                current['type'] = 'class'
                current['name'] = name
                class_obj = module_members[name]

                current['constructor'] = get_ab_func_sig(
                    dict(inspect.getmembers(class_obj))['__init__']
                )
                members = {}
                current['members'] = members
                class_members = get_public_members(class_obj)
                for class_member_name, class_member_obj in class_members.items():
                    members[class_member_name] = get_ab_func_sig(class_member_obj)

            if inspect.isfunction(module_members[name]):
                current['type'] = 'function'
                current['name'] = name
                func_obj = module_members[name]

                current['paras'] = get_ab_func_sig(func_obj)

        except ValueError:
            pass
    return res


def get_public_members(obj):
    """Get public class members.

    It detect if the name of the object starts with the "_", which is the naming convention used in sklean. Python doesn't have real "private" members.

    Attention:
        The type of members
            1. public
                1. properties -- How to deal with properties? #TODO
                2. functions -- only functions should be exposed
            2. private
    """
    def isprivate(name):
        if name[0] == '_':
            return True
        else:
            return False

    public_members = {}
    for k, v in inspect.getmembers(obj):
        if not isprivate(k):
            public_members[k] = v
    return public_members


def get_parameters(doc, type_table):
    """Get parameters from the doc of a class, function, or property object.

    Given the sklean docstring follows the numpy conventions, this function use the numpy docstring parser to read the doc of sklean.
    """
    scraper = type_scraper.TypeScraper(type_table=type_table)
    r = docscrape.NumpyDocString(doc)
    paras = {}
    for p in r['Parameters']:

        para_str = str(p.type)
        para_type = scraper.scrap(para_str)
        if is_valid_para(para_type, type_table):
            paras[p.name] = scraper.scrap(para_str)
        else:
            continue
    return paras


def is_valid_para(para_type, type_table):
    """Check if it is a valid parameter type contained in the type table.
    """
    # The values of the table contain all known destination types
    if para_type in type_table.values():
        return True
    return True


def is_valid_function(paras):
    """Check if a valid method with parameters

        Parameters:
            paras: A dictionary contains all parameters of the method

        Exampls:
            For some situation the there will no parameters due to empty doc string. This should be recorded and processed futher, e.g., {'set_params': {}} is not acceptable when doing conversion.
    """
    if len(paras) != 0:
        return True
    return True


def if_has_para_doc():
    pass
