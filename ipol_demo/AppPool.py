
import threading


class AppPool(object):
    """
    App object pool used by the init_func decorator to
    obtain instances of the app object
    Used to fix a bug
    https://tools.ipol.im/mailman/archive/discuss/2012-December/000969.html
    """

    pool_lock = threading.Lock()

    class __AppPool(object):
        """
        App Pool singleton pattern implementation
        """
        pool = {}

        def pool_tidyup(self):
            """
            Removes old app objects from the pool, to save memory
            """
            keys_to_remove = []
            # Get keys of the objects to remove
            for key in self.pool.keys():
                entry = self.pool[key]
                timestamp = entry['timestamp']
                if time.time() - timestamp > 7200: # two hours
                    keys_to_remove.append(key)
            # Remove old objects
            for key in keys_to_remove:
                del self.pool[key]
            

        def get_app(self, exec_id):
            """
            Obtains the app object associated to the exec_id ID
            """
            if exec_id in self.pool:
                return self.pool[exec_id]['app_object']
            else:
                return None

        def add_app(self, exec_id, app_object):
            """
            Adds an app object and to the pool.
            The creation time is also stored
            """
            # Remove stored old app objects
            self.pool_tidyup()
            # Add app_object and timestamp
            entry = {'app_object': app_object,
                     'timestamp': time.time()}
            self.pool[exec_id] = entry

    # Singleton object instance
    instance = None

    @staticmethod
    def get_instance():
        """
        Get an app pool singleton instance
        """

        try:
            # Acquire lock
            AppPool.pool_lock.acquire()

            # Set singleton object instance
            if AppPool.instance is None:
                AppPool.instance = AppPool.__AppPool()
        finally:
            # Release lock
            AppPool.pool_lock.release()

        return AppPool.instance
