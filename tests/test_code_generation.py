"""Generate yaml and python code from the target functions
"""
from jinja2 import Environment, PackageLoader, FileSystemLoader
from tests.utilities import signature_scraper, type_scraper
from numpydoc import docscrape
import inspect
import pprint
import pytest
import sklearn.linear_model
import os
import numpy as np
import re


@pytest.fixture
def type_table():
    """
        Keys are substring of the type definition.

        Attention:
            The types on the righthand side obey the standrd of openAPI instead of python.
    """
    re_key = {
        'array': 'array',
        'numpy': 'array',
        'bool': 'boolean',
        'int': 'integer',
        'float': 'number'
    }
    return re_key


class TestYAMLGenerator:

    @pytest.fixture
    def sigs(self):
        sigs = {0: {'class_name': 'LinearRegression',
                    'constructor': {'copy_X': 'bool',
                                    'fit_intercept': 'bool',
                                    'n_jobs': 'int',
                                    'normalize': 'bool'},
                    'members': {'fit': {'X': 'list', 'y': 'list'},
                                'property': 'property',
                                'get_params': {'deep': 'bool'},
                                'predict': {'X': 'list'},
                                'score': {'X': 'list', 'sample_weight': 'list', 'y': 'list'}}}}
        return sigs

    def test_parse_sigs_to_yaml(self, sigs):
        """
        Parse the signatures of functions to a dictionary that is used to generate yaml files.

        f = {0: {'name': 'linear-regression',
                 'request_method': 'post',
                 'doc_string': 'this is a doc string',
                 'operation_id': 'cloudmesh.linear_regression',
                 'paras': {
                    'file_name': {'name': 'file_name', 'type': 'string'},
                    'intercept': {'name': 'intercept', 'type': 'int'}
                }}}
        """

    def test_generate_yaml(self):
        """Generate yaml file using the python template engine"""
        env = Environment(loader=FileSystemLoader('./tests/test_assets'))
        template = env.get_template('component.yaml')

        # f and g are the functions to generate
        f = {'name': 'linear-regression',
             'request_method': 'post',
             'doc_string': 'this is a doc string',
             'operation_id': 'cloudmesh.linear_regression',
             'paras': {
                 'file_name': {'name': 'file_name', 'type': 'string'},
                 'intercept': {'name': 'intercept', 'type': 'int'}
             }}

        g = {'name': 'logistic-regression',
             'request_method': 'post',
             'doc_string': 'this is a doc string',
             'operation_id': 'cloudmesh.linear_regression',
             'paras': {
                 'file_name': {'name': 'file_name', 'type': 'string'},
                 'intercept': {'name': 'intercept', 'type': 'int'}
             }}

        all = {1: g, 2: f}

        print(template.render(all=all))


class TestSignatureScraper:
    """Test Signature Retrievers

    In order to automate REST API generate process, the signature retriever would collect the signatures of class, func-
    tions and properties.

    Notes:
        Workflow:
        1. Using signature scraper to get names, types, and saved in a dictionary
        2. 

    Notes:
        1. Given a list of class, to acquire the signatures of class __init__ attribute, and the members.
        2. Some functions are private and should not be exposed. Making a list to ignore those functions or properties.
        3. What if the parameter of a function is class instance?
        4. Some of the functions do not have type information in the docstring.
        5. How to handle properties of a class? how to constrcut its yaml and corresping rest api?
        6. What if the parameters are optional?
        7. What is the type of kwarg***?
        8. what about the functions with side effects?
    """

    def test_retrive_linear_regression(self, type_table):
        """Only retrive the signature of the linear regression

            Attetion:
                1. the failed attempts to get type of parameters to class or functions are excluded. Set the predicate functions in the signature_scraper to see the failed attempts, i.e., is_valid_function(), is_valid_para().
        """
        sample_module = ['LinearRegression']
        types = []
        sigs = signature_scraper.get_signatures(
            sample_module, type_table, types)
        pprint.pprint(sigs)
        # np.save('./tests/test_assets/literal_types_lg', types)

    def test_retrive_linear_model(self, type_table):
        """This method will return all function signatures of the linear model defined in the __all__ attribute

            Attention:
                1. Priviate members whose name start with a "_" are excluded.
                2. Failed attempts to get the parameters types are ignore, and will not be added to the output so far.
        """
        sample_module = sklearn.linear_model.__all__
        types = []
        sigs = signature_scraper.get_signatures(
            sample_module, type_table, types)
        pprint.pprint(sigs)

    def test_get_all_known_types(self):
        pass

    def test_exclude_private_members(self):
        pass

    def test_exclude_functions(self):
        pass

    def test_get_parameters(self, sample_parameters):
        for p in sample_parameters:
            print(p.name, ':', str(p.type).split(' ')[0])

    def test_generate_data_type_table(self):
        pass


class TestTypeScraper:
    """Match types from text what literally defined.

        The types are crucial to generate yaml and endpoint functinos.

        Examples:
            x = [[1,2],[3,4]]
            reg = LinearRegression(X= x ...)
            The x must be a list when it is passed to the counstructor. When the functions are automatically generated, it must know the type of the x given mapped by connexion from request or errors occur.
    """
    @pytest.fixture
    def literal_types(self):
        """A sequence of strings include the parameter types information

            Examples:
                ['int, optional', 'float, optional', 'float, optional',
                'float, optional', 'float, optional', 'float, optional',
                'boolean, optional', 'float, optional', 'boolean, optional',
                'boolean, optional, default False',
                'boolean, optional, default True.',
                'boolean, optional, default False']
        """
        return np.load('./tests/test_assets/literal_types.npy', allow_pickle=True)

    @pytest.fixture
    def literal_types_lg(self):
        """A sequence of strings include the parameter types informations
            Examples:
                ['int, optional', 'float, optional', 'float, optional',
                'float, optional', 'float, optional', 'float, optional',
                'boolean, optional', 'float, optional', 'boolean, optional',
                'boolean, optional, default False',
                'boolean, optional, default True.',
                'boolean, optional, default False']
        """
        return np.load('./tests/test_assets/literal_types_lg.npy', allow_pickle=True)

    def test_match_types(self, literal_types_lg, type_table):
        """
        Scraper receives a type table defined by the developer.
        """
        typer_scraper = type_scraper.TypeScraper(type_table=type_table)
        for type in literal_types_lg:
            print(typer_scraper.scrap(type))

    def test_print_types(self, literal_types_lg):
        print(literal_types_lg)

    def test_re(self):
        res = re.search(
            'boolean', 'boolean, optional, default True', re.IGNORECASE)
        print(res)
