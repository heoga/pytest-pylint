# -*- coding: utf-8 -*-
"""
Unit testing module for pytest-pylti plugin
"""
import sys

pytest_plugins = 'pytester',  # pylint: disable=invalid-name


def test_basic(testdir):
    """Verify basic pylint checks"""
    testdir.makepyfile("""import sys""")
    result = testdir.runpytest('--pylint')
    assert 'Missing module docstring' in result.stdout.str()
    assert 'Unused import sys' in result.stdout.str()
    assert 'Final newline missing' in result.stdout.str()
    assert 'passed' not in result.stdout.str()


def test_error_control(testdir):
    """Verify that error types are configurable"""
    testdir.makepyfile("""import sys""")
    result = testdir.runpytest('--pylint', '--pylint-error-types=EF')
    assert '1 passed' in result.stdout.str()


def test_pylintrc_file(testdir):
    """Verify that a specified pylint rc file will work."""
    rcfile = testdir.makefile('rc', """
[FORMAT]

max-line-length=3
""")
    testdir.makepyfile("""import sys""")
    result = testdir.runpytest(
        '--pylint', '--pylint-rcfile={0}'.format(rcfile.strpath)
    )
    assert 'Line too long (10/3)' in result.stdout.str()


def test_pylintrc_file_beside_ini(testdir):
    """
    Verify that a specified pylint rc file will work what placed into pytest
    ini dir.
    """
    non_cwd_dir = testdir.mkdir('non_cwd_dir')

    rcfile = non_cwd_dir.join('foo.rc')
    rcfile.write("""
[FORMAT]

max-line-length=3
""")

    inifile = non_cwd_dir.join('foo.ini')
    inifile.write("""
[pytest]
addopts = --pylint --pylint-rcfile={0}
""".format(rcfile.basename))

    pyfile = testdir.makepyfile("""import sys""")

    result = testdir.runpytest(
        pyfile.strpath
    )
    assert 'Line too long (10/3)' not in result.stdout.str()

    result = testdir.runpytest(
        '-c', inifile.strpath, pyfile.strpath
    )
    assert 'Line too long (10/3)' in result.stdout.str()


def test_pylintrc_ignore(testdir):
    """Verify that a pylintrc file with ignores will work."""
    rcfile = testdir.makefile('rc', """
[MASTER]

ignore = test_pylintrc_ignore.py
""")
    testdir.makepyfile("""import sys""")
    result = testdir.runpytest(
        '--pylint', '--pylint-rcfile={0}'.format(rcfile.strpath)
    )
    assert 'collected 0 items' in result.stdout.str()


def test_pylintrc_msg_template(testdir):
    """Verify that msg-template from pylintrc file is handled."""
    rcfile = testdir.makefile('rc', """
[REPORTS]

msg-template=start {msg_id} end
""")
    testdir.makepyfile("""import sys""")
    result = testdir.runpytest(
        '--pylint', '--pylint-rcfile={0}'.format(rcfile.strpath)
    )
    assert 'start W0611 end' in result.stdout.str()


def test_tracer_disabled(testdir):
    """Verify basic pylint checks"""
    class Tracer(object):
        """A dummy tracer which just counts how many times it was called."""
        calls = 0

        def tracer(self, _frame, _event, _arg):
            """The tracer which counts calls only."""
            self.calls = self.calls + 1

        def reset_calls(self):
            """Resets the call count of the tracer to zero."""
            self.calls = 0

    test_tracer = Tracer()
    sys.settrace(test_tracer.tracer)

    testdir.makepyfile("""import sys""")
    result = testdir.runpytest('--pylint')
    expected_lines = (
        'Missing module docstring',
        'Unused import sys',
        'Final newline missing',
    )
    for line in expected_lines:
        assert line in result.stdout.str()
    assert 'passed' not in result.stdout.str()
    original_calls = test_tracer.calls

    test_tracer.reset_calls()
    off_result = testdir.runpytest('--pylint', '--pylint-pause-tracer')
    for line in expected_lines:
        assert line in off_result.stdout.str()
    assert 'passed' not in off_result.stdout.str()
    new_calls = test_tracer.calls
    assert new_calls < 0.8 * original_calls
