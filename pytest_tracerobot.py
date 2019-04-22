import os
import pytest
import tracerobot


def common_items(iter1, iter2):
    common = []
    for first, second in zip(iter1, iter2):
        if first != second:
            break
        common.append(first)
    return common


class TraceRobotPlugin:
    def __init__(self, config):
        print("__init__")

        self.config = config
        self._stack = []

    @property
    def current_path(self):
        return [path for path, _ in self._stack]

    def _start_suite(self, name):
        # TODO: How to get meaningful suite docstring/metadata/source?
        suite = tracerobot.start_suite(name)
        self._stack.append((name, suite))

    def _end_suite(self):
        _, suite = self._stack.pop(-1)
        tracerobot.end_suite(suite)

    # Initialization hooks

    def pytest_sessionstart(self, session):
        print("pytest_sessionstart")
        output_path = self.config.getoption('robot_output')
        tracerobot.configure(logfile=output_path)

    def pytest_sessionfinish(self, session, exitstatus):
        while self._stack:
            self._end_suite()

        tracerobot.close()

    # Test running hooks

    def pytest_runtest_logstart(self, nodeid, location):
        """Each directory and test file maps to a Robot Framework suite.
        Because pytest doesn't seem to provide hook for entering/leaving
        suites as such, the current suite must be determined before each test.
        """
        filename, linenum, testname = location

        target = filename.split(os.sep)
        common = common_items(self.current_path, target)

        while len(self.current_path) > len(common):
            self._end_suite()

        assert self.current_path == common

        while len(self.current_path) < len(target):
            name = target[len(self.current_path)]
            self._start_suite(name)

        assert self.current_path == target

    def pytest_runtest_call(self, item):
        markers = [marker.name for marker in item.iter_markers()]

        # TODO: Store in plugin instead of test object?
        item.rt_test_info = tracerobot.start_test(
            name=item.name,
            tags=markers)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item, nextitem):
        # TODO: Figure out how to wrap around individual fixture teardowns
        # All fixture teardowns run during yield (if they exist)

        # Might have to re-implement pytest_runtest_teardown from _pytest.runner
        # or do some ugly monkeypatching of the Session, like this:
        #
        # def monkey_finalizer(self, colitem):
        #     ... call finalizers and wrap them here ...
        #
        # import types
        # state = item.session._setupstate
        # state._callfinalizers = types.MethodType(monkey_finalizer, state)
        #
        yield

    def pytest_runtest_makereport(self, item, call):
        if not call.when == 'call':
            return

        if call.excinfo:
            error_msg = call.excinfo.exconly()
        else:
            error_msg = None

        tracerobot.end_test(item.rt_test_info, error_msg)

    # Reporting hooks

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        fixture = tracerobot.start_keyword(
            name=fixturedef.argname,
            type='setup'
        )

        outcome = yield

        # TODO: This might raise, handle it
        result = outcome.get_result()
        tracerobot.end_keyword(fixture, result)


def pytest_addoption(parser):
    group = parser.getgroup('tracerobot')
    group.addoption(
        '--robot-output',
        default='output.xml',
        help='Path to Robot Framework XML output'
    )


def pytest_configure(config):
    print("pytest_configure")
    plugin = TraceRobotPlugin(config)
    config.pluginmanager.register(plugin)
