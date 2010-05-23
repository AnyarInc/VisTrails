############################################################################
##
## Copyright (C) 2006-2010 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
""" Module used when running  vistrails uninteractively """
import os.path
import uuid
import core.interpreter.default
import core.db.io
from core.configuration import get_vistrails_configuration
from core.db.io import load_vistrail
from core.db.locator import XMLFileLocator, ZIPFileLocator
from core.utils import VistrailsInternalError, expression
from core.vistrail.controller import VistrailController
from core.vistrail.vistrail import Vistrail

################################################################################
    
def run_and_get_results(w_list, parameters='', workflow_info=None, 
                        update_vistrail=False, extra_info=None):
    """run_and_get_results(w_list: list of (locator, version), parameters: str,
                           workflow_info:str, update_vistrail: boolean)
    Run all workflows in w_list, and returns an interpreter result object.
    version can be a tag name or a version id.
    
    """
    elements = parameters.split("&")
    aliases = {}
    result = []
    for locator, workflow in w_list:
        (v, abstractions , thumbnails)  = load_vistrail(locator)
        controller = VistrailController()
        controller.set_vistrail(v, locator, abstractions, thumbnails)
        if type(workflow) == type("str"):
            version = v.get_version_number(workflow)
        elif type(workflow) in [ type(1), long]:
            version = workflow
        elif workflow is None:
            version = controller.get_latest_version_in_graph()
        else:
            msg = "Invalid version tag or number: %s" % workflow
            raise VistrailsInternalError(msg)
        controller.change_selected_version(version)
        
        for e in elements:
            pos = e.find("=")
            if pos != -1:
                key = e[:pos].strip()
                value = e[pos+1:].strip()
            
                if controller.current_pipeline.has_alias(key):
                    aliases[key] = value
                    
        if workflow_info is not None and controller.current_pipeline is not None:
            from gui.pipeline_view import QPipelineView
            pipeline_view = QPipelineView()
            pipeline_view.scene().setupScene(controller.current_pipeline)
            base_fname = "%s_%s_pipeline.pdf" % (locator.short_name, version)
            filename = os.path.join(workflow_info, base_fname)
            pipeline_view.scene().saveToPDF(filename)
            del pipeline_view

            base_fname = "%s_%s_pipeline.xml" % (locator.short_name, version)
            filename = os.path.join(workflow_info, base_fname)
            core.db.io.save_workflow(controller.current_pipeline, filename)
        if not update_vistrail:
            conf = get_vistrails_configuration()
            if conf.has('thumbs'):
                conf.thumbs.autoSave = False    
        (results, _) = controller.execute_current_workflow(aliases,
                                                                 extra_info)
        run = results[0]
        run.workflow_info = (locator.name, version)
        run.pipeline = controller.current_pipeline
        

        #not sure if you need to add the abstractions back
        #but just to be safe
        if update_vistrail:
            controller.write_vistrail(locator)
        result.append(run)
    return result
    
def run(w_list, parameters='', workflow_info=None, update_vistrail=False,
        extra_info=None):
    """run(w_list: list of (locator, version), parameters: str) -> boolean
    Run all workflows in w_list, version can be a tag name or a version id.
    Returns list of errors (empty list if there are no errors)
    """
    all_errors = []
    results = run_and_get_results(w_list, parameters, workflow_info, 
                                  update_vistrail,extra_info)
    for result in results:
        (objs, errors, executed) = (result.objects,
                                    result.errors, result.executed)
        for err in sorted(errors.iteritems()):
            all_errors.append(result.workflow_info + err)
    return all_errors

def cleanup():
    core.interpreter.cached.CachedInterpreter.cleanup()

################################################################################
#Testing

import core.packagemanager
import core.system
import sys
import unittest
import core.vistrail
import random
from core.vistrail.module import Module

class TestConsoleMode(unittest.TestCase):

    def setUp(self, *args, **kwargs):
        manager = core.packagemanager.get_package_manager()
        if manager.has_package('edu.utah.sci.vistrails.console_mode_test'):
            return

#         m = __import__('console_mode_test')
#         sys.path = old_path
        old_path = sys.path
        sys.path.append(core.system.vistrails_root_directory() +
                        '/tests/resources')
#         d = {'console_mode_test': 'tests.resources.'}
        manager.add_package('console_mode_test')
        manager.initialize_packages()
        sys.path = old_path

    def test1(self):
        locator = XMLFileLocator(core.system.vistrails_root_directory() +
                                 '/tests/resources/dummy.xml')
        result = run([(locator, "int chain")])
        self.assertEqual(len(result), 0)

    def test_tuple(self):
        from core.vistrail.module_param import ModuleParam
        from core.vistrail.module_function import ModuleFunction
        from core.vistrail.module import Module
        from core.utils import DummyView
        interpreter = core.interpreter.default.get_default_interpreter()
        v = DummyView()
        p = core.vistrail.pipeline.Pipeline()
        params = [ModuleParam(type='Float',
                              val='2.0',
                              ),
                  ModuleParam(type='Float',
                              val='2.0',
                              )]
        p.add_module(Module(id=0,
                           name='TestTupleExecution',
                           package='edu.utah.sci.vistrails.console_mode_test',
                           functions=[ModuleFunction(name='input',
                                                     parameters=params)],
                           ))
        kwargs = {'locator': XMLFileLocator('foo'),
                  'current_version': 1L,
                  'view': v,
                  }
        interpreter.execute(p, **kwargs)

    def test_python_source(self):
        locator = XMLFileLocator(core.system.vistrails_root_directory() +
                                 '/tests/resources/pythonsource.xml')
        result = run([(locator,"testPortsAndFail")])
        self.assertEqual(len(result), 0)

    def test_python_source_2(self):
        locator = XMLFileLocator(core.system.vistrails_root_directory() +
                                 '/tests/resources/pythonsource.xml')
        result = run_and_get_results([(locator, "test_simple_success")])[0]
        self.assertEquals(len(result.executed), 1)

    def test_dynamic_module_error(self):
        locator = XMLFileLocator(core.system.vistrails_root_directory() + 
                                 '/tests/resources/dynamic_module_error.xml')
        result = run([(locator, "test")])
        self.assertNotEqual(len(result), 0)

    def test_change_parameter(self):
        locator = XMLFileLocator(core.system.vistrails_root_directory() + 
                                 '/tests/resources/test_change_vistrail.xml')
        result = run([(locator, "v1")])
        self.assertEqual(len(result), 0)

        result = run([(locator, "v2")])
        self.assertEquals(len(result), 0)

    def test_ticket_73(self):
        # Tests serializing a custom-named module to disk
        locator = XMLFileLocator(core.system.vistrails_root_directory() + 
                                 '/tests/resources/test_ticket_73.xml')
        v = locator.load()

        import tempfile
        import os
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        locator = XMLFileLocator(filename)
        try:
            locator.save(v)
        finally:
            os.remove(filename)

if __name__ == '__main__':
    unittest.main()
