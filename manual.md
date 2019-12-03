# Cloudmesh Analytics Manual

## How to Run This Project

The project uses a code generator to generate the web application that exposes the APIs. The generated example is put under the ./manual-files/server.

To launch the server, switch to the directory under the server where contains Dockerfile

```
> username@ cloudmesh-analytics % cd server
```
Build the docker image
```
> username@ server %  docker build -t analytics .
Sending build context to Docker daemon  35.84kB
...
Successfully built cea0ebdf4c85
Successfully tagged analytics:latest
```
Run the project.
```
> username@ server %  docker run -p 8000:5000 analytics
 * Serving Flask app "server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

## Scikit-Learn REST API Generation

### Introduction

Scikit-Learn offers various functionalities related to the machine learning, i.e., the classification model and linear regression model. When it comes to expose its AI functionalities, then repetitively work occurs. 

### A Laborious Example

For example, making two regression methods from the linear model of Scikit-learn, which are the liner regression and logistic regression, involves writing the code in the similar pattern. The examples are based Flask, which is a python web application framework. 
```python
# server.py
from flask import Flask
app = connexion.App(__name__, specification_dir=".")
app.add_api('analytics.yaml')
@app.route('/')
def hello_world():
    return 'Hello, World!'
```

```
# analytics.yaml
...
paths:
  /LinearRegression_constructor/:
      post:
        summary: this is a doc string
        operationId: analytics.LinearRegression_constructor
```

```python
# analytics.py
def LinearRegression_constructor(body):
    try:
        paras = body['paras'] 
        res = LinearRegression(**paras)
    except Exception as e:
        return jsonify({'Error': str(e)})
    return jsonify({'return': 'successfully constructed'})
```
Also, in order to expose the linear regression class as a RESTful interface, one should write the yaml file which defines the routing, and the endpoint function to handle this request.

The example implies that each request to a specific function requires a corresponding definition under the path field in the yaml file. So it is not surprising that will take a large amount of time to write hundreds of functions.

### Automating the Process
Similarly, when adding a the logistic regression, the new endpoint function and corresponding yaml field follow the same pattern, which is shown as,
```
# analytics.yaml
...
paths:
  ...
  /LogisticrRegression_constructor/:
      post:
        summary: this is a doc string
        operationId: analytics.LogisticRegression_constructor
```

```python
# analytics.py
...
def LogisticRegression_constructor(body):
    try:
        paras = body['paras']
        res = LogisticRegression(**paras)
    except Exception as e:
        return jsonify({'Error': str(e)})
    return jsonify({'return': 'successfully constructed'})
```
In order to expose a function as a REST API, there are limited types of functions in the Scikit-learn. Those can be summarized as,

|Function Type/Return|  Yes | No |
|:-----------:|:-------------:|:------:|
|Constructor| object        |\|
|Methods    | getters|setter|
|Property   | attributes|\|

From the table, the function can be a constructor to initialize a new class instance without return value, or getter and setter functions. Some classes have public properties, i.e., LinearRegression.coef_. Therefore, the ways to handle the same types of functions are almost identical, which makes it easier to just write a template for each type of function, and others can be automatically generated.

### Generate the APIs

####  Get Function Signatures

The code generator reads a python module that contains classes, and generate a web application that exposes the functions from the module as REST APIs. 

Function signatures need to be captured before the generation. The signature_scraper class will scrape the functions from a module, and return re-organize signature into a python dict. The shown example reads the signatures of the linear regression class. Note that the complete code example can be found in the Appendix. 

```python
# main.py
from cms_autoapi import SignaturesScraper
import sklearn.linear_model

# The type table
type_table = {
    'matrix': 'array',
    'array': 'array',
    'array-like': 'array',
    'numpy array': 'array',
    'bool': 'boolean',
    'int': 'integer',
    'float': 'number'
}

# The module to read
module = sklearn.linear_model
# The classes to read from the module
classes = ['LinearRegression']
# If type table is specified, it will read all classes in the module
sigs = SignatureScraper().get_signatures(
    module=module,
    classes=classes,
    type_table=type_table)

# The example output of sigs
{0: {'class_name': 'LinearRegression',
     'constructor': {'copy_X': 'bool',
                    'fit_intercept': 'bool',
                    'n_jobs': 'int',
                    'normalize': 'bool'},
     'members': {'fit': {'X': 'list', 'y': 'list'},
                'property': 'property',
                'get_params': {'deep': 'bool'},
                'predict': {'X': 'list'},
                'score': {'X': 'list',
                'sample_weight': 'list', 'y': 'list'}}}}
```

The signature scraper is optional for constructing the signature dictionary. This scraper is designed to parse the signatures from doc strings of sciki-learn classes. The **type table** is required for the signature scraper to search the doc string of functions or classes to match and retrieve the types of parameters due to lacking of types definitions in the signatures. 

However, the type doesn't affect the code generation but for generating more accurate definitions for request bodies in the yaml file. One can write the signature dictionary manually by following the format:
```
{INDEX_NUMBER: {'CLASS_NAME': '',
                'CONSTRUCTOR': {'PARAMETER': 'TYPE'},
                'METHODS': {'PARAMETER': 'TYPE'}}}
```
* The index number refers the class to include
* Constructor refers to the __init__ method of the class
* Defining the formal parameter names as keys and corresponding values as type. **The type is optional but would be used to validate the data from request bodies before passing them to the endpoint functions.**

### Generate Endpoint Functions

```python
# main.py
...
from cms_autoapi import CodeGenerator

# Initialize the code generator
code_gen = CodeGenerator(
        # function signatures
        func_signatures=sigs,
        # the currenting working directory for 
        # the generated web application
        cwd='.',
        # The operation id for paths in the yaml file
        # The function name would follow this prefix
        # such as analytics.LinearRegression
        function_operation_id_root='analytics',
        # The seperated endpoint to file operations
        file_operation_id_root='file',
        # The server url for defining the yaml
        server_url='http://localhost:5000/cloudmesh-analytics',
        # There are built in code template for 
        # generating code
        template_folder='./code_templates',
        # The foler to save the generated file
        output_folder='./build')

# Generate the analytics.py which includes endpoint functions
code_gen.generate_handlers(
    output_name='analytics.py', template_name='handlers.j2')
```

The example demonstrates how to generate the endpoint functions, exported to the *analytics.py* file. For running a flask application. The analytics.yaml file and server.py are required as well.  

```python
...
code_gen.generate_server(
    output_name='server.py', template_name='server.j2')
code_gen.generate_api_specification(
    output_name='analytics.yaml', template_name='component.j2')
```

The series steps will generate a minimal runnable flask web application, which expose the functions defined in the signature dictionary as REST APIs. The settings such as host, or port, routing paths of the server is set by default or automatically generated using the functions and parameters names in the signature dictionary.

### Example Usage

By far the folder tree is shown as, and the example will demonstrate how to fit a linear model and predict the result using the current exposed REST APIs.

```
build
├── analytics.py
├── analytics.yaml
└── server.py
```

1. Launch the server by running the following command

```
> python ./server.py
```

2. Send a request to test whether the server works

```
curl -X POST "http://localhost:8000/cloudmesh-analytics/LinearRegression_constructor/" -H "accept: */*" -H "Content-Type: application/json" -d "{\"paras\":{\"n_jobs\":1}}"
{"return":"successfully constructed"}
```

This example sends a request to construct a linear regression object by specifying  parameters in the json string. It returns the message to indicate the instance is successfully created. 

3. Fit a model

```
curl -X POST "http://localhost:8000/cloudmesh-analytics/LinearRegression_fit/" -H "accept: */*" -H "Content-Type: application/json" -d "{\"paras\":{\"X\":[[1,2]], \"y\":[[3,4]]}}"
{"return":"LinearRegression(copy_X=True, fit_intercept=True, n_jobs=1, normalize=False)"}
```

Fit a model specifying X as [[1,2]] and y as [[3, 4]], the server would response with the signatures of the fitted model

4. Predict

```
curl -X POST "http://localhost:8000/cloudmesh-analytics/LinearRegression_predict/" -H "accept: /" -H "Content-Type: application/json" -d "{"paras":{"X":[[1,2]]}}" 
{"return":"[[3. 4.]]"}
```

The predicate result is [[3, 4]] by applying the fitted model

The value of X and y can be a file name that was uploaded before, for example,

```
curl -X POST "http://localhost:8000/cloudmesh-analytics/file/upload" -H "accept: application/json" -H "Content-Type: multipart/form-data"
```

Then predict by specifying the file name which is the data source

```
curl -X POST "http://localhost:8000/cloudmesh-analytics/LinearRegression_predict/" -H "accept: /" -H "Content-Type: application/json" -d "{"paras":{"X":\"test_upload\"}}" 
{"return":"[[3. 4.]]"}
```


### Generate the Command-Line Interface

To develop the command-line interface working under the existing cloudmesh commands. The code generator is able to generate definitions recognized by docopt. 

```python
# main.py
...
code_gen.generate_command_runner(
    output_name='command.py', template_name='command_runner.j2')
code_gen.generate_command_setting(
    output_name='command_setting.json', template_name='command_setting.j2')
```

The current folder structure is, 

```
command
├── command.py
└── command_setting.json
```

A glance of the generated definition,

```
# command.py
...
analytics LinearRegression[--fit_intercept=VALUE] [--normalize=VALUE] [--copy_X=VALUE] [--n_jobs=VALUE] 
analytics LinearRegression fit [--X=VALUE] [--y=VALUE]  [--sample_weight=VALUE] 
analytics LinearRegression predict [--X=VALUE] 
...
```

Copy and paste the command.py and *command_setting.json* to the cloudmesh/command, then the current folder structure for cloud cloudmesh-analytics is,

```
cloudmesh/analytics
├── __init__.py
├── api
│   ├── __init__.py
│   └── manager.py
└── command
    ├── __init__.py
    ├── command.py
    └── command_setting.json
```

Doing predication is much simpler by typing the following commands,

```
> cms analytics LinearRegression --n_jobs=1 
{"return":"successfully constructed"}
> cms analytics LinearRegression fit --X=[[1,2]] --y=[[3,4]]
{"return":"LinearRegression(copy_X=True, fit_intercept=True, n_jobs=1, normalize=False)"}
> cms analytics LinearRegression predict --X=[[1,2]]
# or cms analytics LinearRegression predict --X=test_upload
{"return":"[[3. 4.]]"}
```

## Appendix

### main.py

```python
"""The main.py generates a web application that exposes the LinearRegression class of Scikit-Learn as REST APIs.
To run this file, put the cms_autoapi.py under the same directory as the main.py

"""
import sklearn.linear_model
from cms_autoapi import SignatureScraper
from cms_autoapi import CodeGenerator

# Type table
type_table = {
    'matrix': 'array',
    'array': 'array',
    'array-like': 'array',
    'numpy array': 'array',
    'bool': 'boolean',
    'int': 'integer',
    'float': 'number'
}

# The module to read
module = sklearn.linear_model
# The classes to read from the module
classes = ['LinearRegression']
# If type table is specified, it will read all classes in the module
sigs = SignatureScraper().get_signatures(
    module=module,
    classes=classes,
    type_table=type_table)

code_gen = CodeGenerator(
        func_signatures=sigs,
        cwd='.',
        function_operation_id_root='analytics',
        file_operation_id_root='file',
        server_url='http://localhost:5000/cloudmesh-analytics',
        template_folder='./code_templates',
        output_folder='./build'
    )
code_gen.generate_command_runner(
    output_name='command_runner.py', template_name='command_runner.j2')
code_gen.generate_command_setting(
    output_name='command_setting.json', template_name='command_setting.j2')
code_gen.generate_handlers(
    output_name='analytics.py', template_name='handlers.j2')
code_gen.generate_command_definitions(
    output_name='command_docstring.py', template_name='command_docstring.j2')
code_gen.generate_api_specification(
    output_name='analytics.yaml', template_name='component.j2')
code_gen.generate_file_operations(
    output_name='file.py', template_name='file.j2')
code_gen.generate_server(
    output_name='server.py', template_name='server.j2')
```
