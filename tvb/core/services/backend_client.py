# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
"""
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>
.. moduleauthor:: Yann Gordon <yann@invalid.tvb>
"""
import Queue
import threading
from subprocess import Popen, PIPE
from tvb.basic.profile import TvbProfile as tvb_profile
from tvb.basic.config.settings import TVBSettings as config
from tvb.basic.logger.builder import get_logger
from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.core.services.workflowservice import WorkflowService
import tvb.core.utils as utils


LOGGER  = get_logger(__name__)
CURRENT_ACTIVE_THREADS = []
LOCKS_QUEUE = Queue.Queue(0)
for i in range(config.MAX_THREADS_NUMBER):
    LOCKS_QUEUE.put(1)
    
    

def run_cluster_job(operation_id, user_name_label):
    """
    Threaded Popen
    It is the function called by the Stand Alone client in a Thread.
    This function executes a new process with the command "sublist"
    """
    call_arg = config.CLUSTER_SCHEDULE_COMMAND % (operation_id, user_name_label)
    proc = Popen([call_arg], stdout=PIPE, shell=True)
    job_id = proc.stdout.read().replace('\n', '').split('OAR_JOB_ID=')[-1]
    LOGGER.debug("Storing job identifier=%s for operation id=%s launched on cluster."%(operation_id, job_id))
    op_ident = model.OperationProcessIdentifier(operation_id, job_id=job_id)
    dao.store_entity(op_ident)
    

class ClusterSchedulerClient(object):
    """
    Simple class, to mimic the same behavior we are expecting from ServerProxy.
    """
    
    @staticmethod
    def execute(operation_id, user_name_label='Unknown'):
        """Call the correct system command to submit a job to the cluster."""
        thread = threading.Thread(target=run_cluster_job, kwargs={'operation_id' : operation_id,
                                                                  'user_name_label' : user_name_label})
        thread.start()


class OperationExecutor(threading.Thread):
    """
    Thread in charge for starting an operation.
    """
    
    def __init__(self, op_id, label):
        threading.Thread.__init__(self)
        self.operation_id = op_id
        self.user_name_label = label  
        self._stop = threading.Event()
        
    def run(self):
        """
        Get the required data from the operation queue and launch the operation.
        """
        #Try to get a spot to launch own operation.
        LOCKS_QUEUE.get(True)
        operation_id = self.operation_id
        user_name_label = self.user_name_label
        oper = [config().get_python_path(), '-m',
                'tvb.core.cluster_launcher', str(operation_id), user_name_label]
        if tvb_profile.CURRENT_SELECTED_PROFILE is not None:
            oper.extend([tvb_profile.SUBPARAM_PROFILE, tvb_profile.CURRENT_SELECTED_PROFILE])

        if self.stopped() is False:
            launched_process = Popen(oper, stdout=PIPE, stderr=PIPE)
            LOGGER.debug("Storing pid=%s for operation id=%s launched on local machine."%(operation_id, 
                                                                                          launched_process.pid))
            op_ident = model.OperationProcessIdentifier(operation_id, pid=launched_process.pid)
            dao.store_entity(op_ident)
            if self.stopped():
                #In the exceptional case where both the thread stop and the os.kill() called from 
                #operation service are somehow done between the self.stopped() check and the popen call
                utils.stop_pid(launched_process.pid)
            launched_process.communicate()
            LOGGER.debug("====================================================")
            LOGGER.debug("Finished with launch of operation %s"%(operation_id,))
            returned = launched_process.wait()
            if returned != 0 and not self.stopped():
                # Process did not end as expected. (e.g. Segmentation fault)
                operation = dao.get_operation_by_id(self.operation_id)
                LOGGER.error("Operation suffered fatal failure with exit code: %s" % returned)
                message = "Operation failed unexpectedly. Probably untracked segmentation fault."
                operation.mark_complete(model.STATUS_ERROR, message)
                dao.store_entity(operation)
                burst_entity = dao.get_burst_for_operation_id(self.operation_id)
                if burst_entity:
                    message = "Error on burst operation. Probably untracked segmentation fault."
                    WorkflowService().mark_burst_finished(burst_entity, error=True, error_message=message)
            del launched_process
        else:
            operation = dao.get_operation_by_id(self.operation_id)
            operation.mark_cancelled()
            dao.store_entity(operation)
        #Give back empty spot now that you finished your operation
        CURRENT_ACTIVE_THREADS.remove(self)
        LOCKS_QUEUE.put(1)


    def stop(self):
        """ Mark current thread for stop"""
        self._stop.set()
        
    def stopped(self):
        """Check if current thread was marked for stop."""
        return self._stop.isSet()

            
class StandAloneClient(object):
    """
    Instead of communicating with a back-end cluster, fire locally a new thread.
    """
    @staticmethod
    def execute(operation_id, user_name_label="Unknown"):
        """Start asynchronous operation locally"""
        thread = OperationExecutor(operation_id, user_name_label)
        CURRENT_ACTIVE_THREADS.append(thread)
        thread.start()
     
    @staticmethod   
    def stop_operation(operation_id):
        """ Stop a thread for a given operation id """
        for thread in CURRENT_ACTIVE_THREADS:
            if int(thread.operation_id) == operation_id:
                thread.stop()
    
    @staticmethod        
    def stop_operations(operation_ids):
        """ Stop a thread for a given operation id """
        any_stopped = False
        for thread in CURRENT_ACTIVE_THREADS:
            if int(thread.operation_id) in operation_ids:
                thread.stop()
                any_stopped = True
        return any_stopped



if config.DEPLOY_CLUSTER:
    #Return an entity capable to submit jobs to the cluster.
    BACKEND_CLIENT = ClusterSchedulerClient()
else:
    #Return a thread launcher.
    BACKEND_CLIENT = StandAloneClient()

