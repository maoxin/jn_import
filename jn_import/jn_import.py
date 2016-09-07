import os
import sys
import types
from IPython import get_ipython
from nbformat import read
from IPython.core.interactiveshell import InteractiveShell


def find_notebook(fullname, path=None):
    """
    find a notebook, given its fully qualified name and an optional path
    """
    print("path in find_notebook: {}".format(path))
    print("fullname in find_notebook: {}".format(fullname))
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path


class NotebookLoader(object):
    """
    Module Loader for Jupyter Notebooks
    """

    def __init__(self, path=None):
        print("path in Loader: {}".format(path))
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        path = find_notebook(fullname, self.path)
        print("fullname in Loader: {}".format(fullname))

        print("importing Jupyter notebook from {}".format(path))

        # load the notebook object
        with open(path, 'r', encoding='utf-8') as f:
            nb = read(f, 4)

        # create the module and add it to sys.modules
        # if name in sys.moduls:
        #    return sys.moduls[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__dict__['get_ipython'] = get_ipython
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(cell.source)
                    # run the code in the module
                    exec(code, mod.__dict__)

        finally:
            self.shell.user_ns = save_user_ns
        return mod


class NotebookFinder(object):
    """Module finder that locates Jupyter Notebooks"""

    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        print('path in Finder: {}'.format(path))
        print("fullname in Finder: {}".format(fullname))
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]

sys.meta_path.append(NotebookFinder())
