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
        'matrix': 'array',
        'array': 'array',
        'array-like': 'array',
        'numpy array': 'array',
        'bool': 'boolean',
        'int': 'integer',
        'float': 'number'
    }
    return re_key


@pytest.fixture
def linear_regression_signatures(type_table):
        """Only retrive the signature of the linear regression
            Attetion:
                1. the failed attempts to get type of parameters to class or functions are excluded. Set the predicate functions in the signature_scraper to see the failed attempts, i.e., is_valid_function(), is_valid_para().
        """
        sample_module = ['LinearRegression']
        sigs = signature_scraper.get_signatures(
            sample_module, type_table, )
        return sigs

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

    @pytest.fixture
    def table_yamlInfo(self, sigs):
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
        table_yaml = {}
        count = 0
        for i, class_i in sigs.items():
            # build the yaml information table for class constructor
            count += 1
            class_i_name = class_i['class_name']
            constructor_yaml_info = {}
            constructor_yaml_info['name'] = class_i_name + '-constructor'
            constructor_yaml_info['request_method'] = 'post'
            constructor_yaml_info['doc_string'] = 'this is a doc string'
            constructor_yaml_info['operation_id'] = 'cloudmesh.' + class_i_name + '_constructor'
            constructor_yaml_info['paras'] = {}
            for init_para_name, init_para_type in class_i['constructor'].items():
                constructor_yaml_info['paras'][init_para_name] = {'name':init_para_name, 'type':init_para_type}
            table_yaml[count] = constructor_yaml_info

            # build the yaml information table for class members
            for member_name, parameters in class_i['members'].items():
                count += 1
                if (member_name != 'property'):
                    member_yaml_info = {}
                    member_yaml_info['name'] = class_i_name + '-' + member_name
                    member_yaml_info['request_method'] = 'post'
                    member_yaml_info['doc_string'] = 'this is a doc string'
                    member_yaml_info['operation_id'] = 'cloudmesh.' + class_i_name + '_' + member_name
                    member_yaml_info['paras'] = {}
                    for member_para_name, member_para_type in parameters.items():
                        member_yaml_info['paras'][member_para_name] = {'name':member_para_name, 'type':member_para_type}
                    table_yaml[count] = member_yaml_info

        return table_yaml

    def test_generate_yaml(self, table_yamlInfo):
        """Generate yaml file using the python template engine"""
        env = Environment(loader=FileSystemLoader('./tests/test_assets'))
        template = env.get_template('component.yaml')

        # # f and g are the functions to generate
        # f = {'name': 'linear-regression',
        #      'request_method': 'post',
        #      'doc_string': 'this is a doc string',
        #      'operation_id': 'cloudmesh.linear_regression',
        #      'paras': {
        #          'file_name': {'name': 'file_name', 'type': 'string'},
        #          'intercept': {'name': 'intercept', 'type': 'int'}
        #      }}
        #
        # g = {'name': 'logistic-regression',
        #      'request_method': 'post',
        #      'doc_string': 'this is a doc string',
        #      'operation_id': 'cloudmesh.linear_regression',
        #      'paras': {
        #          'file_name': {'name': 'file_name', 'type': 'string'},
        #          'intercept': {'name': 'intercept', 'type': 'int'}
        #      }}

        # all = {1: g, 2: f}
        all = table_yamlInfo
        generated_yaml = template.render(all=all)
        with open('./tests/test_assets/generated_yaml.yaml', 'w') as f:
            f.write(generated_yaml)


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

    def test_retrive_linear_model(self, type_table):
        """This method will return all function signatures of the linear model defined in the __all__ attribute

            Attention:
                1. Priviate members whose name start with a "_" are excluded.
                2. Failed attempts to get the parameters types are ignore, and will not be added to the output so far.
        """
        sample_module = sklearn.linear_model.__all__
        # sample_module = ['ARDRegression', 'LinearRegression']
        # sample_module = ['RidgeClassifier']
        sigs = signature_scraper.get_signatures(
            sample_module, type_table)
        pprint.pprint(sigs)


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


class TestGenerateFunctionApplications:

    def test_generate(self, linear_regression_signatures):
        """Generate endpoint functions given parameters
        """
        env = Environment(loader=FileSystemLoader('./tests/test_assets'))
        template = env.get_template('endpoint_template.j2')

        all = {}
        all['cwd'] = './cm/cloudmesh-analytics/tests/test_assets/'
        all['sigs'] = linear_regression_signatures
        res = template.render(all=all)
        with open('./tests/test_assets/res.py', 'w') as f:
            f.write(res)
