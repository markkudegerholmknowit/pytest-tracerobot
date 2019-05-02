import os
import pytest
import traceback
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

    def _get_error_msg(self, call):
        if call and call.excinfo:
            print("error:", call.excinfo)
            if False:
                excinfo = traceback.format_exception(
                    call.excinfo.type,
                    call.excinfo.value,
                    call.excinfo.tb,
                    5)
                return '\n'.join(excinfo)
            return str(call.excinfo.getrepr(style="short"))

        else:
            return None

    def _is_test_started(self, item):
        try:
            item.rt_test_info
            return True
        except AttributeError:
            return False

    def _is_test_with_setup_and_teardown(self, item):
        try:
            return item.rt_test_with_setup_and_teardown
        except AttributeError:
            return False

    def _has_test_setup(self, item):
        try:
            item.rt_test_setup_info
            return True
        except AttributeError:
            return False

    def _has_test_body(self, item):
        try:
            item.rt_test_body_info
            return True
        except AttributeError:
            return False

    def _has_test_teardown(self, item):
        try:
            item.rt_test_teardown_info
            return True
        except AttributeError:
            return False

    def _start_test_envelope(self, item, with_setup_and_teardown=False):
        """ test envelope is either
                keyword("setup") + keyword("test body") + keyword("teardown")
            or just
                test body
                """
        if self._is_test_started(item):
            return

        markers = [marker.name for marker in item.iter_markers()]

        print("start test envelope")
        item.rt_test_info = tracerobot.start_test(
            name=item.name,
            tags=markers)
        item.rt_test_with_setup_and_teardown = with_setup_and_teardown

    def _start_test_setup(self, item, fixturedef):
        assert(self._is_test_with_setup_and_teardown)

        if self._has_test_setup(item):
            self._finish_test_setup(item)

        print("start test setup")
        item.rt_test_setup_info = tracerobot.start_keyword(
            fixturedef.argname, "setup")

    def _finish_test_setup(self, item, call=None):
        if self._has_test_setup(item):
            error_msg = self._get_error_msg(call)
            print("finish test setup")
            tracerobot.end_keyword(item.rt_test_setup_info, error_msg)
            item.rt_test_setup_info = None

    def _start_test_body(self, item):
        assert(self._is_test_with_setup_and_teardown)
        print("start test body")
        item.rt_test_body_info = tracerobot.start_keyword(item.name, "kw")

    def _finish_test_body(self, item, call=None):
        if self._has_test_body(item):
            print("finish test body")
            error_msg = self._get_error_msg(call)
            tracerobot.end_keyword(item.rt_test_body_info, error_msg=error_msg)
            item.rt_test_body_info = None

    def _start_test_teardown(self, item):
        assert(self._is_test_with_setup_and_teardown)
        print("start test teardown")
        item.rt_test_teardown_info = tracerobot.start_keyword(
            "fixture(s)", "teardown")

    def _finish_test_teardown(self, item, call=None):
        if self._has_test_teardown(item):
            print("finish test teardown")
            error_msg = self._get_error_msg(call)
            tracerobot.end_keyword(item.rt_test_teardown_info, error_msg)
            item.rt_test_teardown_info = None

    def _finish_test_envelope(self, item, call=None):
        if self._is_test_started(item):
            print("start test envelope")
            error_msg = self._get_error_msg(call)
            tracerobot.end_test(item.rt_test_info, error_msg)
            item.rt_test_info = None


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

            self._start_test_envelope(
                item, with_setup_and_teardown=True)
            self._start_test_setup(item, fixturedef)

            yield
        else:
            fixture = tracerobot.start_keyword(
                name=fixturedef.argname
            )

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


        if HOOK_DEBUG:
            print("pytest_runtest_makereport", item, call);

        if call.when == "setup":
            #  finish setup phase (if any), start test body

            if self._is_test_with_setup_and_teardown(item):
                self._finish_test_setup(item, call)
                if call.excinfo:
                    # setup failed, test aborted
                    self._finish_test_envelope(item, call)
                else:
                    self._start_test_body(item)
            else:
                self._start_test_envelope(item)

        # pytest_runtest_call(item) gets called between "setup" and "call"

        elif call.when == "call":
            if self._is_test_with_setup_and_teardown(item):
                self._finish_test_body(item, call)
                self._start_test_teardown(item)
            else:
                self._finish_test_envelope(item, call)

            #tracerobot.set_test_phase("teardown")

        elif call.when == "teardown":
            if self._is_test_with_setup_and_teardown(item):
                self._finish_test_teardown(item, call)
                self._finish_test_envelope(item, call)


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
