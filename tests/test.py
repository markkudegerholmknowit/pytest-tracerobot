from tracerobot.decorators import keyword, KeywordClass
import requests
import pytest

@keyword
def rlog(msg):
    """ A dummy function that injects msg into trace log """
    pass

@keyword
def check_sum(a,b,result):
    assert a + b == result

@pytest.fixture
def fixtureWithSetup():
    rlog("setup")

@pytest.fixture
def fixtureWithSetupAndTeardown1():
    rlog("setup")
    yield
    rlog("teardown")

@pytest.fixture
def fixtureWithSetupAndTeardown2():
    rlog("setup2")
    yield
    rlog("teardown2")

@pytest.fixture(scope="module")
def moduleFixture():
    rlog("module setup")
    yield
    rlog("module teardown")

@pytest.fixture
def fixtureWithSetupError():
    assert False

@pytest.fixture
def fixtureWithTeardownError():
    rlog("setup")
    yield
    assert False


@pytest.fixture
def testFixture2():
    rlog("setup2")
    yield
    rlog("teardown2")

@pytest.mark.critical
def test_passing_test():
    """ A simple passing test """
    check_sum(1,2,3)

@pytest.mark.critical
def test_direct_assert():
    """ A test that fails with inlined assertion error """
    rlog("here!")
    raise AssertionError("foo")

@pytest.mark.critical
def test_keyword_assert():
    """ A test that fails within keyword """
    check_sum(1,2,4)

@pytest.mark.critical
def test_fixture_setup(fixtureWithSetup):
    """ A test with a fixture with a setup """
    rlog("here")

@pytest.mark.critical
def test_fixture_setup_and_teardown(fixtureWithSetupAndTeardown1):
    """ A test with passing fixture setup and teardown """
    rlog("here")

@pytest.mark.critical
def test_two_fixtures(fixtureWithSetupAndTeardown1, fixtureWithSetupAndTeardown2):
    """ A test with two function-scoped fixtures """
    rlog("here")

@pytest.mark.critical
def test_module_and_test_fixtures(moduleFixture, fixtureWithSetupAndTeardown1):
    """ A test with one module-scoped and one function-scoped fixture """
    rlog("here")

@pytest.mark.critical
def test_setup_assert(fixtureWithSetupError):
    """ A test that fails in fixture setup phase """
    rlog("here")

@pytest.mark.critical
def test_teardown_assert(fixtureWithTeardownError):
    """ A test that fails in fixture teardown phase """
    rlog("here")
