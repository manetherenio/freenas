class ListenDelegate:
    """
    Represents something (e.g. service) that needs to be handle a deletion of a static IP address from the system.
    """

    async def get_listen_state(self):
        """
        Returns a state object that will be passed to subsequent functions.
        """
        raise NotImplementedError

    async def set_listen_state(self, state):
        """
        Set to listen on the addresses from the state.
        """
        raise NotImplementedError

    async def listens_on(self, state, ip):
        """
        Checks if we are listening on an IP address.
        """
        raise NotImplementedError

    async def reset_listens(self):
        """
        Listen on all IP addresses.
        """
        raise NotImplementedError


class ServiceListenDelegate(ListenDelegate):
    """
    Service listening on IP address.
    """

    def __init__(self, middleware, plugin, field):
        self.middleware = middleware
        self.plugin = plugin
        self.field = field

    @property
    def service(self):
        return self.middleware.get_service(self.plugin)._config.service

    async def get_listen_state(self):
        config = await self.middleware.call(f"{self.plugin}.config")
        return config[self.field]

    async def set_listen_state(self, state):
        await self.middleware.call(f"{self.plugin}.update", {self.field: state})


class ServiceListenSingleDelegate(ServiceListenDelegate):
    """
    Service listening on a single IP address.
    """

    def __init__(self, *args, empty_value="0.0.0.0"):
        super().__init__(*args)
        self.empty_value = empty_value

    async def listens_on(self, state, ip):
        return state == ip

    async def reset_listens(self):
        await self.set_listen_state(self.empty_value)


class ServiceListenMultipleDelegate(ServiceListenDelegate):
    """
    Service listening on multiple IP addresses.
    """

    async def listens_on(self, state, ip):
        return ip in state

    async def reset_listens(self):
        await self.set_listen_state([])
