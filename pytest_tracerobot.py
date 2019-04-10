import os
import pytest
import tracerobot

HOOK_DEBUG=True

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

    # Reporting hooks

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):

        scope = fixturedef.scope    # 'function', 'class', 'module', 'session'

        if HOOK_DEBUG:
            print("pytest_fixture_setup", fixturedef, request, request.node);

        if scope == 'function':
            item = request.node
            markers = [marker.name for marker in item.iter_markers()]

            print("handle_per_function_fixture start_test")
            test = tracerobot.start_test(
                name=item.name,
                tags=markers)
            tracerobot.set_test_phase("setup")
            item.rt_test_info = test

            yield
        else:
            fixture = tracerobot.start_keyword(
                name=fixturedef.argname
            )

            # TODO: This might raise, handle it?
            outcome = yield

            result = outcome.get_result()
            tracerobot.end_keyword(fixture, result)


    def pytest_runtest_call(self, item):
        pass

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

        #call.when: (post)"setup", (post)"call", (post)"teardown"
        #note: setup and teardown are called even if a test has no fixture

        markers = [marker.name for marker in item.iter_markers()]

        if HOOK_DEBUG:
            print("pytest_runtest_makereport", item, markers, call);

        if call.when == "setup":
            # start test unless already started by test fixture
            try:
                dummy = item.rt_test_info
            except AttributeError:
                print(" makereport start_test")
                item.rt_test_info = tracerobot.start_test(item.name)

            # setup phase in now finished, actual test will follow
            tracerobot.set_test_phase("test")

            if call.excinfo:
                # todo: now it's not possible to see if the problem was with the
                # setup or teardown
                error_msg = call.excinfo.exconly()
                tracerobot.end_test(item.rt_test_info, error_msg)
                item.rt_test_info = None

        # pytest_runtest_call(item) gets called between "setup" and "call"

        elif call.when == "call":
            if call.excinfo:
                item.error_msg = call.excinfo.exconly()

            tracerobot.set_test_phase("teardown")
            pass

        elif call.when == "teardown":
            if item.rt_test_info:

                error_msg = None
                if item.error_msg:
                    error_msg = item.error_msg
                elif call.excinfo:
                    # todo: now it's not possible to see if the problem was with the
                    # setup or teardown
                    error_msg = call.excinfo.exconly()

                tracerobot.end_test(item.rt_test_info, error_msg)



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
