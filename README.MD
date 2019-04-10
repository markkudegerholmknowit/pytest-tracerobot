# TraceRobot plugin for PyTest

## What is it?

TraceRobot is a Python-based test execution tracer. It outputs Robot Framework
compatible trace log (XML) of the instrumented tests. TraceRobot execution
trace shows which test suites, tests and keywords were run, which parameters
were used for those, what the keywords returned, and what kind of failures
there were, if any.

The generated XML log can be converted into a human-friendly log and report HTML pages
using 'rebot' tool from Robot Framework.

pytest-tracerobot is a Pytest plugin that glues the TraceRobot with PyTest
framework. With this plugin, you get automatic instrumentation of Pytest suites
(test directories and files) and test cases. Keyword-level instrumentation
is done using TraceRobot decorator and base classes.

Sounds complicated? Well, not really. See the examples and you will understand!

## Current status

Current development status is Alpha / PoC phase.
I'm looking for volunteers to assist in development of TraceRobot and this  
plugin.

## Prerequisites

PyTest-TraceRobot needs Python 3, PyPi (pip3) and TraceRobot module.  
TraceRobot module has a dependency to Robot Framework.
PyTest-TraceRobot has been tested with Python 3.5.2 and Robot Framework 3.1.1.

## Installation

First, install the TraceRobot module from
https://github.com/markkudegerholmknowit/tracerobot.git

(This is going to be a PyPi package at some point, but we're not there yet).

Extract the pytest-tracerobot tarball or clone it from github.
In the sources directory, run

sudo -H ./setup.py install

This should also install the other dependencies if necessary.

## Running the example code

After installing the module, you can run the example code under the "example"
directory.

The example code comprises of a SUT (Software Under Testing), and a few
test cases for that. The SUT is a very simple HTTP API stub.

To run the SUT, you will need to have Python "flask" module installed.
Flask is a REST API framework for Python. Use the following command to
install it:

`sudo -H pip3 install flask`

Run the SUT (Software Under testing) in one terminal:

`./gameserver.py`

Then, open an another terminal for running the tests:

`./run.sh`

This script runs both the tests and calls 'rebot' tool from Robot framework
to generate report.html and log.html from the generated output.xml.

If all goes well, you can use your favorite browser to open the report
and/or log documents.

About the sample tests:
  - testgameserver.py has a few simple test cases testing the actual
    gameserver SUT.
  - math.py is an example that illustrates how easy it can be to write
    tests with pytest and pytest-tracerobot at the minimum.

## Writing test suites, test cases and keywords

Based on Robot Framework testing model, TraceRobot inherits the following
basic concepts:
  1 Suite: a collection of tests. There can be one or multiple suites per test run,
    and suites can be nested.
    Suites can have setup and teardown related keywords.
  1 Test case: a single test case. Test cases cannot be nested.
    Test cases can have setup and teardown related keywords.
  1 Keyword: basically any Python function used by a test case. Keywords can
    call other keywords.

With pytest-tracerobot, the suite and test case level instrumentation happens
automatically. To instrument the keywords, you will need to:

  - decorate all functions you want to get traced with @keyword

    OR

  - derive your keyword classes from KeywordClass base class. This will
    automatically instrument all public methods in that class to be keywords.


## What is missing

There are some concepts in PyPi that are not directly transferable to
Robot Framework logs and vice versa. (TBD)

## Acknowledgements

Specials thanks go to Mica Nyholm and Ossi Rajuvaara for feedback and ideas!

I'm also thankful to Robot Framework and PyTest community for producing such
high-quality open-source products.
